"""Migration Core Infrastructure for Knowledge Graph Relationships.

This module provides the foundation for migrating relationship data between different
schema versions, with comprehensive transaction management, rollback capabilities,
and progress tracking. It implements base migration classes with validation hooks,
error handling, and batch processing support.

Key Features:
- MigrationManager class with full transaction support
- Base migration classes with validation and error handling
- Comprehensive logging and state management
- Rollback capabilities for safe migration operations
- Batch processing for large datasets
- Progress tracking and reporting
"""

import logging
import json
import uuid
import difflib
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union
from contextlib import contextmanager

import transaction
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from plone import api
from plone.api.exc import InvalidParameterError
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from ZODB.POSException import ConflictError

logger = logging.getLogger("knowledge.curator.migration")


class MigrationError(Exception):
    """Base exception for migration errors."""
    pass


class MigrationValidationError(MigrationError):
    """Exception for validation errors during migration."""
    pass


class MigrationTransactionError(MigrationError):
    """Exception for transaction-related errors."""
    pass


class MigrationRollbackError(MigrationError):
    """Exception for rollback-related errors."""
    pass


class MigrationState:
    """Enumeration of migration states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PAUSED = "paused"


class MigrationProgress:
    """Class to track migration progress and statistics."""
    
    def __init__(self, total_items: int = 0):
        self.total_items = total_items
        self.processed_items = 0
        self.successful_items = 0
        self.failed_items = 0
        self.skipped_items = 0
        self.start_time = None
        self.end_time = None
        self.current_batch = 0
        self.total_batches = 0
        self.errors = []
        self.warnings = []
        
    def start(self):
        """Mark the start of migration."""
        self.start_time = datetime.now()
        
    def finish(self):
        """Mark the end of migration."""
        self.end_time = datetime.now()
        
    def add_success(self, item_id: str = None, details: str = None):
        """Record a successful migration."""
        self.processed_items += 1
        self.successful_items += 1
        if details:
            logger.debug(f"Success migrating {item_id}: {details}")
            
    def add_failure(self, item_id: str, error: str, exception: Exception = None):
        """Record a failed migration."""
        self.processed_items += 1
        self.failed_items += 1
        self.errors.append({
            'item_id': item_id,
            'error': error,
            'exception': str(exception) if exception else None,
            'timestamp': datetime.now().isoformat()
        })
        logger.error(f"Failed migrating {item_id}: {error}")
        
    def add_skip(self, item_id: str, reason: str):
        """Record a skipped migration."""
        self.processed_items += 1
        self.skipped_items += 1
        logger.info(f"Skipped migrating {item_id}: {reason}")
        
    def add_warning(self, item_id: str, warning: str):
        """Record a warning during migration."""
        self.warnings.append({
            'item_id': item_id,
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        })
        logger.warning(f"Warning for {item_id}: {warning}")
        
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_items == 0:
            return 100.0
        return (self.processed_items / self.total_items) * 100.0
        
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100.0
        
    @property
    def duration(self) -> Optional[float]:
        """Calculate migration duration in seconds."""
        if not self.start_time:
            return None
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary for serialization."""
        return {
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'skipped_items': self.skipped_items,
            'completion_percentage': self.completion_percentage,
            'success_rate': self.success_rate,
            'duration': self.duration,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_batch': self.current_batch,
            'total_batches': self.total_batches,
            'errors': self.errors[-10:],  # Last 10 errors
            'warnings': self.warnings[-10:],  # Last 10 warnings
        }


class MigrationBackup:
    """Class to manage backup data for rollback capabilities."""
    
    def __init__(self):
        self.backup_data = {}
        self.backup_metadata = {
            'created': datetime.now().isoformat(),
            'version': '1.0.0',
            'items_count': 0
        }
        
    def backup_object(self, obj, fields: List[str] = None):
        """Create backup of object data before migration.
        
        Args:
            obj: The object to backup
            fields: Specific fields to backup, if None backup all relevant fields
        """
        obj_path = '/'.join(obj.getPhysicalPath())
        obj_uid = getattr(obj, 'UID', lambda: obj_path)()
        
        backup_entry = {
            'uid': obj_uid,
            'path': obj_path,
            'portal_type': getattr(obj, 'portal_type', 'Unknown'),
            'title': getattr(obj, 'title', 'Untitled'),
            'backed_up_at': datetime.now().isoformat(),
            'fields': {}
        }
        
        # Determine fields to backup
        if fields is None:
            fields = self._get_migration_relevant_fields(obj)
            
        # Backup field values
        for field_name in fields:
            try:
                value = getattr(obj, field_name, None)
                if value is not None:
                    # Handle different data types for serialization
                    if isinstance(value, (list, tuple)):
                        # Convert to list for JSON serialization
                        backup_entry['fields'][field_name] = list(value)
                    elif isinstance(value, dict):
                        # Convert to dict for JSON serialization
                        backup_entry['fields'][field_name] = dict(value)
                    elif hasattr(value, '__dict__'):
                        # Handle complex objects by extracting relevant attributes
                        backup_entry['fields'][field_name] = self._serialize_complex_object(value)
                    else:
                        # Handle simple types
                        backup_entry['fields'][field_name] = value
                        
            except Exception as e:
                logger.warning(f"Could not backup field {field_name} for {obj_path}: {e}")
                backup_entry['fields'][field_name] = f"<BACKUP_ERROR: {str(e)}>"
                
        self.backup_data[obj_uid] = backup_entry
        self.backup_metadata['items_count'] += 1
        
        logger.debug(f"Backed up {obj_path} with {len(backup_entry['fields'])} fields")
        
    def restore_object(self, obj):
        """Restore object from backup data.
        
        Args:
            obj: The object to restore
        """
        obj_uid = getattr(obj, 'UID', lambda: '/'.join(obj.getPhysicalPath()))()
        
        if obj_uid not in self.backup_data:
            raise MigrationRollbackError(f"No backup data found for {obj_uid}")
            
        backup_entry = self.backup_data[obj_uid]
        restored_fields = []
        
        for field_name, value in backup_entry['fields'].items():
            try:
                if value == f"<BACKUP_ERROR:":
                    continue  # Skip fields that couldn't be backed up
                    
                # Restore the field value
                if isinstance(value, list):
                    setattr(obj, field_name, PersistentList(value))
                elif isinstance(value, dict):
                    setattr(obj, field_name, PersistentMapping(value))
                else:
                    setattr(obj, field_name, value)
                    
                restored_fields.append(field_name)
                
            except Exception as e:
                logger.error(f"Could not restore field {field_name} for {obj_uid}: {e}")
                
        logger.info(f"Restored {len(restored_fields)} fields for {backup_entry['path']}")
        return restored_fields
        
    def _get_migration_relevant_fields(self, obj) -> List[str]:
        """Get fields that are relevant for migration backup."""
        portal_type = getattr(obj, 'portal_type', '')
        
        # Define fields by content type that are commonly migrated
        field_mappings = {
            'KnowledgeItem': [
                'prerequisite_items', 'enables_items', 'atomic_concepts',
                'tags', 'learning_progress', 'mastery_threshold',
                'knowledge_item_connections', 'relationships'
            ],
            'ResearchNote': [
                'key_insights', 'authors', 'connections', 'relationships',
                'builds_upon', 'contradicts', 'replication_studies'
            ],
            'LearningGoal': [
                'milestones', 'learning_objectives', 'assessment_criteria',
                'competencies', 'target_knowledge_items', 'relationships',
                'knowledge_item_connections', 'overall_progress'
            ],
            'ProjectLog': [
                'entries', 'deliverables', 'stakeholders', 'resources_used',
                'success_metrics', 'lessons_learned', 'relationships',
                'attached_learning_goal', 'knowledge_item_progress'
            ],
            'BookmarkPlus': [
                'tags', 'related_knowledge_items', 'annotated_knowledge_items',
                'sharing_permissions', 'relationships'
            ]
        }
        
        return field_mappings.get(portal_type, [])
        
    def _serialize_complex_object(self, obj) -> Dict[str, Any]:
        """Serialize complex objects for backup."""
        if hasattr(obj, 'UID'):
            return {'__type__': 'reference', 'uid': obj.UID()}
        elif hasattr(obj, '__dict__'):
            return {'__type__': 'object', 'data': dict(obj.__dict__)}
        else:
            return {'__type__': 'unknown', 'repr': repr(obj)}
            
    def export_backup(self) -> Dict[str, Any]:
        """Export backup data for external storage."""
        return {
            'metadata': self.backup_metadata,
            'data': self.backup_data
        }
        
    def import_backup(self, backup_data: Dict[str, Any]):
        """Import backup data from external storage."""
        self.backup_metadata = backup_data.get('metadata', {})
        self.backup_data = backup_data.get('data', {})


class BaseMigration(ABC):
    """Abstract base class for all migration operations.
    
    Provides common functionality for validation, error handling,
    transaction management, and progress tracking.
    """
    
    def __init__(self, context, batch_size: int = 50):
        self.context = context
        self.catalog = api.portal.get_tool("portal_catalog")
        self.batch_size = batch_size
        self.progress = MigrationProgress()
        self.backup = MigrationBackup()
        self.state = MigrationState.PENDING
        self.validation_hooks = []
        self.pre_migration_hooks = []
        self.post_migration_hooks = []
        self.error_handlers = {}
        
    @abstractmethod
    def get_migration_items(self) -> List[Any]:
        """Get items to be migrated. Must be implemented by subclasses."""
        pass
        
    @abstractmethod
    def migrate_item(self, item: Any) -> bool:
        """Migrate a single item. Must be implemented by subclasses.
        
        Args:
            item: The item to migrate
            
        Returns:
            bool: True if migration succeeded, False otherwise
        """
        pass
        
    def add_validation_hook(self, hook: Callable[[Any], Tuple[bool, str]]):
        """Add validation hook that runs before migration.
        
        Args:
            hook: Function that takes an item and returns (is_valid, message)
        """
        self.validation_hooks.append(hook)
        
    def add_pre_migration_hook(self, hook: Callable[[Any], None]):
        """Add hook that runs before migrating each item."""
        self.pre_migration_hooks.append(hook)
        
    def add_post_migration_hook(self, hook: Callable[[Any, bool], None]):
        """Add hook that runs after migrating each item.
        
        Args:
            hook: Function that takes (item, success) as arguments
        """
        self.post_migration_hooks.append(hook)
        
    def add_error_handler(self, error_type: type, handler: Callable[[Exception, Any], bool]):
        """Add error handler for specific exception types.
        
        Args:
            error_type: Exception type to handle
            handler: Function that takes (exception, item) and returns True if handled
        """
        self.error_handlers[error_type] = handler
        
    def validate_item(self, item: Any) -> Tuple[bool, List[str]]:
        """Run validation hooks on an item.
        
        Args:
            item: Item to validate
            
        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        messages = []
        is_valid = True
        
        for hook in self.validation_hooks:
            try:
                valid, message = hook(item)
                if not valid:
                    is_valid = False
                if message:
                    messages.append(message)
            except Exception as e:
                is_valid = False
                messages.append(f"Validation hook error: {str(e)}")
                
        return is_valid, messages
        
    def run_pre_migration_hooks(self, item: Any):
        """Run pre-migration hooks."""
        for hook in self.pre_migration_hooks:
            try:
                hook(item)
            except Exception as e:
                logger.warning(f"Pre-migration hook failed: {e}")
                
    def run_post_migration_hooks(self, item: Any, success: bool):
        """Run post-migration hooks."""
        for hook in self.post_migration_hooks:
            try:
                hook(item, success)
            except Exception as e:
                logger.warning(f"Post-migration hook failed: {e}")
                
    def handle_error(self, exception: Exception, item: Any) -> bool:
        """Handle errors using registered error handlers.
        
        Args:
            exception: The exception that occurred
            item: The item being processed
            
        Returns:
            bool: True if error was handled, False otherwise
        """
        for error_type, handler in self.error_handlers.items():
            if isinstance(exception, error_type):
                try:
                    return handler(exception, item)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")
                    
        return False
        
    def get_item_identifier(self, item: Any) -> str:
        """Get a string identifier for an item for logging."""
        if hasattr(item, 'UID'):
            return f"{item.UID()} ({getattr(item, 'title', 'No title')})"
        elif hasattr(item, 'getId'):
            return item.getId()
        elif hasattr(item, 'id'):
            return item.id
        else:
            return str(item)
            
    def run(self, validate_first: bool = True, create_backup: bool = True) -> Dict[str, Any]:
        """Run the migration with full transaction support.
        
        Args:
            validate_first: Whether to validate all items before migration
            create_backup: Whether to create backup before migration
            
        Returns:
            Dict containing migration results and statistics
        """
        logger.info(f"Starting migration: {self.__class__.__name__}")
        
        try:
            self.state = MigrationState.IN_PROGRESS
            items = self.get_migration_items()
            self.progress.total_items = len(items)
            self.progress.start()
            
            logger.info(f"Found {len(items)} items to migrate")
            
            # Validation phase
            if validate_first:
                logger.info("Running pre-migration validation...")
                validation_errors = []
                
                for item in items:
                    is_valid, messages = self.validate_item(item)
                    if not is_valid:
                        validation_errors.extend([
                            f"{self.get_item_identifier(item)}: {msg}" 
                            for msg in messages
                        ])
                        
                if validation_errors:
                    self.state = MigrationState.FAILED
                    raise MigrationValidationError(
                        f"Validation failed with {len(validation_errors)} errors: "
                        f"{validation_errors[:5]}"  # Show first 5 errors
                    )
                    
                logger.info("Pre-migration validation passed")
                
            # Process items in batches
            batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]
            self.progress.total_batches = len(batches)
            
            for batch_idx, batch in enumerate(batches):
                self.progress.current_batch = batch_idx + 1
                logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} items)")
                
                try:
                    self._process_batch(batch, create_backup)
                    
                    # Commit after each batch
                    transaction.savepoint()
                    logger.debug(f"Batch {batch_idx + 1} committed")
                    
                except Exception as e:
                    logger.error(f"Batch {batch_idx + 1} failed: {e}")
                    # Continue with next batch rather than failing entire migration
                    continue
                    
            self.progress.finish()
            self.state = MigrationState.COMPLETED
            
            # Final commit
            transaction.commit()
            
            result = {
                'status': 'completed',
                'progress': self.progress.to_dict(),
                'backup_available': bool(self.backup.backup_data),
                'state': self.state
            }
            
            logger.info(f"Migration completed: {self.progress.successful_items}/{self.progress.total_items} items migrated successfully")
            return result
            
        except Exception as e:
            self.state = MigrationState.FAILED
            self.progress.finish()
            
            logger.error(f"Migration failed: {e}")
            
            # Rollback transaction
            try:
                transaction.abort()
                logger.info("Transaction rolled back")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
                
            raise MigrationError(f"Migration failed: {e}")
            
    def _process_batch(self, batch: List[Any], create_backup: bool):
        """Process a batch of items."""
        for item in batch:
            item_id = self.get_item_identifier(item)
            
            try:
                # Create backup if requested
                if create_backup:
                    self.backup.backup_object(item)
                    
                # Run pre-migration hooks
                self.run_pre_migration_hooks(item)
                
                # Migrate the item
                success = self.migrate_item(item)
                
                if success:
                    self.progress.add_success(item_id, "Migration completed")
                    # Re-index the object after successful migration
                    if hasattr(item, 'reindexObject'):
                        item.reindexObject()
                else:
                    self.progress.add_failure(item_id, "Migration returned False")
                    
                # Run post-migration hooks
                self.run_post_migration_hooks(item, success)
                
            except Exception as e:
                # Try error handlers first
                if not self.handle_error(e, item):
                    self.progress.add_failure(item_id, str(e), e)
                    
                # Run post-migration hooks even on failure
                self.run_post_migration_hooks(item, False)
                
    def rollback(self) -> Dict[str, Any]:
        """Rollback the migration using backup data.
        
        Returns:
            Dict containing rollback results
        """
        if not self.backup.backup_data:
            raise MigrationRollbackError("No backup data available for rollback")
            
        logger.info(f"Starting rollback of {len(self.backup.backup_data)} items")
        
        rollback_progress = MigrationProgress(len(self.backup.backup_data))
        rollback_progress.start()
        
        try:
            for uid, backup_entry in self.backup.backup_data.items():
                try:
                    # Find the object by UID
                    brains = self.catalog(UID=uid)
                    if not brains:
                        rollback_progress.add_failure(uid, "Object not found in catalog")
                        continue
                        
                    obj = brains[0].getObject()
                    
                    # Restore the object
                    restored_fields = self.backup.restore_object(obj)
                    
                    # Re-index the object
                    if hasattr(obj, 'reindexObject'):
                        obj.reindexObject()
                        
                    rollback_progress.add_success(uid, f"Restored {len(restored_fields)} fields")
                    
                except Exception as e:
                    rollback_progress.add_failure(uid, str(e), e)
                    
            rollback_progress.finish()
            self.state = MigrationState.ROLLED_BACK
            
            # Commit rollback changes
            transaction.commit()
            
            result = {
                'status': 'rolled_back',
                'progress': rollback_progress.to_dict(),
                'state': self.state
            }
            
            logger.info(f"Rollback completed: {rollback_progress.successful_items}/{rollback_progress.total_items} items restored")
            return result
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            transaction.abort()
            raise MigrationRollbackError(f"Rollback failed: {e}")


class MigrationManager:
    """Central manager for migration operations with transaction support.
    
    Provides coordination of multiple migrations, state management,
    and comprehensive logging and reporting.
    """
    
    def __init__(self, context):
        self.context = context
        self.catalog = api.portal.get_tool("portal_catalog")
        self.migrations = []
        self.state = MigrationState.PENDING
        self.overall_progress = MigrationProgress()
        self.migration_log = []
        self.registry = queryUtility(IRegistry)
        
    def add_migration(self, migration: BaseMigration):
        """Add a migration to be managed.
        
        Args:
            migration: BaseMigration instance to add
        """
        self.migrations.append(migration)
        logger.info(f"Added migration: {migration.__class__.__name__}")
        
    def run_all_migrations(self, 
                          validate_first: bool = True, 
                          create_backup: bool = True,
                          stop_on_failure: bool = False) -> Dict[str, Any]:
        """Run all registered migrations with transaction coordination.
        
        Args:
            validate_first: Whether to validate before migration
            create_backup: Whether to create backups
            stop_on_failure: Whether to stop if a migration fails
            
        Returns:
            Dict containing overall results
        """
        if not self.migrations:
            raise MigrationError("No migrations registered")
            
        logger.info(f"Starting migration manager with {len(self.migrations)} migrations")
        
        self.state = MigrationState.IN_PROGRESS
        self.overall_progress.total_items = len(self.migrations)
        self.overall_progress.start()
        
        results = []
        successful_migrations = 0
        
        # Create savepoint before starting
        savepoint = transaction.savepoint()
        
        try:
            for idx, migration in enumerate(self.migrations):
                migration_name = migration.__class__.__name__
                logger.info(f"Running migration {idx + 1}/{len(self.migrations)}: {migration_name}")
                
                try:
                    # Create nested savepoint for this migration
                    migration_savepoint = transaction.savepoint()
                    
                    result = migration.run(validate_first, create_backup)
                    
                    results.append({
                        'migration': migration_name,
                        'result': result,
                        'index': idx
                    })
                    
                    if result['status'] == 'completed':
                        successful_migrations += 1
                        self.overall_progress.add_success(migration_name)
                    else:
                        self.overall_progress.add_failure(migration_name, "Migration did not complete")
                        
                        if stop_on_failure:
                            logger.error(f"Stopping migration sequence due to failure in {migration_name}")
                            break
                            
                except Exception as e:
                    logger.error(f"Migration {migration_name} failed: {e}")
                    
                    # Rollback this migration only
                    migration_savepoint.rollback()
                    
                    self.overall_progress.add_failure(migration_name, str(e), e)
                    
                    results.append({
                        'migration': migration_name,
                        'result': {'status': 'failed', 'error': str(e)},
                        'index': idx
                    })
                    
                    if stop_on_failure:
                        logger.error(f"Stopping migration sequence due to failure in {migration_name}")
                        break
                        
            self.overall_progress.finish()
            
            # Determine overall state
            if successful_migrations == len(self.migrations):
                self.state = MigrationState.COMPLETED
                transaction.commit()
                logger.info("All migrations completed successfully")
            elif successful_migrations == 0:
                self.state = MigrationState.FAILED
                savepoint.rollback()
                logger.error("All migrations failed")
            else:
                self.state = MigrationState.COMPLETED  # Partial success
                transaction.commit()
                logger.warning(f"Partial success: {successful_migrations}/{len(self.migrations)} migrations completed")
                
            overall_result = {
                'status': 'completed' if successful_migrations > 0 else 'failed',
                'successful_migrations': successful_migrations,
                'total_migrations': len(self.migrations),
                'overall_progress': self.overall_progress.to_dict(),
                'migration_results': results,
                'state': self.state
            }
            
            # Store results in registry for later access
            self._store_migration_results(overall_result)
            
            return overall_result
            
        except Exception as e:
            logger.error(f"Migration manager failed: {e}")
            savepoint.rollback()
            self.state = MigrationState.FAILED
            raise MigrationError(f"Migration manager failed: {e}")
            
    def rollback_all_migrations(self) -> Dict[str, Any]:
        """Rollback all migrations that have backup data.
        
        Returns:
            Dict containing rollback results
        """
        logger.info(f"Starting rollback of {len(self.migrations)} migrations")
        
        rollback_results = []
        successful_rollbacks = 0
        
        # Rollback in reverse order
        for migration in reversed(self.migrations):
            migration_name = migration.__class__.__name__
            
            try:
                if migration.backup.backup_data:
                    result = migration.rollback()
                    rollback_results.append({
                        'migration': migration_name,
                        'result': result
                    })
                    
                    if result['status'] == 'rolled_back':
                        successful_rollbacks += 1
                        
                else:
                    logger.warning(f"No backup data available for {migration_name}")
                    rollback_results.append({
                        'migration': migration_name,
                        'result': {'status': 'no_backup', 'message': 'No backup data available'}
                    })
                    
            except Exception as e:
                logger.error(f"Rollback of {migration_name} failed: {e}")
                rollback_results.append({
                    'migration': migration_name,
                    'result': {'status': 'failed', 'error': str(e)}
                })
                
        overall_rollback = {
            'status': 'completed' if successful_rollbacks > 0 else 'failed',
            'successful_rollbacks': successful_rollbacks,
            'total_migrations': len(self.migrations),
            'rollback_results': rollback_results
        }
        
        logger.info(f"Rollback completed: {successful_rollbacks}/{len(self.migrations)} migrations rolled back")
        return overall_rollback
        
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current status of all migrations.
        
        Returns:
            Dict containing status information
        """
        migration_statuses = []
        
        for migration in self.migrations:
            migration_statuses.append({
                'name': migration.__class__.__name__,
                'state': migration.state,
                'progress': migration.progress.to_dict(),
                'has_backup': bool(migration.backup.backup_data)
            })
            
        return {
            'overall_state': self.state,
            'overall_progress': self.overall_progress.to_dict(),
            'migration_count': len(self.migrations),
            'migrations': migration_statuses
        }
        
    def _store_migration_results(self, results: Dict[str, Any]):
        """Store migration results in registry for persistence."""
        if self.registry:
            try:
                self.registry['knowledge.curator.last_migration_results'] = json.dumps(results, default=str)
                self.registry['knowledge.curator.last_migration_timestamp'] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"Could not store migration results in registry: {e}")
                
    @contextmanager
    def transaction_scope(self, description: str = "Migration operation"):
        """Context manager for transaction handling.
        
        Args:
            description: Description of the operation for logging
        """
        savepoint = transaction.savepoint()
        logger.debug(f"Starting transaction scope: {description}")
        
        try:
            yield
            logger.debug(f"Transaction scope completed: {description}")
        except Exception as e:
            logger.error(f"Transaction scope failed, rolling back: {description} - {e}")
            savepoint.rollback()
            raise
            
    def create_progress_report(self) -> str:
        """Create a human-readable progress report.
        
        Returns:
            Formatted progress report string
        """
        report = []
        report.append("=" * 60)
        report.append("MIGRATION PROGRESS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Overall status
        report.append(f"Overall State: {self.state}")
        report.append(f"Total Migrations: {len(self.migrations)}")
        report.append("")
        
        # Individual migration status
        for idx, migration in enumerate(self.migrations, 1):
            name = migration.__class__.__name__
            progress = migration.progress
            
            report.append(f"{idx}. {name}")
            report.append(f"   State: {migration.state}")
            report.append(f"   Progress: {progress.completion_percentage:.1f}% "
                         f"({progress.processed_items}/{progress.total_items})")
            report.append(f"   Success Rate: {progress.success_rate:.1f}%")
            
            if progress.duration:
                report.append(f"   Duration: {progress.duration:.1f}s")
                
            if progress.errors:
                report.append(f"   Errors: {len(progress.errors)}")
                
            if progress.warnings:
                report.append(f"   Warnings: {len(progress.warnings)}")
                
            report.append("")
            
        return "\n".join(report)


# Example Migration Classes

class SimpleConnectionMigration(BaseMigration):
    """Example migration class for converting simple connections to relationships.
    
    This demonstrates how to use the BaseMigration infrastructure for a common
    migration pattern: converting simple UID lists to structured relationship objects.
    """
    
    def __init__(self, context, content_type: str = 'ResearchNote', batch_size: int = 50):
        super().__init__(context, batch_size)
        self.content_type = content_type
        
        # Add validation hooks
        self.add_validation_hook(validate_uid_references(self.catalog))
        self.add_validation_hook(self._validate_has_connections_field)
        
        # Add error handler for common issues
        self.add_error_handler(AttributeError, self._handle_missing_attribute)
        
    def get_migration_items(self) -> List[Any]:
        """Get items that need connection migration."""
        brains = self.catalog(portal_type=self.content_type)
        items = []
        
        for brain in brains:
            try:
                obj = brain.getObject()
                # Only include items that have old-style connections
                if hasattr(obj, 'connections') and getattr(obj, 'connections', []):
                    items.append(obj)
            except Exception as e:
                logger.warning(f"Could not access object {brain.getPath()}: {e}")
                
        return items
        
    def migrate_item(self, item: Any) -> bool:
        """Migrate connections field to relationships field."""
        try:
            old_connections = getattr(item, 'connections', [])
            if not old_connections:
                return True  # Nothing to migrate
                
            # Initialize relationships field
            if not hasattr(item, 'relationships'):
                item.relationships = PersistentList()
                
            source_uid = item.UID()
            
            for target_uid in old_connections:
                if isinstance(target_uid, str):
                    # Create structured relationship
                    relationship = PersistentMapping()
                    relationship['source_uid'] = source_uid
                    relationship['target_uid'] = target_uid
                    relationship['relationship_type'] = 'related'
                    relationship['strength'] = 0.5
                    relationship['metadata'] = PersistentMapping()
                    relationship['created'] = datetime.now()
                    relationship['confidence'] = 0.8
                    
                    item.relationships.append(relationship)
                    
            # Remove old connections field
            delattr(item, 'connections')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate connections for {self.get_item_identifier(item)}: {e}")
            return False
            
    def _validate_has_connections_field(self, item: Any) -> Tuple[bool, str]:
        """Validate that item has connections field to migrate."""
        if not hasattr(item, 'connections'):
            return False, "No connections field found"
        return True, "Has connections field"
        
    def _handle_missing_attribute(self, exception: AttributeError, item: Any) -> bool:
        """Handle missing attribute errors gracefully."""
        logger.warning(f"Missing attribute for {self.get_item_identifier(item)}: {exception}")
        # Skip items with missing attributes
        self.progress.add_skip(self.get_item_identifier(item), f"Missing attribute: {exception}")
        return True  # Error handled


class KnowledgeItemRelationshipMigration(BaseMigration):
    """Example migration for Knowledge Items with prerequisite/enables relationships.
    
    Demonstrates more complex migration logic with multiple relationship types
    and enhanced validation.
    """
    
    def __init__(self, context, batch_size: int = 25):
        super().__init__(context, batch_size)
        
        # Add comprehensive validation
        self.add_validation_hook(validate_uid_references(self.catalog))
        self.add_validation_hook(self._validate_knowledge_item_fields)
        self.add_validation_hook(self._validate_no_circular_dependencies)
        
        # Add error handlers
        self.add_error_handler(ValueError, self._handle_value_error)
        self.add_error_handler(KeyError, self._handle_key_error)
        
    def get_migration_items(self) -> List[Any]:
        """Get Knowledge Items that need relationship migration."""
        brains = self.catalog(portal_type='KnowledgeItem')
        items = []
        
        for brain in brains:
            try:
                obj = brain.getObject()
                # Check if item needs migration (has old-style fields)
                if (hasattr(obj, 'prerequisite_items') or hasattr(obj, 'enables_items') 
                    and not hasattr(obj, 'knowledge_item_connections')):
                    items.append(obj)
            except Exception as e:
                logger.warning(f"Could not access Knowledge Item {brain.getPath()}: {e}")
                
        return items
        
    def migrate_item(self, item: Any) -> bool:
        """Migrate prerequisite/enables to structured knowledge_item_connections."""
        try:
            # Initialize connections field
            if not hasattr(item, 'knowledge_item_connections'):
                item.knowledge_item_connections = PersistentList()
                
            source_uid = item.UID()
            migrated_connections = 0
            
            # Migrate prerequisite relationships
            prerequisites = getattr(item, 'prerequisite_items', [])
            for prereq_uid in prerequisites:
                if isinstance(prereq_uid, str):
                    connection = self._create_connection(
                        source_uid, prereq_uid, 'prerequisite', 0.9, 0.8
                    )
                    item.knowledge_item_connections.append(connection)
                    migrated_connections += 1
                    
            # Migrate enables relationships
            enables = getattr(item, 'enables_items', [])
            for enables_uid in enables:
                if isinstance(enables_uid, str):
                    connection = self._create_connection(
                        source_uid, enables_uid, 'enables', 0.7, 0.8
                    )
                    item.knowledge_item_connections.append(connection)
                    migrated_connections += 1
                    
            # Clean up old fields
            if hasattr(item, 'prerequisite_items'):
                delattr(item, 'prerequisite_items')
            if hasattr(item, 'enables_items'):
                delattr(item, 'enables_items')
                
            logger.debug(f"Migrated {migrated_connections} connections for {item.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate Knowledge Item {self.get_item_identifier(item)}: {e}")
            return False
            
    def _create_connection(self, source_uid: str, target_uid: str, 
                          connection_type: str, strength: float, 
                          mastery_requirement: float) -> PersistentMapping:
        """Create a structured connection object."""
        connection = PersistentMapping()
        connection['source_item_uid'] = source_uid
        connection['target_item_uid'] = target_uid
        connection['connection_type'] = connection_type
        connection['strength'] = strength
        connection['mastery_requirement'] = mastery_requirement
        connection['created'] = datetime.now()
        connection['metadata'] = PersistentMapping()
        
        return connection
        
    def _validate_knowledge_item_fields(self, item: Any) -> Tuple[bool, str]:
        """Validate Knowledge Item has required fields."""
        required_fields = ['title', 'description', 'knowledge_type']
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(item, field) or not getattr(item, field):
                missing_fields.append(field)
                
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
            
        return True, "All required fields present"
        
    def _validate_no_circular_dependencies(self, item: Any) -> Tuple[bool, str]:
        """Validate that there are no circular dependencies."""
        item_uid = item.UID()
        prerequisites = getattr(item, 'prerequisite_items', [])
        enables = getattr(item, 'enables_items', [])
        
        # Check for direct circular reference
        if item_uid in prerequisites or item_uid in enables:
            return False, "Item references itself"
            
        # Check for prerequisite that this item also enables
        common = set(prerequisites) & set(enables)
        if common:
            return False, f"Circular dependency detected with: {list(common)}"
            
        return True, "No circular dependencies detected"
        
    def _handle_value_error(self, exception: ValueError, item: Any) -> bool:
        """Handle value errors during migration."""
        logger.warning(f"Value error for {self.get_item_identifier(item)}: {exception}")
        self.progress.add_warning(self.get_item_identifier(item), f"Value error: {exception}")
        return False  # Don't skip, let migration attempt continue
        
    def _handle_key_error(self, exception: KeyError, item: Any) -> bool:
        """Handle key errors during migration."""
        logger.warning(f"Key error for {self.get_item_identifier(item)}: {exception}")
        self.progress.add_warning(self.get_item_identifier(item), f"Key error: {exception}")
        return False  # Don't skip, let migration attempt continue


class LearningGoalPrerequisitesMigration(BaseMigration):
    """Migration class for converting Learning Goal text prerequisites to Knowledge Item UID references.
    
    This migration converts text-based prerequisites in Learning Goals to structured
    UID references pointing to actual Knowledge Items. It includes fuzzy matching
    algorithms for partial matches and creates a manual review queue for ambiguous cases.
    """
    
    def __init__(self, context, batch_size: int = 25, fuzzy_threshold: float = 0.8):
        super().__init__(context, batch_size)
        self.fuzzy_threshold = fuzzy_threshold
        self.knowledge_items = {}
        self.knowledge_items_by_title = {}
        self.knowledge_items_by_content = {}
        self.manual_review_items = []
        self.statistics = {
            'exact_matches': 0,
            'fuzzy_matches_by_score': {},
            'unmatched_prerequisites': [],
            'duplicate_matches': []
        }
        
        # Add validation hooks
        self.add_validation_hook(self._validate_has_prerequisites)
        
        # Build knowledge item indexes
        self._build_knowledge_item_indexes()
        
    def _build_knowledge_item_indexes(self):
        """Build lookup indexes for efficient Knowledge Item matching."""
        logger.info("Building Knowledge Item indexes for prerequisite matching...")
        
        knowledge_item_brains = self.catalog(portal_type='KnowledgeItem')
        
        for brain in knowledge_item_brains:
            try:
                obj = brain.getObject()
                uid = obj.UID()
                title = getattr(obj, 'title', '').strip().lower()
                description = getattr(obj, 'description', '').strip().lower()
                content = getattr(obj, 'content', '').strip().lower()
                
                self.knowledge_items[uid] = {
                    'object': obj,
                    'title': title,
                    'description': description,
                    'content': content,
                    'full_text': f"{title} {description} {content}".strip()
                }
                
                # Index by title for exact matching
                if title:
                    self.knowledge_items_by_title[title] = uid
                    
                # Index key phrases from content for matching
                if content:
                    # Extract meaningful words (remove common words)
                    words = content.split()
                    meaningful_words = [w for w in words if len(w) > 3 and w not in 
                                      ['the', 'and', 'or', 'but', 'with', 'this', 'that', 'they', 'them', 'their']]
                    for word in meaningful_words:
                        if word not in self.knowledge_items_by_content:
                            self.knowledge_items_by_content[word] = []
                        self.knowledge_items_by_content[word].append(uid)
                        
            except Exception as e:
                logger.warning(f"Could not process Knowledge Item {brain.getPath()}: {e}")
                
        logger.info(f"Built indexes for {len(self.knowledge_items)} Knowledge Items")
        
    def get_migration_items(self) -> List[Any]:
        """Get Learning Goals that have text prerequisites to migrate."""
        brains = self.catalog(portal_type='LearningGoal')
        items = []
        
        for brain in brains:
            try:
                obj = brain.getObject()
                # Only include goals that have text prerequisites to migrate
                if hasattr(obj, 'prerequisite_knowledge') and getattr(obj, 'prerequisite_knowledge', []):
                    items.append(obj)
            except Exception as e:
                logger.warning(f"Could not access Learning Goal {brain.getPath()}: {e}")
                
        return items
        
    def migrate_item(self, learning_goal: Any) -> bool:
        """Migrate prerequisites for a single Learning Goal."""
        try:
            goal_uid = learning_goal.UID()
            goal_title = learning_goal.title
            
            # Get existing prerequisite_knowledge field
            prerequisites = getattr(learning_goal, 'prerequisite_knowledge', [])
            if not prerequisites:
                return True  # Nothing to migrate
                
            # Initialize new field for UID references if it doesn't exist
            if not hasattr(learning_goal, 'prerequisite_knowledge_items'):
                learning_goal.prerequisite_knowledge_items = PersistentList()
            else:
                # Clear existing UID references to avoid duplicates
                learning_goal.prerequisite_knowledge_items = PersistentList()
                
            converted_count = 0
            goal_manual_review = []
            
            for prerequisite_text in prerequisites:
                if not prerequisite_text or not prerequisite_text.strip():
                    continue
                    
                matches = self._find_best_matches(prerequisite_text)
                
                if not matches:
                    # No matches found - add to manual review
                    goal_manual_review.append({
                        'prerequisite_text': prerequisite_text,
                        'reason': 'No matching Knowledge Items found',
                        'suggestions': []
                    })
                    self.statistics['unmatched_prerequisites'].append({
                        'goal_title': goal_title,
                        'goal_uid': goal_uid,
                        'prerequisite_text': prerequisite_text
                    })
                    
                elif len(matches) == 1 and matches[0]['score'] >= self.fuzzy_threshold:
                    # Single high-confidence match - auto-convert
                    match = matches[0]
                    learning_goal.prerequisite_knowledge_items.append(match['uid'])
                    converted_count += 1
                    
                    if match['match_type'] == 'exact_title':
                        self.statistics['exact_matches'] += 1
                    else:
                        score_range = f"{int(match['score'] * 10) / 10:.1f}"
                        if score_range not in self.statistics['fuzzy_matches_by_score']:
                            self.statistics['fuzzy_matches_by_score'][score_range] = 0
                        self.statistics['fuzzy_matches_by_score'][score_range] += 1
                        
                else:
                    # Multiple matches or low confidence - add to manual review
                    goal_manual_review.append({
                        'prerequisite_text': prerequisite_text,
                        'reason': f"Multiple potential matches found ({len(matches)})",
                        'suggestions': [{
                            'uid': m['uid'],
                            'title': m['item'].title,
                            'score': m['score'],
                            'reason': m['reason']
                        } for m in matches]
                    })
                    
                    # Track duplicate matches for statistics
                    if len(matches) > 1:
                        self.statistics['duplicate_matches'].append({
                            'goal_title': goal_title,
                            'goal_uid': goal_uid,
                            'prerequisite_text': prerequisite_text,
                            'match_count': len(matches),
                            'top_score': matches[0]['score']
                        })
                        
            # Store manual review items for this goal
            if goal_manual_review:
                self.manual_review_items.append({
                    'goal_uid': goal_uid,
                    'goal_title': goal_title,
                    'manual_review_items': goal_manual_review
                })
                
            # Log progress
            if converted_count > 0:
                logger.debug(f"Converted {converted_count} prerequisites for '{goal_title}'")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate prerequisites for {self.get_item_identifier(learning_goal)}: {e}")
            return False
            
    def _find_best_matches(self, prerequisite_text: str, max_matches: int = 3) -> List[Dict[str, Any]]:
        """
        Find best matching Knowledge Items for a prerequisite text.
        
        Returns list of matches with similarity scores and reasons.
        """
        matches = []
        prerequisite_lower = prerequisite_text.strip().lower()
        
        if not prerequisite_lower:
            return matches
            
        # 1. Exact title match
        if prerequisite_lower in self.knowledge_items_by_title:
            uid = self.knowledge_items_by_title[prerequisite_lower]
            matches.append({
                'uid': uid,
                'item': self.knowledge_items[uid]['object'],
                'score': 1.0,
                'match_type': 'exact_title',
                'reason': f"Exact title match: '{prerequisite_text}'"
            })
            return matches[:max_matches]
            
        # 2. Fuzzy matching against titles and content
        for uid, item_data in self.knowledge_items.items():
            # Check title similarity
            if item_data['title']:
                title_similarity = difflib.SequenceMatcher(
                    None, prerequisite_lower, item_data['title']
                ).ratio()
                
                if title_similarity >= self.fuzzy_threshold:
                    matches.append({
                        'uid': uid,
                        'item': item_data['object'],
                        'score': title_similarity,
                        'match_type': 'fuzzy_title',
                        'reason': f"Title similarity ({title_similarity:.2f}): '{item_data['title']}'"
                    })
                    
            # Check full text similarity (with lower threshold)
            full_text_similarity = difflib.SequenceMatcher(
                None, prerequisite_lower, item_data['full_text']
            ).ratio()
            
            if full_text_similarity >= (self.fuzzy_threshold * 0.7):  # Lower threshold for content
                matches.append({
                    'uid': uid,
                    'item': item_data['object'],
                    'score': full_text_similarity,
                    'match_type': 'fuzzy_content',
                    'reason': f"Content similarity ({full_text_similarity:.2f}): '{item_data['title']}'"
                })
                
        # 3. Keyword-based matching
        prerequisite_words = [w for w in prerequisite_lower.split() if len(w) > 3]
        for word in prerequisite_words:
            if word in self.knowledge_items_by_content:
                for uid in self.knowledge_items_by_content[word]:
                    # Calculate keyword match score
                    item_words = self.knowledge_items[uid]['full_text'].split()
                    common_words = set(prerequisite_words) & set(item_words)
                    keyword_score = len(common_words) / max(len(prerequisite_words), 1)
                    
                    if keyword_score >= (self.fuzzy_threshold * 0.6):  # Even lower threshold for keywords
                        matches.append({
                            'uid': uid,
                            'item': self.knowledge_items[uid]['object'],
                            'score': keyword_score,
                            'match_type': 'keyword',
                            'reason': f"Keyword match ({keyword_score:.2f}): '{self.knowledge_items[uid]['title']}' (words: {', '.join(common_words)})"
                        })
                        
        # Remove duplicates and sort by score
        unique_matches = {}
        for match in matches:
            uid = match['uid']
            if uid not in unique_matches or match['score'] > unique_matches[uid]['score']:
                unique_matches[uid] = match
                
        sorted_matches = sorted(unique_matches.values(), key=lambda x: x['score'], reverse=True)
        return sorted_matches[:max_matches]
        
    def _validate_has_prerequisites(self, item: Any) -> Tuple[bool, str]:
        """Validate that item has prerequisite_knowledge field to migrate."""
        if not hasattr(item, 'prerequisite_knowledge'):
            return False, "No prerequisite_knowledge field found"
        prerequisites = getattr(item, 'prerequisite_knowledge', [])
        if not prerequisites:
            return False, "No prerequisites to migrate"
        return True, f"Has {len(prerequisites)} prerequisites to migrate"
        
    def get_manual_review_report(self) -> Dict[str, Any]:
        """Generate a comprehensive manual review report."""
        return {
            'total_goals_needing_review': len(self.manual_review_items),
            'total_unmatched_items': sum(len(goal['manual_review_items']) for goal in self.manual_review_items),
            'statistics': self.statistics,
            'goals_requiring_review': self.manual_review_items
        }


# Convenience function for running the Learning Goal prerequisites migration
def run_learning_goal_prerequisites_migration(context, batch_size: int = 25, fuzzy_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Convenience function to run the Learning Goal prerequisites migration.
    
    Args:
        context: The migration context (usually portal root)
        batch_size: Number of items to process per batch (default: 25)
        fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0-1.0, default: 0.8)
        
    Returns:
        Dict containing migration results with statistics and review queue
    """
    migration = LearningGoalPrerequisitesMigration(context, batch_size, fuzzy_threshold)
    
    try:
        # Run the migration with validation and backup
        results = migration.run(validate_first=True, create_backup=True)
        
        # Add manual review data to results
        manual_review_report = migration.get_manual_review_report()
        results['manual_review_report'] = manual_review_report
        results['statistics'] = migration.statistics
        
        # Log summary
        logger.info("Learning Goal Prerequisites Migration Summary:")
        logger.info(f"  Total items processed: {results['progress']['processed_items']}")
        logger.info(f"  Successful conversions: {results['progress']['successful_items']}")
        logger.info(f"  Failed conversions: {results['progress']['failed_items']}")
        logger.info(f"  Items needing manual review: {manual_review_report['total_goals_needing_review']}")
        logger.info(f"  Exact matches: {migration.statistics['exact_matches']}")
        logger.info(f"  Fuzzy matches by score: {migration.statistics['fuzzy_matches_by_score']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Learning Goal prerequisites migration failed: {e}")
        raise


# Utility functions for common migration patterns

def create_relationship_migration(source_field: str, 
                                target_field: str,
                                relationship_type: str = 'related',
                                default_strength: float = 0.5) -> Callable:
    """Create a migration function for converting simple references to relationships.
    
    Args:
        source_field: Field containing simple UID references
        target_field: Field to store structured relationships
        relationship_type: Type of relationship to create
        default_strength: Default strength for relationships
        
    Returns:
        Migration function
    """
    def migrate_relationships(obj):
        """Migrate simple references to structured relationships."""
        source_refs = getattr(obj, source_field, [])
        if not source_refs:
            return True
            
        # Initialize target field if not present
        if not hasattr(obj, target_field):
            setattr(obj, target_field, PersistentList())
            
        target_relationships = getattr(obj, target_field)
        source_uid = obj.UID()
        
        for target_uid in source_refs:
            if isinstance(target_uid, str):
                # Create structured relationship
                relationship = PersistentMapping()
                relationship['source_uid'] = source_uid
                relationship['target_uid'] = target_uid
                relationship['relationship_type'] = relationship_type
                relationship['strength'] = default_strength
                relationship['metadata'] = PersistentMapping()
                relationship['created'] = datetime.now()
                relationship['confidence'] = 0.8
                
                target_relationships.append(relationship)
                
        # Remove old field after migration
        if hasattr(obj, source_field):
            delattr(obj, source_field)
            
        return True
        
    return migrate_relationships


def migrate_learning_goal_prerequisites(context, batch_size: int = 25, fuzzy_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Migrate Learning Goal prerequisite_knowledge text fields to Knowledge Item UID references.
    
    This function converts text-based prerequisites in Learning Goals to structured
    UID references pointing to actual Knowledge Items. It includes fuzzy matching
    algorithms for partial matches and creates a manual review queue for ambiguous cases.
    
    Args:
        context: The migration context (usually portal root)
        batch_size: Number of items to process per batch (default: 25)
        fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0-1.0, default: 0.8)
        
    Returns:
        Dict containing migration results with statistics and review queue
    """
    import difflib
    from plone import api
    from plone.registry.interfaces import IRegistry
    from zope.component import queryUtility
    
    logger.info("Starting Learning Goal prerequisites migration...")
    
    # Initialize results structure
    results = {
        'status': 'completed',
        'total_learning_goals': 0,
        'processed_goals': 0,
        'successful_conversions': 0,
        'failed_conversions': 0,
        'fuzzy_matches': 0,
        'manual_review_needed': [],
        'errors': [],
        'statistics': {
            'exact_matches': 0,
            'fuzzy_matches_by_score': {},
            'unmatched_prerequisites': [],
            'duplicate_matches': []
        }
    }
    
    try:
        catalog = api.portal.get_tool("portal_catalog")
        
        # Get all Learning Goals that need migration
        learning_goal_brains = catalog(portal_type='LearningGoal')
        results['total_learning_goals'] = len(learning_goal_brains)
        
        # Get all Knowledge Items for matching
        knowledge_item_brains = catalog(portal_type='KnowledgeItem')
        knowledge_items = {}
        knowledge_items_by_title = {}
        knowledge_items_by_content = {}
        
        # Build lookup indexes for efficient matching
        for brain in knowledge_item_brains:
            try:
                obj = brain.getObject()
                uid = obj.UID()
                title = getattr(obj, 'title', '').strip().lower()
                description = getattr(obj, 'description', '').strip().lower()
                content = getattr(obj, 'content', '').strip().lower()
                
                knowledge_items[uid] = {
                    'object': obj,
                    'title': title,
                    'description': description,
                    'content': content,
                    'full_text': f"{title} {description} {content}".strip()
                }
                
                # Index by title for exact matching
                if title:
                    knowledge_items_by_title[title] = uid
                    
                # Index key phrases from content for matching
                if content:
                    # Extract meaningful phrases (remove common words)
                    words = content.split()
                    meaningful_words = [w for w in words if len(w) > 3 and w not in 
                                      ['the', 'and', 'or', 'but', 'with', 'this', 'that', 'they', 'them', 'their']]
                    for word in meaningful_words:
                        if word not in knowledge_items_by_content:
                            knowledge_items_by_content[word] = []
                        knowledge_items_by_content[word].append(uid)
                        
            except Exception as e:
                logger.warning(f"Could not process Knowledge Item {brain.getPath()}: {e}")
                
        logger.info(f"Built indexes for {len(knowledge_items)} Knowledge Items")
        
        def find_best_matches(prerequisite_text: str, max_matches: int = 3) -> List[Dict[str, Any]]:
            """
            Find best matching Knowledge Items for a prerequisite text.
            
            Returns list of matches with similarity scores and reasons.
            """
            matches = []
            prerequisite_lower = prerequisite_text.strip().lower()
            
            if not prerequisite_lower:
                return matches
                
            # 1. Exact title match
            if prerequisite_lower in knowledge_items_by_title:
                uid = knowledge_items_by_title[prerequisite_lower]
                matches.append({
                    'uid': uid,
                    'item': knowledge_items[uid]['object'],
                    'score': 1.0,
                    'match_type': 'exact_title',
                    'reason': f"Exact title match: '{prerequisite_text}'"
                })
                results['statistics']['exact_matches'] += 1
                return matches[:max_matches]
                
            # 2. Fuzzy matching against titles and content
            for uid, item_data in knowledge_items.items():
                # Check title similarity
                if item_data['title']:
                    title_similarity = difflib.SequenceMatcher(
                        None, prerequisite_lower, item_data['title']
                    ).ratio()
                    
                    if title_similarity >= fuzzy_threshold:
                        matches.append({
                            'uid': uid,
                            'item': item_data['object'],
                            'score': title_similarity,
                            'match_type': 'fuzzy_title',
                            'reason': f"Title similarity ({title_similarity:.2f}): '{item_data['title']}'"
                        })
                        
                # Check full text similarity (with lower threshold)
                full_text_similarity = difflib.SequenceMatcher(
                    None, prerequisite_lower, item_data['full_text']
                ).ratio()
                
                if full_text_similarity >= (fuzzy_threshold * 0.7):  # Lower threshold for content
                    matches.append({
                        'uid': uid,
                        'item': item_data['object'],
                        'score': full_text_similarity,
                        'match_type': 'fuzzy_content',
                        'reason': f"Content similarity ({full_text_similarity:.2f}): '{item_data['title']}'"
                    })
                    
            # 3. Keyword-based matching
            prerequisite_words = [w for w in prerequisite_lower.split() if len(w) > 3]
            for word in prerequisite_words:
                if word in knowledge_items_by_content:
                    for uid in knowledge_items_by_content[word]:
                        # Calculate keyword match score
                        item_words = knowledge_items[uid]['full_text'].split()
                        common_words = set(prerequisite_words) & set(item_words)
                        keyword_score = len(common_words) / max(len(prerequisite_words), 1)
                        
                        if keyword_score >= (fuzzy_threshold * 0.6):  # Even lower threshold for keywords
                            matches.append({
                                'uid': uid,
                                'item': knowledge_items[uid]['object'],
                                'score': keyword_score,
                                'match_type': 'keyword',
                                'reason': f"Keyword match ({keyword_score:.2f}): '{knowledge_items[uid]['title']}' (words: {', '.join(common_words)})"
                            })
                            
            # Remove duplicates and sort by score
            unique_matches = {}
            for match in matches:
                uid = match['uid']
                if uid not in unique_matches or match['score'] > unique_matches[uid]['score']:
                    unique_matches[uid] = match
                    
            sorted_matches = sorted(unique_matches.values(), key=lambda x: x['score'], reverse=True)
            return sorted_matches[:max_matches]
            
        def convert_prerequisites_for_goal(learning_goal) -> Dict[str, Any]:
            """
            Convert prerequisites for a single Learning Goal.
            
            Returns conversion results for this goal.
            """
            goal_results = {
                'goal_uid': learning_goal.UID(),
                'goal_title': learning_goal.title,
                'converted_count': 0,
                'failed_count': 0,
                'manual_review_items': [],
                'conversion_details': []
            }
            
            # Get existing prerequisite_knowledge field
            prerequisites = getattr(learning_goal, 'prerequisite_knowledge', [])
            if not prerequisites:
                return goal_results
                
            # Initialize new field for UID references if it doesn't exist
            if not hasattr(learning_goal, 'prerequisite_knowledge_items'):
                learning_goal.prerequisite_knowledge_items = PersistentList()
            else:
                # Clear existing UID references to avoid duplicates
                learning_goal.prerequisite_knowledge_items = PersistentList()
                
            for prerequisite_text in prerequisites:
                if not prerequisite_text or not prerequisite_text.strip():
                    continue
                    
                matches = find_best_matches(prerequisite_text)
                
                conversion_detail = {
                    'original_text': prerequisite_text,
                    'matches_found': len(matches),
                    'status': 'pending'
                }
                
                if not matches:
                    # No matches found - add to manual review
                    conversion_detail['status'] = 'no_matches'
                    conversion_detail['action'] = 'manual_review'
                    goal_results['failed_count'] += 1
                    goal_results['manual_review_items'].append({
                        'prerequisite_text': prerequisite_text,
                        'reason': 'No matching Knowledge Items found',
                        'suggestions': []
                    })
                    results['statistics']['unmatched_prerequisites'].append({
                        'goal_title': learning_goal.title,
                        'goal_uid': learning_goal.UID(),
                        'prerequisite_text': prerequisite_text
                    })
                    
                elif len(matches) == 1 and matches[0]['score'] >= fuzzy_threshold:
                    # Single high-confidence match - auto-convert
                    match = matches[0]
                    learning_goal.prerequisite_knowledge_items.append(match['uid'])
                    conversion_detail['status'] = 'converted'
                    conversion_detail['matched_uid'] = match['uid']
                    conversion_detail['matched_title'] = match['item'].title
                    conversion_detail['match_score'] = match['score']
                    conversion_detail['match_type'] = match['match_type']
                    
                    goal_results['converted_count'] += 1
                    
                    if match['match_type'] == 'exact_title':
                        results['statistics']['exact_matches'] += 1
                    else:
                        results['fuzzy_matches'] += 1
                        score_range = f"{int(match['score'] * 10) / 10:.1f}"
                        if score_range not in results['statistics']['fuzzy_matches_by_score']:
                            results['statistics']['fuzzy_matches_by_score'][score_range] = 0
                        results['statistics']['fuzzy_matches_by_score'][score_range] += 1
                        
                else:
                    # Multiple matches or low confidence - add to manual review
                    conversion_detail['status'] = 'ambiguous'
                    conversion_detail['action'] = 'manual_review'
                    conversion_detail['candidate_matches'] = [
                        {
                            'uid': m['uid'],
                            'title': m['item'].title,
                            'score': m['score'],
                            'match_type': m['match_type'],
                            'reason': m['reason']
                        } for m in matches
                    ]
                    
                    goal_results['failed_count'] += 1
                    goal_results['manual_review_items'].append({
                        'prerequisite_text': prerequisite_text,
                        'reason': f"Multiple potential matches found ({len(matches)})",
                        'suggestions': [{
                            'uid': m['uid'],
                            'title': m['item'].title,
                            'score': m['score'],
                            'reason': m['reason']
                        } for m in matches]
                    })
                    
                    # Track duplicate matches for statistics
                    if len(matches) > 1:
                        results['statistics']['duplicate_matches'].append({
                            'goal_title': learning_goal.title,
                            'goal_uid': learning_goal.UID(),
                            'prerequisite_text': prerequisite_text,
                            'match_count': len(matches),
                            'top_score': matches[0]['score']
                        })
                        
                goal_results['conversion_details'].append(conversion_detail)
                
            return goal_results
            
        # Process Learning Goals in batches
        successful_goals = 0
        failed_goals = 0
        
        for i in range(0, len(learning_goal_brains), batch_size):
            batch = learning_goal_brains[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} items)")
            
            for brain in batch:
                try:
                    learning_goal = brain.getObject()
                    results['processed_goals'] += 1
                    
                    # Convert prerequisites for this goal
                    goal_conversion = convert_prerequisites_for_goal(learning_goal)
                    
                    if goal_conversion['converted_count'] > 0:
                        successful_goals += 1
                        results['successful_conversions'] += goal_conversion['converted_count']
                        
                        # Reindex the object after modification
                        learning_goal.reindexObject()
                        logger.debug(f"Successfully migrated {goal_conversion['converted_count']} prerequisites for '{learning_goal.title}'")
                        
                    if goal_conversion['manual_review_items']:
                        results['manual_review_needed'].append(goal_conversion)
                        
                    if goal_conversion['failed_count'] > 0:
                        results['failed_conversions'] += goal_conversion['failed_count']
                        
                except Exception as e:
                    failed_goals += 1
                    error_msg = f"Error processing Learning Goal {brain.getPath()}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    
            # Commit after each batch
            try:
                transaction.savepoint()
                logger.debug(f"Committed batch {i // batch_size + 1}")
            except Exception as e:
                logger.warning(f"Could not create savepoint after batch: {e}")
                
        # Final commit
        transaction.commit()
        
        # Update final statistics
        results['successful_goals'] = successful_goals
        results['failed_goals'] = failed_goals
        
        # Store results in registry for later access
        registry = queryUtility(IRegistry)
        if registry:
            try:
                import json
                registry['knowledge.curator.prerequisite_migration_results'] = json.dumps(results, default=str)
                registry['knowledge.curator.prerequisite_migration_timestamp'] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"Could not store migration results in registry: {e}")
                
        # Log comprehensive summary
        logger.info("=" * 60)
        logger.info("LEARNING GOAL PREREQUISITES MIGRATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total Learning Goals: {results['total_learning_goals']}")
        logger.info(f"Successfully Processed: {results['processed_goals']}")
        logger.info(f"Successful Conversions: {results['successful_conversions']}")
        logger.info(f"Failed Conversions: {results['failed_conversions']}")
        logger.info(f"Exact Matches: {results['statistics']['exact_matches']}")
        logger.info(f"Fuzzy Matches: {results['fuzzy_matches']}")
        logger.info(f"Manual Review Items: {len(results['manual_review_needed'])}")
        logger.info(f"Unmatched Prerequisites: {len(results['statistics']['unmatched_prerequisites'])}")
        
        if results['manual_review_needed']:
            logger.info("\nMANUAL REVIEW REQUIRED:")
            for goal_review in results['manual_review_needed']:
                logger.info(f"  Goal: {goal_review['goal_title']} ({goal_review['goal_uid']})")
                for item in goal_review['manual_review_items']:
                    logger.info(f"    - '{item['prerequisite_text']}' ({item['reason']})")
                    if item['suggestions']:
                        logger.info(f"      Suggestions: {len(item['suggestions'])} items")
                        
        if results['errors']:
            logger.warning(f"\nERRORS ENCOUNTERED: {len(results['errors'])}")
            for error in results['errors'][-5:]:  # Show last 5 errors
                logger.warning(f"  {error}")
                
        logger.info("=" * 60)
        
        return results
        
    except Exception as e:
        error_msg = f"Migration failed with error: {str(e)}"
        logger.error(error_msg)
        results['status'] = 'failed'
        results['errors'].append(error_msg)
        
        # Rollback on failure
        try:
            transaction.abort()
            logger.info("Transaction rolled back due to error")
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")
            
        raise MigrationError(error_msg)


def migrate_research_note_connections(context) -> Dict[str, Any]:
    """
    Migrate Research Note connections to Knowledge Item annotations.
    
    This function analyzes Research Note content to identify references to Knowledge Items
    through text analysis and pattern matching, then creates proper Knowledge Item annotations
    while maintaining original content integrity.
    
    Args:
        context: The migration context (usually portal root)
        
    Returns:
        Dict containing migration results with statistics and details
    """
    logger.info("Starting Research Note connections migration...")
    
    # Initialize results structure
    results = {
        'status': 'completed',
        'total_research_notes': 0,
        'processed_notes': 0,
        'successful_migrations': 0,
        'failed_migrations': 0,
        'detected_references': 0,
        'created_annotations': 0,
        'content_patterns_matched': 0,
        'title_patterns_matched': 0,
        'uid_patterns_matched': 0,
        'manual_review_needed': [],
        'errors': [],
        'statistics': {
            'exact_title_matches': 0,
            'fuzzy_content_matches': 0,
            'uid_reference_matches': 0,
            'legacy_connection_matches': 0,
            'low_confidence_matches': 0,
            'reference_types': {},
            'annotation_types_created': {}
        }
    }
    
    try:
        catalog = api.portal.get_tool("portal_catalog")
        
        # Get all Research Notes
        research_note_brains = catalog(portal_type='ResearchNote')
        results['total_research_notes'] = len(research_note_brains)
        
        # Build Knowledge Item index for efficient matching
        knowledge_items = {}
        knowledge_items_by_title = {}
        knowledge_items_by_content_keywords = {}
        
        logger.info("Building Knowledge Item indexes...")
        ki_brains = catalog(portal_type='KnowledgeItem')
        
        for brain in ki_brains:
            try:
                obj = brain.getObject()
                uid = obj.UID()
                title = getattr(obj, 'title', '').strip().lower()
                description = getattr(obj, 'description', '').strip().lower()
                content = getattr(obj, 'content', '')
                
                # Extract text content from RichText if needed
                if hasattr(content, 'raw'):
                    content_text = content.raw.strip().lower()
                else:
                    content_text = str(content).strip().lower()
                
                knowledge_items[uid] = {
                    'object': obj,
                    'title': title,
                    'description': description,
                    'content': content_text,
                    'full_text': f"{title} {description} {content_text}".strip()
                }
                
                # Index by exact title for fast lookup
                if title:
                    knowledge_items_by_title[title] = uid
                
                # Index by key content words for text analysis
                content_words = set()
                for text in [title, description, content_text]:
                    if text:
                        # Extract meaningful words (longer than 3 chars, not common words)
                        words = [w.lower() for w in text.split() if len(w) > 3 and w.lower() not in 
                               {'this', 'that', 'with', 'from', 'they', 'them', 'their', 'there', 'where', 'when'}]
                        content_words.update(words)
                
                for word in content_words:
                    if word not in knowledge_items_by_content_keywords:
                        knowledge_items_by_content_keywords[word] = []
                    knowledge_items_by_content_keywords[word].append(uid)
                    
            except Exception as e:
                logger.warning(f"Could not index Knowledge Item {brain.getPath()}: {e}")
                
        logger.info(f"Built indexes for {len(knowledge_items)} Knowledge Items")
        
        def find_knowledge_item_references(research_note) -> List[Dict[str, Any]]:
            """
            Analyze Research Note content for Knowledge Item references.
            
            Returns list of potential references with confidence scores and reasons.
            """
            references = []
            note_uid = research_note.UID()
            note_title = getattr(research_note, 'title', '').strip().lower()
            note_description = getattr(research_note, 'description', '').strip().lower()
            
            # Get note content
            content = getattr(research_note, 'content', '')
            if hasattr(content, 'raw'):
                note_content = content.raw.strip().lower()
            else:
                note_content = str(content).strip().lower()
            
            # Combine all text for analysis
            full_note_text = f"{note_title} {note_description} {note_content}".strip()
            
            # 1. Check legacy connections field
            legacy_connections = getattr(research_note, 'connections', [])
            for uid in legacy_connections:
                if uid in knowledge_items:
                    references.append({
                        'target_uid': uid,
                        'knowledge_item': knowledge_items[uid]['object'],
                        'confidence': 0.9,
                        'match_type': 'legacy_connection',
                        'reason': 'Found in legacy connections field',
                        'text_evidence': 'Legacy connection field',
                        'annotation_type': 'reference',
                        'evidence_type': 'historical'
                    })
                    results['statistics']['legacy_connection_matches'] += 1
            
            # 2. Look for explicit UID references in content
            import re
            uid_pattern = r'[a-f0-9-]{36}'  # Standard UUID pattern
            uid_matches = re.findall(uid_pattern, full_note_text)
            for uid in uid_matches:
                if uid in knowledge_items:
                    references.append({
                        'target_uid': uid,
                        'knowledge_item': knowledge_items[uid]['object'],
                        'confidence': 0.95,
                        'match_type': 'uid_reference',
                        'reason': f'Explicit UID reference found in content: {uid}',
                        'text_evidence': f'UID: {uid}',
                        'annotation_type': 'reference',
                        'evidence_type': 'explicit'
                    })
                    results['statistics']['uid_reference_matches'] += 1
            
            # 3. Exact title matching in content
            for ki_title, ki_uid in knowledge_items_by_title.items():
                if ki_title and ki_title in full_note_text:
                    # Make sure it's not just a substring
                    import re
                    word_boundary_pattern = r'\b' + re.escape(ki_title) + r'\b'
                    if re.search(word_boundary_pattern, full_note_text, re.IGNORECASE):
                        references.append({
                            'target_uid': ki_uid,
                            'knowledge_item': knowledge_items[ki_uid]['object'],
                            'confidence': 0.85,
                            'match_type': 'exact_title',
                            'reason': f'Exact title match found: "{ki_title}"',
                            'text_evidence': f'Title reference: "{ki_title}"',
                            'annotation_type': 'discusses',
                            'evidence_type': 'textual'
                        })
                        results['statistics']['exact_title_matches'] += 1
            
            # 4. Fuzzy content matching using keyword overlap
            note_words = set([w.lower() for w in full_note_text.split() if len(w) > 3])
            
            for ki_uid, ki_data in knowledge_items.items():
                if ki_uid in [ref['target_uid'] for ref in references]:
                    continue  # Skip if already found
                    
                ki_words = set([w.lower() for w in ki_data['full_text'].split() if len(w) > 3])
                
                # Calculate keyword overlap
                common_words = note_words & ki_words
                if len(common_words) >= 3:  # Require at least 3 common meaningful words
                    overlap_score = len(common_words) / max(len(note_words), len(ki_words), 1)
                    
                    if overlap_score >= 0.1:  # At least 10% overlap
                        confidence = min(0.8, overlap_score * 2)  # Scale to confidence
                        
                        references.append({
                            'target_uid': ki_uid,
                            'knowledge_item': ki_data['object'],
                            'confidence': confidence,
                            'match_type': 'fuzzy_content',
                            'reason': f'Content overlap with {len(common_words)} common words (score: {overlap_score:.2f})',
                            'text_evidence': f'Common terms: {", ".join(list(common_words)[:5])}',
                            'annotation_type': 'relates_to',
                            'evidence_type': 'thematic'
                        })
                        results['statistics']['fuzzy_content_matches'] += 1
            
            # Remove duplicates and sort by confidence
            unique_refs = {}
            for ref in references:
                uid = ref['target_uid']
                if uid not in unique_refs or ref['confidence'] > unique_refs[uid]['confidence']:
                    unique_refs[uid] = ref
            
            return sorted(unique_refs.values(), key=lambda x: x['confidence'], reverse=True)
        
        def migrate_note_connections(research_note) -> Dict[str, Any]:
            """
            Migrate connections for a single Research Note.
            
            Returns migration results for this note.
            """
            note_results = {
                'note_uid': research_note.UID(),
                'note_title': research_note.title,
                'references_found': 0,
                'annotations_created': 0,
                'low_confidence_refs': 0,
                'migration_details': []
            }
            
            # Find potential references
            references = find_knowledge_item_references(research_note)
            note_results['references_found'] = len(references)
            
            if not references:
                return note_results
            
            # Get existing annotated Knowledge Items to avoid duplicates
            existing_annotations = set(getattr(research_note, 'annotated_knowledge_items', []))
            
            for ref in references:
                target_uid = ref['target_uid']
                confidence = ref['confidence']
                
                migration_detail = {
                    'target_uid': target_uid,
                    'target_title': ref['knowledge_item'].title,
                    'confidence': confidence,
                    'match_type': ref['match_type'],
                    'reason': ref['reason'],
                    'text_evidence': ref['text_evidence']
                }
                
                if confidence >= 0.7 and target_uid not in existing_annotations:
                    # High confidence - create annotation
                    try:
                        # Initialize field if it doesn't exist
                        if not hasattr(research_note, 'annotated_knowledge_items'):
                            research_note.annotated_knowledge_items = []
                        
                        # Add to annotated items
                        if target_uid not in research_note.annotated_knowledge_items:
                            research_note.annotated_knowledge_items.append(target_uid)
                            note_results['annotations_created'] += 1
                            results['created_annotations'] += 1
                        
                        # Set annotation metadata if not already set
                        if not hasattr(research_note, 'annotation_type') or not research_note.annotation_type:
                            research_note.annotation_type = ref['annotation_type']
                        if not hasattr(research_note, 'evidence_type') or not research_note.evidence_type:
                            research_note.evidence_type = ref['evidence_type']
                        if not hasattr(research_note, 'confidence_level') or not research_note.confidence_level:
                            if confidence >= 0.9:
                                research_note.confidence_level = 'high'
                            elif confidence >= 0.7:
                                research_note.confidence_level = 'medium'
                            else:
                                research_note.confidence_level = 'low'
                        if not hasattr(research_note, 'annotation_scope') or not research_note.annotation_scope:
                            research_note.annotation_scope = 'whole_item'
                        
                        migration_detail['status'] = 'annotation_created'
                        
                        # Track annotation types
                        ann_type = ref['annotation_type']
                        if ann_type not in results['statistics']['annotation_types_created']:
                            results['statistics']['annotation_types_created'][ann_type] = 0
                        results['statistics']['annotation_types_created'][ann_type] += 1
                        
                    except Exception as e:
                        migration_detail['status'] = 'failed'
                        migration_detail['error'] = str(e)
                        logger.error(f"Failed to create annotation for {target_uid}: {e}")
                        
                elif confidence < 0.7:
                    # Low confidence - add to manual review
                    migration_detail['status'] = 'low_confidence'
                    note_results['low_confidence_refs'] += 1
                    results['statistics']['low_confidence_matches'] += 1
                    
                else:
                    # Already exists
                    migration_detail['status'] = 'already_exists'
                
                note_results['migration_details'].append(migration_detail)
                
                # Track reference types
                ref_type = ref['match_type']
                if ref_type not in results['statistics']['reference_types']:
                    results['statistics']['reference_types'][ref_type] = 0
                results['statistics']['reference_types'][ref_type] += 1
            
            return note_results
        
        # Process Research Notes
        for brain in research_note_brains:
            try:
                research_note = brain.getObject()
                results['processed_notes'] += 1
                
                # Migrate connections for this note
                note_migration = migrate_note_connections(research_note)
                
                if note_migration['annotations_created'] > 0:
                    results['successful_migrations'] += 1
                    results['detected_references'] += note_migration['references_found']
                    
                    # Reindex the object
                    research_note.reindexObject()
                    logger.debug(f"Migrated {note_migration['annotations_created']} annotations for '{research_note.title}'")
                
                # Track items needing manual review
                if note_migration['low_confidence_refs'] > 0:
                    results['manual_review_needed'].append(note_migration)
                
            except Exception as e:
                results['failed_migrations'] += 1
                error_msg = f"Error processing Research Note {brain.getPath()}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Commit changes
        transaction.commit()
        
        # Log comprehensive summary
        logger.info("=" * 60)
        logger.info("RESEARCH NOTE CONNECTIONS MIGRATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total Research Notes: {results['total_research_notes']}")
        logger.info(f"Successfully Processed: {results['processed_notes']}")
        logger.info(f"Successful Migrations: {results['successful_migrations']}")
        logger.info(f"Failed Migrations: {results['failed_migrations']}")
        logger.info(f"Total References Detected: {results['detected_references']}")
        logger.info(f"Annotations Created: {results['created_annotations']}")
        logger.info(f"Manual Review Items: {len(results['manual_review_needed'])}")
        
        logger.info("\nMatch Type Statistics:")
        for match_type, count in results['statistics']['reference_types'].items():
            logger.info(f"  {match_type}: {count}")
        
        logger.info("\nAnnotation Types Created:")
        for ann_type, count in results['statistics']['annotation_types_created'].items():
            logger.info(f"  {ann_type}: {count}")
        
        return results
        
    except Exception as e:
        error_msg = f"Migration failed with error: {str(e)}"
        logger.error(error_msg)
        results['status'] = 'failed'
        results['errors'].append(error_msg)
        
        # Rollback on failure
        try:
            transaction.abort()
            logger.info("Transaction rolled back due to error")
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")
        
        raise MigrationError(error_msg)


# Convenience function for running the Research Note connections migration
def run_research_note_connections_migration(context) -> Dict[str, Any]:
    """
    Convenience function to run the Research Note connections migration.
    
    This function analyzes Research Note content to identify references to Knowledge Items
    through text analysis and pattern matching, then creates proper Knowledge Item annotations.
    
    Usage:
        from knowledge.curator.upgrades.migrate_relationships import run_research_note_connections_migration
        results = run_research_note_connections_migration(portal)
    
    Args:
        context: The migration context (usually portal root)
        
    Returns:
        Dict containing migration results with statistics and details
    """
    try:
        results = migrate_research_note_connections(context)
        
        # Log summary for easy viewing
        logger.info("Research Note Connections Migration Summary:")
        logger.info(f"  Total Research Notes: {results['total_research_notes']}")
        logger.info(f"  Successfully Migrated: {results['successful_migrations']}")
        logger.info(f"  Annotations Created: {results['created_annotations']}")
        logger.info(f"  Manual Review Items: {len(results['manual_review_needed'])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Research Note connections migration failed: {e}")
        raise


def validate_uid_references(catalog) -> Callable:
    """Create a validation hook to check UID references.
    
    Args:
        catalog: Portal catalog for UID lookups
        
    Returns:
        Validation function
    """
    def validate_references(obj) -> Tuple[bool, str]:
        """Validate that UID references point to existing objects."""
        # Get all UID fields to check
        uid_fields = [
            'prerequisite_items', 'enables_items', 'target_knowledge_items',
            'related_knowledge_items', 'annotated_knowledge_items'
        ]
        
        invalid_refs = []
        
        for field_name in uid_fields:
            refs = getattr(obj, field_name, [])
            if refs:
                for ref in refs:
                    uid = ref if isinstance(ref, str) else getattr(ref, 'UID', lambda: None)()
                    if uid:
                        brains = catalog(UID=uid)
                        if not brains:
                            invalid_refs.append(f"{field_name}: {uid}")
                            
        if invalid_refs:
            return False, f"Invalid UID references: {', '.join(invalid_refs)}"
            
        return True, "All UID references valid"
        
    return validate_references


def log_migration_statistics(migration_results: Dict[str, Any]):
    """Log comprehensive migration statistics.
    
    Args:
        migration_results: Results from migration manager
    """
    logger.info("=" * 60)
    logger.info("MIGRATION STATISTICS")
    logger.info("=" * 60)
    
    overall_progress = migration_results.get('overall_progress', {})
    
    logger.info(f"Total Migrations: {migration_results.get('total_migrations', 0)}")
    logger.info(f"Successful Migrations: {migration_results.get('successful_migrations', 0)}")
    logger.info(f"Overall Status: {migration_results.get('status', 'unknown')}")
    
    if overall_progress:
        logger.info(f"Total Duration: {overall_progress.get('duration', 'unknown')}s")
        logger.info(f"Success Rate: {overall_progress.get('success_rate', 0):.1f}%")
        
    # Log individual migration results
    for result in migration_results.get('migration_results', []):
        migration = result.get('migration', 'Unknown')
        status = result.get('result', {}).get('status', 'unknown')
        logger.info(f"  {migration}: {status}")
        
    logger.info("=" * 60)


class DataIntegrityValidationError(MigrationError):
    """Exception for data integrity validation errors."""
    pass


class CircularDependencyError(DataIntegrityValidationError):
    """Exception for circular dependency detection."""
    pass


class OrphanedReferenceError(DataIntegrityValidationError):
    """Exception for orphaned reference detection."""
    pass


class DataIntegrityValidator:
    """Comprehensive data integrity validation system for Knowledge Curator.
    
    This class provides methods to detect orphaned references, identify circular 
    dependencies in Knowledge Item relationships, and validate data integrity 
    across all migration scenarios.
    """
    
    def __init__(self, context):
        self.context = context
        self.catalog = api.portal.get_tool("portal_catalog")
        self.validation_results = {
            'orphaned_references': [],
            'circular_dependencies': [],
            'integrity_violations': [],
            'validation_errors': [],
            'statistics': {
                'total_items_checked': 0,
                'total_references_validated': 0,
                'orphaned_count': 0,
                'circular_dependency_count': 0,
                'integrity_violation_count': 0
            }
        }
        
    def validate_all_data_integrity(self, include_content_types: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive data integrity validation across all content types.
        
        Args:
            include_content_types: List of content types to check, if None checks all
            
        Returns:
            Dict containing comprehensive validation results
        """
        logger.info("Starting comprehensive data integrity validation...")
        
        # Default content types to check
        if include_content_types is None:
            include_content_types = [
                'KnowledgeItem', 'ResearchNote', 'LearningGoal', 
                'ProjectLog', 'BookmarkPlus'
            ]
        
        # Reset validation results
        self.validation_results = {
            'orphaned_references': [],
            'circular_dependencies': [],
            'integrity_violations': [],
            'validation_errors': [],
            'statistics': {
                'total_items_checked': 0,
                'total_references_validated': 0,
                'orphaned_count': 0,
                'circular_dependency_count': 0,
                'integrity_violation_count': 0
            }
        }
        
        try:
            # 1. Validate orphaned references
            logger.info("Checking for orphaned references...")
            orphaned_refs = self.detect_orphaned_references(include_content_types)
            self.validation_results['orphaned_references'] = orphaned_refs
            self.validation_results['statistics']['orphaned_count'] = len(orphaned_refs)
            
            # 2. Detect circular dependencies
            logger.info("Checking for circular dependencies...")
            circular_deps = self.detect_circular_dependencies()
            self.validation_results['circular_dependencies'] = circular_deps
            self.validation_results['statistics']['circular_dependency_count'] = len(circular_deps)
            
            # 3. Validate relationship integrity
            logger.info("Validating relationship integrity...")
            integrity_violations = self.validate_relationship_integrity(include_content_types)
            self.validation_results['integrity_violations'] = integrity_violations
            self.validation_results['statistics']['integrity_violation_count'] = len(integrity_violations)
            
            # 4. Generate validation report
            validation_report = self.generate_validation_report()
            
            logger.info(f"Data integrity validation completed. Found {len(orphaned_refs)} orphaned references, "
                       f"{len(circular_deps)} circular dependencies, and {len(integrity_violations)} integrity violations.")
            
            return {
                'status': 'completed',
                'validation_results': self.validation_results,
                'validation_report': validation_report,
                'summary': {
                    'total_issues': len(orphaned_refs) + len(circular_deps) + len(integrity_violations),
                    'critical_issues': len([issue for issue in circular_deps if issue.get('severity') == 'critical']),
                    'data_integrity_score': self._calculate_integrity_score()
                }
            }
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            self.validation_results['validation_errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'context': 'comprehensive_validation'
            })
            raise DataIntegrityValidationError(f"Validation failed: {e}")
    
    def detect_orphaned_references(self, content_types: List[str]) -> List[Dict[str, Any]]:
        """Detect orphaned references across all content types.
        
        Args:
            content_types: List of content types to check for orphaned references
            
        Returns:
            List of dictionaries describing orphaned references
        """
        orphaned_references = []
        
        # Define field mappings for each content type
        uid_field_mappings = {
            'KnowledgeItem': [
                'prerequisite_items', 'enables_items', 'target_knowledge_items',
                'knowledge_item_connections', 'related_knowledge_items'
            ],
            'ResearchNote': [
                'annotated_knowledge_items', 'related_knowledge_items',
                'builds_upon', 'contradicts', 'replication_studies'
            ],
            'LearningGoal': [
                'prerequisite_knowledge_items', 'target_knowledge_items',
                'milestone_knowledge_items', 'attached_learning_goal'
            ],
            'ProjectLog': [
                'attached_learning_goal', 'related_knowledge_items',
                'milestone_deliverables'
            ],
            'BookmarkPlus': [
                'related_knowledge_items', 'annotated_knowledge_items'
            ]
        }
        
        for content_type in content_types:
            logger.debug(f"Checking orphaned references for {content_type}...")
            
            brains = self.catalog(portal_type=content_type)
            uid_fields = uid_field_mappings.get(content_type, [])
            
            for brain in brains:
                try:
                    obj = brain.getObject()
                    self.validation_results['statistics']['total_items_checked'] += 1
                    
                    # Check each UID field for orphaned references
                    for field_name in uid_fields:
                        field_value = getattr(obj, field_name, None)
                        
                        if field_value:
                            orphaned_in_field = self._check_field_for_orphaned_refs(
                                obj, field_name, field_value
                            )
                            orphaned_references.extend(orphaned_in_field)
                            
                except Exception as e:
                    logger.warning(f"Could not check {brain.getPath()} for orphaned references: {e}")
                    self.validation_results['validation_errors'].append({
                        'error': str(e),
                        'object_path': brain.getPath(),
                        'context': 'orphaned_reference_detection'
                    })
        
        return orphaned_references
    
    def _check_field_for_orphaned_refs(self, obj, field_name: str, field_value) -> List[Dict[str, Any]]:
        """Check a specific field for orphaned references.
        
        Args:
            obj: The object being checked
            field_name: Name of the field
            field_value: Value of the field to check
            
        Returns:
            List of orphaned reference details
        """
        orphaned_refs = []
        
        # Handle different field value types
        if isinstance(field_value, (list, tuple)):
            uids_to_check = field_value
        elif isinstance(field_value, str):
            uids_to_check = [field_value]
        elif hasattr(field_value, '__iter__'):
            # Handle PersistentList or other iterable types
            uids_to_check = list(field_value)
        else:
            return orphaned_refs
        
        for item in uids_to_check:
            uid = None
            
            # Extract UID from different formats
            if isinstance(item, str):
                # Simple UID string
                uid = item
            elif isinstance(item, dict) and 'target_uid' in item:
                # Structured relationship object
                uid = item['target_uid']
            elif isinstance(item, dict) and 'source_uid' in item:
                # Check both source and target UIDs in relationships
                source_uid = item.get('source_uid')
                target_uid = item.get('target_uid')
                
                for check_uid, uid_type in [(source_uid, 'source'), (target_uid, 'target')]:
                    if check_uid and not self._uid_exists(check_uid):
                        orphaned_refs.append({
                            'object_uid': obj.UID(),
                            'object_path': '/'.join(obj.getPhysicalPath()),
                            'object_title': getattr(obj, 'title', 'Untitled'),
                            'object_type': getattr(obj, 'portal_type', 'Unknown'),
                            'field_name': field_name,
                            'orphaned_uid': check_uid,
                            'uid_type': uid_type,
                            'relationship_data': item,
                            'severity': 'high',
                            'detected_at': datetime.now().isoformat()
                        })
                        self.validation_results['statistics']['total_references_validated'] += 1
                continue
            elif hasattr(item, 'UID'):
                # Object with UID method
                uid = item.UID()
            else:
                continue
            
            if uid and not self._uid_exists(uid):
                orphaned_refs.append({
                    'object_uid': obj.UID(),
                    'object_path': '/'.join(obj.getPhysicalPath()),
                    'object_title': getattr(obj, 'title', 'Untitled'),
                    'object_type': getattr(obj, 'portal_type', 'Unknown'),
                    'field_name': field_name,
                    'orphaned_uid': uid,
                    'uid_type': 'reference',
                    'severity': 'high',
                    'detected_at': datetime.now().isoformat()
                })
            
            self.validation_results['statistics']['total_references_validated'] += 1
        
        return orphaned_refs
    
    def _uid_exists(self, uid: str) -> bool:
        """Check if a UID exists in the catalog.
        
        Args:
            uid: UID to check
            
        Returns:
            True if UID exists, False otherwise
        """
        try:
            brains = self.catalog(UID=uid)
            return len(brains) > 0
        except Exception:
            return False
    
    def detect_circular_dependencies(self) -> List[Dict[str, Any]]:
        """Detect circular dependencies in Knowledge Item relationships.
        
        Returns:
            List of circular dependency chains
        """
        circular_dependencies = []
        
        # Build relationship graph for Knowledge Items
        knowledge_items = {}
        ki_brains = self.catalog(portal_type='KnowledgeItem')
        
        # First pass: collect all relationships
        for brain in ki_brains:
            try:
                obj = brain.getObject()
                uid = obj.UID()
                
                # Extract prerequisite and enables relationships
                prerequisites = []
                enables = []
                
                # Check old-style fields
                if hasattr(obj, 'prerequisite_items'):
                    prerequisites.extend(getattr(obj, 'prerequisite_items', []))
                if hasattr(obj, 'enables_items'):
                    enables.extend(getattr(obj, 'enables_items', []))
                
                # Check new-style structured relationships
                if hasattr(obj, 'knowledge_item_connections'):
                    connections = getattr(obj, 'knowledge_item_connections', [])
                    for connection in connections:
                        if isinstance(connection, dict):
                            conn_type = connection.get('connection_type', '')
                            target_uid = connection.get('target_item_uid') or connection.get('target_uid')
                            
                            if conn_type == 'prerequisite' and target_uid:
                                prerequisites.append(target_uid)
                            elif conn_type == 'enables' and target_uid:
                                enables.append(target_uid)
                
                knowledge_items[uid] = {
                    'object': obj,
                    'prerequisites': list(set(prerequisites)),  # Remove duplicates
                    'enables': list(set(enables)),
                    'title': getattr(obj, 'title', 'Untitled')
                }
                
            except Exception as e:
                logger.warning(f"Could not process {brain.getPath()} for circular dependency detection: {e}")
        
        # Second pass: detect circular dependencies using DFS
        visited = set()
        recursion_stack = set()
        
        def detect_cycle_dfs(uid: str, path: List[str]) -> List[str]:
            """DFS to detect cycles in the dependency graph."""
            if uid in recursion_stack:
                # Found a cycle - return the cycle path
                cycle_start = path.index(uid)
                return path[cycle_start:] + [uid]
            
            if uid not in knowledge_items or uid in visited:
                return []
            
            visited.add(uid)
            recursion_stack.add(uid)
            
            # Check prerequisites (reverse dependencies)
            for prereq_uid in knowledge_items[uid]['prerequisites']:
                if prereq_uid in knowledge_items:
                    cycle = detect_cycle_dfs(prereq_uid, path + [uid])
                    if cycle:
                        return cycle
            
            recursion_stack.remove(uid)
            return []
        
        # Check each Knowledge Item for circular dependencies
        for uid in knowledge_items:
            if uid not in visited:
                cycle = detect_cycle_dfs(uid, [])
                if cycle:
                    # Build detailed circular dependency information
                    cycle_items = []
                    for i, cycle_uid in enumerate(cycle[:-1]):  # Exclude duplicate at end
                        next_uid = cycle[(i + 1) % (len(cycle) - 1)]
                        
                        if cycle_uid in knowledge_items:
                            cycle_items.append({
                                'uid': cycle_uid,
                                'title': knowledge_items[cycle_uid]['title'],
                                'path': knowledge_items[cycle_uid]['object'].absolute_url(),
                                'depends_on': next_uid,
                                'depends_on_title': knowledge_items.get(next_uid, {}).get('title', 'Unknown')
                            })
                    
                    if cycle_items:
                        circular_dependencies.append({
                            'cycle_type': 'prerequisite_dependency',
                            'cycle_length': len(cycle_items),
                            'cycle_items': cycle_items,
                            'cycle_path': ' -> '.join([knowledge_items.get(uid, {}).get('title', uid) for uid in cycle[:-1]]) + ' -> ' + cycle_items[0]['title'],
                            'severity': 'critical' if len(cycle_items) <= 3 else 'high',
                            'detected_at': datetime.now().isoformat(),
                            'resolution_suggestion': self._suggest_cycle_resolution(cycle_items)
                        })
        
        # Also check for simple bidirectional dependencies
        for uid, item_data in knowledge_items.items():
            for enables_uid in item_data['enables']:
                if enables_uid in knowledge_items:
                    # Check if the enabled item also enables this item back
                    if uid in knowledge_items[enables_uid]['enables']:
                        circular_dependencies.append({
                            'cycle_type': 'bidirectional_enables',
                            'cycle_length': 2,
                            'cycle_items': [
                                {
                                    'uid': uid,
                                    'title': item_data['title'],
                                    'path': item_data['object'].absolute_url(),
                                    'depends_on': enables_uid,
                                    'depends_on_title': knowledge_items[enables_uid]['title']
                                },
                                {
                                    'uid': enables_uid,
                                    'title': knowledge_items[enables_uid]['title'],
                                    'path': knowledge_items[enables_uid]['object'].absolute_url(),
                                    'depends_on': uid,
                                    'depends_on_title': item_data['title']
                                }
                            ],
                            'cycle_path': f"{item_data['title']} <-> {knowledge_items[enables_uid]['title']}",
                            'severity': 'medium',
                            'detected_at': datetime.now().isoformat(),
                            'resolution_suggestion': "Remove one of the bidirectional 'enables' relationships"
                        })
        
        return circular_dependencies
    
    def _suggest_cycle_resolution(self, cycle_items: List[Dict[str, Any]]) -> str:
        """Suggest resolution for a circular dependency cycle.
        
        Args:
            cycle_items: List of items in the circular dependency
            
        Returns:
            Resolution suggestion string
        """
        if len(cycle_items) == 2:
            return "Break the cycle by removing one of the bidirectional dependencies"
        elif len(cycle_items) == 3:
            return "Consider if one of the three items could be an intermediate step rather than a direct dependency"
        else:
            return f"Complex cycle with {len(cycle_items)} items - review the logical dependency order and remove the weakest link"
    
    def validate_relationship_integrity(self, content_types: List[str]) -> List[Dict[str, Any]]:
        """Validate relationship integrity across content types.
        
        Args:
            content_types: List of content types to validate
            
        Returns:
            List of integrity violations
        """
        integrity_violations = []
        
        for content_type in content_types:
            logger.debug(f"Validating relationship integrity for {content_type}...")
            
            brains = self.catalog(portal_type=content_type)
            
            for brain in brains:
                try:
                    obj = brain.getObject()
                    
                    # Check for relationship consistency
                    violations = self._check_relationship_consistency(obj)
                    integrity_violations.extend(violations)
                    
                    # Check for invalid relationship structures
                    structure_violations = self._check_relationship_structure(obj)
                    integrity_violations.extend(structure_violations)
                    
                except Exception as e:
                    logger.warning(f"Could not validate {brain.getPath()}: {e}")
                    integrity_violations.append({
                        'object_uid': brain.UID,
                        'object_path': brain.getPath(),
                        'object_type': content_type,
                        'violation_type': 'validation_error',
                        'description': f"Could not validate object: {str(e)}",
                        'severity': 'medium',
                        'detected_at': datetime.now().isoformat()
                    })
        
        return integrity_violations
    
    def _check_relationship_consistency(self, obj) -> List[Dict[str, Any]]:
        """Check relationship consistency for an object.
        
        Args:
            obj: Object to check
            
        Returns:
            List of consistency violations
        """
        violations = []
        obj_uid = obj.UID()
        obj_type = getattr(obj, 'portal_type', 'Unknown')
        
        # Check for inconsistent relationship data
        if obj_type == 'KnowledgeItem':
            # Check prerequisite/enables consistency
            old_prereqs = getattr(obj, 'prerequisite_items', [])
            old_enables = getattr(obj, 'enables_items', [])
            new_connections = getattr(obj, 'knowledge_item_connections', [])
            
            if (old_prereqs or old_enables) and new_connections:
                violations.append({
                    'object_uid': obj_uid,
                    'object_path': '/'.join(obj.getPhysicalPath()),
                    'object_title': getattr(obj, 'title', 'Untitled'),
                    'object_type': obj_type,
                    'violation_type': 'mixed_relationship_formats',
                    'description': 'Object has both old-style and new-style relationships',
                    'severity': 'medium',
                    'detected_at': datetime.now().isoformat(),
                    'resolution': 'Complete migration to new relationship format'
                })
        
        elif obj_type == 'ResearchNote':
            # Check annotation consistency
            old_connections = getattr(obj, 'connections', [])
            annotated_items = getattr(obj, 'annotated_knowledge_items', [])
            
            if old_connections and not annotated_items:
                violations.append({
                    'object_uid': obj_uid,
                    'object_path': '/'.join(obj.getPhysicalPath()),
                    'object_title': getattr(obj, 'title', 'Untitled'),
                    'object_type': obj_type,
                    'violation_type': 'incomplete_annotation_migration',
                    'description': 'Has legacy connections but no Knowledge Item annotations',
                    'severity': 'low',
                    'detected_at': datetime.now().isoformat(),
                    'resolution': 'Complete migration to annotation format'
                })
        
        return violations
    
    def _check_relationship_structure(self, obj) -> List[Dict[str, Any]]:
        """Check relationship structure validity.
        
        Args:
            obj: Object to check
            
        Returns:
            List of structure violations
        """
        violations = []
        obj_uid = obj.UID()
        obj_type = getattr(obj, 'portal_type', 'Unknown')
        
        # Check structured relationships format
        if hasattr(obj, 'knowledge_item_connections'):
            connections = getattr(obj, 'knowledge_item_connections', [])
            
            for i, connection in enumerate(connections):
                if not isinstance(connection, dict):
                    violations.append({
                        'object_uid': obj_uid,
                        'object_path': '/'.join(obj.getPhysicalPath()),
                        'object_title': getattr(obj, 'title', 'Untitled'),
                        'object_type': obj_type,
                        'violation_type': 'invalid_relationship_structure',
                        'description': f'Connection {i} is not a dictionary: {type(connection)}',
                        'severity': 'high',
                        'detected_at': datetime.now().isoformat(),
                        'resolution': 'Fix relationship data structure'
                    })
                    continue
                
                # Check required fields
                required_fields = ['source_uid', 'target_uid', 'relationship_type']
                missing_fields = [field for field in required_fields if field not in connection]
                
                if missing_fields:
                    violations.append({
                        'object_uid': obj_uid,
                        'object_path': '/'.join(obj.getPhysicalPath()),
                        'object_title': getattr(obj, 'title', 'Untitled'),
                        'object_type': obj_type,
                        'violation_type': 'incomplete_relationship_data',
                        'description': f'Connection {i} missing required fields: {missing_fields}',
                        'severity': 'medium',
                        'detected_at': datetime.now().isoformat(),
                        'resolution': f'Add missing fields: {", ".join(missing_fields)}'
                    })
        
        return violations
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report.
        
        Returns:
            Formatted validation report string
        """
        report = []
        report.append("=" * 80)
        report.append("DATA INTEGRITY VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        stats = self.validation_results['statistics']
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  Total Items Checked: {stats['total_items_checked']}")
        report.append(f"  Total References Validated: {stats['total_references_validated']}")
        report.append(f"  Orphaned References Found: {stats['orphaned_count']}")
        report.append(f"  Circular Dependencies Found: {stats['circular_dependency_count']}")
        report.append(f"  Integrity Violations Found: {stats['integrity_violation_count']}")
        report.append("")
        
        # Data integrity score
        integrity_score = self._calculate_integrity_score()
        report.append(f"DATA INTEGRITY SCORE: {integrity_score:.1f}%")
        report.append("")
        
        # Detailed findings
        if self.validation_results['orphaned_references']:
            report.append("ORPHANED REFERENCES:")
            report.append("-" * 40)
            for ref in self.validation_results['orphaned_references'][:10]:  # Show first 10
                report.append(f"  Object: {ref['object_title']} ({ref['object_type']})")
                report.append(f"  Field: {ref['field_name']}")
                report.append(f"  Orphaned UID: {ref['orphaned_uid']}")
                report.append(f"  Severity: {ref['severity']}")
                report.append("")
        
        if self.validation_results['circular_dependencies']:
            report.append("CIRCULAR DEPENDENCIES:")
            report.append("-" * 40)
            for dep in self.validation_results['circular_dependencies'][:5]:  # Show first 5
                report.append(f"  Type: {dep['cycle_type']}")
                report.append(f"  Path: {dep['cycle_path']}")
                report.append(f"  Severity: {dep['severity']}")
                report.append(f"  Suggestion: {dep['resolution_suggestion']}")
                report.append("")
        
        if self.validation_results['integrity_violations']:
            report.append("INTEGRITY VIOLATIONS:")
            report.append("-" * 40)
            for violation in self.validation_results['integrity_violations'][:10]:  # Show first 10
                report.append(f"  Object: {violation.get('object_title', 'Unknown')} ({violation.get('object_type', 'Unknown')})")
                report.append(f"  Type: {violation['violation_type']}")
                report.append(f"  Description: {violation['description']}")
                report.append(f"  Severity: {violation['severity']}")
                if 'resolution' in violation:
                    report.append(f"  Resolution: {violation['resolution']}")
                report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _calculate_integrity_score(self) -> float:
        """Calculate a data integrity score based on validation results.
        
        Returns:
            Integrity score as a percentage (0-100)
        """
        stats = self.validation_results['statistics']
        
        if stats['total_items_checked'] == 0:
            return 100.0
        
        # Weight different issues by severity
        total_issues = (
            stats['orphaned_count'] * 3 +  # Orphaned refs are serious
            stats['circular_dependency_count'] * 5 +  # Circular deps are very serious
            stats['integrity_violation_count'] * 2  # Violations are moderate
        )
        
        # Calculate score based on ratio of issues to total items
        max_possible_issues = stats['total_items_checked'] * 5  # Assume worst case
        score = max(0, 100 - (total_issues / max_possible_issues * 100))
        
        return score
    
    def cleanup_orphaned_references(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up orphaned references from the system.
        
        Args:
            dry_run: If True, only report what would be cleaned up
            
        Returns:
            Cleanup results
        """
        logger.info(f"{'Simulating' if dry_run else 'Executing'} orphaned reference cleanup...")
        
        cleanup_results = {
            'status': 'completed',
            'dry_run': dry_run,
            'items_processed': 0,
            'references_removed': 0,
            'cleanup_actions': [],
            'errors': []
        }
        
        try:
            for orphaned_ref in self.validation_results['orphaned_references']:
                try:
                    # Find the object with the orphaned reference
                    brains = self.catalog(UID=orphaned_ref['object_uid'])
                    if not brains:
                        continue
                    
                    obj = brains[0].getObject()
                    field_name = orphaned_ref['field_name']
                    orphaned_uid = orphaned_ref['orphaned_uid']
                    
                    # Get current field value
                    field_value = getattr(obj, field_name, None)
                    if not field_value:
                        continue
                    
                    cleanup_action = {
                        'object_title': orphaned_ref['object_title'],
                        'object_path': orphaned_ref['object_path'],
                        'field_name': field_name,
                        'orphaned_uid': orphaned_uid,
                        'action': 'remove_reference'
                    }
                    
                    if not dry_run:
                        # Actually remove the orphaned reference
                        if isinstance(field_value, list):
                            if orphaned_uid in field_value:
                                field_value.remove(orphaned_uid)
                                cleanup_results['references_removed'] += 1
                        elif isinstance(field_value, str) and field_value == orphaned_uid:
                            setattr(obj, field_name, None)
                            cleanup_results['references_removed'] += 1
                        
                        # Re-index the object
                        obj.reindexObject()
                    
                    cleanup_results['cleanup_actions'].append(cleanup_action)
                    cleanup_results['items_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to clean up orphaned reference in {orphaned_ref.get('object_path', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    cleanup_results['errors'].append(error_msg)
            
            if not dry_run:
                transaction.commit()
                logger.info(f"Orphaned reference cleanup completed. Removed {cleanup_results['references_removed']} references from {cleanup_results['items_processed']} items.")
            else:
                logger.info(f"Orphaned reference cleanup simulation completed. Would remove {cleanup_results['references_removed']} references from {cleanup_results['items_processed']} items.")
            
            return cleanup_results
            
        except Exception as e:
            logger.error(f"Orphaned reference cleanup failed: {e}")
            if not dry_run:
                transaction.abort()
            raise DataIntegrityValidationError(f"Cleanup failed: {e}")


class MigrationRollbackManager:
    """Comprehensive rollback manager for failed migrations.
    
    Provides automated rollback procedures, rollback validation, and
    detailed rollback reporting for complex migration scenarios.
    """
    
    def __init__(self, context):
        self.context = context
        self.catalog = api.portal.get_tool("portal_catalog")
        self.rollback_log = []
        
    def create_pre_migration_snapshot(self, migration_name: str, content_types: List[str] = None) -> Dict[str, Any]:
        """Create a comprehensive snapshot before migration begins.
        
        Args:
            migration_name: Name of the migration
            content_types: List of content types to snapshot
            
        Returns:
            Snapshot metadata
        """
        logger.info(f"Creating pre-migration snapshot for: {migration_name}")
        
        if content_types is None:
            content_types = ['KnowledgeItem', 'ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
        
        snapshot_id = f"{migration_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot_data = {
            'snapshot_id': snapshot_id,
            'migration_name': migration_name,
            'created_at': datetime.now().isoformat(),
            'content_types': content_types,
            'object_snapshots': {},
            'relationship_map': {},
            'statistics': {
                'total_objects': 0,
                'total_relationships': 0,
                'content_type_counts': {}
            }
        }
        
        try:
            for content_type in content_types:
                brains = self.catalog(portal_type=content_type)
                content_type_snapshots = []
                relationship_count = 0
                
                for brain in brains:
                    try:
                        obj = brain.getObject()
                        obj_uid = obj.UID()
                        
                        # Create object snapshot
                        obj_snapshot = self._create_object_snapshot(obj)
                        content_type_snapshots.append(obj_snapshot)
                        
                        # Track relationships
                        obj_relationships = self._extract_object_relationships(obj)
                        if obj_relationships:
                            snapshot_data['relationship_map'][obj_uid] = obj_relationships
                            relationship_count += len(obj_relationships)
                        
                    except Exception as e:
                        logger.warning(f"Could not snapshot {brain.getPath()}: {e}")
                
                snapshot_data['object_snapshots'][content_type] = content_type_snapshots
                snapshot_data['statistics']['content_type_counts'][content_type] = len(content_type_snapshots)
                snapshot_data['statistics']['total_objects'] += len(content_type_snapshots)
                snapshot_data['statistics']['total_relationships'] += relationship_count
            
            # Store snapshot in registry
            self._store_snapshot(snapshot_data)
            
            logger.info(f"Pre-migration snapshot created: {snapshot_id} "
                       f"({snapshot_data['statistics']['total_objects']} objects, "
                       f"{snapshot_data['statistics']['total_relationships']} relationships)")
            
            return {
                'status': 'success',
                'snapshot_id': snapshot_id,
                'statistics': snapshot_data['statistics']
            }
            
        except Exception as e:
            logger.error(f"Failed to create pre-migration snapshot: {e}")
            raise MigrationError(f"Snapshot creation failed: {e}")
    
    def _create_object_snapshot(self, obj) -> Dict[str, Any]:
        """Create a snapshot of an individual object.
        
        Args:
            obj: Object to snapshot
            
        Returns:
            Object snapshot data
        """
        snapshot = {
            'uid': obj.UID(),
            'path': '/'.join(obj.getPhysicalPath()),
            'portal_type': getattr(obj, 'portal_type', 'Unknown'),
            'title': getattr(obj, 'title', 'Untitled'),
            'fields': {},
            'metadata': {
                'created': getattr(obj, 'created', lambda: None)(),
                'modified': getattr(obj, 'modified', lambda: None)(),
                'creation_date': getattr(obj, 'creation_date', None),
                'modification_date': getattr(obj, 'modification_date', None)
            }
        }
        
        # Snapshot migration-relevant fields
        relevant_fields = self._get_migration_relevant_fields(obj)
        
        for field_name in relevant_fields:
            try:
                field_value = getattr(obj, field_name, None)
                if field_value is not None:
                    snapshot['fields'][field_name] = self._serialize_field_value(field_value)
            except Exception as e:
                logger.warning(f"Could not snapshot field {field_name} for {obj.getId()}: {e}")
                snapshot['fields'][field_name] = f"<SNAPSHOT_ERROR: {str(e)}>"
        
        return snapshot
    
    def _extract_object_relationships(self, obj) -> List[Dict[str, Any]]:
        """Extract relationship data from an object.
        
        Args:
            obj: Object to extract relationships from
            
        Returns:
            List of relationship data
        """
        relationships = []
        obj_uid = obj.UID()
        
        # Define relationship fields by content type
        relationship_fields = {
            'KnowledgeItem': [
                ('prerequisite_items', 'prerequisite'),
                ('enables_items', 'enables'),
                ('knowledge_item_connections', 'structured')
            ],
            'ResearchNote': [
                ('connections', 'legacy_connection'),
                ('annotated_knowledge_items', 'annotation'),
                ('builds_upon', 'builds_upon'),
                ('contradicts', 'contradicts')
            ],
            'LearningGoal': [
                ('prerequisite_knowledge_items', 'prerequisite_knowledge'),
                ('target_knowledge_items', 'target_knowledge')
            ]
        }
        
        portal_type = getattr(obj, 'portal_type', '')
        fields_to_check = relationship_fields.get(portal_type, [])
        
        for field_name, relationship_type in fields_to_check:
            field_value = getattr(obj, field_name, [])
            
            if field_value:
                if isinstance(field_value, (list, tuple)):
                    for item in field_value:
                        relationships.append({
                            'source_uid': obj_uid,
                            'target_uid': item if isinstance(item, str) else getattr(item, 'UID', lambda: str(item))(),
                            'relationship_type': relationship_type,
                            'field_name': field_name,
                            'raw_data': self._serialize_field_value(item)
                        })
                elif isinstance(field_value, str):
                    relationships.append({
                        'source_uid': obj_uid,
                        'target_uid': field_value,
                        'relationship_type': relationship_type,
                        'field_name': field_name,
                        'raw_data': field_value
                    })
        
        return relationships
    
    def _get_migration_relevant_fields(self, obj) -> List[str]:
        """Get fields relevant for migration snapshots.
        
        Args:
            obj: Object to get fields for
            
        Returns:
            List of field names
        """
        portal_type = getattr(obj, 'portal_type', '')
        
        field_mappings = {
            'KnowledgeItem': [
                'prerequisite_items', 'enables_items', 'atomic_concepts',
                'tags', 'learning_progress', 'mastery_threshold',
                'knowledge_item_connections', 'relationships', 'content',
                'description', 'knowledge_type'
            ],
            'ResearchNote': [
                'key_insights', 'authors', 'connections', 'relationships',
                'builds_upon', 'contradicts', 'replication_studies',
                'annotated_knowledge_items', 'annotation_type', 'evidence_type',
                'confidence_level', 'annotation_scope', 'content', 'description'
            ],
            'LearningGoal': [
                'milestones', 'learning_objectives', 'assessment_criteria',
                'competencies', 'target_knowledge_items', 'relationships',
                'knowledge_item_connections', 'overall_progress',
                'prerequisite_knowledge', 'prerequisite_knowledge_items',
                'description', 'content'
            ],
            'ProjectLog': [
                'entries', 'deliverables', 'stakeholders', 'resources_used',
                'success_metrics', 'lessons_learned', 'relationships',
                'attached_learning_goal', 'knowledge_item_progress',
                'description', 'content'
            ],
            'BookmarkPlus': [
                'tags', 'related_knowledge_items', 'annotated_knowledge_items',
                'sharing_permissions', 'relationships', 'description', 'url'
            ]
        }
        
        return field_mappings.get(portal_type, ['title', 'description'])
    
    def _serialize_field_value(self, value) -> Any:
        """Serialize field value for snapshot storage.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value
        """
        if isinstance(value, (list, tuple)):
            return [self._serialize_field_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_field_value(v) for k, v in value.items()}
        elif hasattr(value, 'UID'):
            return {'__type__': 'reference', 'uid': value.UID()}
        elif hasattr(value, 'raw'):
            return {'__type__': 'richtext', 'raw': value.raw}
        elif isinstance(value, datetime):
            return {'__type__': 'datetime', 'value': value.isoformat()}
        else:
            return value
    
    def _store_snapshot(self, snapshot_data: Dict[str, Any]):
        """Store snapshot data in registry.
        
        Args:
            snapshot_data: Snapshot data to store
        """
        registry = queryUtility(IRegistry)
        if registry:
            try:
                registry_key = f'knowledge.curator.migration_snapshot_{snapshot_data["snapshot_id"]}'
                registry[registry_key] = json.dumps(snapshot_data, default=str)
                logger.debug(f"Stored snapshot in registry: {registry_key}")
            except Exception as e:
                logger.warning(f"Could not store snapshot in registry: {e}")
    
    def execute_comprehensive_rollback(self, snapshot_id: str, validate_after: bool = True) -> Dict[str, Any]:
        """Execute comprehensive rollback using snapshot data.
        
        Args:
            snapshot_id: ID of the snapshot to rollback to
            validate_after: Whether to validate data integrity after rollback
            
        Returns:
            Rollback results
        """
        logger.info(f"Starting comprehensive rollback to snapshot: {snapshot_id}")
        
        rollback_results = {
            'status': 'in_progress',
            'snapshot_id': snapshot_id,
            'started_at': datetime.now().isoformat(),
            'objects_restored': 0,
            'relationships_restored': 0,
            'errors': [],
            'warnings': [],
            'validation_results': None
        }
        
        # Create a savepoint before rollback
        savepoint = transaction.savepoint()
        
        try:
            # Load snapshot data
            snapshot_data = self._load_snapshot(snapshot_id)
            if not snapshot_data:
                raise MigrationRollbackError(f"Snapshot not found: {snapshot_id}")
            
            # Restore objects by content type
            for content_type, objects in snapshot_data['object_snapshots'].items():
                logger.info(f"Restoring {len(objects)} {content_type} objects...")
                
                for obj_snapshot in objects:
                    try:
                        # Find the object
                        brains = self.catalog(UID=obj_snapshot['uid'])
                        if not brains:
                            rollback_results['warnings'].append(f"Object not found for rollback: {obj_snapshot['uid']}")
                            continue
                        
                        obj = brains[0].getObject()
                        
                        # Restore field values
                        restored_fields = 0
                        for field_name, field_value in obj_snapshot['fields'].items():
                            try:
                                if field_value != f"<SNAPSHOT_ERROR:":
                                    deserialized_value = self._deserialize_field_value(field_value)
                                    setattr(obj, field_name, deserialized_value)
                                    restored_fields += 1
                            except Exception as e:
                                rollback_results['warnings'].append(f"Could not restore field {field_name} for {obj_snapshot['uid']}: {str(e)}")
                        
                        # Re-index the object
                        obj.reindexObject()
                        rollback_results['objects_restored'] += 1
                        
                        logger.debug(f"Restored {restored_fields} fields for {obj_snapshot['title']}")
                        
                    except Exception as e:
                        error_msg = f"Failed to restore object {obj_snapshot['uid']}: {str(e)}"
                        logger.error(error_msg)
                        rollback_results['errors'].append(error_msg)
            
            # Restore relationships
            logger.info("Restoring relationship data...")
            for obj_uid, relationships in snapshot_data['relationship_map'].items():
                try:
                    brains = self.catalog(UID=obj_uid)
                    if not brains:
                        continue
                    
                    obj = brains[0].getObject()
                    
                    # Group relationships by field
                    field_relationships = defaultdict(list)
                    for rel in relationships:
                        field_relationships[rel['field_name']].append(rel)
                    
                    # Restore each field's relationships
                    for field_name, field_rels in field_relationships.items():
                        try:
                            if field_name.endswith('_connections') or field_name == 'relationships':
                                # Structured relationships
                                restored_value = [self._deserialize_field_value(rel['raw_data']) for rel in field_rels]
                            else:
                                # Simple UID lists
                                restored_value = [rel['target_uid'] for rel in field_rels]
                            
                            setattr(obj, field_name, restored_value)
                            rollback_results['relationships_restored'] += len(field_rels)
                            
                        except Exception as e:
                            rollback_results['warnings'].append(f"Could not restore relationships in field {field_name} for {obj_uid}: {str(e)}")
                    
                    obj.reindexObject()
                    
                except Exception as e:
                    error_msg = f"Failed to restore relationships for {obj_uid}: {str(e)}"
                    logger.error(error_msg)
                    rollback_results['errors'].append(error_msg)
            
            # Commit rollback changes
            transaction.commit()
            
            rollback_results['status'] = 'completed'
            rollback_results['completed_at'] = datetime.now().isoformat()
            
            # Post-rollback validation if requested
            if validate_after:
                logger.info("Running post-rollback validation...")
                validator = DataIntegrityValidator(self.context)
                validation_results = validator.validate_all_data_integrity()
                rollback_results['validation_results'] = validation_results
            
            logger.info(f"Comprehensive rollback completed. Restored {rollback_results['objects_restored']} objects "
                       f"and {rollback_results['relationships_restored']} relationships.")
            
            return rollback_results
            
        except Exception as e:
            logger.error(f"Comprehensive rollback failed: {e}")
            savepoint.rollback()
            rollback_results['status'] = 'failed'
            rollback_results['error'] = str(e)
            rollback_results['failed_at'] = datetime.now().isoformat()
            raise MigrationRollbackError(f"Rollback failed: {e}")
    
    def _load_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Load snapshot data from registry.
        
        Args:
            snapshot_id: Snapshot ID to load
            
        Returns:
            Snapshot data or None if not found
        """
        registry = queryUtility(IRegistry)
        if registry:
            try:
                registry_key = f'knowledge.curator.migration_snapshot_{snapshot_id}'
                snapshot_json = registry.get(registry_key)
                if snapshot_json:
                    return json.loads(snapshot_json)
            except Exception as e:
                logger.error(f"Could not load snapshot from registry: {e}")
        
        return None
    
    def _deserialize_field_value(self, value) -> Any:
        """Deserialize field value from snapshot storage.
        
        Args:
            value: Value to deserialize
            
        Returns:
            Deserialized value
        """
        if isinstance(value, dict):
            if value.get('__type__') == 'reference':
                # For now, just return the UID - could be enhanced to resolve object
                return value['uid']
            elif value.get('__type__') == 'richtext':
                # Return the raw text - could be enhanced to reconstruct RichText object
                return value['raw']
            elif value.get('__type__') == 'datetime':
                return datetime.fromisoformat(value['value'])
            else:
                return {k: self._deserialize_field_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize_field_value(item) for item in value]
        else:
            return value
    
    def list_available_snapshots(self) -> List[Dict[str, Any]]:
        """List all available migration snapshots.
        
        Returns:
            List of snapshot metadata
        """
        snapshots = []
        registry = queryUtility(IRegistry)
        
        if registry:
            for key in registry.keys():
                if key.startswith('knowledge.curator.migration_snapshot_'):
                    try:
                        snapshot_data = json.loads(registry[key])
                        snapshots.append({
                            'snapshot_id': snapshot_data['snapshot_id'],
                            'migration_name': snapshot_data['migration_name'],
                            'created_at': snapshot_data['created_at'],
                            'content_types': snapshot_data['content_types'],
                            'statistics': snapshot_data['statistics']
                        })
                    except Exception as e:
                        logger.warning(f"Could not parse snapshot {key}: {e}")
        
        return sorted(snapshots, key=lambda x: x['created_at'], reverse=True)


# Enhanced validation functions with comprehensive integrity checks

def validate_migration_prerequisites(context) -> Dict[str, Any]:
    """Validate that all prerequisites for migration are met.
    
    Args:
        context: Migration context
        
    Returns:
        Validation results
    """
    logger.info("Validating migration prerequisites...")
    
    validator = DataIntegrityValidator(context)
    validation_results = validator.validate_all_data_integrity()
    
    prerequisites_met = {
        'data_integrity_score': validation_results['summary']['data_integrity_score'],
        'critical_issues': validation_results['summary']['critical_issues'],
        'total_issues': validation_results['summary']['total_issues'],
        'ready_for_migration': validation_results['summary']['critical_issues'] == 0,
        'recommendations': []
    }
    
    if not prerequisites_met['ready_for_migration']:
        prerequisites_met['recommendations'].append("Resolve critical data integrity issues before migration")
    
    if validation_results['summary']['total_issues'] > 0:
        prerequisites_met['recommendations'].append("Consider fixing non-critical issues for best results")
    
    logger.info(f"Migration prerequisites validation completed. Ready for migration: {prerequisites_met['ready_for_migration']}")
    
    return prerequisites_met


def run_comprehensive_migration_with_validation(context, migrations: List[BaseMigration], 
                                               create_snapshot: bool = True) -> Dict[str, Any]:
    """Run comprehensive migration with full validation and rollback support.
    
    Args:
        context: Migration context
        migrations: List of migrations to run
        create_snapshot: Whether to create pre-migration snapshot
        
    Returns:
        Comprehensive migration results
    """
    logger.info(f"Starting comprehensive migration with {len(migrations)} migrations")
    
    migration_results = {
        'status': 'in_progress',
        'started_at': datetime.now().isoformat(),
        'pre_migration_validation': None,
        'snapshot_id': None,
        'migration_results': None,
        'post_migration_validation': None,
        'rollback_available': False
    }
    
    try:
        # Step 1: Pre-migration validation
        logger.info("Step 1: Pre-migration validation...")
        prerequisites = validate_migration_prerequisites(context)
        migration_results['pre_migration_validation'] = prerequisites
        
        if not prerequisites['ready_for_migration']:
            raise MigrationError("Critical data integrity issues prevent migration. Please resolve them first.")
        
        # Step 2: Create pre-migration snapshot
        if create_snapshot:
            logger.info("Step 2: Creating pre-migration snapshot...")
            rollback_manager = MigrationRollbackManager(context)
            snapshot_result = rollback_manager.create_pre_migration_snapshot("comprehensive_migration")
            migration_results['snapshot_id'] = snapshot_result['snapshot_id']
            migration_results['rollback_available'] = True
        
        # Step 3: Run migrations
        logger.info("Step 3: Running migrations...")
        migration_manager = MigrationManager(context)
        
        for migration in migrations:
            migration_manager.add_migration(migration)
        
        migration_result = migration_manager.run_all_migrations(
            validate_first=True,
            create_backup=True,
            stop_on_failure=False
        )
        migration_results['migration_results'] = migration_result
        
        # Step 4: Post-migration validation
        logger.info("Step 4: Post-migration validation...")
        validator = DataIntegrityValidator(context)
        post_validation = validator.validate_all_data_integrity()
        migration_results['post_migration_validation'] = post_validation
        
        # Determine overall status
        if migration_result['status'] == 'completed' and post_validation['summary']['critical_issues'] == 0:
            migration_results['status'] = 'completed_successfully'
        elif migration_result['status'] == 'completed':
            migration_results['status'] = 'completed_with_warnings'
        else:
            migration_results['status'] = 'completed_with_errors'
        
        migration_results['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"Comprehensive migration completed with status: {migration_results['status']}")
        
        return migration_results
        
    except Exception as e:
        logger.error(f"Comprehensive migration failed: {e}")
        migration_results['status'] = 'failed'
        migration_results['error'] = str(e)
        migration_results['failed_at'] = datetime.now().isoformat()
        
        # Offer rollback if snapshot was created
        if migration_results['rollback_available']:
            logger.info("Pre-migration snapshot is available for rollback if needed")
        
        raise MigrationError(f"Comprehensive migration failed: {e}")
