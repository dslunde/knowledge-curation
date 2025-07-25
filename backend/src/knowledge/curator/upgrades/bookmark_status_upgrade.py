"""Upgrade step for BookmarkPlus status tracking fields.

This upgrade:
1. Updates existing BookmarkPlus objects with new status values
2. Sets default timestamps for existing bookmarks
3. Migrates old status values to new schema
"""

from datetime import datetime
from plone import api
import logging

logger = logging.getLogger("knowledge.curator.upgrades")


def upgrade_bookmark_status_fields(context):
    """Upgrade BookmarkPlus objects to use new status tracking fields.
    
    - Updates read_status vocabulary values
    - Adds access_date and last_reviewed_date fields
    - Migrates old status values to new ones
    """
    catalog = api.portal.get_tool("portal_catalog")
    
    # Find all BookmarkPlus objects
    brains = catalog(portal_type='BookmarkPlus')
    
    logger.info(f"Starting BookmarkPlus status upgrade for {len(brains)} items")
    
    status_mapping = {
        'unread': 'unread',
        'reading': 'in_progress',
        'read': 'completed',
    }
    
    updated_count = 0
    error_count = 0
    
    for brain in brains:
        try:
            obj = brain.getObject()
            
            # Update read_status if needed
            current_status = getattr(obj, 'read_status', 'unread')
            if current_status in status_mapping:
                new_status = status_mapping[current_status]
                if new_status != current_status:
                    obj.read_status = new_status
                    logger.info(f"Updated status for {obj.Title()}: {current_status} -> {new_status}")
            
            # Set access_date if not present
            if not hasattr(obj, 'access_date') or obj.access_date is None:
                # Use creation date as a reasonable default
                obj.access_date = obj.created()
                logger.debug(f"Set access_date for {obj.Title()} to creation date")
            
            # Set last_reviewed_date for completed items
            if not hasattr(obj, 'last_reviewed_date') or obj.last_reviewed_date is None:
                if obj.read_status in ['completed', 'archived']:
                    # Use modification date as a reasonable default
                    obj.last_reviewed_date = obj.modified()
                    logger.debug(f"Set last_reviewed_date for {obj.Title()} to modification date")
            
            # Reindex the object to update catalog
            obj.reindexObject(idxs=['read_status'])
            
            updated_count += 1
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error upgrading bookmark {brain.getPath()}: {str(e)}")
    
    logger.info(f"BookmarkPlus status upgrade complete. Updated: {updated_count}, Errors: {error_count}")
    
    return f"Upgraded {updated_count} BookmarkPlus objects ({error_count} errors)"


def add_bookmark_status_indexes(context):
    """Add catalog indexes for the new bookmark status fields."""
    catalog = api.portal.get_tool("portal_catalog")
    
    indexes_to_add = [
        ('read_status', 'FieldIndex'),
        ('access_date', 'DateIndex'),
        ('last_reviewed_date', 'DateIndex'),
    ]
    
    for index_name, index_type in indexes_to_add:
        if index_name not in catalog.indexes():
            catalog.addIndex(index_name, index_type)
            logger.info(f"Added {index_type} for {index_name}")
    
    # Add metadata columns for easy access
    metadata_to_add = ['read_status', 'access_date', 'last_reviewed_date']
    
    for metadata_name in metadata_to_add:
        if metadata_name not in catalog.schema():
            catalog.addColumn(metadata_name)
            logger.info(f"Added metadata column for {metadata_name}")
    
    return "Catalog indexes and metadata added for bookmark status tracking"