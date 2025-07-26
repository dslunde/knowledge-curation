"""Vector Database Configuration Management."""

import os

from plone import api
from plone.api.exc import CannotGetPortalError, InvalidParameterError
from zope.component import ComponentLookupError


def get_vector_config():
    """Get vector database configuration from environment or defaults."""
    # Get configuration from environment variables with defaults
    config = {
        # Qdrant connection settings
        "qdrant_host": os.environ.get("QDRANT_HOST", "localhost"),
        "qdrant_port": int(os.environ.get("QDRANT_PORT", "6333")),
        "qdrant_api_key": os.environ.get("QDRANT_API_KEY"),
        "qdrant_https": os.environ.get("QDRANT_HTTPS", "false").lower() == "true",
        # Embedding model settings
        "embedding_model": os.environ.get(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        # Search settings
        "default_search_limit": int(os.environ.get("VECTOR_SEARCH_LIMIT", "10")),
        "default_score_threshold": float(
            os.environ.get("VECTOR_SCORE_THRESHOLD", "0.5")
        ),
        # Batch processing settings
        "batch_size": int(os.environ.get("VECTOR_BATCH_SIZE", "100")),
        "embedding_batch_size": int(os.environ.get("EMBEDDING_BATCH_SIZE", "32")),
        # Feature flags
        "auto_index_on_create": os.environ.get(
            "VECTOR_AUTO_INDEX_CREATE", "true"
        ).lower()
        == "true",
        "auto_index_on_modify": os.environ.get(
            "VECTOR_AUTO_INDEX_MODIFY", "true"
        ).lower()
        == "true",
        "auto_delete_on_remove": os.environ.get("VECTOR_AUTO_DELETE", "true").lower()
        == "true",
    }

    # Try to get settings from Plone registry if available
    try:
        portal = api.portal.get()
        if portal:
            registry = api.portal.get_registry_record

            # Override with registry values if they exist
            registry_keys = [
                ("knowledge.curator.vector.qdrant_host", "qdrant_host"),
                ("knowledge.curator.vector.qdrant_port", "qdrant_port"),
                ("knowledge.curator.vector.qdrant_api_key", "qdrant_api_key"),
                ("knowledge.curator.vector.embedding_model", "embedding_model"),
                (
                    "knowledge.curator.vector.default_search_limit",
                    "default_search_limit",
                ),
                (
                    "knowledge.curator.vector.default_score_threshold",
                    "default_score_threshold",
                ),
            ]

            for registry_key, config_key in registry_keys:
                try:
                    value = registry(registry_key)
                    if value is not None:
                        config[config_key] = value
                except (AttributeError, KeyError, InvalidParameterError):
                    # Registry key doesn't exist, use default
                    pass
    except (AttributeError, ComponentLookupError, CannotGetPortalError):
        # Portal not available or registry not accessible
        pass

    return config


# Configuration constants
SUPPORTED_CONTENT_TYPES = ["KnowledgeItem", "BookmarkPlus", "ResearchNote", "LearningGoal", "ProjectLog", "KnowledgeContainer"]

INDEXED_WORKFLOW_STATES = ["private", "process", "reviewed", "published"]

# Model configurations with their dimensions
EMBEDDING_MODELS = {
    "sentence-transformers/all-MiniLM-L6-v2": {
        "dimension": 384,
        "max_seq_length": 256,
        "description": "Fast and efficient model for general text",
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "dimension": 768,
        "max_seq_length": 384,
        "description": "Higher quality embeddings, slower",
    },
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
        "dimension": 384,
        "max_seq_length": 128,
        "description": "Multilingual support",
    },
}
