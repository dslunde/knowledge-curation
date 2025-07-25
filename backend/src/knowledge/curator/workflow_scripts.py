"""Workflow scripts for knowledge management workflows."""

from datetime import datetime
from knowledge.curator.interfaces import IAIEnhanced, IKnowledgeItem
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import queryAdapter
from zope.annotation.interfaces import IAnnotations
from plone import api
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import transaction

import logging


logger = logging.getLogger("knowledge.curator.workflow")

# Enhancement priority configuration
ENHANCEMENT_PRIORITY_CONFIG = {
    "KnowledgeItem": {
        "base_priority": 100,  # Highest priority for Knowledge Items
        "workflow_multipliers": {
            "process": 2.0,  # Double priority when in process state
            "connect": 1.5,
            "reviewed": 1.2,
            "private": 1.0,
            "published": 0.8  # Lower priority for published items
        },
        "age_decay_factor": 0.95,  # Priority decays by 5% per day
        "confidence_boost": 1.5  # Boost for low confidence items needing re-analysis
    },
    "BookmarkPlus": {
        "base_priority": 75,
        "workflow_multipliers": {
            "process": 1.8,
            "reviewed": 1.2,
            "private": 1.0,
            "published": 0.7
        },
        "age_decay_factor": 0.92,
        "confidence_boost": 1.3
    },
    "ResearchNote": {
        "base_priority": 60,
        "workflow_multipliers": {
            "process": 1.5,
            "reviewed": 1.1,
            "private": 1.0,
            "published": 0.6
        },
        "age_decay_factor": 0.90,
        "confidence_boost": 1.2
    },
    "LearningGoal": {
        "base_priority": 50,
        "workflow_multipliers": {
            "active": 1.5,
            "review": 1.3,
            "planning": 1.0,
            "completed": 0.5,
            "abandoned": 0.1
        },
        "age_decay_factor": 0.88,
        "confidence_boost": 1.1
    },
    "ProjectLog": {
        "base_priority": 40,
        "workflow_multipliers": {
            "process": 1.3,
            "reviewed": 1.1,
            "private": 1.0,
            "published": 0.5
        },
        "age_decay_factor": 0.85,
        "confidence_boost": 1.0
    },
    "default": {
        "base_priority": 30,
        "workflow_multipliers": {
            "default": 1.0
        },
        "age_decay_factor": 0.80,
        "confidence_boost": 1.0
    }
}


def calculate_enhancement_priority(obj):
    """Calculate enhancement priority score for an object."""
    portal_type = obj.portal_type
    
    # Get configuration for this type
    config = ENHANCEMENT_PRIORITY_CONFIG.get(
        portal_type, 
        ENHANCEMENT_PRIORITY_CONFIG["default"]
    )
    
    # Start with base priority
    priority = config["base_priority"]
    
    # Apply workflow state multiplier
    try:
        state = api.content.get_state(obj)
        multiplier = config["workflow_multipliers"].get(
            state, 
            config["workflow_multipliers"].get("default", 1.0)
        )
        priority *= multiplier
    except Exception:
        pass
    
    # Apply age decay (newer items get higher priority)
    try:
        created = obj.created()
        age_days = (datetime.now() - created.asdatetime()).days
        decay = config["age_decay_factor"] ** age_days
        priority *= decay
    except Exception:
        pass
    
    # Boost priority for items with low AI confidence
    ai_adapter = queryAdapter(obj, IAIEnhanced)
    if ai_adapter:
        confidence = getattr(ai_adapter, 'overall_confidence', None)
        if confidence is not None and confidence < 0.7:
            priority *= config["confidence_boost"]
    
    # Special boost for Knowledge Items
    if IKnowledgeItem.providedBy(obj):
        # Additional factors for Knowledge Items
        if not getattr(obj, 'ai_summary', None):
            priority *= 1.5  # No AI summary yet
        if not getattr(obj, 'extracted_concepts', None):
            priority *= 1.3  # No concepts extracted
        if not getattr(obj, 'connections', None):
            priority *= 1.2  # No connections established
    
    return priority


def update_embeddings(state_change):
    """Update embeddings when entering the process state."""
    obj = state_change.object
    
    # Queue for enhancement with calculated priority
    queue_for_enhancement(obj, operation="embeddings")
    
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


def queue_for_enhancement(obj, operation="full", priority_override=None):
    """Add an object to the enhancement queue with priority."""
    portal = api.portal.get()
    annotations = IAnnotations(portal)
    
    # Initialize enhancement queue if needed
    if "knowledge.curator.enhancement_queue" not in annotations:
        annotations["knowledge.curator.enhancement_queue"] = PersistentMapping()
    
    queue = annotations["knowledge.curator.enhancement_queue"]
    
    # Calculate priority
    priority = priority_override or calculate_enhancement_priority(obj)
    
    # Create queue entry
    entry = PersistentMapping({
        "uid": obj.UID(),
        "path": "/".join(obj.getPhysicalPath()),
        "portal_type": obj.portal_type,
        "title": obj.Title(),
        "priority": priority,
        "operation": operation,
        "queued_at": datetime.now().isoformat(),
        "state": api.content.get_state(obj),
        "attempts": 0,
        "last_attempt": None,
        "error": None
    })
    
    # Add to queue with UID as key for easy lookup
    queue[obj.UID()] = entry
    
    # Log the queueing
    logger.info(
        f"Queued {obj.portal_type} '{obj.Title()}' for {operation} enhancement "
        f"with priority {priority:.2f}"
    )
    
    # Commit to ensure persistence
    transaction.savepoint(optimistic=True)
    
    return entry


def get_enhancement_queue(limit=None, min_priority=None):
    """Get enhancement queue sorted by priority."""
    portal = api.portal.get()
    annotations = IAnnotations(portal)
    
    queue = annotations.get("knowledge.curator.enhancement_queue", {})
    
    # Convert to list and sort by priority
    items = list(queue.values())
    
    # Filter by minimum priority if specified
    if min_priority is not None:
        items = [item for item in items if item.get("priority", 0) >= min_priority]
    
    # Sort by priority (highest first)
    items.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    # Apply limit if specified
    if limit:
        items = items[:limit]
    
    return items


def process_enhancement_queue(batch_size=10, content_type_filter=None):
    """Process items from the enhancement queue."""
    items = get_enhancement_queue(limit=batch_size)
    
    # Filter by content type if specified
    if content_type_filter:
        items = [item for item in items if item["portal_type"] == content_type_filter]
    
    # Prioritize Knowledge Items
    knowledge_items = [item for item in items if item["portal_type"] == "KnowledgeItem"]
    other_items = [item for item in items if item["portal_type"] != "KnowledgeItem"]
    
    # Process Knowledge Items first
    processed = []
    for item in knowledge_items + other_items:
        try:
            obj = api.content.get(UID=item["uid"])
            if obj:
                # Process enhancement (placeholder for actual implementation)
                logger.info(f"Processing enhancement for {obj.Title()} (priority: {item['priority']:.2f})")
                
                # Update queue entry
                portal = api.portal.get()
                annotations = IAnnotations(portal)
                queue = annotations["knowledge.curator.enhancement_queue"]
                
                # Remove from queue after successful processing
                if item["uid"] in queue:
                    del queue[item["uid"]]
                
                processed.append(item)
                
                # Commit after each item to ensure progress is saved
                transaction.savepoint(optimistic=True)
            else:
                # Object no longer exists, remove from queue
                portal = api.portal.get()
                annotations = IAnnotations(portal)
                queue = annotations["knowledge.curator.enhancement_queue"]
                if item["uid"] in queue:
                    del queue[item["uid"]]
                    
        except Exception as e:
            logger.error(f"Failed to process {item['uid']}: {str(e)}")
            # Update error in queue
            portal = api.portal.get()
            annotations = IAnnotations(portal)
            queue = annotations["knowledge.curator.enhancement_queue"]
            if item["uid"] in queue:
                queue[item["uid"]]["attempts"] += 1
                queue[item["uid"]]["last_attempt"] = datetime.now().isoformat()
                queue[item["uid"]]["error"] = str(e)
    
    return processed


def suggest_connections(state_change):
    """Suggest connections when entering the connect state."""
    obj = state_change.object
    
    # Queue for connection suggestions with high priority
    queue_for_enhancement(obj, operation="connections", 
                         priority_override=calculate_enhancement_priority(obj) * 1.5)

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

    if not getattr(obj, "tags", None):
        errors.append("At least one tag is required")

    # Check AI processing
    if not getattr(obj, "ai_summary", None):
        errors.append("AI summary has not been generated")
        # Queue for immediate AI processing if Knowledge Item
        if IKnowledgeItem.providedBy(obj):
            queue_for_enhancement(obj, operation="ai_summary", 
                                priority_override=200)  # Very high priority

    if errors:
        raise WorkflowException(
            "Cannot publish. Please fix the following issues: " + "; ".join(errors)
        )


def record_start_time(state_change):
    """Record when a learning goal was activated."""
    obj = state_change.object

    try:
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(obj)

        if "knowledge.curator.learning_timeline" not in annotations:
            annotations["knowledge.curator.learning_timeline"] = {}

        timeline = annotations["knowledge.curator.learning_timeline"]
        timeline["started_at"] = datetime.now().isoformat()

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

        timeline = annotations.get("knowledge.curator.learning_timeline", {})
        timeline["completed_at"] = datetime.now().isoformat()

        # Calculate duration if start time exists
        if "started_at" in timeline:
            start = datetime.fromisoformat(timeline["started_at"])
            end = datetime.fromisoformat(timeline["completed_at"])
            duration = end - start
            timeline["duration_days"] = duration.days

        annotations["knowledge.curator.learning_timeline"] = timeline

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

    # Queue for enhancement based on transition
    enhancement_triggers = {
        "start_processing": "full",
        "start_connecting": "connections",
        "submit_for_review": "ai_summary",
        "ready_to_publish": "final_check"
    }
    
    if transition_id in enhancement_triggers:
        operation = enhancement_triggers[transition_id]
        # Give Knowledge Items priority boost
        priority_multiplier = 1.5 if IKnowledgeItem.providedBy(obj) else 1.0
        priority = calculate_enhancement_priority(obj) * priority_multiplier
        queue_for_enhancement(obj, operation=operation, priority_override=priority)

    # Add any additional transition handling here
    # For example, sending notifications, updating indexes, etc.


def get_queue_statistics():
    """Get statistics about the enhancement queue."""
    portal = api.portal.get()
    annotations = IAnnotations(portal)
    queue = annotations.get("knowledge.curator.enhancement_queue", {})
    
    stats = {
        "total": len(queue),
        "by_type": {},
        "by_operation": {},
        "by_state": {},
        "knowledge_items": 0,
        "average_priority": 0,
        "highest_priority": None,
        "oldest_item": None
    }
    
    if not queue:
        return stats
    
    priorities = []
    oldest_date = None
    
    for item in queue.values():
        # Count by type
        portal_type = item.get("portal_type", "unknown")
        stats["by_type"][portal_type] = stats["by_type"].get(portal_type, 0) + 1
        
        # Count Knowledge Items specifically
        if portal_type == "KnowledgeItem":
            stats["knowledge_items"] += 1
        
        # Count by operation
        operation = item.get("operation", "unknown")
        stats["by_operation"][operation] = stats["by_operation"].get(operation, 0) + 1
        
        # Count by state
        state = item.get("state", "unknown")
        stats["by_state"][state] = stats["by_state"].get(state, 0) + 1
        
        # Track priorities
        priority = item.get("priority", 0)
        priorities.append(priority)
        
        # Find oldest item
        queued_at = item.get("queued_at")
        if queued_at:
            if oldest_date is None or queued_at < oldest_date:
                oldest_date = queued_at
                stats["oldest_item"] = {
                    "uid": item.get("uid"),
                    "title": item.get("title"),
                    "queued_at": queued_at
                }
    
    # Calculate statistics
    if priorities:
        stats["average_priority"] = sum(priorities) / len(priorities)
        max_priority = max(priorities)
        # Find item with highest priority
        for item in queue.values():
            if item.get("priority", 0) == max_priority:
                stats["highest_priority"] = {
                    "uid": item.get("uid"),
                    "title": item.get("title"),
                    "priority": max_priority,
                    "portal_type": item.get("portal_type")
                }
                break
    
    return stats
