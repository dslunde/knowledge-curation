"""Event subscribers for automatic vector database operations."""

from knowledge.curator.vector.config import get_vector_config
from knowledge.curator.vector.config import INDEXED_WORKFLOW_STATES
from knowledge.curator.vector.config import SUPPORTED_CONTENT_TYPES
from knowledge.curator.vector.management import VectorCollectionManager
from knowledge.curator.interfaces import IKnowledgeItem
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
    """Check if content should be indexed in vector database.
    
    Knowledge Items receive priority indexing based on their enhancement priority score.
    """
    from knowledge.curator.config.enhancement_priority import should_prioritize_content_type
    from knowledge.curator.workflow_scripts import calculate_enhancement_priority
    
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
        
    # Knowledge Items get priority indexing
    if obj.portal_type == "KnowledgeItem":
        # Calculate priority score to determine urgency
        try:
            priority_score = calculate_enhancement_priority(obj)
            logger.info(f"Knowledge Item {obj.absolute_url()} priority score: {priority_score}")
            # Always index Knowledge Items but log their priority
            return True
        except Exception as e:
            logger.warning(f"Could not calculate priority for {obj.absolute_url()}: {e}")
            # Still index even if priority calculation fails
            return True
    
    # Check if other content types should be prioritized
    if should_prioritize_content_type(obj.portal_type):
        logger.info(f"Prioritizing {obj.portal_type}: {obj.absolute_url()}")
        return True

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
            # Update relationships for Knowledge Items
            if obj.portal_type == "KnowledgeItem":
                _update_dependent_content_relationships(obj)
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
            # Update relationships for Knowledge Items
            if obj.portal_type == "KnowledgeItem":
                _update_dependent_content_relationships(obj)
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

    logger.info(
        f"Workflow transition for {obj.absolute_url()}: {old_state} -> {new_state}"
    )

    # Check if we should index or remove from index
    should_index_now = new_state in INDEXED_WORKFLOW_STATES
    was_indexed = old_state in INDEXED_WORKFLOW_STATES if old_state else False

    try:
        manager = VectorCollectionManager()

        if should_index_now and not was_indexed:
            # Entering an indexed state - create/update vector
            success = manager.update_content_vector(obj)
            if success:
                logger.info(
                    f"Created vector after transition to {new_state}: "
                    f"{obj.absolute_url()}"
                )
                # Update relationships for Knowledge Items
                if obj.portal_type == "KnowledgeItem":
                    _update_dependent_content_relationships(obj)

        elif was_indexed and not should_index_now:
            # Leaving an indexed state - remove vector
            success = manager.delete_content_vector(obj.UID())
            if success:
                logger.info(
                    f"Deleted vector after transition to {new_state}: "
                    f"{obj.absolute_url()}"
                )

        elif should_index_now and was_indexed:
            # Moving between indexed states - update vector
            success = manager.update_content_vector(obj)
            if success:
                logger.info(
                    f"Updated vector after transition to {new_state}: "
                    f"{obj.absolute_url()}"
                )
                # Update relationships for Knowledge Items
                if obj.portal_type == "KnowledgeItem":
                    _update_dependent_content_relationships(obj)

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


def _update_dependent_content_relationships(knowledge_item):
    """Update dependent content relationships when Knowledge Item changes.
    
    Maintains Knowledge Item prerequisite and enables relationships when content
    changes, ensuring the knowledge graph connections remain consistent.
    
    Args:
        knowledge_item: The KnowledgeItem object that was modified
    """
    from knowledge.curator.interfaces import IKnowledgeItem
    
    # Only process Knowledge Items
    if not IKnowledgeItem.providedBy(knowledge_item):
        return
        
    try:
        logger.info(f"Updating relationships for Knowledge Item: {knowledge_item.absolute_url()}")
        
        # Update prerequisite relationships
        _update_prerequisite_relationships(knowledge_item)
        
        # Update enables relationships
        _update_enables_relationships(knowledge_item)
        
        # Validate relationship integrity
        _validate_relationship_integrity(knowledge_item)
        
        logger.info(f"Successfully updated relationships for: {knowledge_item.absolute_url()}")
        
    except Exception as e:
        logger.error(f"Error updating relationships for {knowledge_item.absolute_url()}: {e}")


def _update_prerequisite_relationships(knowledge_item):
    """Update prerequisite relationships for a Knowledge Item.
    
    Ensures that prerequisite items still exist and maintains bidirectional
    relationship consistency between prerequisite_items and enables_items.
    """
    if not hasattr(knowledge_item, 'prerequisite_items') or not knowledge_item.prerequisite_items:
        return
        
    # Get current prerequisites
    current_prerequisites = list(knowledge_item.prerequisite_items)
    valid_prerequisites = []
    
    for prereq_uid in current_prerequisites:
        try:
            prereq_item = api.content.get(UID=prereq_uid)
            if prereq_item and IKnowledgeItem.providedBy(prereq_item):
                valid_prerequisites.append(prereq_uid)
                
                # Ensure bidirectional relationship
                if hasattr(prereq_item, 'enables_items'):
                    if not prereq_item.enables_items:
                        prereq_item.enables_items = []
                    if knowledge_item.UID() not in prereq_item.enables_items:
                        prereq_item.enables_items.append(knowledge_item.UID())
                        prereq_item._p_changed = True
                        logger.debug(f"Added enables relationship: {prereq_item.absolute_url()} -> {knowledge_item.absolute_url()}")
            else:
                logger.warning(f"Invalid prerequisite reference {prereq_uid} removed from {knowledge_item.absolute_url()}")
                
        except Exception as e:
            logger.error(f"Error processing prerequisite {prereq_uid}: {e}")
    
    # Update prerequisite list if items were removed
    if len(valid_prerequisites) != len(current_prerequisites):
        knowledge_item.prerequisite_items = valid_prerequisites
        knowledge_item._p_changed = True


def _update_enables_relationships(knowledge_item):
    """Update enables relationships for a Knowledge Item.
    
    Ensures that enabled items still exist and maintains bidirectional
    relationship consistency between enables_items and prerequisite_items.
    """
    if not hasattr(knowledge_item, 'enables_items') or not knowledge_item.enables_items:
        return
        
    # Get current enabled items
    current_enabled = list(knowledge_item.enables_items)
    valid_enabled = []
    
    for enabled_uid in current_enabled:
        try:
            enabled_item = api.content.get(UID=enabled_uid)
            if enabled_item and IKnowledgeItem.providedBy(enabled_item):
                valid_enabled.append(enabled_uid)
                
                # Ensure bidirectional relationship
                if hasattr(enabled_item, 'prerequisite_items'):
                    if not enabled_item.prerequisite_items:
                        enabled_item.prerequisite_items = []
                    if knowledge_item.UID() not in enabled_item.prerequisite_items:
                        enabled_item.prerequisite_items.append(knowledge_item.UID())
                        enabled_item._p_changed = True
                        logger.debug(f"Added prerequisite relationship: {knowledge_item.absolute_url()} -> {enabled_item.absolute_url()}")
            else:
                logger.warning(f"Invalid enables reference {enabled_uid} removed from {knowledge_item.absolute_url()}")
                
        except Exception as e:
            logger.error(f"Error processing enabled item {enabled_uid}: {e}")
    
    # Update enables list if items were removed
    if len(valid_enabled) != len(current_enabled):
        knowledge_item.enables_items = valid_enabled
        knowledge_item._p_changed = True


def _validate_relationship_integrity(knowledge_item):
    """Validate relationship integrity for a Knowledge Item.
    
    Checks for circular dependencies and ensures relationship consistency
    across the knowledge graph.
    """
    try:
        # Use the knowledge item's built-in validation
        if hasattr(knowledge_item, 'validate_relationships'):
            validation_result = knowledge_item.validate_relationships()
            if not validation_result['valid']:
                logger.warning(f"Relationship integrity issues for {knowledge_item.absolute_url()}: {validation_result['errors']}")
                
                # Attempt to fix circular dependencies by removing problematic prerequisites
                if hasattr(knowledge_item, 'prerequisite_items') and knowledge_item.prerequisite_items:
                    for error in validation_result['errors']:
                        if 'Circular dependency' in error:
                            # Extract the problematic UID and remove it
                            for prereq_uid in list(knowledge_item.prerequisite_items):
                                if knowledge_item._would_create_circular_dependency(prereq_uid):
                                    knowledge_item.prerequisite_items.remove(prereq_uid)
                                    knowledge_item._p_changed = True
                                    logger.info(f"Removed circular dependency: {prereq_uid} from {knowledge_item.absolute_url()}")
            else:
                logger.debug(f"Relationship integrity validated for: {knowledge_item.absolute_url()}")
                
    except Exception as e:
        logger.error(f"Error validating relationship integrity for {knowledge_item.absolute_url()}: {e}")
