"""Event handlers for Knowledge Item relationships."""

from plone import api
from zope.component import adapter
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from knowledge.curator.interfaces import IKnowledgeItem
import logging

logger = logging.getLogger('knowledge.curator')


@adapter(IKnowledgeItem, IObjectRemovedEvent)
def handle_knowledge_item_deletion(obj, event):
    """Handle cascade operations when a Knowledge Item is deleted.
    
    When a Knowledge Item is deleted:
    1. Remove it from the prerequisite_items of any items that depend on it
    2. Remove it from the enables_items of any items that it depends on
    """
    # Skip if we're moving the item (not actually deleting)
    if event.oldParent is None or event.newParent is not None:
        return
    
    deleted_uid = obj.UID()
    catalog = api.portal.get_tool('portal_catalog')
    
    # Remove from prerequisite_items of items that were enabled by this one
    if hasattr(obj, 'enables_items') and obj.enables_items:
        for enabled_uid in obj.enables_items:
            try:
                enabled_item = api.content.get(UID=enabled_uid)
                if enabled_item and hasattr(enabled_item, 'prerequisite_items'):
                    if deleted_uid in enabled_item.prerequisite_items:
                        enabled_item.prerequisite_items.remove(deleted_uid)
                        enabled_item._p_changed = True
                        logger.info(f"Removed deleted item {deleted_uid} from prerequisites of {enabled_uid}")
            except Exception as e:
                logger.error(f"Error updating enabled item {enabled_uid}: {e}")
    
    # Remove from enables_items of items that were prerequisites for this one
    if hasattr(obj, 'prerequisite_items') and obj.prerequisite_items:
        for prereq_uid in obj.prerequisite_items:
            try:
                prereq_item = api.content.get(UID=prereq_uid)
                if prereq_item and hasattr(prereq_item, 'enables_items'):
                    if deleted_uid in prereq_item.enables_items:
                        prereq_item.enables_items.remove(deleted_uid)
                        prereq_item._p_changed = True
                        logger.info(f"Removed deleted item {deleted_uid} from enables list of {prereq_uid}")
            except Exception as e:
                logger.error(f"Error updating prerequisite item {prereq_uid}: {e}")


@adapter(IKnowledgeItem, IObjectRemovedEvent)
def validate_knowledge_item_before_deletion(obj, event):
    """Validate if a Knowledge Item can be safely deleted.
    
    This could be used to prevent deletion of items that are critical prerequisites,
    but for now we'll just log warnings.
    """
    # Skip if we're moving the item (not actually deleting)
    if event.oldParent is None or event.newParent is not None:
        return
    
    # Check if this item is a prerequisite for many others
    if hasattr(obj, 'enables_items') and obj.enables_items:
        enabled_count = len(obj.enables_items)
        if enabled_count > 5:  # Arbitrary threshold
            logger.warning(
                f"Knowledge Item '{obj.Title()}' being deleted is a prerequisite for "
                f"{enabled_count} other items. This may impact learning paths."
            )