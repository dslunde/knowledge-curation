"""Workflow scripts for knowledge management workflows."""

from datetime import datetime
from knowledge.curator.interfaces import IAIEnhanced
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import queryAdapter

import logging


logger = logging.getLogger("knowledge.curator.workflow")


def update_embeddings(state_change):
    """Update embeddings when entering the process state."""
    obj = state_change.object

    # Check if object has AI enhancement behavior
    ai_adapter = queryAdapter(obj, IAIEnhanced)
    if ai_adapter:
        try:
            # This would call your AI service to generate embeddings
            # For now, we'll just log the action
            logger.info(f"Updating embeddings for {obj.absolute_url()}")

            # In a real implementation, you would:
            # 1. Extract text content from the object
            # 2. Send to AI service for embedding generation
            # 3. Store the embeddings
            # ai_adapter.update_embeddings()

        except Exception as e:
            logger.error(f"Failed to update embeddings: {e!s}")


def suggest_connections(state_change):
    """Suggest connections when entering the connect state."""
    obj = state_change.object

    try:
        # This would use embeddings to find similar content
        logger.info(f"Suggesting connections for {obj.absolute_url()}")

        # In a real implementation:
        # 1. Get the object's embedding vector
        # 2. Search for similar content using vector similarity
        # 3. Store suggestions in an annotation

        # For now, we'll just add a marker annotation
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(obj)
        annotations["knowledge.curator.connection_suggestions"] = {
            "suggested_at": datetime.now().isoformat(),
            "suggestions": [],  # Would contain actual suggestions
        }

    except Exception as e:
        logger.error(f"Failed to suggest connections: {e!s}")


def validate_for_publishing(state_change):
    """Validate content before publishing."""
    obj = state_change.object
    errors = []

    # Check required fields
    if not obj.title:
        errors.append("Title is required")

    if not obj.description:
        errors.append("Description is required")

    if not getattr(obj, 'tags', None):
        errors.append("At least one tag is required")

    # Check AI processing
    if not getattr(obj, "ai_summary", None):
        errors.append("AI summary has not been generated")

    if errors:
        raise WorkflowException(
            "Cannot publish. Please fix the following issues: " +
            "; ".join(errors)
        )


def record_start_time(state_change):
    """Record when a learning goal was activated."""
    obj = state_change.object

    try:
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(obj)

        if 'knowledge.curator.learning_timeline' not in annotations:
            annotations['knowledge.curator.learning_timeline'] = {}

        timeline = annotations['knowledge.curator.learning_timeline']
        timeline['started_at'] = datetime.now().isoformat()

        # Initialize progress tracking
        if not hasattr(obj, "progress"):
            obj.progress = 0.0

    except Exception as e:
        logger.error(f"Failed to record start time: {e!s}")


def calculate_progress(state_change):
    """Calculate progress when entering review state."""
    obj = state_change.object

    try:
        # Simple progress calculation based on completed milestones
        if hasattr(obj, "milestones") and obj.milestones:
            completed = sum(1 for m in obj.milestones if m.get("completed", False))
            total = len(obj.milestones)
            obj.progress = (completed / total) * 100 if total > 0 else 0
        else:
            obj.progress = 0.0

        logger.info(f"Calculated progress for {obj.title}: {obj.progress}%")

    except Exception as e:
        logger.error(f"Failed to calculate progress: {e!s}")


def validate_completion(state_change):
    """Validate that a learning goal can be completed."""
    obj = state_change.object

    # Check minimum progress
    progress = getattr(obj, "progress", 0)
    if progress < 80:
        raise WorkflowException(
            f"Cannot complete learning goal. Progress is only {progress}%. "
            "Minimum 80% progress required."
        )

    # Check if reflection/summary is provided
    if not getattr(obj, "reflection", None):
        raise WorkflowException(
            "Please provide a reflection or summary of your learning before completing."
        )


def record_completion_time(state_change):
    """Record when a learning goal was completed."""
    obj = state_change.object

    try:
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(obj)

        timeline = annotations.get('knowledge.curator.learning_timeline', {})
        timeline['completed_at'] = datetime.now().isoformat()

        # Calculate duration if start time exists
        if "started_at" in timeline:
            start = datetime.fromisoformat(timeline["started_at"])
            end = datetime.fromisoformat(timeline["completed_at"])
            duration = end - start
            timeline['duration_days'] = duration.days

        annotations['knowledge.curator.learning_timeline'] = timeline

        # Set final progress to 100%
        obj.progress = 100.0

    except Exception as e:
        logger.error(f"Failed to record completion time: {e!s}")


# Workflow transition event handlers
def handle_workflow_transition(obj, event):
    """Handle workflow transitions for additional processing."""
    if not event.transition:
        return

    transition_id = event.transition.id
    workflow_id = event.workflow.id

    logger.info(
        f"Workflow transition: {workflow_id}/{transition_id} for {obj.absolute_url()}"
    )

    # Add any additional transition handling here
    # For example, sending notifications, updating indexes, etc.
