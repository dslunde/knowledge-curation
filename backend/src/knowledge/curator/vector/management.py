"""Vector database collection management utilities."""

from datetime import datetime
<<<<<<< HEAD
from knowledge.curator.vector.adapter import QdrantAdapter
from knowledge.curator.vector.config import get_vector_config
from knowledge.curator.vector.embeddings import EmbeddingGenerator
from plone import api
from Products.CMFCore.utils import getToolByName
from typing import Any

import json
import logging

=======
from typing import Any
import logging
import json
>>>>>>> fixing_linting_and_tests

logger = logging.getLogger("knowledge.curator.vector")


class VectorCollectionManager:
    """Manage vector database collections and operations."""

    def __init__(self):
        """Initialize manager components."""
        config = get_vector_config()
        self.adapter = QdrantAdapter(
            host=config["qdrant_host"],
            port=config["qdrant_port"],
            api_key=config.get("qdrant_api_key"),
            https=config.get("qdrant_https", False),
        )
        self.embeddings = EmbeddingGenerator(config["embedding_model"])

    def initialize_database(self) -> bool:
        """Initialize the vector database with proper configuration."""
        try:
            # Initialize collection with correct vector size
            vector_size = self.embeddings.embedding_dimension
            self.adapter.initialize_collection(vector_size)

            logger.info(f"Initialized vector database with dimension {vector_size}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

<<<<<<< HEAD
    def rebuild_index(
        self,
        content_types: list[str] | None = None,
        batch_size: int = 100,
        clear_first: bool = True,
    ) -> dict[str, Any]:
=======
    def rebuild_index(self, content_types: list[str] | None = None,
                     batch_size: int = 100, clear_first: bool = True) -> dict[str, Any]:
>>>>>>> fixing_linting_and_tests
        """Rebuild the entire vector index."""
        try:
            start_time = datetime.now()

            # Clear collection if requested
            if clear_first:
                self.adapter.clear_collection()

            # Get all relevant content
            if content_types is None:
<<<<<<< HEAD
                content_types = [
                    "BookmarkPlus",
                    "ResearchNote",
                    "LearningGoal",
                    "ProjectLog",
                ]
=======
                content_types = ["BookmarkPlus", "ResearchNote", "LearningGoal", "ProjectLog"]
>>>>>>> fixing_linting_and_tests

            query = {
                "portal_type": content_types,
                "review_state": ["private", "process", "reviewed", "published"],
            }

            catalog = getToolByName(api.portal.get(), "portal_catalog")
            brains = catalog.searchResults(**query)
            total_items = len(brains)

            logger.info(f"Found {total_items} items to index")

            # Process in batches
            processed = 0
            errors = 0
            batch_documents = []
            batch_texts = []

            for brain in brains:
                try:
                    obj = brain.getObject()

                    # Prepare document metadata
                    doc = {
                        "uid": brain.UID,
                        "path": brain.getPath(),
                        "title": brain.Title,
                        "description": brain.Description,
                        "content_type": brain.portal_type,
                        "workflow_state": brain.review_state,
                        "modified": brain.modified.ISO8601(),
                        "tags": getattr(obj, "tags", []),
                        "knowledge_type": getattr(obj, "knowledge_type", None),
                    }

                    # Prepare text for embedding
                    text = self.embeddings.prepare_content_text(obj)

                    batch_documents.append(doc)
                    batch_texts.append(text)

                    # Process batch when full
                    if len(batch_documents) >= batch_size:
                        embeddings = self.embeddings.generate_embeddings(
<<<<<<< HEAD
                            batch_texts, batch_size=32
                        )
                        self.adapter.add_vectors(
                            batch_documents, embeddings, batch_size
                        )
=======
                            batch_texts,
                            batch_size=32
                        )
                        self.adapter.add_vectors(batch_documents, embeddings, batch_size)
>>>>>>> fixing_linting_and_tests

                        processed += len(batch_documents)
                        logger.info(f"Processed {processed}/{total_items} items")

                        batch_documents = []
                        batch_texts = []

                except Exception as e:
                    logger.error(f"Error processing {brain.getPath()}: {e}")
                    errors += 1

            # Process remaining items
            if batch_documents:
                embeddings = self.embeddings.generate_embeddings(
                    batch_texts, batch_size=32
                )
                self.adapter.add_vectors(batch_documents, embeddings, batch_size)
                processed += len(batch_documents)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "total_items": total_items,
                "processed": processed,
                "errors": errors,
                "duration_seconds": duration,
                "items_per_second": processed / duration if duration > 0 else 0,
            }

            logger.info(f"Index rebuild completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")
<<<<<<< HEAD
            return {"success": False, "error": str(e)}
=======
            return {
                "success": False,
                "error": str(e)
            }
>>>>>>> fixing_linting_and_tests

    def update_content_vector(self, content_object) -> bool:
        """Update vector for a single content object."""
        try:
            # Prepare document metadata
            doc = {
                "uid": content_object.UID(),
                "path": "/".join(content_object.getPhysicalPath()),
                "title": content_object.Title(),
                "description": content_object.Description(),
                "content_type": content_object.portal_type,
                "workflow_state": api.content.get_state(content_object),
                "modified": content_object.modified().ISO8601(),
                "tags": getattr(content_object, "tags", []),
                "knowledge_type": getattr(content_object, "knowledge_type", None),
            }

            # Generate embedding
            text = self.embeddings.prepare_content_text(content_object)
            embedding = self.embeddings.generate_embedding(text)

            # Update vector
<<<<<<< HEAD
            return self.adapter.update_vector(content_object.UID(), embedding, doc)
=======
            return self.adapter.update_vector(
                content_object.UID(),
                embedding,
                doc
            )
>>>>>>> fixing_linting_and_tests

        except Exception as e:
            logger.error(f"Failed to update content vector: {e}")
            return False

    def delete_content_vector(self, uid: str) -> bool:
        """Delete vector for a content object."""
        try:
            return self.adapter.delete_vector(uid)
        except Exception as e:
            logger.error(f"Failed to delete content vector: {e}")
            return False

    def get_database_stats(self) -> dict[str, Any]:
        """Get statistics about the vector database."""
        try:
            info = self.adapter.get_collection_info()

            # Get content type distribution
            all_points = []
            offset = None
            while True:
                batch, next_offset = self.adapter.client.scroll(
                    collection_name=self.adapter.collection_name,
                    limit=100,
                    offset=offset,
                )
                all_points.extend(batch)
                if next_offset is None:
                    break
                offset = next_offset

            # Count by content type
            type_counts = {}
            state_counts = {}

            for point in all_points:
                content_type = point.payload.get("content_type", "unknown")
                type_counts[content_type] = type_counts.get(content_type, 0) + 1

                state = point.payload.get("workflow_state", "unknown")
                state_counts[state] = state_counts.get(state, 0) + 1

            stats = {
                "collection_info": info,
                "content_type_distribution": type_counts,
                "workflow_state_distribution": state_counts,
                "total_vectors": len(all_points),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    def health_check(self) -> dict[str, Any]:
        """Perform health check on vector database."""
        try:
            # Check Qdrant connection
            self.adapter.client.get_collections()
            qdrant_healthy = True
            qdrant_error = None

        except Exception as e:
            qdrant_healthy = False
            qdrant_error = str(e)

        try:
            # Check embedding model
            test_embedding = self.embeddings.generate_embedding("test")
            embedding_healthy = (
                len(test_embedding) == self.embeddings.embedding_dimension
            )
            embedding_error = None

        except Exception as e:
            embedding_healthy = False
            embedding_error = str(e)

        # Check collection exists
        collection_exists = False
        if qdrant_healthy:
            try:
                info = self.adapter.get_collection_info()
                collection_exists = info.get("status") is not None
            except Exception:
                pass

        return {
            "healthy": qdrant_healthy and embedding_healthy and collection_exists,
            "qdrant": {"healthy": qdrant_healthy, "error": qdrant_error},
            "embeddings": {
                "healthy": embedding_healthy,
                "error": embedding_error,
                "model": self.embeddings.model_name,
                "dimension": self.embeddings.embedding_dimension,
            },
            "collection": {
                "exists": collection_exists,
                "name": self.adapter.collection_name,
            },
        }

    def backup_vectors(self, backup_path: str) -> bool:
        """Backup vector data to a file."""
        try:
            # Get all vectors with metadata
            all_points = []
            offset = None

            while True:
                batch, next_offset = self.adapter.client.scroll(
                    collection_name=self.adapter.collection_name,
                    limit=100,
                    offset=offset,
                    with_vectors=True,
                )

                for point in batch:
                    all_points.append({
                        "id": point.id,
                        "vector": point.vector,
                        "payload": point.payload,
                    })

                if next_offset is None:
                    break
                offset = next_offset

            # Save to file
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "collection_name": self.adapter.collection_name,
                "vector_dimension": self.embeddings.embedding_dimension,
                "total_points": len(all_points),
                "points": all_points,
            }

<<<<<<< HEAD
            with open(backup_path, "w") as f:
=======
            with open(backup_path, 'w') as f:
>>>>>>> fixing_linting_and_tests
                json.dump(backup_data, f)

            logger.info(f"Backed up {len(all_points)} vectors to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to backup vectors: {e}")
            return False

    def restore_vectors(self, backup_path: str) -> bool:
        """Restore vector data from a backup file."""
        try:
            # Load backup data
            with open(backup_path) as f:
                backup_data = json.load(f)

            # Verify compatibility
            if backup_data["vector_dimension"] != self.embeddings.embedding_dimension:
                logger.error(
                    f"Dimension mismatch: backup has {backup_data['vector_dimension']}, "
                    f"current model has {self.embeddings.embedding_dimension}"
                )
                return False

            # Clear existing data
            self.adapter.clear_collection()

            # Restore points in batches
            points = backup_data["points"]
            batch_size = 100

            for i in range(0, len(points), batch_size):
<<<<<<< HEAD
                batch = points[i : i + batch_size]
=======
                batch = points[i:i + batch_size]
>>>>>>> fixing_linting_and_tests

                documents = []
                embeddings = []

                for point in batch:
                    documents.append(point["payload"])
                    embeddings.append(point["vector"])

                self.adapter.add_vectors(documents, embeddings, batch_size)

            logger.info(f"Restored {len(points)} vectors from {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore vectors: {e}")
            return False
