"""Qdrant vector database adapter for Plone knowledge system."""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from typing import Any
import logging
import uuid


logger = logging.getLogger("knowledge.curator.vector")


class QdrantAdapter:
    """Adapter for Qdrant vector database operations."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: str | None = None,
        https: bool = False,
    ):
        """Initialize Qdrant client with configuration."""
        self.client = QdrantClient(host=host, port=port, api_key=api_key, https=https)
        self.collection_name = "plone_knowledge"
        self.vector_size = 384  # Default for sentence-transformers/all-MiniLM-L6-v2

    def initialize_collection(self, vector_size: int | None = None):
        """Create or recreate the collection with proper configuration."""
        if vector_size:
            self.vector_size = vector_size

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if exists:
                logger.info(f"Collection '{self.collection_name}' already exists")
            else:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                logger.info(f"Created collection '{self.collection_name}'")

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    def add_vectors(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[list[float]],
        batch_size: int = 100,
    ) -> bool:
        """Add multiple vectors to the collection in batches."""
        try:
            points = []
            for i, (doc, embedding) in enumerate(
                zip(documents, embeddings, strict=False)
            ):
                point_id = str(uuid.uuid4())
                payload = {
                    "uid": doc.get("uid"),
                    "path": doc.get("path"),
                    "title": doc.get("title"),
                    "description": doc.get("description"),
                    "content_type": doc.get("content_type"),
                    "workflow_state": doc.get("workflow_state"),
                    "modified": doc.get("modified"),
                    "tags": doc.get("tags", []),
                    "knowledge_type": doc.get("knowledge_type"),
                }

                points.append(
                    PointStruct(id=point_id, vector=embedding, payload=payload)
                )

                # Upload in batches
                if len(points) >= batch_size:
                    self.client.upsert(
                        collection_name=self.collection_name, points=points
                    )
                    points = []

            # Upload remaining points
            if points:
                self.client.upsert(collection_name=self.collection_name, points=points)

            logger.info(f"Added {len(documents)} vectors to collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            return False

    def update_vector(
        self, uid: str, embedding: list[float], metadata: dict[str, Any] | None = None
    ) -> bool:
        """Update a single vector by UID."""
        try:
            # Find existing point by UID
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="uid", match=MatchValue(value=uid))]
                ),
                limit=1,
            )

            if results[0]:
                point_id = results[0][0].id
                # Update the vector
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload=metadata or results[0][0].payload,
                        )
                    ],
                )
                logger.info(f"Updated vector for UID: {uid}")
                return True
            else:
                # Create new point if not found
                return self.add_vectors([metadata], [embedding])

        except Exception as e:
            logger.error(f"Failed to update vector: {e}")
            return False

    def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        try:
            # Build filter conditions
            filter_conditions = []
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        filter_conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )

            search_filter = (
                Filter(must=filter_conditions) if filter_conditions else None
            )

            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
            )

            # Format results
            similar_items = []
            for result in results:
                item = result.payload.copy()
                item["score"] = result.score
                item["vector_id"] = result.id
                similar_items.append(item)

            return similar_items

        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            return []

    def find_related_content(
        self, uid: str, limit: int = 5, score_threshold: float = 0.6
    ) -> list[dict[str, Any]]:
        """Find content related to a specific item by UID."""
        try:
            # Get the vector for the given UID
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="uid", match=MatchValue(value=uid))]
                ),
                limit=1,
                with_vectors=True,
            )

            if not results[0]:
                logger.warning(f"No vector found for UID: {uid}")
                return []

            # Search for similar content, excluding the source
            query_vector = results[0][0].vector
            similar = self.search_similar(
                query_vector,
                limit=limit + 1,  # Get extra to exclude self
                score_threshold=score_threshold,
            )

            # Filter out the source document
            return [item for item in similar if item.get("uid") != uid][:limit]

        except Exception as e:
            logger.error(f"Failed to find related content: {e}")
            return []

    def delete_vector(self, uid: str) -> bool:
        """Delete vector by UID."""
        try:
            # Find and delete point by UID
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="uid", match=MatchValue(value=uid))]
                ),
                limit=1,
            )

            if results[0]:
                point_id = results[0][0].id
                self.client.delete(
                    collection_name=self.collection_name, points_selector=[point_id]
                )
                logger.info(f"Deleted vector for UID: {uid}")
                return True
            else:
                logger.warning(f"No vector found to delete for UID: {uid}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            return False

    def get_collection_info(self) -> dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "status": info.status,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}

    def clear_collection(self) -> bool:
        """Clear all vectors from the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.initialize_collection()
            logger.info("Collection cleared and recreated")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
