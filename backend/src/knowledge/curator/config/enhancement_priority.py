"""Enhancement Priority Configuration.

This module contains the configuration for automatic enhancement workflow priority.
Knowledge Items receive the highest priority in all enhancement operations.
"""

from plone import api
from plone.api.exc import InvalidParameterError
import os

# Default enhancement priority configuration
DEFAULT_ENHANCEMENT_PRIORITY_CONFIG = {
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
        "confidence_boost": 1.5,  # Boost for low confidence items needing re-analysis
        "special_factors": {
            "no_ai_summary": 1.5,  # Boost if no AI summary
            "no_concepts": 1.3,    # Boost if no concepts extracted
            "no_connections": 1.2, # Boost if no connections
            "low_confidence": 1.5  # Boost if confidence < 0.7
        }
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
        "confidence_boost": 1.3,
        "special_factors": {}
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
        "confidence_boost": 1.2,
        "special_factors": {}
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
        "confidence_boost": 1.1,
        "special_factors": {}
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
        "confidence_boost": 1.0,
        "special_factors": {}
    },
    "default": {
        "base_priority": 30,
        "workflow_multipliers": {
            "default": 1.0
        },
        "age_decay_factor": 0.80,
        "confidence_boost": 1.0,
        "special_factors": {}
    }
}

# Queue processing configuration
QUEUE_PROCESSING_CONFIG = {
    "batch_sizes": {
        "default": 20,
        "knowledge_items": 10,  # Dedicated batch size for Knowledge Items
        "high_priority": 30,    # Larger batch for high priority items
        "scheduled": 50         # Batch size for scheduled processing
    },
    "priority_thresholds": {
        "critical": 100,        # Process immediately
        "high": 75,            # Process in next batch
        "medium": 50,          # Normal processing
        "low": 25              # Process when queue is light
    },
    "processing_order": [
        "KnowledgeItem",       # Always process Knowledge Items first
        "BookmarkPlus",
        "ResearchNote",
        "LearningGoal",
        "ProjectLog"
    ],
    "knowledge_item_ratio": 0.5,  # At least 50% of batch should be Knowledge Items
    "max_retries": 3,
    "retry_delay_hours": 24,
    "stale_entry_days": 7
}

# Enhancement operations configuration
ENHANCEMENT_OPERATIONS = {
    "full": {
        "description": "Complete AI enhancement including summary, tags, concepts, and connections",
        "priority_multiplier": 1.0,
        "required_for": ["KnowledgeItem", "ResearchNote"]
    },
    "embeddings": {
        "description": "Generate or update vector embeddings",
        "priority_multiplier": 1.2,
        "required_for": ["KnowledgeItem"]
    },
    "connections": {
        "description": "Find and suggest content connections",
        "priority_multiplier": 1.5,
        "required_for": ["KnowledgeItem", "ResearchNote"]
    },
    "ai_summary": {
        "description": "Generate AI summary only",
        "priority_multiplier": 1.3,
        "required_for": ["KnowledgeItem"]
    },
    "concepts": {
        "description": "Extract concepts and knowledge gaps",
        "priority_multiplier": 1.1,
        "required_for": ["KnowledgeItem", "ResearchNote"]
    },
    "final_check": {
        "description": "Final validation before publishing",
        "priority_multiplier": 2.0,  # High priority for publishing workflow
        "required_for": ["KnowledgeItem"]
    }
}


def get_enhancement_priority_config():
    """Get enhancement priority configuration.
    
    Checks for environment variables or registry settings to override defaults.
    """
    config = DEFAULT_ENHANCEMENT_PRIORITY_CONFIG.copy()
    
    # Check for environment variable overrides
    knowledge_item_priority = os.environ.get("KNOWLEDGE_ITEM_PRIORITY")
    if knowledge_item_priority:
        try:
            config["KnowledgeItem"]["base_priority"] = float(knowledge_item_priority)
        except ValueError:
            pass
    
    # Try to get from Plone registry
    try:
        portal = api.portal.get()
        if portal:
            # Check for registry overrides
            try:
                ki_priority = api.portal.get_registry_record(
                    "knowledge.curator.enhancement.knowledge_item_priority"
                )
                if ki_priority:
                    config["KnowledgeItem"]["base_priority"] = ki_priority
            except (InvalidParameterError, KeyError):
                pass
            
            # Check for Knowledge Item ratio override
            try:
                ki_ratio = api.portal.get_registry_record(
                    "knowledge.curator.enhancement.knowledge_item_ratio"
                )
                if ki_ratio:
                    QUEUE_PROCESSING_CONFIG["knowledge_item_ratio"] = ki_ratio
            except (InvalidParameterError, KeyError):
                pass
                
    except Exception:
        # Portal not available, use defaults
        pass
    
    return config


def get_queue_processing_config():
    """Get queue processing configuration."""
    return QUEUE_PROCESSING_CONFIG.copy()


def get_enhancement_operations():
    """Get enhancement operations configuration."""
    return ENHANCEMENT_OPERATIONS.copy()


def should_prioritize_content_type(portal_type):
    """Check if a content type should be prioritized.
    
    Args:
        portal_type: The portal type to check
        
    Returns:
        bool: True if the content type should be prioritized
    """
    # Knowledge Items always get priority
    if portal_type == "KnowledgeItem":
        return True
    
    # Check configuration
    config = get_enhancement_priority_config()
    type_config = config.get(portal_type, config["default"])
    
    # Prioritize if base priority is above medium threshold
    return type_config.get("base_priority", 0) >= QUEUE_PROCESSING_CONFIG["priority_thresholds"]["medium"]


def get_operation_priority_multiplier(operation, portal_type):
    """Get priority multiplier for a specific operation and content type.
    
    Args:
        operation: The enhancement operation
        portal_type: The content type
        
    Returns:
        float: Priority multiplier
    """
    operations = get_enhancement_operations()
    op_config = operations.get(operation, {})
    
    # Check if operation is required for this type
    required_for = op_config.get("required_for", [])
    base_multiplier = op_config.get("priority_multiplier", 1.0)
    
    # Give extra boost if operation is required for this type
    if portal_type in required_for:
        return base_multiplier * 1.2
    
    return base_multiplier