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
from collections import defaultdict

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
    """Update embeddings when entering the process state with Knowledge Item priority."""
    obj = state_change.object
    
    # Detect content type and apply appropriate priority
    is_knowledge_item = IKnowledgeItem.providedBy(obj)
    base_priority = calculate_enhancement_priority(obj)
    
    # Apply Knowledge Item priority boost
    if is_knowledge_item:
        # Knowledge Items get significant priority boost for embeddings
        priority_multiplier = 2.5
        priority = base_priority * priority_multiplier
        logger.info(f"Knowledge Item detected: {obj.Title()} - priority boosted to {priority:.2f}")
    else:
        priority = base_priority
    
    # Queue for enhancement with calculated priority
    queue_for_enhancement(obj, operation="embeddings", priority_override=priority)
    
    # Check if object has AI enhancement behavior
    ai_adapter = queryAdapter(obj, IAIEnhanced)
    if ai_adapter:
        try:
            logger.info(f"Updating embeddings for {obj.portal_type} '{obj.Title()}' with priority {priority:.2f}")

            # Enhanced embedding parameters for Knowledge Items
            embedding_params = _get_embedding_parameters(obj)
            
            # Extract content with type-specific optimization
            content_data = _extract_content_for_embedding(obj)
            
            # Log the content extraction for debugging
            logger.info(f"Extracted {len(content_data.get('text', ''))} characters for embedding generation")
            
            # Store embedding metadata for queue processing
            _store_embedding_metadata(obj, embedding_params, content_data, priority)

            # In a real implementation, you would:
            # 1. Use content_data to generate embeddings with embedding_params
            # 2. Generate optimized vectors for atomic concepts (Knowledge Items)
            # 3. Store enhanced vector representations
            # ai_adapter.update_embeddings(content_data, embedding_params)

        except Exception as e:
            logger.error(f"Failed to update embeddings for {obj.Title()}: {e!s}")


def _get_embedding_parameters(obj):
    """Get optimized embedding parameters based on content type."""
    is_knowledge_item = IKnowledgeItem.providedBy(obj)
    
    if is_knowledge_item:
        # Optimized parameters for atomic knowledge units
        return {
            "model": "text-embedding-ada-002",  # Use higher quality model
            "chunk_strategy": "atomic_concepts",  # Preserve atomic units
            "max_chunk_size": 2000,  # Larger chunks for context
            "overlap": 200,  # Maintain concept continuity
            "normalize": True,
            "dimensions": 1536,  # Full dimensionality
            "concept_extraction": True,  # Extract key concepts
            "relationship_mapping": True,  # Map concept relationships
            "semantic_density": "high",  # Prioritize semantic richness
            "priority_boost": True
        }
    else:
        # Standard parameters for other content types
        return {
            "model": "text-embedding-ada-002",
            "chunk_strategy": "standard",
            "max_chunk_size": 1000,
            "overlap": 100,
            "normalize": True,
            "dimensions": 1536,
            "concept_extraction": False,
            "relationship_mapping": False,
            "semantic_density": "standard",
            "priority_boost": False
        }


def _extract_content_for_embedding(obj):
    """Extract and optimize content for embedding generation."""
    is_knowledge_item = IKnowledgeItem.providedBy(obj)
    
    content_data = {
        "title": obj.Title() or "",
        "description": obj.Description() or "",
        "text": "",
        "metadata": {
            "portal_type": obj.portal_type,
            "is_knowledge_item": is_knowledge_item,
            "uid": obj.UID(),
            "url": obj.absolute_url()
        }
    }
    
    # Extract main content
    if hasattr(obj, 'text') and obj.text:
        if hasattr(obj.text, 'raw'):
            content_data["text"] = obj.text.raw
        else:
            content_data["text"] = str(obj.text)
    
    # Knowledge Item specific content extraction
    if is_knowledge_item:
        # Extract atomic concepts and relationships
        if hasattr(obj, 'key_concepts') and obj.key_concepts:
            content_data["key_concepts"] = obj.key_concepts
            
        if hasattr(obj, 'related_topics') and obj.related_topics:
            content_data["related_topics"] = obj.related_topics
            
        if hasattr(obj, 'learning_objectives') and obj.learning_objectives:
            content_data["learning_objectives"] = obj.learning_objectives
            
        # Existing AI enhancements
        if hasattr(obj, 'ai_summary') and obj.ai_summary:
            content_data["ai_summary"] = obj.ai_summary
            
        if hasattr(obj, 'extracted_concepts') and obj.extracted_concepts:
            content_data["extracted_concepts"] = obj.extracted_concepts
            
        # Build enhanced text representation for Knowledge Items
        enhanced_text_parts = [
            content_data["title"],
            content_data["description"],
            content_data["text"]
        ]
        
        # Add conceptual information
        if content_data.get("key_concepts"):
            enhanced_text_parts.append(f"Key concepts: {', '.join(content_data['key_concepts'])}")
            
        if content_data.get("ai_summary"):
            enhanced_text_parts.append(f"Summary: {content_data['ai_summary']}")
            
        content_data["enhanced_text"] = " ".join(filter(None, enhanced_text_parts))
        content_data["metadata"]["enhanced_for_concepts"] = True
    
    # Extract tags for all content types
    if hasattr(obj, 'subject') and obj.subject:
        content_data["tags"] = list(obj.subject)
        
    return content_data


def _store_embedding_metadata(obj, embedding_params, content_data, priority):
    """Store embedding metadata for queue processing."""
    try:
        annotations = IAnnotations(obj)
        
        # Store embedding generation metadata
        embedding_metadata = {
            "parameters": embedding_params,
            "content_length": len(content_data.get("text", "")),
            "priority": priority,
            "queued_at": datetime.now().isoformat(),
            "is_knowledge_item": content_data["metadata"]["is_knowledge_item"],
            "enhanced_for_concepts": content_data["metadata"].get("enhanced_for_concepts", False),
            "content_hash": hash(content_data.get("enhanced_text", content_data.get("text", "")))
        }
        
        annotations["knowledge.curator.embedding_metadata"] = PersistentMapping(embedding_metadata)
        
        # Commit the annotation
        transaction.savepoint(optimistic=True)
        
        logger.info(f"Stored embedding metadata for {obj.Title()} with priority {priority:.2f}")
        
    except Exception as e:
        logger.error(f"Failed to store embedding metadata for {obj.Title()}: {e!s}")


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
    """Process items from the enhancement queue with Knowledge Item prioritization."""
    items = get_enhancement_queue(limit=batch_size * 2)  # Get more items to ensure proper sorting
    
    # Filter by content type if specified
    if content_type_filter:
        items = [item for item in items if item["portal_type"] == content_type_filter]
    
    # Advanced Knowledge Item prioritization
    knowledge_items = []
    embedding_operations = []
    other_items = []
    
    for item in items:
        if item["portal_type"] == "KnowledgeItem":
            knowledge_items.append(item)
            # Separate embedding operations for Knowledge Items
            if item.get("operation") == "embeddings":
                embedding_operations.append(item)
        else:
            other_items.append(item)
    
    # Sort Knowledge Items by priority (highest first)
    knowledge_items.sort(key=lambda x: x.get("priority", 0), reverse=True)
    embedding_operations.sort(key=lambda x: x.get("priority", 0), reverse=True)
    other_items.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    # Process in priority order: KnowledgeItem embeddings first, then other KnowledgeItems, then others
    processing_order = embedding_operations + [ki for ki in knowledge_items if ki not in embedding_operations] + other_items
    
    # Limit to batch size after sorting
    processing_order = processing_order[:batch_size]
    
    logger.info(f"Processing {len(processing_order)} items: {len(embedding_operations)} KI embeddings, "
                f"{len(knowledge_items)} Knowledge Items total, {len(other_items)} other items")
    
    processed = []
    for item in processing_order:
        try:
            obj = api.content.get(UID=item["uid"])
            if obj:
                # Enhanced processing for Knowledge Items
                is_knowledge_item = item["portal_type"] == "KnowledgeItem"
                operation = item.get("operation", "full")
                
                logger.info(f"Processing {operation} enhancement for {obj.portal_type} '{obj.Title()}' "
                           f"(priority: {item['priority']:.2f})")
                
                # Special handling for Knowledge Item embeddings
                if is_knowledge_item and operation == "embeddings":
                    _process_knowledge_item_embeddings(obj, item)
                else:
                    # Standard processing
                    _process_standard_enhancement(obj, item)
                
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


def _process_knowledge_item_embeddings(obj, queue_item):
    """Enhanced processing for Knowledge Item embeddings."""
    logger.info(f"Enhanced Knowledge Item embedding processing for '{obj.Title()}'")
    
    try:
        # Get stored embedding metadata
        annotations = IAnnotations(obj)
        embedding_metadata = annotations.get("knowledge.curator.embedding_metadata", {})
        
        if embedding_metadata:
            params = embedding_metadata.get("parameters", {})
            priority = embedding_metadata.get("priority", 0)
            
            logger.info(f"Using stored embedding parameters for Knowledge Item: "
                       f"chunk_strategy={params.get('chunk_strategy')}, "
                       f"semantic_density={params.get('semantic_density')}, "
                       f"priority={priority:.2f}")
        
        # Extract enhanced content for Knowledge Items
        content_data = _extract_content_for_embedding(obj)
        
        # Validate Knowledge Item specific content
        if content_data["metadata"]["is_knowledge_item"]:
            concepts_count = len(content_data.get("key_concepts", []))
            logger.info(f"Knowledge Item has {concepts_count} key concepts and "
                       f"{len(content_data.get('text', ''))} characters of content")
        
        # Mark as processed (in real implementation, this would generate actual embeddings)
        annotations["knowledge.curator.embedding_processed"] = PersistentMapping({
            "processed_at": datetime.now().isoformat(),
            "content_hash": embedding_metadata.get("content_hash"),
            "enhanced_for_concepts": content_data["metadata"].get("enhanced_for_concepts", False),
            "priority": queue_item.get("priority", 0)
        })
        
        transaction.savepoint(optimistic=True)
        
    except Exception as e:
        logger.error(f"Failed to process Knowledge Item embeddings for {obj.Title()}: {e!s}")
        raise


def _process_standard_enhancement(obj, queue_item):
    """Standard processing for non-Knowledge Item content or non-embedding operations."""
    operation = queue_item.get("operation", "full")
    logger.info(f"Standard {operation} processing for {obj.portal_type} '{obj.Title()}'")
    
    # Standard enhancement processing would go here
    # This is a placeholder for the actual implementation


def suggest_connections(state_change):
    """Suggest connections when entering the connect state."""
    obj = state_change.object
    
    # Queue for connection suggestions with high priority
    queue_for_enhancement(obj, operation="connections", 
                         priority_override=calculate_enhancement_priority(obj) * 1.5)

    try:
        logger.info(f"Suggesting connections for {obj.absolute_url()}")

        # Use enhanced Knowledge Item connection suggestions if applicable
        if IKnowledgeItem.providedBy(obj):
            logger.info(f"Generating Knowledge Item relationship suggestions for {obj.Title()}")
            
            # Generate relationship suggestions for Knowledge Items
            suggestions = _suggest_knowledge_item_connections(obj)
            
            # Store the enhanced suggestions
            annotations = IAnnotations(obj)
            annotations["knowledge.curator.connection_suggestions"] = {
                "suggested_at": datetime.now().isoformat(),
                "suggestions": suggestions,  # Enhanced suggestions with confidence scores
                "suggestion_type": "knowledge_item_relationships"
            }
            
            logger.info(f"Generated {suggestions.get('total_suggestions', 0)} relationship suggestions for Knowledge Item {obj.Title()}")
        else:
            # For non-Knowledge Items, use basic similarity search
            from knowledge.curator.vector.search import SimilaritySearch
            
            search = SimilaritySearch()
            similar_items = search.find_similar_content(
                obj.UID(),
                limit=10,
                score_threshold=0.6,
                same_type_only=False
            )
            
            # Store basic similarity suggestions
            annotations = IAnnotations(obj)
            annotations["knowledge.curator.connection_suggestions"] = {
                "suggested_at": datetime.now().isoformat(),
                "suggestions": similar_items,
                "suggestion_type": "general_similarity"
            }
            
            logger.info(f"Generated {len(similar_items)} similarity suggestions for {obj.portal_type} {obj.Title()}")

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
    """Get enhanced statistics about the enhancement queue with Knowledge Item focus."""
    portal = api.portal.get()
    annotations = IAnnotations(portal)
    queue = annotations.get("knowledge.curator.enhancement_queue", {})
    
    stats = {
        "total": len(queue),
        "by_type": {},
        "by_operation": {},
        "by_state": {},
        "knowledge_items": 0,
        "knowledge_item_embeddings": 0,
        "average_priority": 0,
        "knowledge_item_avg_priority": 0,
        "highest_priority": None,
        "highest_priority_ki": None,
        "oldest_item": None,
        "embedding_operations": 0,
        "priority_distribution": {
            "very_high": 0,  # >150
            "high": 0,       # 100-150
            "medium": 0,     # 50-100
            "low": 0         # <50
        }
    }
    
    if not queue:
        return stats
    
    priorities = []
    ki_priorities = []
    oldest_date = None
    
    for item in queue.values():
        # Count by type
        portal_type = item.get("portal_type", "unknown")
        stats["by_type"][portal_type] = stats["by_type"].get(portal_type, 0) + 1
        
        # Count Knowledge Items specifically
        if portal_type == "KnowledgeItem":
            stats["knowledge_items"] += 1
            ki_priorities.append(item.get("priority", 0))
            
            # Count Knowledge Item embedding operations
            if item.get("operation") == "embeddings":
                stats["knowledge_item_embeddings"] += 1
        
        # Count operations
        operation = item.get("operation", "unknown")
        stats["by_operation"][operation] = stats["by_operation"].get(operation, 0) + 1
        
        # Count embedding operations
        if operation == "embeddings":
            stats["embedding_operations"] += 1
        
        # Count by state
        state = item.get("state", "unknown")
        stats["by_state"][state] = stats["by_state"].get(state, 0) + 1
        
        # Track priorities
        priority = item.get("priority", 0)
        priorities.append(priority)
        
        # Priority distribution
        if priority > 150:
            stats["priority_distribution"]["very_high"] += 1
        elif priority > 100:
            stats["priority_distribution"]["high"] += 1
        elif priority > 50:
            stats["priority_distribution"]["medium"] += 1
        else:
            stats["priority_distribution"]["low"] += 1
        
        # Find oldest item
        queued_at = item.get("queued_at")
        if queued_at:
            if oldest_date is None or queued_at < oldest_date:
                oldest_date = queued_at
                stats["oldest_item"] = {
                    "uid": item.get("uid"),
                    "title": item.get("title"),
                    "queued_at": queued_at,
                    "portal_type": portal_type,
                    "operation": operation
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
                    "portal_type": item.get("portal_type"),
                    "operation": item.get("operation")
                }
                break
    
    # Knowledge Item specific statistics
    if ki_priorities:
        stats["knowledge_item_avg_priority"] = sum(ki_priorities) / len(ki_priorities)
        max_ki_priority = max(ki_priorities)
        
        # Find Knowledge Item with highest priority
        for item in queue.values():
            if (item.get("portal_type") == "KnowledgeItem" and 
                item.get("priority", 0) == max_ki_priority):
                stats["highest_priority_ki"] = {
                    "uid": item.get("uid"),
                    "title": item.get("title"),
                    "priority": max_ki_priority,
                    "operation": item.get("operation")
                }
                break
    
    # Calculate percentages
    if stats["total"] > 0:
        stats["knowledge_item_percentage"] = (stats["knowledge_items"] / stats["total"]) * 100
        stats["embedding_percentage"] = (stats["embedding_operations"] / stats["total"]) * 100
        stats["ki_embedding_percentage"] = (stats["knowledge_item_embeddings"] / stats["total"]) * 100
    
    return stats


def get_knowledge_item_queue_status():
    """Get detailed status of Knowledge Items in the enhancement queue."""
    portal = api.portal.get()
    annotations = IAnnotations(portal)
    queue = annotations.get("knowledge.curator.enhancement_queue", {})
    
    ki_items = []
    for item in queue.values():
        if item.get("portal_type") == "KnowledgeItem":
            ki_items.append({
                "uid": item.get("uid"),
                "title": item.get("title"),
                "priority": item.get("priority", 0),
                "operation": item.get("operation", "unknown"),
                "state": item.get("state", "unknown"),
                "queued_at": item.get("queued_at"),
                "attempts": item.get("attempts", 0),
                "last_attempt": item.get("last_attempt"),
                "error": item.get("error")
            })
    
    # Sort by priority (highest first)
    ki_items.sort(key=lambda x: x["priority"], reverse=True)
    
    # Separate embedding operations
    embedding_items = [item for item in ki_items if item["operation"] == "embeddings"]
    other_items = [item for item in ki_items if item["operation"] != "embeddings"]
    
    return {
        "total_knowledge_items": len(ki_items),
        "embedding_operations": len(embedding_items),
        "other_operations": len(other_items),
        "all_items": ki_items,
        "embedding_items": embedding_items,
        "processing_order": embedding_items + other_items
    }


def validate_knowledge_item_priority_queue():
    """Validate that Knowledge Item priority queue is working correctly."""
    stats = get_queue_statistics()
    ki_status = get_knowledge_item_queue_status()
    
    validation_results = {
        "total_items": stats["total"],
        "knowledge_items": stats["knowledge_items"],
        "knowledge_item_embeddings": stats["knowledge_item_embeddings"],
        "priority_validation": {
            "ki_avg_priority": stats.get("knowledge_item_avg_priority", 0),
            "overall_avg_priority": stats.get("average_priority", 0),
            "ki_priority_boost": stats.get("knowledge_item_avg_priority", 0) > stats.get("average_priority", 0)
        },
        "processing_order_correct": True,
        "embedding_priority_check": True
    }
    
    # Validate processing order
    if ki_status["processing_order"]:
        # Check if embedding operations come first
        embedding_count = len(ki_status["embedding_items"])
        if embedding_count > 0:
            first_items = ki_status["processing_order"][:embedding_count]
            all_embeddings = all(item["operation"] == "embeddings" for item in first_items)
            validation_results["processing_order_correct"] = all_embeddings
            
        # Check if priorities are properly sorted within each group
        embedding_priorities = [item["priority"] for item in ki_status["embedding_items"]]
        other_priorities = [item["priority"] for item in ki_status["other_operations"]]
        
        embedding_sorted = embedding_priorities == sorted(embedding_priorities, reverse=True)
        other_sorted = other_priorities == sorted(other_priorities, reverse=True)
        
        validation_results["embedding_priority_check"] = embedding_sorted and other_sorted
    
    validation_results["validation_passed"] = (
        validation_results["priority_validation"]["ki_priority_boost"] and
        validation_results["processing_order_correct"] and
        validation_results["embedding_priority_check"]
    )
    
    return validation_results


def _suggest_knowledge_item_connections(knowledge_item, similarity_threshold=0.7, max_suggestions=10):
    """Suggest relationships between Knowledge Items based on content similarity and semantic analysis.
    
    This function analyzes Knowledge Item embeddings to identify potential prerequisite_items 
    and enables_items relationships using cosine similarity and semantic analysis.
    
    Args:
        knowledge_item: The Knowledge Item object to find connections for
        similarity_threshold: Minimum similarity score for suggestions (default: 0.7)
        max_suggestions: Maximum number of suggestions to return per relationship type (default: 10)
        
    Returns:
        dict: Dictionary containing relationship suggestions with confidence scores:
            {
                'prerequisite_suggestions': [
                    {
                        'uid': 'item_uid',
                        'title': 'Item Title',
                        'similarity_score': 0.85,
                        'confidence': 0.82,
                        'reasoning': 'Semantic analysis explanation',
                        'existing_relationship': False
                    }
                ],
                'enables_suggestions': [...],
                'bidirectional_suggestions': [...],
                'total_suggestions': 15,
                'analysis_metadata': {
                    'processed_at': '2024-01-01T12:00:00',
                    'similarity_threshold': 0.7,
                    'total_knowledge_items_analyzed': 150,
                    'embedding_model': 'all-MiniLM-L6-v2'
                }
            }
    """
    if not IKnowledgeItem.providedBy(knowledge_item):
        logger.error(f"Object {knowledge_item} is not a Knowledge Item")
        return {
            'prerequisite_suggestions': [],
            'enables_suggestions': [],
            'bidirectional_suggestions': [],
            'total_suggestions': 0,
            'error': 'Invalid Knowledge Item provided'
        }
    
    try:
        # Import vector search utilities
        from knowledge.curator.vector.search import SimilaritySearch
        from knowledge.curator.vector.embeddings import EmbeddingGenerator
        
        logger.info(f"Generating relationship suggestions for Knowledge Item: {knowledge_item.Title()}")
        
        # Initialize similarity search components
        similarity_search = SimilaritySearch()
        embedding_generator = EmbeddingGenerator()
        
        # Get current Knowledge Item's content for analysis
        current_uid = knowledge_item.UID()
        current_content = _extract_content_for_embedding(knowledge_item)
        
        # Get existing relationships to avoid duplicates
        existing_prerequisites = set(getattr(knowledge_item, 'prerequisite_items', []) or [])
        existing_enables = set(getattr(knowledge_item, 'enables_items', []) or [])
        
        # Find similar Knowledge Items using vector similarity
        similar_items = similarity_search.find_similar_content(
            current_uid,
            limit=max_suggestions * 3,  # Get more candidates for filtering
            score_threshold=similarity_threshold * 0.8,  # Lower threshold for initial search
            same_type_only=True  # Only Knowledge Items
        )
        
        # Initialize suggestion collections
        prerequisite_suggestions = []
        enables_suggestions = []
        bidirectional_suggestions = []
        
        # Analyze each similar item for relationship potential
        for similar_item in similar_items:
            try:
                candidate_uid = similar_item['uid']
                candidate_similarity = similar_item.get('score', 0.0)
                
                # Skip if similarity is below threshold
                if candidate_similarity < similarity_threshold:
                    continue
                    
                # Get the candidate Knowledge Item
                candidate_brain = api.content.find(UID=candidate_uid)
                if not candidate_brain:
                    continue
                    
                candidate_item = candidate_brain[0].getObject()
                if not IKnowledgeItem.providedBy(candidate_item):
                    continue
                
                # Skip existing relationships
                if candidate_uid in existing_prerequisites or candidate_uid in existing_enables:
                    continue
                
                # Analyze relationship potential
                relationship_analysis = _analyze_knowledge_item_relationship(
                    knowledge_item, candidate_item, candidate_similarity, embedding_generator
                )
                
                # Add to appropriate suggestion lists based on analysis
                if relationship_analysis['prerequisite_confidence'] >= 0.6:
                    prerequisite_suggestions.append({
                        'uid': candidate_uid,
                        'title': candidate_item.Title(),
                        'similarity_score': candidate_similarity,
                        'confidence': relationship_analysis['prerequisite_confidence'],
                        'reasoning': relationship_analysis['prerequisite_reasoning'],
                        'existing_relationship': False,
                        'difficulty_comparison': relationship_analysis.get('difficulty_comparison', 'unknown'),
                        'concept_overlap': relationship_analysis.get('concept_overlap', 0.0)
                    })
                
                if relationship_analysis['enables_confidence'] >= 0.6:
                    enables_suggestions.append({
                        'uid': candidate_uid,
                        'title': candidate_item.Title(),
                        'similarity_score': candidate_similarity,
                        'confidence': relationship_analysis['enables_confidence'],
                        'reasoning': relationship_analysis['enables_reasoning'],
                        'existing_relationship': False,
                        'difficulty_comparison': relationship_analysis.get('difficulty_comparison', 'unknown'),
                        'concept_overlap': relationship_analysis.get('concept_overlap', 0.0)
                    })
                
                if relationship_analysis['bidirectional_confidence'] >= 0.7:
                    bidirectional_suggestions.append({
                        'uid': candidate_uid,
                        'title': candidate_item.Title(),
                        'similarity_score': candidate_similarity,
                        'confidence': relationship_analysis['bidirectional_confidence'],
                        'reasoning': relationship_analysis['bidirectional_reasoning'],
                        'existing_relationship': False,
                        'concept_overlap': relationship_analysis.get('concept_overlap', 0.0)
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to analyze relationship with {similar_item.get('uid', 'unknown')}: {e}")
                continue
        
        # Sort suggestions by confidence score (highest first)
        prerequisite_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        enables_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        bidirectional_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Limit to max_suggestions
        prerequisite_suggestions = prerequisite_suggestions[:max_suggestions]
        enables_suggestions = enables_suggestions[:max_suggestions]
        bidirectional_suggestions = bidirectional_suggestions[:max_suggestions]
        
        # Create result dictionary
        suggestions = {
            'prerequisite_suggestions': prerequisite_suggestions,
            'enables_suggestions': enables_suggestions,
            'bidirectional_suggestions': bidirectional_suggestions,
            'total_suggestions': len(prerequisite_suggestions) + len(enables_suggestions) + len(bidirectional_suggestions),
            'analysis_metadata': {
                'processed_at': datetime.now().isoformat(),
                'similarity_threshold': similarity_threshold,
                'total_knowledge_items_analyzed': len(similar_items),
                'embedding_model': embedding_generator.model_name,
                'knowledge_item_uid': current_uid,
                'knowledge_item_title': knowledge_item.Title()
            }
        }
        
        # Store suggestions in annotations for future reference
        _store_relationship_suggestions(knowledge_item, suggestions)
        
        logger.info(f"Generated {suggestions['total_suggestions']} relationship suggestions for {knowledge_item.Title()}")
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to suggest Knowledge Item connections for {knowledge_item.Title()}: {e}")
        return {
            'prerequisite_suggestions': [],
            'enables_suggestions': [],
            'bidirectional_suggestions': [],
            'total_suggestions': 0,
            'error': str(e),
            'analysis_metadata': {
                'processed_at': datetime.now().isoformat(),
                'similarity_threshold': similarity_threshold,
                'error': str(e)
            }
        }


def _analyze_knowledge_item_relationship(source_item, candidate_item, similarity_score, embedding_generator):
    """Analyze the potential relationship between two Knowledge Items.
    
    Args:
        source_item: The source Knowledge Item
        candidate_item: The candidate Knowledge Item for relationship
        similarity_score: Cosine similarity score between the items
        embedding_generator: EmbeddingGenerator instance for additional analysis
        
    Returns:
        dict: Analysis results with confidence scores and reasoning
    """
    try:
        # Extract key attributes for comparison
        source_concepts = set(getattr(source_item, 'atomic_concepts', []) or [])
        candidate_concepts = set(getattr(candidate_item, 'atomic_concepts', []) or [])
        
        source_difficulty = getattr(source_item, 'difficulty_level', 'intermediate')
        candidate_difficulty = getattr(candidate_item, 'difficulty_level', 'intermediate')
        
        source_type = getattr(source_item, 'knowledge_type', 'factual')
        candidate_type = getattr(candidate_item, 'knowledge_type', 'factual')
        
        # Calculate concept overlap
        concept_overlap = 0.0
        if source_concepts and candidate_concepts:
            intersection = source_concepts.intersection(candidate_concepts)
            union = source_concepts.union(candidate_concepts)
            concept_overlap = len(intersection) / len(union) if union else 0.0
        
        # Difficulty level mapping for comparison
        difficulty_order = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
        
        source_diff_level = difficulty_order.get(source_difficulty, 2)
        candidate_diff_level = difficulty_order.get(candidate_difficulty, 2)
        difficulty_diff = source_diff_level - candidate_diff_level
        
        # Initialize analysis results
        analysis = {
            'prerequisite_confidence': 0.0,
            'prerequisite_reasoning': '',
            'enables_confidence': 0.0,
            'enables_reasoning': '',
            'bidirectional_confidence': 0.0,
            'bidirectional_reasoning': '',
            'concept_overlap': concept_overlap,
            'difficulty_comparison': f"{candidate_difficulty} -> {source_difficulty}"
        }
        
        # Analyze prerequisite relationship potential
        # Candidate could be a prerequisite if:
        # 1. It has lower or equal difficulty
        # 2. High concept overlap suggests foundational knowledge
        # 3. Certain knowledge types suggest prerequisite nature
        
        prerequisite_score = similarity_score * 0.4  # Base similarity contribution
        
        if difficulty_diff >= 0:  # Candidate is easier or same difficulty
            prerequisite_score += 0.3
            
        prerequisite_score += concept_overlap * 0.2  # Concept overlap contribution
        
        # Knowledge type analysis for prerequisites
        prerequisite_types = ['factual', 'conceptual', 'procedural']
        if candidate_type in prerequisite_types and source_type in ['procedural', 'metacognitive']:
            prerequisite_score += 0.1
            
        analysis['prerequisite_confidence'] = min(prerequisite_score, 1.0)
        analysis['prerequisite_reasoning'] = f"Similarity: {similarity_score:.2f}, Difficulty: {candidate_difficulty} → {source_difficulty}, Concept overlap: {concept_overlap:.2f}"
        
        # Analyze enables relationship potential
        # Source could enable candidate if:
        # 1. Source is easier or foundational
        # 2. Knowledge types suggest enabling relationship
        # 3. High concept overlap with foundational concepts
        
        enables_score = similarity_score * 0.4  # Base similarity contribution
        
        if difficulty_diff <= 0:  # Source is easier or same difficulty
            enables_score += 0.3
            
        enables_score += concept_overlap * 0.2  # Concept overlap contribution
        
        # Knowledge type analysis for enables
        if source_type in prerequisite_types and candidate_type in ['procedural', 'metacognitive']:
            enables_score += 0.1
            
        analysis['enables_confidence'] = min(enables_score, 1.0)
        analysis['enables_reasoning'] = f"Similarity: {similarity_score:.2f}, Difficulty: {source_difficulty} → {candidate_difficulty}, Concept overlap: {concept_overlap:.2f}"
        
        # Analyze bidirectional relationship potential
        # High similarity with significant concept overlap suggests mutual reinforcement
        
        bidirectional_score = similarity_score * 0.5  # Higher weight for similarity
        bidirectional_score += concept_overlap * 0.3  # Higher weight for concept overlap
        
        # Same difficulty and knowledge type suggest peer relationship
        if abs(difficulty_diff) <= 1 and source_type == candidate_type:
            bidirectional_score += 0.2
            
        analysis['bidirectional_confidence'] = min(bidirectional_score, 1.0)
        analysis['bidirectional_reasoning'] = f"High similarity: {similarity_score:.2f}, Strong concept overlap: {concept_overlap:.2f}, Similar complexity levels"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze relationship between {source_item.Title()} and {candidate_item.Title()}: {e}")
        return {
            'prerequisite_confidence': 0.0,
            'prerequisite_reasoning': f'Analysis failed: {str(e)}',
            'enables_confidence': 0.0,
            'enables_reasoning': f'Analysis failed: {str(e)}',
            'bidirectional_confidence': 0.0,
            'bidirectional_reasoning': f'Analysis failed: {str(e)}',
            'concept_overlap': 0.0,
            'difficulty_comparison': 'unknown'
        }


def _store_relationship_suggestions(knowledge_item, suggestions):
    """Store relationship suggestions in Knowledge Item annotations for future reference.
    
    Args:
        knowledge_item: The Knowledge Item object
        suggestions: Dictionary of suggestions to store
    """
    try:
        annotations = IAnnotations(knowledge_item)
        
        # Store suggestions with metadata
        suggestion_data = PersistentMapping({
            'suggestions': suggestions,
            'stored_at': datetime.now().isoformat(),
            'version': '1.0'
        })
        
        annotations['knowledge.curator.relationship_suggestions'] = suggestion_data
        
        # Commit the annotation
        transaction.savepoint(optimistic=True)
        
        logger.info(f"Stored relationship suggestions for {knowledge_item.Title()}")
        
    except Exception as e:
        logger.error(f"Failed to store relationship suggestions for {knowledge_item.Title()}: {e}")


def get_relationship_suggestions(knowledge_item, refresh=False):
    """Get stored relationship suggestions for a Knowledge Item.
    
    Args:
        knowledge_item: The Knowledge Item object
        refresh: Whether to regenerate suggestions (default: False)
        
    Returns:
        dict: Stored suggestions or newly generated ones
    """
    try:
        if refresh:
            return _suggest_knowledge_item_connections(knowledge_item)
            
        annotations = IAnnotations(knowledge_item)
        suggestion_data = annotations.get('knowledge.curator.relationship_suggestions')
        
        if suggestion_data:
            return suggestion_data.get('suggestions', {})
        else:
            # No stored suggestions, generate new ones
            return _suggest_knowledge_item_connections(knowledge_item)
            
    except Exception as e:
        logger.error(f"Failed to get relationship suggestions for {knowledge_item.Title()}: {e}")
        return {
            'prerequisite_suggestions': [],
            'enables_suggestions': [],
            'bidirectional_suggestions': [],
            'total_suggestions': 0,
            'error': str(e)
        }


def update_learning_goal_progress(knowledge_item=None, updated_mastery_levels=None, 
                                learning_goals=None, trigger_event=None):
    """Update Learning Goal progress based on Knowledge Item mastery level changes.
    
    This function automatically updates Learning Goal progress when Knowledge Item 
    mastery levels change. It considers weighted progress calculations, dependency 
    chains, and mastery thresholds to provide accurate progress tracking.
    
    Args:
        knowledge_item: The Knowledge Item whose mastery changed (optional)
        updated_mastery_levels: Dict mapping Knowledge Item UIDs to new mastery levels
                              (optional, will be computed if not provided)
        learning_goals: List of Learning Goal objects to update (optional, will find all if not provided)
        trigger_event: The event that triggered this update (for logging)
        
    Returns:
        dict containing:
            - updated_goals: List of updated Learning Goal objects
            - progress_changes: Dict mapping goal UID to progress change data
            - total_updated: Number of goals updated
            - errors: List of any errors encountered
    """
    logger.info("Starting Learning Goal progress update process")
    
    # Initialize result structure
    result = {
        'updated_goals': [],
        'progress_changes': {},
        'total_updated': 0,
        'errors': [],
        'trigger_info': {
            'knowledge_item_uid': knowledge_item.UID() if knowledge_item else None,
            'knowledge_item_title': knowledge_item.Title() if knowledge_item else None,
            'trigger_event': str(trigger_event) if trigger_event else 'manual_update',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        from plone import api
        
        # Get the mastery levels to work with
        current_mastery_levels = {}
        
        if updated_mastery_levels:
            # Use provided mastery levels
            current_mastery_levels = updated_mastery_levels.copy()
        elif knowledge_item:
            # Single Knowledge Item update - get its current mastery
            current_mastery_levels[knowledge_item.UID()] = getattr(knowledge_item, 'learning_progress', 0.0)
        else:
            # Get mastery levels for all Knowledge Items
            logger.info("No specific mastery levels provided, querying all Knowledge Items")
            catalog = api.portal.get_tool(name='portal_catalog')
            knowledge_items = catalog(portal_type='KnowledgeItem')
            
            for brain in knowledge_items:
                try:
                    item = brain.getObject()
                    if item:
                        current_mastery_levels[item.UID()] = getattr(item, 'learning_progress', 0.0)
                except Exception as e:
                    logger.warning(f"Failed to get mastery for Knowledge Item {brain.UID}: {e}")
        
        # Find Learning Goals to update
        goals_to_update = []
        
        if learning_goals:
            # Use provided Learning Goals
            goals_to_update = learning_goals
        else:
            # Find all Learning Goals that reference the updated Knowledge Items
            catalog = api.portal.get_tool(name='portal_catalog')
            all_goals = catalog(portal_type='LearningGoal')
            
            for brain in all_goals:
                try:
                    goal = brain.getObject()
                    if goal and _goal_references_knowledge_items(goal, set(current_mastery_levels.keys())):
                        goals_to_update.append(goal)
                except Exception as e:
                    logger.warning(f"Failed to check Learning Goal {brain.UID}: {e}")
                    result['errors'].append(f"Failed to access Learning Goal {brain.UID}: {e}")
        
        logger.info(f"Found {len(goals_to_update)} Learning Goals to update")
        
        # Update each Learning Goal
        for goal in goals_to_update:
            try:
                goal_uid = goal.UID()
                goal_title = goal.Title()
                
                logger.info(f"Updating progress for Learning Goal: {goal_title} ({goal_uid})")
                
                # Store previous progress for comparison
                previous_progress = getattr(goal, 'overall_progress', 0.0)
                
                # Calculate new progress using the Learning Goal's method
                progress_data = goal.calculate_overall_progress(current_mastery_levels)
                
                # Update the goal's progress fields
                new_progress = progress_data['weighted_progress']
                goal.overall_progress = new_progress
                
                # Update deprecated progress field for backwards compatibility
                goal.progress = int(new_progress * 100)
                
                # Calculate progress change
                progress_change = new_progress - previous_progress
                
                # Store change data
                change_data = {
                    'goal_uid': goal_uid,
                    'goal_title': goal_title,
                    'previous_progress': previous_progress,
                    'new_progress': new_progress,
                    'progress_change': progress_change,
                    'progress_percentage': int(new_progress * 100),
                    'items_mastered': progress_data['items_mastered'],
                    'total_items': progress_data['total_items'],
                    'prerequisite_satisfaction': progress_data['prerequisite_satisfaction'],
                    'bottlenecks': progress_data['bottlenecks'],
                    'next_milestones': progress_data['next_milestones'],
                    'updated_at': datetime.now().isoformat()
                }
                
                result['progress_changes'][goal_uid] = change_data
                result['updated_goals'].append(goal)
                result['total_updated'] += 1
                
                # Log the update with detailed information
                logger.info(
                    f"Updated Learning Goal '{goal_title}': "
                    f"{previous_progress:.3f} -> {new_progress:.3f} "
                    f"(change: {progress_change:+.3f}, "
                    f"items mastered: {progress_data['items_mastered']}/{progress_data['total_items']}, "
                    f"prerequisites: {progress_data['prerequisite_satisfaction']:.1f}%)"
                )
                
                # Store progress update metadata in annotations
                _store_progress_update_metadata(goal, change_data, current_mastery_levels, trigger_event)
                
                # Trigger any necessary follow-up actions
                _trigger_progress_milestones(goal, change_data, progress_data)
                
                # Mark the object as changed
                goal._p_changed = True
                
            except Exception as e:
                error_msg = f"Failed to update Learning Goal {goal.Title()}: {e}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
        
        # Commit changes if any goals were updated
        if result['total_updated'] > 0:
            transaction.savepoint(optimistic=True)
            logger.info(f"Successfully updated {result['total_updated']} Learning Goals")
        else:
            logger.info("No Learning Goals required updates")
            
    except Exception as e:
        error_msg = f"Critical error in update_learning_goal_progress: {e}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
    
    return result


def _goal_references_knowledge_items(learning_goal, knowledge_item_uids):
    """Check if a Learning Goal references any of the specified Knowledge Items.
    
    Args:
        learning_goal: The Learning Goal object to check
        knowledge_item_uids: Set of Knowledge Item UIDs to check for
        
    Returns:
        bool: True if the goal references any of the Knowledge Items
    """
    try:
        # Check starting knowledge item
        if (hasattr(learning_goal, 'starting_knowledge_item') and 
            learning_goal.starting_knowledge_item and
            learning_goal.starting_knowledge_item in knowledge_item_uids):
            return True
        
        # Check target knowledge items
        if (hasattr(learning_goal, 'target_knowledge_items') and 
            learning_goal.target_knowledge_items):
            for target_uid in learning_goal.target_knowledge_items:
                if target_uid in knowledge_item_uids:
                    return True
        
        # Check knowledge item connections
        if (hasattr(learning_goal, 'knowledge_item_connections') and 
            learning_goal.knowledge_item_connections):
            for conn in learning_goal.knowledge_item_connections:
                source_uid = conn.get('source_item_uid')
                target_uid = conn.get('target_item_uid')
                if (source_uid in knowledge_item_uids or 
                    target_uid in knowledge_item_uids):
                    return True
        
        return False
        
    except Exception as e:
        logger.warning(f"Error checking goal references for {learning_goal.Title()}: {e}")
        return False


def _store_progress_update_metadata(learning_goal, change_data, mastery_levels, trigger_event):
    """Store metadata about the progress update for tracking and debugging.
    
    Args:
        learning_goal: The Learning Goal object
        change_data: Dictionary containing change information
        mastery_levels: Dictionary of current mastery levels
        trigger_event: The event that triggered the update
    """
    try:
        annotations = IAnnotations(learning_goal)
        
        # Initialize progress update history if needed
        if "knowledge.curator.progress_updates" not in annotations:
            annotations["knowledge.curator.progress_updates"] = PersistentList()
        
        update_history = annotations["knowledge.curator.progress_updates"]
        
        # Create update record
        update_record = PersistentMapping({
            'timestamp': change_data['updated_at'],
            'trigger_event': str(trigger_event) if trigger_event else 'manual_update',
            'progress_change': change_data['progress_change'],
            'new_progress': change_data['new_progress'],
            'items_mastered': change_data['items_mastered'],
            'total_items': change_data['total_items'],
            'prerequisite_satisfaction': change_data['prerequisite_satisfaction'],
            'mastery_snapshot': PersistentMapping(mastery_levels),
            'bottlenecks_count': len(change_data.get('bottlenecks', [])),
            'milestones_pending': len(change_data.get('next_milestones', []))
        })
        
        # Add to history (keep last 50 updates)
        update_history.append(update_record)
        if len(update_history) > 50:
            update_history.pop(0)
        
        # Store current progress summary
        annotations["knowledge.curator.current_progress_summary"] = PersistentMapping({
            'last_updated': change_data['updated_at'],
            'current_progress': change_data['new_progress'],
            'progress_percentage': change_data['progress_percentage'],
            'items_mastered': change_data['items_mastered'],
            'total_items': change_data['total_items'],
            'bottlenecks': [b['item_uid'] for b in change_data.get('bottlenecks', [])],
            'next_milestones': [m['item_uid'] for m in change_data.get('next_milestones', [])]
        })
        
        transaction.savepoint(optimistic=True)
        logger.debug(f"Stored progress update metadata for {learning_goal.Title()}")
        
    except Exception as e:
        logger.error(f"Failed to store progress update metadata: {e}")


def _trigger_progress_milestones(learning_goal, change_data, progress_data):
    """Trigger milestone notifications and actions based on progress changes.
    
    Args:
        learning_goal: The Learning Goal object
        change_data: Dictionary containing change information
        progress_data: Full progress calculation data
    """
    try:
        goal_title = learning_goal.Title()
        progress_change = change_data['progress_change']
        new_progress = change_data['new_progress']
        
        # Check for significant progress milestones
        milestone_thresholds = [0.25, 0.5, 0.75, 0.9, 1.0]
        previous_progress = change_data['previous_progress']
        
        for threshold in milestone_thresholds:
            if previous_progress < threshold <= new_progress:
                milestone_percentage = int(threshold * 100)
                logger.info(
                    f"Learning Goal milestone reached: '{goal_title}' "
                    f"achieved {milestone_percentage}% completion"
                )
                
                # Store milestone achievement
                _record_progress_milestone(learning_goal, threshold, change_data, progress_data)
        
        # Check for bottleneck alerts
        bottlenecks = progress_data.get('bottlenecks', [])
        if bottlenecks and progress_change < 0.01:  # Progress stalled with bottlenecks
            logger.warning(
                f"Learning Goal '{goal_title}' has {len(bottlenecks)} bottlenecks "
                f"that may be blocking progress: {[b['item_uid'] for b in bottlenecks[:3]]}"
            )
        
        # Check for completion
        if new_progress >= 1.0 and previous_progress < 1.0:
            logger.info(f"Learning Goal COMPLETED: '{goal_title}' has reached 100% mastery!")
            _record_goal_completion(learning_goal, change_data, progress_data)
        
    except Exception as e:
        logger.error(f"Failed to trigger progress milestones: {e}")


def _record_progress_milestone(learning_goal, threshold, change_data, progress_data):
    """Record a progress milestone achievement.
    
    Args:
        learning_goal: The Learning Goal object
        threshold: The milestone threshold reached (0.0-1.0)
        change_data: Dictionary containing change information
        progress_data: Full progress calculation data
    """
    try:
        annotations = IAnnotations(learning_goal)
        
        # Initialize milestones record if needed
        if "knowledge.curator.progress_milestones" not in annotations:
            annotations["knowledge.curator.progress_milestones"] = PersistentList()
        
        milestones = annotations["knowledge.curator.progress_milestones"]
        
        # Create milestone record
        milestone_record = PersistentMapping({
            'threshold': threshold,
            'percentage': int(threshold * 100),
            'achieved_at': change_data['updated_at'],
            'progress_at_achievement': change_data['new_progress'],
            'items_mastered': change_data['items_mastered'],
            'total_items': change_data['total_items'],
            'prerequisite_satisfaction': change_data['prerequisite_satisfaction'],
            'milestone_type': 'progress_percentage'
        })
        
        milestones.append(milestone_record)
        transaction.savepoint(optimistic=True)
        
        logger.info(f"Recorded {int(threshold * 100)}% milestone for {learning_goal.Title()}")
        
    except Exception as e:
        logger.error(f"Failed to record progress milestone: {e}")


def _record_goal_completion(learning_goal, change_data, progress_data):
    """Record Learning Goal completion.
    
    Args:
        learning_goal: The Learning Goal object
        change_data: Dictionary containing change information
        progress_data: Full progress calculation data
    """
    try:
        annotations = IAnnotations(learning_goal)
        
        # Record completion data
        completion_data = PersistentMapping({
            'completed_at': change_data['updated_at'],
            'final_progress': change_data['new_progress'],
            'items_mastered': change_data['items_mastered'],
            'total_items': change_data['total_items'],
            'prerequisite_satisfaction': change_data['prerequisite_satisfaction'],
            'learning_path_segments': progress_data.get('path_segments', []),
            'completion_type': 'automatic_mastery_based'
        })
        
        annotations["knowledge.curator.completion_record"] = completion_data
        
        # Update goal's workflow state if possible
        try:
            workflow_tool = api.portal.get_tool('portal_workflow')
            available_transitions = [t['id'] for t in workflow_tool.getTransitionsFor(learning_goal)]
            
            if 'complete' in available_transitions:
                api.content.transition(obj=learning_goal, transition='complete')
                logger.info(f"Automatically transitioned Learning Goal '{learning_goal.Title()}' to completed state")
        except Exception as e:
            logger.warning(f"Could not transition Learning Goal to completed state: {e}")
        
        transaction.savepoint(optimistic=True)
        logger.info(f"Recorded completion for Learning Goal: {learning_goal.Title()}")
        
    except Exception as e:
        logger.error(f"Failed to record goal completion: {e}")


def get_learning_goal_progress_history(learning_goal, limit=None):
    """Get the progress update history for a Learning Goal.
    
    Args:
        learning_goal: The Learning Goal object
        limit: Maximum number of updates to return (optional)
        
    Returns:
        list: List of progress update records
    """
    try:
        if not learning_goal:
            return []
            
        annotations = IAnnotations(learning_goal)
        update_history = annotations.get("knowledge.curator.progress_updates", [])
        
        # Convert to regular list and reverse to get most recent first
        history_list = list(reversed(update_history))
        
        if limit:
            history_list = history_list[:limit]
        
        return history_list
        
    except Exception as e:
        goal_title = learning_goal.Title() if learning_goal else "None"
        logger.error(f"Failed to get progress history for {goal_title}: {e}")
        return []


def _recalculate_learning_goal_progress(learning_goals=None, knowledge_items=None, 
                                      project_logs=None, batch_size=50, 
                                      force_recalculation=False, track_changes=True):
    """Recalculate and synchronize Learning Goal progress across all associated content.
    
    This function performs comprehensive Learning Goal progress recalculation by:
    1. Collecting mastery data from Knowledge Items and Project Logs
    2. Detecting circular dependencies and resolving them
    3. Batch processing for efficiency with large datasets
    4. Synchronizing progress data between all content types
    5. Handling edge cases like orphaned references and inconsistent data
    
    Args:
        learning_goals: List of Learning Goal objects to recalculate (optional, processes all if None)
        knowledge_items: List of Knowledge Items that may have updated mastery (optional)
        project_logs: List of Project Logs that may have progress updates (optional)
        batch_size: Number of Learning Goals to process in each batch (default: 50)
        force_recalculation: Force recalculation even if no changes detected (default: False)
        track_changes: Whether to track and log detailed changes (default: True)
        
    Returns:
        dict containing:
            - processed_goals: Number of Learning Goals processed
            - updated_goals: Number of Learning Goals that had progress changes
            - batch_count: Number of batches processed
            - errors: List of errors encountered
            - warnings: List of warnings about data inconsistencies
            - circular_dependencies: List of circular dependency issues found and resolved
            - processing_time: Total processing time in seconds
            - change_summary: Summary of all changes made
            - consistency_issues: Data consistency problems detected
    """
    from datetime import datetime
    from collections import defaultdict, deque
    import time
    
    logger.info("Starting comprehensive Learning Goal progress recalculation")
    start_time = time.time()
    
    # Initialize result structure
    result = {
        'processed_goals': 0,
        'updated_goals': 0,
        'batch_count': 0,
        'errors': [],
        'warnings': [],
        'circular_dependencies': [],
        'processing_time': 0.0,
        'change_summary': {
            'progress_increases': 0,
            'progress_decreases': 0,
            'total_change_magnitude': 0.0,
            'new_completions': 0,
            'items_synchronized': 0
        },
        'consistency_issues': {
            'orphaned_references': [],
            'missing_knowledge_items': [],
            'inconsistent_mastery_levels': [],
            'duplicate_connections': []
        },
        'performance_metrics': {
            'avg_processing_time_per_goal': 0.0,
            'items_per_second': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    }
    
    try:
        from plone import api
        
        # Step 1: Collect all relevant content if not provided
        if learning_goals is None:
            logger.info("Collecting all Learning Goals from catalog")
            catalog = api.portal.get_tool(name='portal_catalog')
            learning_goal_brains = catalog(portal_type='LearningGoal')
            learning_goals = []
            
            for brain in learning_goal_brains:
                try:
                    goal = brain.getObject()
                    if goal:
                        learning_goals.append(goal)
                except Exception as e:
                    result['errors'].append(f"Failed to load Learning Goal {brain.UID}: {e}")
        
        if knowledge_items is None:
            logger.info("Collecting all Knowledge Items from catalog")
            catalog = api.portal.get_tool(name='portal_catalog')
            ki_brains = catalog(portal_type='KnowledgeItem')
            knowledge_items = []
            
            for brain in ki_brains:
                try:
                    item = brain.getObject()
                    if item:
                        knowledge_items.append(item)
                except Exception as e:
                    result['errors'].append(f"Failed to load Knowledge Item {brain.UID}: {e}")
        
        if project_logs is None:
            logger.info("Collecting all Project Logs from catalog")
            catalog = api.portal.get_tool(name='portal_catalog')
            pl_brains = catalog(portal_type='ProjectLog')
            project_logs = []
            
            for brain in pl_brains:
                try:
                    log = brain.getObject()
                    if log:
                        project_logs.append(log)
                except Exception as e:
                    result['errors'].append(f"Failed to load Project Log {brain.UID}: {e}")
        
        logger.info(f"Processing {len(learning_goals)} Learning Goals, "
                   f"{len(knowledge_items)} Knowledge Items, "
                   f"and {len(project_logs)} Project Logs")
        
        # Step 2: Build comprehensive mastery data map with caching
        mastery_cache = {}
        mastery_data = _build_comprehensive_mastery_map(
            knowledge_items, project_logs, mastery_cache, result
        )
        
        # Step 3: Detect and resolve circular dependencies
        dependency_graph = _build_learning_goal_dependency_graph(learning_goals)
        circular_deps = _detect_and_resolve_circular_dependencies(
            dependency_graph, learning_goals, result
        )
        
        # Step 4: Determine processing order based on dependencies
        processing_order = _determine_processing_order(dependency_graph, learning_goals)
        
        # Step 5: Process Learning Goals in batches
        total_goals = len(processing_order)
        batches = [processing_order[i:i + batch_size] 
                  for i in range(0, total_goals, batch_size)]
        
        logger.info(f"Processing {total_goals} Learning Goals in {len(batches)} batches of size {batch_size}")
        
        goal_processing_times = []
        items_processed = 0
        
        for batch_idx, goal_batch in enumerate(batches):
            result['batch_count'] += 1
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} "
                       f"({len(goal_batch)} goals)")
            
            batch_start_time = time.time()
            
            for goal in goal_batch:
                goal_start_time = time.time()
                
                try:
                    # Get goal metadata
                    goal_uid = goal.UID()
                    goal_title = goal.Title()
                    
                    logger.debug(f"Processing Learning Goal: {goal_title} ({goal_uid})")
                    
                    # Check if recalculation is needed
                    if not force_recalculation and not _needs_recalculation(goal, mastery_data):
                        logger.debug(f"Skipping {goal_title} - no changes detected")
                        result['performance_metrics']['cache_hits'] += 1
                        continue
                    
                    result['performance_metrics']['cache_misses'] += 1
                    
                    # Store previous progress for comparison
                    previous_progress = getattr(goal, 'overall_progress', 0.0)
                    
                    # Get mastery data relevant to this goal
                    goal_mastery_data = _extract_goal_mastery_data(goal, mastery_data, result)
                    
                    # Validate data consistency for this goal
                    _validate_goal_data_consistency(goal, goal_mastery_data, result)
                    
                    # Calculate new progress using the goal's method
                    progress_result = goal.calculate_overall_progress(goal_mastery_data)
                    new_progress = progress_result.get('weighted_progress', 0.0)
                    
                    # Update goal progress fields
                    goal.overall_progress = new_progress
                    goal.progress = int(new_progress * 100)  # Backward compatibility
                    
                    # Track changes
                    progress_change = new_progress - previous_progress
                    if track_changes and abs(progress_change) > 0.001:  # Significant change
                        result['updated_goals'] += 1
                        
                        if progress_change > 0:
                            result['change_summary']['progress_increases'] += 1
                        else:
                            result['change_summary']['progress_decreases'] += 1
                        
                        result['change_summary']['total_change_magnitude'] += abs(progress_change)
                        
                        # Check for new completions
                        if previous_progress < 1.0 and new_progress >= 1.0:
                            result['change_summary']['new_completions'] += 1
                        
                        # Store detailed change metadata
                        _store_recalculation_metadata(goal, {
                            'previous_progress': previous_progress,
                            'new_progress': new_progress,
                            'progress_change': progress_change,
                            'items_mastered': progress_result.get('items_mastered', 0),
                            'total_items': progress_result.get('total_items', 0),
                            'recalculated_at': datetime.now().isoformat(),
                            'batch_number': batch_idx + 1,
                            'mastery_data_source': 'comprehensive_sync'
                        })
                        
                        logger.info(f"Updated {goal_title}: {previous_progress:.3f} → {new_progress:.3f} "
                                   f"(Δ{progress_change:+.3f})")
                    
                    # Synchronize with related Project Logs
                    _sync_progress_to_project_logs(goal, goal_mastery_data, result)
                    
                    # Mark as changed and commit periodically
                    goal._p_changed = True
                    result['processed_goals'] += 1
                    items_processed += 1
                    
                    # Track processing time
                    goal_processing_time = time.time() - goal_start_time
                    goal_processing_times.append(goal_processing_time)
                    
                except Exception as e:
                    error_msg = f"Failed to process Learning Goal {goal.Title()}: {e}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            # Commit batch and log progress
            batch_time = time.time() - batch_start_time
            logger.info(f"Completed batch {batch_idx + 1} in {batch_time:.2f}s")
            
            # Commit transaction at batch boundaries for better performance
            try:
                transaction.savepoint(optimistic=True)
            except Exception as e:
                logger.warning(f"Failed to commit batch {batch_idx + 1}: {e}")
        
        # Step 6: Final consistency check and cleanup
        _perform_final_consistency_check(learning_goals, mastery_data, result)
        
        # Calculate performance metrics
        total_time = time.time() - start_time
        result['processing_time'] = round(total_time, 2)
        
        if goal_processing_times:
            result['performance_metrics']['avg_processing_time_per_goal'] = \
                round(sum(goal_processing_times) / len(goal_processing_times), 4)
        
        if total_time > 0:
            result['performance_metrics']['items_per_second'] = \
                round(items_processed / total_time, 2)
        
        # Final transaction commit
        transaction.savepoint(optimistic=True)
        
        logger.info(f"Learning Goal progress recalculation completed: "
                   f"{result['processed_goals']} processed, "
                   f"{result['updated_goals']} updated, "
                   f"{len(result['errors'])} errors, "
                   f"in {result['processing_time']}s")
        
    except Exception as e:
        error_msg = f"Critical error in _recalculate_learning_goal_progress: {e}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
        result['processing_time'] = time.time() - start_time
    
    return result


def _build_comprehensive_mastery_map(knowledge_items, project_logs, mastery_cache, result):
    """Build a comprehensive map of knowledge item mastery levels from all sources.
    
    Args:
        knowledge_items: List of Knowledge Item objects
        project_logs: List of Project Log objects
        mastery_cache: Cache dictionary for performance
        result: Result dictionary to track issues
        
    Returns:
        dict: Mapping of knowledge item UIDs to mastery levels
    """
    mastery_data = {}
    
    # Collect mastery from Knowledge Items (their learning_progress field)
    for ki in knowledge_items:
        try:
            ki_uid = ki.UID()
            mastery_level = getattr(ki, 'learning_progress', 0.0)
            
            # Validate mastery level
            if not isinstance(mastery_level, (int, float)):
                mastery_level = 0.0
            elif mastery_level < 0.0:
                mastery_level = 0.0
            elif mastery_level > 1.0:
                mastery_level = 1.0
            
            mastery_data[ki_uid] = float(mastery_level)
            
        except Exception as e:
            result['warnings'].append(f"Failed to get mastery from Knowledge Item {ki.Title()}: {e}")
    
    # Overlay mastery from Project Logs (they may have more recent data)
    for pl in project_logs:
        try:
            if hasattr(pl, 'knowledge_item_progress') and pl.knowledge_item_progress:
                for ki_uid, mastery_level in pl.knowledge_item_progress.items():
                    # Validate mastery level
                    if not isinstance(mastery_level, (int, float)):
                        continue
                    elif mastery_level < 0.0:
                        mastery_level = 0.0
                    elif mastery_level > 1.0:
                        mastery_level = 1.0
                    
                    # Check for inconsistencies
                    existing_mastery = mastery_data.get(ki_uid)
                    if existing_mastery is not None and abs(existing_mastery - mastery_level) > 0.1:
                        result['consistency_issues']['inconsistent_mastery_levels'].append({
                            'knowledge_item_uid': ki_uid,
                            'knowledge_item_mastery': existing_mastery,
                            'project_log_mastery': mastery_level,
                            'project_log_title': pl.Title()
                        })
                    
                    # Use Project Log data as it's typically more recent
                    mastery_data[ki_uid] = float(mastery_level)
                    result['change_summary']['items_synchronized'] += 1
                    
        except Exception as e:
            result['warnings'].append(f"Failed to get mastery from Project Log {pl.Title()}: {e}")
    
    logger.info(f"Built mastery map for {len(mastery_data)} knowledge items")
    return mastery_data


def _build_learning_goal_dependency_graph(learning_goals):
    """Build a dependency graph between Learning Goals based on shared knowledge items.
    
    Args:
        learning_goals: List of Learning Goal objects
        
    Returns:
        dict: Adjacency list representing dependencies between goals
    """
    dependency_graph = {}
    
    # Build knowledge item to goals mapping
    ki_to_goals = defaultdict(list)
    
    for goal in learning_goals:
        goal_uid = goal.UID()
        dependency_graph[goal_uid] = []
        
        # Collect all knowledge items referenced by this goal
        referenced_items = set()
        
        if hasattr(goal, 'starting_knowledge_item') and goal.starting_knowledge_item:
            referenced_items.add(goal.starting_knowledge_item)
        
        if hasattr(goal, 'target_knowledge_items') and goal.target_knowledge_items:
            referenced_items.update(goal.target_knowledge_items)
        
        if hasattr(goal, 'knowledge_item_connections') and goal.knowledge_item_connections:
            for conn in goal.knowledge_item_connections:
                source_uid = conn.get('source_item_uid')
                target_uid = conn.get('target_item_uid')
                if source_uid:
                    referenced_items.add(source_uid)
                if target_uid:
                    referenced_items.add(target_uid)
        
        # Map knowledge items to this goal
        for ki_uid in referenced_items:
            ki_to_goals[ki_uid].append(goal_uid)
    
    # Build dependencies: if goals share knowledge items, create dependency edge
    for ki_uid, goal_uids in ki_to_goals.items():
        if len(goal_uids) > 1:
            # Create dependencies between goals that share this knowledge item
            for i, goal_uid_1 in enumerate(goal_uids):
                for goal_uid_2 in goal_uids[i+1:]:
                    # Add bidirectional dependency
                    if goal_uid_2 not in dependency_graph[goal_uid_1]:
                        dependency_graph[goal_uid_1].append(goal_uid_2)
                    if goal_uid_1 not in dependency_graph[goal_uid_2]:
                        dependency_graph[goal_uid_2].append(goal_uid_1)
    
    return dependency_graph


def _detect_and_resolve_circular_dependencies(dependency_graph, learning_goals, result):
    """Detect circular dependencies and resolve them by breaking weakest links.
    
    Args:
        dependency_graph: Adjacency list of dependencies
        learning_goals: List of Learning Goal objects
        result: Result dictionary to track circular dependencies
        
    Returns:
        list: List of circular dependency chains found and resolved
    """
    circular_deps = []
    
    def find_cycle_dfs(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in dependency_graph.get(node, []):
            if neighbor not in visited:
                cycle = find_cycle_dfs(neighbor, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        path.pop()
        rec_stack.remove(node)
        return None
    
    visited = set()
    for goal_uid in dependency_graph:
        if goal_uid not in visited:
            cycle = find_cycle_dfs(goal_uid, visited, set(), [])
            if cycle:
                circular_deps.append(cycle)
                result['circular_dependencies'].append({
                    'cycle': cycle,
                    'resolved_by': 'breaking_weakest_link'
                })
                
                # Break the cycle by removing the weakest dependency
                # For simplicity, remove the last edge in the cycle
                if len(cycle) >= 2:
                    node1, node2 = cycle[-2], cycle[-1]
                    if node2 in dependency_graph.get(node1, []):
                        dependency_graph[node1].remove(node2)
                    if node1 in dependency_graph.get(node2, []):
                        dependency_graph[node2].remove(node1)
                
                logger.warning(f"Resolved circular dependency: {' -> '.join(cycle)}")
    
    return circular_deps


def _determine_processing_order(dependency_graph, learning_goals):
    """Determine optimal processing order based on dependencies using topological sort.
    
    Args:
        dependency_graph: Adjacency list of dependencies
        learning_goals: List of Learning Goal objects
        
    Returns:
        list: Learning Goals in optimal processing order
    """
    from collections import deque
    
    # Calculate in-degrees
    in_degree = {goal.UID(): 0 for goal in learning_goals}
    
    for goal_uid in dependency_graph:
        for dependent_uid in dependency_graph[goal_uid]:
            if dependent_uid in in_degree:
                in_degree[dependent_uid] += 1
    
    # Topological sort using Kahn's algorithm
    queue = deque([goal_uid for goal_uid, degree in in_degree.items() if degree == 0])
    processing_order = []
    goal_uid_to_object = {goal.UID(): goal for goal in learning_goals}
    
    while queue:
        current_uid = queue.popleft()
        if current_uid in goal_uid_to_object:
            processing_order.append(goal_uid_to_object[current_uid])
        
        for dependent_uid in dependency_graph.get(current_uid, []):
            if dependent_uid in in_degree:
                in_degree[dependent_uid] -= 1
                if in_degree[dependent_uid] == 0:
                    queue.append(dependent_uid)
    
    # Add any remaining goals that weren't in the dependency graph
    processed_uids = {goal.UID() for goal in processing_order}
    for goal in learning_goals:
        if goal.UID() not in processed_uids:
            processing_order.append(goal)
    
    return processing_order


def _needs_recalculation(goal, mastery_data):
    """Check if a Learning Goal needs recalculation based on change detection.
    
    Args:
        goal: Learning Goal object
        mastery_data: Current mastery data map
        
    Returns:
        bool: True if recalculation is needed
    """
    try:
        # Check if goal has cached mastery data
        annotations = IAnnotations(goal)
        cached_data = annotations.get("knowledge.curator.cached_mastery_data")
        
        if not cached_data:
            return True  # No cached data, need to calculate
        
        # Get knowledge items referenced by this goal
        referenced_items = set()
        
        if hasattr(goal, 'starting_knowledge_item') and goal.starting_knowledge_item:
            referenced_items.add(goal.starting_knowledge_item)
        
        if hasattr(goal, 'target_knowledge_items') and goal.target_knowledge_items:
            referenced_items.update(goal.target_knowledge_items)
        
        if hasattr(goal, 'knowledge_item_connections') and goal.knowledge_item_connections:
            for conn in goal.knowledge_item_connections:
                source_uid = conn.get('source_item_uid')
                target_uid = conn.get('target_item_uid')
                if source_uid:
                    referenced_items.add(source_uid)
                if target_uid:
                    referenced_items.add(target_uid)
        
        # Check if any referenced item has changed
        for item_uid in referenced_items:
            current_mastery = mastery_data.get(item_uid, 0.0)
            cached_mastery = cached_data.get(item_uid, 0.0)
            
            if abs(current_mastery - cached_mastery) > 0.001:  # Significant change
                return True
        
        return False
        
    except Exception:
        return True  # Error checking, recalculate to be safe


def _extract_goal_mastery_data(goal, mastery_data, result):
    """Extract mastery data relevant to a specific Learning Goal.
    
    Args:
        goal: Learning Goal object
        mastery_data: Complete mastery data map
        result: Result dictionary to track issues
        
    Returns:
        dict: Mastery data filtered for this goal's knowledge items
    """
    goal_mastery_data = {}
    
    # Collect all knowledge items referenced by this goal
    referenced_items = set()
    
    if hasattr(goal, 'starting_knowledge_item') and goal.starting_knowledge_item:
        referenced_items.add(goal.starting_knowledge_item)
    
    if hasattr(goal, 'target_knowledge_items') and goal.target_knowledge_items:
        referenced_items.update(goal.target_knowledge_items)
    
    if hasattr(goal, 'knowledge_item_connections') and goal.knowledge_item_connections:
        for conn in goal.knowledge_item_connections:
            source_uid = conn.get('source_item_uid')
            target_uid = conn.get('target_item_uid')
            if source_uid:
                referenced_items.add(source_uid)
            if target_uid:
                referenced_items.add(target_uid)
    
    # Extract mastery data for referenced items
    for item_uid in referenced_items:
        if item_uid in mastery_data:
            goal_mastery_data[item_uid] = mastery_data[item_uid]
        else:
            # Missing knowledge item
            result['consistency_issues']['missing_knowledge_items'].append({
                'knowledge_item_uid': item_uid,
                'learning_goal_title': goal.Title(),
                'learning_goal_uid': goal.UID()
            })
            goal_mastery_data[item_uid] = 0.0  # Default to no mastery
    
    return goal_mastery_data


def _validate_goal_data_consistency(goal, goal_mastery_data, result):
    """Validate data consistency for a Learning Goal.
    
    Args:
        goal: Learning Goal object
        goal_mastery_data: Mastery data for this goal
        result: Result dictionary to track issues
    """
    try:
        # Check for orphaned references in knowledge_item_connections
        if hasattr(goal, 'knowledge_item_connections') and goal.knowledge_item_connections:
            seen_connections = set()
            for conn in goal.knowledge_item_connections:
                source_uid = conn.get('source_item_uid')
                target_uid = conn.get('target_item_uid')
                
                # Check for duplicate connections
                conn_key = (source_uid, target_uid)
                if conn_key in seen_connections:
                    result['consistency_issues']['duplicate_connections'].append({
                        'source_uid': source_uid,
                        'target_uid': target_uid,
                        'learning_goal_title': goal.Title()
                    })
                else:
                    seen_connections.add(conn_key)
                
                # Check for orphaned references
                if source_uid and source_uid not in goal_mastery_data:
                    result['consistency_issues']['orphaned_references'].append({
                        'type': 'connection_source',
                        'knowledge_item_uid': source_uid,
                        'learning_goal_title': goal.Title()
                    })
                
                if target_uid and target_uid not in goal_mastery_data:
                    result['consistency_issues']['orphaned_references'].append({
                        'type': 'connection_target',
                        'knowledge_item_uid': target_uid,
                        'learning_goal_title': goal.Title()
                    })
        
    except Exception as e:
        result['warnings'].append(f"Failed to validate consistency for {goal.Title()}: {e}")


def _store_recalculation_metadata(goal, metadata):
    """Store metadata about the recalculation for audit and debugging.
    
    Args:
        goal: Learning Goal object
        metadata: Dictionary containing recalculation metadata
    """
    try:
        annotations = IAnnotations(goal)
        
        # Initialize recalculation history if needed
        if "knowledge.curator.recalculation_history" not in annotations:
            annotations["knowledge.curator.recalculation_history"] = PersistentList()
        
        history = annotations["knowledge.curator.recalculation_history"]
        
        # Create recalculation record
        record = PersistentMapping(metadata)
        history.append(record)
        
        # Keep only last 100 recalculations
        if len(history) > 100:
            history.pop(0)
        
        # Store current mastery snapshot for change detection
        if 'mastery_data' in metadata:
            annotations["knowledge.curator.cached_mastery_data"] = PersistentMapping(
                metadata['mastery_data']
            )
        
        transaction.savepoint(optimistic=True)
        
    except Exception as e:
        logger.error(f"Failed to store recalculation metadata for {goal.Title()}: {e}")


def _sync_progress_to_project_logs(goal, goal_mastery_data, result):
    """Synchronize Learning Goal progress back to related Project Logs.
    
    Args:
        goal: Learning Goal object
        goal_mastery_data: Mastery data for this goal
        result: Result dictionary to track sync operations
    """
    try:
        from plone import api
        
        # Find Project Logs that reference this Learning Goal
        catalog = api.portal.get_tool(name='portal_catalog')
        goal_uid = goal.UID()
        
        # Search for Project Logs with attached_learning_goal field
        project_logs = catalog(
            portal_type='ProjectLog',
            SearchableText=goal_uid  # This might find references in various fields
        )
        
        for brain in project_logs:
            try:
                pl = brain.getObject()
                if not pl:
                    continue
                
                # Check if this Project Log is actually attached to our goal
                if (hasattr(pl, 'attached_learning_goal') and 
                    pl.attached_learning_goal == goal_uid):
                    
                    # Update the Project Log's knowledge item progress to match
                    if hasattr(pl, 'knowledge_item_progress'):
                        updated_items = 0
                        for ki_uid, mastery in goal_mastery_data.items():
                            current_mastery = pl.knowledge_item_progress.get(ki_uid, 0.0)
                            if abs(current_mastery - mastery) > 0.001:
                                pl.knowledge_item_progress[ki_uid] = mastery
                                updated_items += 1
                        
                        if updated_items > 0:
                            pl.add_entry(
                                description=f"Synchronized {updated_items} knowledge item mastery levels from Learning Goal",
                                author="System",
                                entry_type="sync"
                            )
                            pl._p_changed = True
                            result['change_summary']['items_synchronized'] += updated_items
                        
            except Exception as e:
                result['warnings'].append(f"Failed to sync to Project Log {brain.UID}: {e}")
        
    except Exception as e:
        result['warnings'].append(f"Failed to sync progress to Project Logs for {goal.Title()}: {e}")


def _perform_final_consistency_check(learning_goals, mastery_data, result):
    """Perform a final consistency check after all processing is complete.
    
    Args:
        learning_goals: List of processed Learning Goal objects
        mastery_data: Final mastery data map
        result: Result dictionary to update with final checks
    """
    try:
        logger.info("Performing final consistency check")
        
        # Check for Learning Goals with zero progress that should have some
        for goal in learning_goals:
            try:
                overall_progress = getattr(goal, 'overall_progress', 0.0)
                
                if overall_progress == 0.0:
                    # Check if goal has any knowledge items with mastery > 0
                    goal_mastery_data = _extract_goal_mastery_data(goal, mastery_data, result)
                    has_mastery = any(mastery > 0.0 for mastery in goal_mastery_data.values())
                    
                    if has_mastery:
                        result['warnings'].append(
                            f"Learning Goal '{goal.Title()}' has zero progress but "
                            f"contains knowledge items with mastery > 0"
                        )
                
            except Exception as e:
                result['warnings'].append(f"Failed consistency check for {goal.Title()}: {e}")
        
        # Log summary of consistency issues
        if result['consistency_issues']['orphaned_references']:
            logger.warning(f"Found {len(result['consistency_issues']['orphaned_references'])} orphaned references")
        
        if result['consistency_issues']['missing_knowledge_items']:
            logger.warning(f"Found {len(result['consistency_issues']['missing_knowledge_items'])} missing knowledge items")
        
        if result['consistency_issues']['inconsistent_mastery_levels']:
            logger.warning(f"Found {len(result['consistency_issues']['inconsistent_mastery_levels'])} inconsistent mastery levels")
        
        if result['consistency_issues']['duplicate_connections']:
            logger.warning(f"Found {len(result['consistency_issues']['duplicate_connections'])} duplicate connections")
        
    except Exception as e:
        result['warnings'].append(f"Failed to perform final consistency check: {e}")
