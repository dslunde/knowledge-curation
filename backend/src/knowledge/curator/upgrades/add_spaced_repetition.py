"""Upgrade step to add spaced repetition behavior to existing content."""

from plone import api
import logging

logger = logging.getLogger('knowledge.curator')


def add_spaced_repetition_to_content(context):
    """Add spaced repetition behavior to existing knowledge content."""

    catalog = api.portal.get_tool('portal_catalog')

    # Content types to update
    portal_types = ['ResearchNote', 'BookmarkPlus', 'LearningGoal']

    # Get portal_types tool
    types_tool = api.portal.get_tool('portal_types')

    # Update FTIs to include behavior
    behavior = 'knowledge.curator.spaced_repetition'
    updated_types = []

    for portal_type in portal_types:
        fti = types_tool.get(portal_type)
        if fti:
            behaviors = list(fti.behaviors)
            if behavior not in behaviors:
                behaviors.append(behavior)
                fti.behaviors = tuple(behaviors)
                updated_types.append(portal_type)
                logger.info(f"Added spaced repetition behavior to {portal_type}")

    # Find and update existing content
    brains = catalog(portal_type=portal_types)
    updated_count = 0

    for brain in brains:
        try:
            obj = brain.getObject()
            # The behavior adapter will be available after FTI update
            # Just reindex to ensure catalog is updated
            obj.reindexObject()
            updated_count += 1
        except Exception as e:
            logger.error(f"Error updating {brain.getPath()}: {e!s}")

    logger.info(f"Updated {updated_count} existing items with spaced repetition support")
    logger.info(f"Updated content types: {', '.join(updated_types)}")

    return f"Successfully added spaced repetition to {len(updated_types)} content types and {updated_count} items"
