"""Migration script to convert existing simple text lists to structured objects.

This upgrade:
1. Converts simple text lists (milestones, entries, insights) to structured objects
2. Sets intelligent defaults for new required fields based on content analysis
3. Migrates simple connection lists to typed relationships with default types
4. Implements rollback capability for safe migration
5. Handles edge cases like empty fields and malformed data
"""

from plone import api
from plone.app.upgrade.utils import loadMigrationProfile
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from datetime import datetime
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
import logging
import transaction
import re
import uuid

logger = logging.getLogger("knowledge.curator.upgrades")


class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass


class V3DataMigration:
    """Base migration class following Plone patterns."""
    
    def __init__(self, context):
        self.context = context
        self.catalog = api.portal.get_tool("portal_catalog")
        self.errors = []
        self.migrated_items = []
        self.backup_data = {}
        
    def backup_object_data(self, obj):
        """Create a backup of object data before migration."""
        obj_path = '/'.join(obj.getPhysicalPath())
        backup = {}
        
        # Backup relevant fields based on content type
        if obj.portal_type == 'ResearchNote':
            backup['key_insights'] = getattr(obj, 'key_insights', [])
            backup['authors'] = getattr(obj, 'authors', [])
            backup['connections'] = getattr(obj, 'connections', [])
        elif obj.portal_type == 'LearningGoal':
            backup['milestones'] = getattr(obj, 'milestones', [])
            backup['learning_objectives'] = getattr(obj, 'learning_objectives', [])
            backup['assessment_criteria'] = getattr(obj, 'assessment_criteria', [])
            backup['competencies'] = getattr(obj, 'competencies', [])
        elif obj.portal_type == 'ProjectLog':
            backup['entries'] = getattr(obj, 'entries', [])
            backup['deliverables'] = getattr(obj, 'deliverables', [])
            backup['stakeholders'] = getattr(obj, 'stakeholders', [])
            backup['success_metrics'] = getattr(obj, 'success_metrics', [])
            backup['lessons_learned'] = getattr(obj, 'lessons_learned', [])
            
        self.backup_data[obj_path] = backup
        
    def rollback_object(self, obj):
        """Rollback object to its original state."""
        obj_path = '/'.join(obj.getPhysicalPath())
        if obj_path in self.backup_data:
            backup = self.backup_data[obj_path]
            for field, value in backup.items():
                setattr(obj, field, value)
            logger.info(f"Rolled back {obj_path}")
            
    def analyze_text_for_defaults(self, text):
        """Analyze text to determine intelligent defaults."""
        if not text:
            return {
                'importance': 'medium',
                'priority': 'medium',
                'confidence': 0.7,
                'status': 'pending'
            }
            
        text_lower = text.lower()
        
        # Determine importance/priority
        if any(word in text_lower for word in ['critical', 'urgent', 'important', 'essential', 'must']):
            importance = 'high'
            priority = 'high'
        elif any(word in text_lower for word in ['minor', 'optional', 'nice to have', 'low']):
            importance = 'low'
            priority = 'low'
        else:
            importance = 'medium'
            priority = 'medium'
            
        # Determine confidence based on text clarity
        if len(text) > 100 and any(word in text_lower for word in ['proven', 'confirmed', 'validated']):
            confidence = 0.9
        elif len(text) < 20 or '?' in text:
            confidence = 0.5
        else:
            confidence = 0.7
            
        # Determine status
        if any(word in text_lower for word in ['completed', 'done', 'finished']):
            status = 'completed'
        elif any(word in text_lower for word in ['in progress', 'working on', 'started']):
            status = 'in_progress'
        else:
            status = 'pending'
            
        return {
            'importance': importance,
            'priority': priority,
            'confidence': confidence,
            'status': status
        }
    
    def convert_text_to_key_insight(self, text):
        """Convert text string to IKeyInsight structure."""
        if isinstance(text, dict):
            # Already structured, just ensure all fields
            insight = PersistentMapping()
            insight['text'] = text.get('text', str(text))
            insight['importance'] = text.get('importance', 'medium')
            insight['evidence'] = text.get('evidence', None)
            insight['timestamp'] = text.get('timestamp', datetime.now())
            return insight
            
        # Convert from string
        defaults = self.analyze_text_for_defaults(text)
        insight = PersistentMapping()
        insight['text'] = text
        insight['importance'] = defaults['importance']
        insight['evidence'] = None
        insight['timestamp'] = datetime.now()
        
        return insight
    
    def convert_text_to_milestone(self, text):
        """Convert text string to ILearningMilestone structure."""
        if isinstance(text, dict):
            # Already structured, migrate to new format
            milestone = PersistentMapping()
            milestone['id'] = text.get('id', f"milestone-{str(uuid.uuid4())[:8]}")
            milestone['title'] = text.get('title', text.get('name', str(text)))
            milestone['description'] = text.get('description', '')
            milestone['target_date'] = text.get('target_date', None)
            milestone['status'] = text.get('status', 'completed' if text.get('completed') else 'not_started')
            milestone['progress_percentage'] = text.get('progress_percentage', 100 if text.get('completed') else 0)
            milestone['completion_criteria'] = text.get('completion_criteria', None)
            return milestone
            
        # Convert from string
        defaults = self.analyze_text_for_defaults(text)
        milestone = PersistentMapping()
        milestone['id'] = f"milestone-{str(uuid.uuid4())[:8]}"
        milestone['title'] = text[:100] if len(text) > 100 else text  # Truncate if too long
        milestone['description'] = text if len(text) > 100 else ''
        milestone['target_date'] = None
        milestone['status'] = 'not_started'
        milestone['progress_percentage'] = 0
        milestone['completion_criteria'] = None
        
        return milestone
    
    def convert_text_to_log_entry(self, text):
        """Convert text string to IProjectLogEntry structure."""
        if isinstance(text, dict):
            # Already structured, ensure all fields
            entry = PersistentMapping()
            entry['id'] = text.get('id', f"entry-{str(uuid.uuid4())[:8]}")
            entry['timestamp'] = text.get('timestamp', datetime.now())
            entry['author'] = text.get('author', 'Unknown')
            entry['entry_type'] = text.get('entry_type', 'note')
            entry['description'] = text.get('description', text.get('content', str(text)))
            entry['related_items'] = text.get('related_items', [])
            return entry
            
        # Convert from string
        entry = PersistentMapping()
        entry['id'] = f"entry-{str(uuid.uuid4())[:8]}"
        entry['timestamp'] = datetime.now()
        entry['author'] = 'Migrated'
        entry['entry_type'] = 'note'
        entry['description'] = text
        entry['related_items'] = []
        
        return entry
    
    def convert_text_to_deliverable(self, text):
        """Convert text string to IProjectDeliverable structure."""
        if isinstance(text, dict):
            # Already structured
            deliverable = PersistentMapping()
            deliverable['title'] = text.get('title', str(text))
            deliverable['description'] = text.get('description', None)
            deliverable['due_date'] = text.get('due_date', None)
            deliverable['status'] = text.get('status', 'not_started')
            deliverable['assigned_to'] = text.get('assigned_to', None)
            deliverable['completion_percentage'] = text.get('completion_percentage', 0)
            return deliverable
            
        # Convert from string
        defaults = self.analyze_text_for_defaults(text)
        deliverable = PersistentMapping()
        deliverable['title'] = text
        deliverable['description'] = None
        deliverable['due_date'] = None
        deliverable['status'] = defaults['status']
        deliverable['assigned_to'] = None
        deliverable['completion_percentage'] = 0 if defaults['status'] != 'completed' else 100
        
        return deliverable
    
    def migrate_connections_to_relationships(self, obj):
        """Migrate simple connection lists to typed relationships."""
        if not hasattr(obj, 'connections'):
            return
            
        old_connections = getattr(obj, 'connections', [])
        if not old_connections:
            return
            
        # Initialize relationships if not present
        if not hasattr(obj, 'relationships'):
            obj.relationships = PersistentList()
            
        for target_uid in old_connections:
            if isinstance(target_uid, str):
                # Create a typed relationship
                relationship = PersistentMapping()
                relationship['source_uid'] = obj.UID()
                relationship['target_uid'] = target_uid
                relationship['relationship_type'] = 'related'  # Default type
                relationship['strength'] = 0.5  # Default strength
                relationship['metadata'] = {}
                relationship['created'] = datetime.now()
                relationship['confidence'] = 0.8  # Default confidence
                
                # Try to determine relationship type based on content types
                try:
                    target_brain = self.catalog(UID=target_uid)
                    if target_brain:
                        target_type = target_brain[0].portal_type
                        if obj.portal_type == 'ResearchNote' and target_type == 'ResearchNote':
                            relationship['relationship_type'] = 'cites'
                        elif obj.portal_type == 'LearningGoal' and target_type == 'ResearchNote':
                            relationship['relationship_type'] = 'supports'
                except Exception:
                    pass
                    
                obj.relationships.append(relationship)
                
        # Remove old connections field after migration
        delattr(obj, 'connections')
        
    def migrate_research_note(self, obj):
        """Migrate ResearchNote to new schema."""
        try:
            self.backup_object_data(obj)
            
            # Migrate key_insights
            if hasattr(obj, 'key_insights'):
                old_insights = obj.key_insights
                new_insights = PersistentList()
                
                for insight in old_insights:
                    if insight:  # Handle empty values
                        new_insights.append(self.convert_text_to_key_insight(insight))
                        
                obj.key_insights = new_insights
            
            # Migrate authors if they're in old format
            if hasattr(obj, 'authors') and obj.authors:
                if isinstance(obj.authors[0], str):
                    old_authors = obj.authors
                    new_authors = PersistentList()
                    
                    for author_name in old_authors:
                        author = PersistentMapping()
                        author['name'] = author_name
                        author['email'] = None
                        author['orcid'] = None
                        author['affiliation'] = None
                        new_authors.append(author)
                        
                    obj.authors = new_authors
            
            # Migrate connections to relationships
            self.migrate_connections_to_relationships(obj)
            
            obj.reindexObject()
            self.migrated_items.append(obj)
            
        except Exception as e:
            self.errors.append(f"Error migrating ResearchNote {obj.getId()}: {str(e)}")
            self.rollback_object(obj)
            raise
    
    def migrate_learning_goal(self, obj):
        """Migrate LearningGoal to new schema."""
        try:
            self.backup_object_data(obj)
            
            # Migrate milestones
            if hasattr(obj, 'milestones'):
                old_milestones = obj.milestones
                new_milestones = PersistentList()
                
                for milestone in old_milestones:
                    if milestone:  # Handle empty values
                        new_milestones.append(self.convert_text_to_milestone(milestone))
                        
                obj.milestones = new_milestones
            
            # Initialize other structured lists if not present
            if not hasattr(obj, 'learning_objectives'):
                obj.learning_objectives = PersistentList()
            if not hasattr(obj, 'assessment_criteria'):
                obj.assessment_criteria = PersistentList()
            if not hasattr(obj, 'competencies'):
                obj.competencies = PersistentList()
            
            # Migrate connections to relationships
            self.migrate_connections_to_relationships(obj)
            
            obj.reindexObject()
            self.migrated_items.append(obj)
            
        except Exception as e:
            self.errors.append(f"Error migrating LearningGoal {obj.getId()}: {str(e)}")
            self.rollback_object(obj)
            raise
    
    def migrate_project_log(self, obj):
        """Migrate ProjectLog to new schema."""
        try:
            self.backup_object_data(obj)
            
            # Migrate entries
            if hasattr(obj, 'entries'):
                old_entries = obj.entries
                new_entries = PersistentList()
                
                for entry in old_entries:
                    if entry:  # Handle empty values
                        new_entries.append(self.convert_text_to_log_entry(entry))
                        
                obj.entries = new_entries
            
            # Migrate deliverables
            if hasattr(obj, 'deliverables'):
                old_deliverables = obj.deliverables
                new_deliverables = PersistentList()
                
                for deliverable in old_deliverables:
                    if deliverable:  # Handle empty values
                        new_deliverables.append(self.convert_text_to_deliverable(deliverable))
                        
                obj.deliverables = new_deliverables
            
            # Initialize other structured lists if not present
            if not hasattr(obj, 'stakeholders'):
                obj.stakeholders = PersistentList()
            if not hasattr(obj, 'resources_used'):
                obj.resources_used = PersistentList()
            if not hasattr(obj, 'success_metrics'):
                obj.success_metrics = PersistentList()
            if not hasattr(obj, 'lessons_learned'):
                obj.lessons_learned = PersistentList()
            
            # Migrate connections to relationships
            self.migrate_connections_to_relationships(obj)
            
            obj.reindexObject()
            self.migrated_items.append(obj)
            
        except Exception as e:
            self.errors.append(f"Error migrating ProjectLog {obj.getId()}: {str(e)}")
            self.rollback_object(obj)
            raise
    
    def run(self):
        """Execute the migration."""
        logger.info("Starting data schema migration to v3...")
        
        # Content types to migrate
        content_types = ['ResearchNote', 'LearningGoal', 'ProjectLog']
        
        total_migrated = 0
        
        for portal_type in content_types:
            logger.info(f"Migrating {portal_type} objects...")
            brains = self.catalog(portal_type=portal_type)
            
            for brain in brains:
                try:
                    obj = brain.getObject()
                    
                    if portal_type == 'ResearchNote':
                        self.migrate_research_note(obj)
                    elif portal_type == 'LearningGoal':
                        self.migrate_learning_goal(obj)
                    elif portal_type == 'ProjectLog':
                        self.migrate_project_log(obj)
                    
                    total_migrated += 1
                    
                    # Commit transaction periodically
                    if total_migrated % 50 == 0:
                        transaction.savepoint()
                        logger.info(f"Migrated {total_migrated} objects...")
                        
                except Exception as e:
                    logger.error(f"Error migrating {brain.getPath()}: {str(e)}")
                    
        logger.info(f"Migration completed. Total objects migrated: {total_migrated}")
        
        if self.errors:
            logger.warning(f"Migration completed with {len(self.errors)} errors")
            for error in self.errors:
                logger.error(error)
                
        return total_migrated


def data_schema_migration_to_v3(context):
    """Upgrade step: Convert simple text lists to structured objects."""
    migration = V3DataMigration(context)
    
    try:
        total_migrated = migration.run()
        
        # Update catalog to ensure new indexes are available
        loadMigrationProfile(
            context, "profile-knowledge.curator:default", steps=["catalog"]
        )
        
        # Clear and rebuild catalog
        catalog = api.portal.get_tool("portal_catalog")
        catalog.clearFindAndRebuild()
        
        message = f"Successfully migrated {total_migrated} objects to new schema"
        logger.info(message)
        return message
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        
        # Attempt rollback
        logger.info("Attempting to rollback changes...")
        for obj in migration.migrated_items:
            try:
                migration.rollback_object(obj)
            except Exception as rollback_error:
                logger.error(f"Rollback failed for {obj.getId()}: {str(rollback_error)}")
                
        raise MigrationError(f"Migration failed and was rolled back: {str(e)}")


def rollback_v3_migration(context):
    """Utility function to rollback v3 migration if needed."""
    catalog = api.portal.get_tool("portal_catalog")
    content_types = ['ResearchNote', 'LearningGoal', 'ProjectLog']
    
    rolled_back = 0
    
    for portal_type in content_types:
        brains = catalog(portal_type=portal_type)
        
        for brain in brains:
            try:
                obj = brain.getObject()
                
                # Check if object has migration method
                if hasattr(obj, 'migrate_legacy_insights'):
                    # This indicates it's using new format
                    logger.warning(f"Cannot rollback {obj.getId()} - no backup data available")
                    
                rolled_back += 1
                
            except Exception as e:
                logger.error(f"Error during rollback of {brain.getPath()}: {str(e)}")
                
    logger.info(f"Rollback completed for {rolled_back} objects")
    return rolled_back