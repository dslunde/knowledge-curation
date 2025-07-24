"""Event subscribers for automatic vector database operations."""

from knowledge.curator.vector.config import get_vector_config
from knowledge.curator.vector.config import INDEXED_WORKFLOW_STATES
from knowledge.curator.vector.config import SUPPORTED_CONTENT_TYPES
from knowledge.curator.vector.management import VectorCollectionManager
from plone import api
from Products.CMFCore.interfaces import IContentish
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from zope.component import adapter
from zope.lifecycleevent import IObjectCreatedEvent
from zope.lifecycleevent import IObjectModifiedEvent
from zope.lifecycleevent import IObjectRemovedEvent

import logging


logger = logging.getLogger("knowledge.curator.vector")


def should_index_content(obj):
    """Check if content should be indexed in vector database."""
    # Check content type
    if obj.portal_type not in SUPPORTED_CONTENT_TYPES:
        return False

    # Check workflow state
    try:
        state = api.content.get_state(obj)
        if state not in INDEXED_WORKFLOW_STATES:
            return False
    except (AttributeError, KeyError):
        # No workflow or error getting state
        return False

    return True


@adapter(IContentish, IObjectCreatedEvent)
def content_created(obj, event):
    """Handle content creation - generate embeddings if configured."""
    config = get_vector_config()
    if not config["auto_index_on_create"]:
        return

    if not should_index_content(obj):
        return

    try:
        manager = VectorCollectionManager()
        success = manager.update_content_vector(obj)

        if success:
            logger.info(f"Created vector for new content: {obj.absolute_url()}")
        else:
            logger.warning(f"Failed to create vector for: {obj.absolute_url()}")

    except Exception as e:
        logger.error(f"Error in content created handler: {e}")


@adapter(IContentish, IObjectModifiedEvent)
def content_modified(obj, event):
    """Handle content modification - update embeddings if configured."""
    config = get_vector_config()
    if not config["auto_index_on_modify"]:
        return

    if not should_index_content(obj):
        return

    try:
        manager = VectorCollectionManager()
        success = manager.update_content_vector(obj)

        if success:
            logger.info(f"Updated vector for modified content: {obj.absolute_url()}")
        else:
            logger.warning(f"Failed to update vector for: {obj.absolute_url()}")

    except Exception as e:
        logger.error(f"Error in content modified handler: {e}")


@adapter(IContentish, IObjectRemovedEvent)
def content_removed(obj, event):
    """Handle content removal - delete embeddings if configured."""
    config = get_vector_config()
    if not config["auto_delete_on_remove"]:
        return

    if obj.portal_type not in SUPPORTED_CONTENT_TYPES:
        return

    try:
        manager = VectorCollectionManager()
        success = manager.delete_content_vector(obj.UID())

        if success:
            logger.info(f"Deleted vector for removed content: {obj.UID()}")
        else:
            logger.warning(f"Failed to delete vector for: {obj.UID()}")

    except Exception as e:
        logger.error(f"Error in content removed handler: {e}")


@adapter(IContentish, IAfterTransitionEvent)
def workflow_transition(obj, event):
    """Handle workflow transitions - update vectors when entering process state."""
    if obj.portal_type not in SUPPORTED_CONTENT_TYPES:
        return

    # Get the new state
    new_state = event.new_state.id
    old_state = event.old_state.id if event.old_state else None

    logger.info(f"Workflow transition for {obj.absolute_url()}: {old_state} -> {new_state}")

    # Check if we should index or remove from index
    should_index_now = new_state in INDEXED_WORKFLOW_STATES
    was_indexed = old_state in INDEXED_WORKFLOW_STATES if old_state else False

    try:
        manager = VectorCollectionManager()

        if should_index_now and not was_indexed:
            # Entering an indexed state - create/update vector
            success = manager.update_content_vector(obj)
            if success:
                logger.info(f"Created vector after transition to {new_state}: {obj.absolute_url()}")

        elif was_indexed and not should_index_now:
            # Leaving an indexed state - remove vector
            success = manager.delete_content_vector(obj.UID())
            if success:
                logger.info(f"Deleted vector after transition to {new_state}: {obj.absolute_url()}")

        elif should_index_now and was_indexed:
            # Moving between indexed states - update vector
            success = manager.update_content_vector(obj)
            if success:
                logger.info(f"Updated vector after transition to {new_state}: {obj.absolute_url()}")

    except Exception as e:
        logger.error(f"Error in workflow transition handler: {e}")


def batch_update_vectors(content_uids):
    """Batch update vectors for multiple content items."""
    try:
        manager = VectorCollectionManager()
        updated = 0
        errors = 0

        for uid in content_uids:
            try:
                brain = api.content.find(UID=uid)
                if brain:
                    obj = brain[0].getObject()
                    if should_index_content(obj):
                        success = manager.update_content_vector(obj)
                        if success:
                            updated += 1
                        else:
                            errors += 1
            except Exception as e:
                logger.error(f"Error updating vector for {uid}: {e}")
                errors += 1

        logger.info(f"Batch update completed: {updated} updated, {errors} errors")
        return {"updated": updated, "errors": errors}

    except Exception as e:
        logger.error(f"Batch update failed: {e}")
        return {"updated": 0, "errors": len(content_uids)}
