"""Workflow event handlers and subscribers."""

from knowledge.curator.interfaces import IKnowledgeItem
from knowledge.curator.interfaces import ILearningGoal
from plone import api
from Products.CMFCore.interfaces import IActionSucceededEvent
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.globalrequest import getRequest

import logging


logger = logging.getLogger("knowledge.curator.workflow_events")


@adapter(IKnowledgeItem, IActionSucceededEvent)
def knowledge_item_workflow_changed(obj, event):
    """Handle workflow changes for knowledge items."""
    if not event.transition:
        return

    transition_id = event.transition.id
    _new_state = event.new_state.id

    # Handle specific transitions
    if transition_id == "start_processing":
        handle_start_processing(obj)
    elif transition_id == "start_connecting":
        handle_start_connecting(obj)
    elif transition_id == "ready_to_publish":
        handle_publishing(obj)

    # Update catalog
    obj.reindexObject(idxs=["review_state", "modified"])


@adapter(ILearningGoal, IActionSucceededEvent)
def learning_goal_workflow_changed(obj, event):
    """Handle workflow changes for learning goals."""
    if not event.transition:
        return

    transition_id = event.transition.id

    # Send notifications for important transitions
    if transition_id == "complete":
        send_completion_notification(obj)
    elif transition_id == "abandon":
        log_abandonment(obj)

    # Update catalog
    obj.reindexObject(idxs=["review_state", "modified"])


def handle_start_processing(obj):
    """Handle entering the processing state."""
    request = getRequest()
    if request:
        api.portal.show_message(
            message="Content is now being processed. AI analysis will be performed.",
            request=request,
            type="info",
        )

    # Queue AI processing tasks with priority
    from knowledge.curator.workflow_scripts import queue_for_enhancement, calculate_enhancement_priority
    
    # Knowledge Items get priority processing
    if IKnowledgeItem.providedBy(obj):
        priority = calculate_enhancement_priority(obj) * 2.0  # Double priority
        queue_for_enhancement(obj, operation="full", priority_override=priority)
        logger.info(f"Queued Knowledge Item {obj.absolute_url()} for priority AI processing")
    else:
        queue_for_enhancement(obj, operation="full")
        logger.info(f"Queued {obj.portal_type} {obj.absolute_url()} for AI processing")


def handle_start_connecting(obj):
    """Handle entering the connecting state."""
    # Find and suggest related content
    catalog = api.portal.get_tool("portal_catalog")

    # Simple tag-based suggestions for now
    if hasattr(obj, "tags") and obj.tags:
        query = {
            "Subject": {"query": obj.tags, "operator": "or"},
            "UID": {"not": obj.UID()},  # Exclude self
        }
        brains = catalog.searchResults(**query)

        # Store suggestions
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(obj)
        annotations["knowledge.curator.related_items"] = [
            brain.UID
            for brain in brains[:10]  # Limit to 10 suggestions
        ]

        request = getRequest()
        if request:
            api.portal.show_message(
                message=f"Found {len(brains)} related items based on tags.",
                request=request,
                type="info",
            )


def handle_publishing(obj):
    """Handle publishing of content."""
    # Clear any draft markers
    from zope.annotation.interfaces import IAnnotations

    annotations = IAnnotations(obj)

    if "knowledge.curator.draft" in annotations:
        del annotations["knowledge.curator.draft"]

    # Log publication
    logger.info(f"Published knowledge item: {obj.absolute_url()}")

    # Could send notifications to subscribers here
    request = getRequest()
    if request:
        api.portal.show_message(
            message="Content has been published successfully.",
            request=request,
            type="info",
        )


def send_completion_notification(obj):
    """Send notification when a learning goal is completed."""
    # Get the owner
    owner = obj.Creator()
    member = api.user.get(userid=owner)

    if member and member.getProperty("email"):
        # In a real implementation, send email
        logger.info(
            f"Learning goal '{obj.title}' completed by {owner}. "
            f"Progress: {getattr(obj, 'progress', 0)}%"
        )

    request = getRequest()
    if request:
        api.portal.show_message(
            message="Congratulations! Learning goal completed!",
            request=request,
            type="success",
        )


def log_abandonment(obj):
    """Log when a learning goal is abandoned."""
    from datetime import datetime

    annotations = IAnnotations(obj)
    annotations["knowledge.curator.abandoned"] = {
        "date": datetime.now().isoformat(),
        "progress_at_abandonment": getattr(obj, "progress", 0),
        "reason": getRequest().form.get("reason", "Not specified"),
    }

    logger.info(
        f"Learning goal '{obj.title}' abandoned at "
        f"{getattr(obj, 'progress', 0)}% progress"
    )
