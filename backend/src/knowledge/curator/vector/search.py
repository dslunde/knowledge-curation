"""Similarity search utilities for the vector database."""

from plone import api
from knowledge.curator.vector.adapter import QdrantAdapter
from knowledge.curator.vector.embeddings import EmbeddingGenerator
from knowledge.curator.vector.config import get_vector_config
from typing import Any
import logging

logger = logging.getLogger("knowledge.curator.vector")


class SimilaritySearch:
    """Perform similarity searches on knowledge content."""

    def __init__(self):
        """Initialize search components."""
        config = get_vector_config()
        self.adapter = QdrantAdapter(
            host=config["qdrant_host"],
            port=config["qdrant_port"],
            api_key=config.get("qdrant_api_key"),
            https=config.get("qdrant_https", False)
        )
        self.embeddings = EmbeddingGenerator(config["embedding_model"])

    def search_by_text(self, query: str, limit: int = 10,
                      score_threshold: float = 0.5,
                      content_types: list[str] | None = None,
                      workflow_states: list[str] | None = None,
                      tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Search for similar content by text query."""
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.generate_embedding(query)

            # Build filters
            filters = {}
            if content_types:
                filters["content_type"] = {"$in": content_types}
            if workflow_states:
                filters["workflow_state"] = {"$in": workflow_states}
            if tags:
                filters["tags"] = {"$any": tags}

            # Search similar vectors
            results = self.adapter.search_similar(
                query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )

            # Enhance results with Plone objects
            enhanced_results = []
            for result in results:
                try:
                    brain = api.content.find(UID=result["uid"])
                    if brain:
                        obj = brain[0].getObject()
                        enhanced_result = result.copy()
                        enhanced_result.update({
                            "url": obj.absolute_url(),
                            "created": obj.created().ISO8601(),
                            "creator": obj.Creator(),
                            "review_state": api.content.get_state(obj),
                        })
                        enhanced_results.append(enhanced_result)
                except Exception as e:
                    logger.warning(f"Could not enhance result {result['uid']}: {e}")
                    enhanced_results.append(result)

            return enhanced_results

        except Exception as e:
            logger.error(f"Search by text failed: {e}")
            return []

    def find_similar_content(self, content_uid: str, limit: int = 5,
                           score_threshold: float = 0.6,
                           same_type_only: bool = False) -> list[dict[str, Any]]:
        """Find content similar to a given item."""
        try:
            # Get the content object
            brain = api.content.find(UID=content_uid)
            if not brain:
                logger.warning(f"Content not found: {content_uid}")
                return []

            obj = brain[0].getObject()

            # Find related content
            results = self.adapter.find_related_content(
                content_uid,
                limit=limit,
                score_threshold=score_threshold
            )

            # Filter by type if requested
            if same_type_only:
                content_type = obj.portal_type
                results = [r for r in results if r.get("content_type") == content_type]

            # Enhance results
            enhanced_results = []
            for result in results:
                try:
                    brain = api.content.find(UID=result["uid"])
                    if brain:
                        related_obj = brain[0].getObject()
                        enhanced_result = result.copy()
                        enhanced_result.update({
                            "url": related_obj.absolute_url(),
                            "created": related_obj.created().ISO8601(),
                            "creator": related_obj.Creator(),
                            "review_state": api.content.get_state(related_obj),
                        })
                        enhanced_results.append(enhanced_result)
                except Exception as e:
                    logger.warning(f"Could not enhance result {result['uid']}: {e}")
                    enhanced_results.append(result)

            return enhanced_results

        except Exception as e:
            logger.error(f"Find similar content failed: {e}")
            return []

    def find_duplicates(self, score_threshold: float = 0.9,
                       content_types: list[str] | None = None) -> list[list[dict[str, Any]]]:
        """Find potential duplicate content based on similarity."""
        try:
            # Get all content
            query = {}
            if content_types:
                query["portal_type"] = content_types

            brains = api.content.find(**query)

            # Group duplicates
            duplicate_groups = []
            processed_uids = set()

            for brain in brains:
                uid = brain.UID
                if uid in processed_uids:
                    continue

                # Find similar content
                similar = self.find_similar_content(
                    uid,
                    limit=10,
                    score_threshold=score_threshold,
                    same_type_only=True
                )

                if similar:
                    # Create group including the source
                    group = [{
                        "uid": uid,
                        "title": brain.Title,
                        "path": brain.getPath(),
                        "url": brain.getURL(),
                        "score": 1.0  # Self-similarity
                    }]

                    for item in similar:
                        group.append(item)
                        processed_uids.add(item["uid"])

                    duplicate_groups.append(group)
                    processed_uids.add(uid)

            return duplicate_groups

        except Exception as e:
            logger.error(f"Find duplicates failed: {e}")
            return []

    def semantic_clustering(self, content_types: list[str] | None = None,
                          n_clusters: int = 5) -> dict[str, list[dict[str, Any]]]:
        """Perform semantic clustering on content."""
        try:
            from sklearn.cluster import KMeans
            import numpy as np

            # Get all content
            query = {}
            if content_types:
                query["portal_type"] = content_types

            brains = api.content.find(**query)

            # Collect embeddings and metadata
            embeddings = []
            metadata = []

            for brain in brains:
                # Get vector from database
                results = self.adapter.client.retrieve(
                    collection_name=self.adapter.collection_name,
                    ids=[brain.UID],
                    with_vectors=True
                )

                if results:
                    embeddings.append(results[0].vector)
                    metadata.append({
                        "uid": brain.UID,
                        "title": brain.Title,
                        "path": brain.getPath(),
                        "url": brain.getURL(),
                        "type": brain.portal_type
                    })

            if len(embeddings) < n_clusters:
                logger.warning(f"Not enough content for {n_clusters} clusters")
                n_clusters = len(embeddings)

            # Perform clustering
            X = np.array(embeddings)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(X)

            # Group by cluster
            clusters = {}
            for i, label in enumerate(labels):
                cluster_name = f"cluster_{label}"
                if cluster_name not in clusters:
                    clusters[cluster_name] = []
                clusters[cluster_name].append(metadata[i])

            # Calculate cluster centers and find representative items
            for cluster_name in clusters:
                cluster_indices = [i for i, l in enumerate(labels)
                                 if f"cluster_{l}" == cluster_name]
                cluster_embeddings = X[cluster_indices]
                center = np.mean(cluster_embeddings, axis=0)

                # Find closest item to center
                distances = np.linalg.norm(cluster_embeddings - center, axis=1)
                representative_idx = cluster_indices[np.argmin(distances)]

                # Add cluster info
                for item in clusters[cluster_name]:
                    item["cluster_representative"] = (
                        item["uid"] == metadata[representative_idx]["uid"]
                    )

            return clusters

        except Exception as e:
            logger.error(f"Semantic clustering failed: {e}")
            return {}

    def get_recommendation_candidates(self, user_id: str, limit: int = 20,
                                    min_score: float = 0.5) -> list[dict[str, Any]]:
        """Get content recommendations based on user's recent interactions."""
        try:
            # Get user's recent content (viewed, created, or modified)
            user_content = api.content.find(Creator=user_id, sort_on="modified",
                                          sort_order="descending", sort_limit=10)

            if not user_content:
                # Fallback to popular content
                return self._get_popular_content(limit)

            # Collect embeddings from user's content
            user_embeddings = []
            for brain in user_content:
                results = self.adapter.client.retrieve(
                    collection_name=self.adapter.collection_name,
                    ids=[brain.UID],
                    with_vectors=True
                )
                if results:
                    user_embeddings.append(results[0].vector)

            if not user_embeddings:
                return self._get_popular_content(limit)

            # Calculate average user preference vector
            import numpy as np
            avg_embedding = np.mean(user_embeddings, axis=0).tolist()

            # Search for similar content
            results = self.adapter.search_similar(
                avg_embedding,
                limit=limit * 2,  # Get extra to filter out already seen
                score_threshold=min_score
            )

            # Filter out content user has already interacted with
            user_content_uids = {b.UID for b in user_content}
            recommendations = []

            for result in results:
                if result["uid"] not in user_content_uids:
                    recommendations.append(result)
                    if len(recommendations) >= limit:
                        break

            return recommendations

        except Exception as e:
            logger.error(f"Get recommendations failed: {e}")
            return []

    def _get_popular_content(self, limit: int) -> list[dict[str, Any]]:
        """Get popular content as fallback for recommendations."""
        try:
            # Get recently modified content
            brains = api.content.find(
                sort_on="modified",
                sort_order="descending",
                review_state="published",
                sort_limit=limit
            )

            results = []
            for brain in brains:
                results.append({
                    "uid": brain.UID,
                    "title": brain.Title,
                    "path": brain.getPath(),
                    "url": brain.getURL(),
                    "type": brain.portal_type,
                    "score": 0.0  # No similarity score
                })

            return results

        except Exception as e:
            logger.error(f"Get popular content failed: {e}")
            return []
