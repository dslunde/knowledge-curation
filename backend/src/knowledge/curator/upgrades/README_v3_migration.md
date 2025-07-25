# Knowledge Curator V3 Data Schema Migration

## Overview

This migration (v2 → v3) converts simple text lists to structured objects throughout the Knowledge Curator content types. It provides intelligent defaults based on content analysis and implements safe rollback capabilities.

## What Gets Migrated

### ResearchNote
- **key_insights**: Text list → IKeyInsight objects with:
  - `text`: The insight content
  - `importance`: Analyzed from text (high/medium/low)
  - `evidence`: Optional supporting evidence
  - `timestamp`: When the insight was created
  
- **authors**: Text list → IAuthor objects with:
  - `name`: Author name
  - `email`, `orcid`, `affiliation`: Set to None (can be updated later)

- **connections**: Simple UIDs → IKnowledgeRelationship objects with:
  - `relationship_type`: Intelligent defaults based on content types
  - `strength`: Default 0.5
  - `confidence`: Default 0.8

### LearningGoal
- **milestones**: Text list → ILearningMilestone objects with:
  - `id`: Auto-generated unique ID
  - `title`: From text (truncated if > 100 chars)
  - `description`: Full text if > 100 chars
  - `status`: Analyzed from text
  - `progress_percentage`: Based on status

### ProjectLog
- **entries**: Text list → IProjectLogEntry objects with:
  - `id`: Auto-generated unique ID
  - `timestamp`: Migration timestamp
  - `author`: "Migrated" for old entries
  - `entry_type`: Default "note"
  - `description`: Original text

- **deliverables**: Text list → IProjectDeliverable objects with:
  - `title`: Original text
  - `status`: Analyzed from text
  - `completion_percentage`: Based on status

## Running the Migration

### Via Plone Upgrade Interface

1. Go to Site Setup → Add-ons
2. Find "Knowledge Curator"
3. Click "Upgrade" if available
4. The migration will run automatically as part of the v2→v3 upgrade

### Via Command Line (for testing)

```bash
# Test migration (dry run)
bin/instance debug
>>> from knowledge.curator.upgrades.test_v3_migration import test_migration, check_content_state
>>> check_content_state()  # See current state
>>> test_migration(dry_run=True)  # Test without committing

# Run actual migration
>>> test_migration(dry_run=False)  # Commits changes
```

### Manual Migration

```bash
bin/instance run knowledge/curator/upgrades/to_v3.py
```

## Intelligent Defaults

The migration analyzes text content to set appropriate defaults:

### Importance/Priority Detection
- **High**: Contains words like "critical", "urgent", "important", "essential"
- **Low**: Contains words like "minor", "optional", "nice to have"
- **Medium**: Default for everything else

### Status Detection
- **Completed**: Contains words like "completed", "done", "finished"
- **In Progress**: Contains words like "in progress", "working on", "started"
- **Pending**: Default for everything else

### Confidence Scoring
- **0.9**: Long text (>100 chars) with validation words ("proven", "confirmed")
- **0.5**: Short text (<20 chars) or contains questions
- **0.7**: Default confidence level

### Relationship Type Detection
- ResearchNote → ResearchNote: "cites"
- LearningGoal → ResearchNote: "supports"
- Default: "related"

## Rollback Capabilities

The migration includes comprehensive rollback support:

1. **Automatic Backup**: Before migrating each object, its data is backed up
2. **Error Handling**: If migration fails, the object is automatically rolled back
3. **Transaction Safety**: Uses savepoints every 50 objects
4. **Manual Rollback**: Available via `rollback_v3_migration()` function

## Edge Cases Handled

1. **Empty Values**: Null/empty entries are skipped
2. **Already Migrated**: Objects already in new format are preserved
3. **Mixed Formats**: Handles partially migrated content
4. **Missing Fields**: Initializes required fields if not present
5. **Malformed Data**: Tries to extract usable content, logs errors

## Post-Migration

After migration:
1. Catalog is rebuilt to ensure all indexes are updated
2. Objects are reindexed with new field values
3. Old `connections` fields are removed after conversion to relationships

## Troubleshooting

### Check Migration Status
```python
from knowledge.curator.upgrades.test_v3_migration import check_content_state
check_content_state()
```

### View Migration Logs
Check the Plone instance log for detailed migration progress and any errors.

### Common Issues

1. **"Object has no attribute 'key_insights'"**
   - The content type may not have been properly initialized
   - Run the migration again, it will skip already migrated items

2. **Performance Issues**
   - For large sites, run migration during off-peak hours
   - Consider migrating in batches using the test script

3. **Partial Migration**
   - Check logs for specific errors
   - Failed objects can be migrated individually

## Development Notes

### Adding New Migrations

1. Create converter function in `V3DataMigration` class
2. Add field to `backup_object_data()` method
3. Add migration logic to content type specific method
4. Update this documentation

### Testing New Content Types

Use the test script to create sample content:
```python
from knowledge.curator.upgrades.test_v3_migration import create_test_content
test_content = create_test_content()
```

## Version Information

- **Source Version**: 2
- **Destination Version**: 3
- **Profile**: knowledge.curator:default
- **Handler**: knowledge.curator.upgrades.to_v3.data_schema_migration_to_v3