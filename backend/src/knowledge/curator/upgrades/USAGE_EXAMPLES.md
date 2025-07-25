# Migration Infrastructure Usage Examples

This document provides practical examples of how to use the migration infrastructure in `migrate_relationships.py`.

## Basic Usage

### 1. Simple Connection Migration

```python
from knowledge.curator.upgrades.migrate_relationships import (
    MigrationManager, SimpleConnectionMigration
)

def upgrade_research_note_connections(context):
    """Upgrade step to migrate ResearchNote connections."""
    
    # Create migration manager
    manager = MigrationManager(context)
    
    # Add connection migration for ResearchNotes
    research_migration = SimpleConnectionMigration(
        context, 
        content_type='ResearchNote',
        batch_size=50
    )
    manager.add_migration(research_migration)
    
    # Run migration with full validation and backup
    results = manager.run_all_migrations(
        validate_first=True,
        create_backup=True,
        stop_on_failure=False
    )
    
    return f"Migration completed: {results['successful_migrations']}/{results['total_migrations']} successful"
```

### 2. Knowledge Item Relationship Migration

```python
def upgrade_knowledge_item_relationships(context):
    """Upgrade step to migrate Knowledge Item relationships."""
    
    manager = MigrationManager(context)
    
    # Add Knowledge Item migration with smaller batches for safety
    ki_migration = KnowledgeItemRelationshipMigration(
        context,
        batch_size=25
    )
    manager.add_migration(ki_migration)
    
    try:
        results = manager.run_all_migrations()
        
        # Log detailed statistics
        log_migration_statistics(results)
        
        return results
        
    except Exception as e:
        # Attempt rollback on failure
        logger.error(f"Migration failed: {e}")
        rollback_results = manager.rollback_all_migrations()
        logger.info(f"Rollback completed: {rollback_results}")
        raise
```

## Advanced Usage

### 3. Custom Migration Class

```python
from knowledge.curator.upgrades.migrate_relationships import BaseMigration

class CustomFieldMigration(BaseMigration):
    """Custom migration for specific field transformation."""
    
    def __init__(self, context):
        super().__init__(context, batch_size=30)
        
        # Add custom validation
        self.add_validation_hook(self._validate_custom_field)
        
        # Add custom error handling
        self.add_error_handler(ValueError, self._handle_value_error)
        
    def get_migration_items(self):
        """Get items that need this specific migration."""
        return self.catalog(portal_type='CustomContentType')
        
    def migrate_item(self, item):
        """Perform custom migration logic."""
        try:
            # Your custom migration logic here
            old_value = getattr(item, 'old_field', None)
            if old_value:
                # Transform and set new field
                item.new_field = self._transform_value(old_value)
                delattr(item, 'old_field')
            return True
        except Exception as e:
            logger.error(f"Custom migration failed for {item}: {e}")
            return False
            
    def _validate_custom_field(self, item):
        """Custom validation logic."""
        if not hasattr(item, 'old_field'):
            return False, "No old_field to migrate"
        return True, "Has old_field"
        
    def _transform_value(self, value):
        """Transform old value to new format."""
        # Custom transformation logic
        return f"transformed_{value}"
        
    def _handle_value_error(self, exception, item):
        """Handle value errors gracefully."""
        self.progress.add_warning(
            self.get_item_identifier(item),
            f"Value transformation issue: {exception}"
        )
        return False  # Continue migration attempt
```

### 4. Multiple Content Type Migration

```python
def upgrade_all_relationship_fields(context):
    """Comprehensive migration of all relationship fields."""
    
    manager = MigrationManager(context)
    
    # Add migrations for different content types
    content_types_and_migrations = [
        ('ResearchNote', SimpleConnectionMigration),
        ('LearningGoal', SimpleConnectionMigration), 
        ('ProjectLog', SimpleConnectionMigration),
        ('KnowledgeItem', KnowledgeItemRelationshipMigration),
    ]
    
    for content_type, migration_class in content_types_and_migrations:
        if content_type == 'KnowledgeItem':
            migration = migration_class(context)
        else:
            migration = migration_class(context, content_type)
        manager.add_migration(migration)
    
    # Run all migrations
    results = manager.run_all_migrations(
        validate_first=True,
        create_backup=True,
        stop_on_failure=False  # Continue even if one content type fails
    )
    
    # Generate detailed report
    report = manager.create_progress_report()
    logger.info(f"Migration Report:\\n{report}")
    
    return results
```

## Utility Functions

### 5. Using Utility Functions

```python
from knowledge.curator.upgrades.migrate_relationships import (
    create_relationship_migration, validate_uid_references
)

# Create a migration function for a specific field transformation
migrate_citations = create_relationship_migration(
    source_field='cited_papers',
    target_field='relationships', 
    relationship_type='cites',
    default_strength=0.8
)

# Use in a custom migration
class CitationMigration(BaseMigration):
    def migrate_item(self, item):
        return migrate_citations(item)

# Add UID validation to any migration
def setup_migration_with_validation(migration, catalog):
    """Setup migration with standard validation."""
    migration.add_validation_hook(validate_uid_references(catalog))
    migration.add_validation_hook(lambda item: (
        hasattr(item, 'title') and item.title,
        "Item must have title"
    ))
    return migration
```

## Error Handling and Recovery

### 6. Rollback Capabilities

```python
def safe_migration_with_rollback(context):
    """Perform migration with explicit rollback handling."""
    
    manager = MigrationManager(context)
    
    # Add your migrations
    migration = SimpleConnectionMigration(context, 'ResearchNote')
    manager.add_migration(migration)
    
    try:
        # Attempt migration
        results = manager.run_all_migrations(create_backup=True)
        
        # Verify results meet criteria
        if results['successful_migrations'] < results['total_migrations']:
            logger.warning("Not all migrations succeeded, rolling back...")
            rollback_results = manager.rollback_all_migrations()
            return {
                'status': 'rolled_back',
                'reason': 'Partial failure detected',
                'rollback': rollback_results
            }
            
        return results
        
    except Exception as e:
        logger.error(f"Migration failed catastrophically: {e}")
        
        # Attempt rollback
        try:
            rollback_results = manager.rollback_all_migrations()
            return {
                'status': 'failed_and_rolled_back',
                'error': str(e),
                'rollback': rollback_results
            }
        except Exception as rollback_error:
            logger.error(f"Rollback also failed: {rollback_error}")
            return {
                'status': 'failed_rollback_failed',
                'migration_error': str(e),
                'rollback_error': str(rollback_error)
            }
```

### 7. Progress Monitoring

```python
def migration_with_progress_monitoring(context):
    """Migration with detailed progress monitoring."""
    
    manager = MigrationManager(context)
    migration = SimpleConnectionMigration(context, 'ResearchNote')
    
    # Add progress monitoring hooks
    def log_progress(item, success):
        if migration.progress.processed_items % 10 == 0:
            logger.info(f"Progress: {migration.progress.completion_percentage:.1f}% "
                       f"({migration.progress.processed_items}/{migration.progress.total_items})")
    
    migration.add_post_migration_hook(log_progress)
    manager.add_migration(migration)
    
    # Run with monitoring
    results = manager.run_all_migrations()
    
    # Create detailed report
    final_report = {
        'migration_results': results,
        'detailed_progress': migration.progress.to_dict(),
        'backup_info': {
            'items_backed_up': migration.backup.backup_metadata['items_count'],
            'backup_created': migration.backup.backup_metadata['created']
        }
    }
    
    return final_report
```

## Best Practices

1. **Always create backups** for production migrations
2. **Use validation hooks** to catch issues before migration
3. **Process in batches** to avoid memory issues and allow progress tracking
4. **Handle errors gracefully** with custom error handlers
5. **Test rollback capabilities** before running on production data
6. **Monitor progress** for long-running migrations
7. **Log comprehensively** for debugging and audit trails

## Testing Migration Code

```python
def test_migration_logic():
    """Test migration logic with mock data."""
    
    # Create mock context (for testing)
    class MockContext:
        pass
    
    class MockCatalog:
        def __call__(self, **kwargs):
            return []  # Return empty for testing
            
    context = MockContext()
    
    # Test progress tracking
    progress = MigrationProgress(100)
    progress.start()
    progress.add_success('test1')
    progress.add_failure('test2', 'Test error')
    progress.finish()
    
    assert progress.completion_percentage == 2.0
    assert progress.success_rate == 50.0
    
    # Test backup functionality
    backup = MigrationBackup()
    export = backup.export_backup()
    
    assert 'metadata' in export
    assert 'data' in export
    
    print("✓ All tests passed")

# Run test
test_migration_logic()
```

This infrastructure provides a robust, flexible foundation for migrating relationship data while maintaining data integrity and providing comprehensive error handling and recovery capabilities.