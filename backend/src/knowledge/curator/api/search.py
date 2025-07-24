"""Search API endpoints for semantic and similarity search."""

from knowledge.curator.interfaces import IAIService
from plone import api
from plone.restapi.services import Service
from zope.component import queryUtility
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

import json


@implementer(IPublishTraverse)
class SearchService(Service):
    """Service for semantic and similarity search operations."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if self.request.method == "POST":
            return self.search()
        elif self.request.method == "GET" and self.params:
            if self.params[0] == "similar":
                return self.find_similar()
            elif self.params[0] == "semantic":
                return self.semantic_search()

        self.request.response.setStatus(400)
        return {"error": "Invalid request"}

    def search(self):
        """Perform search based on request data."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        search_type = data.get("type", "semantic")

        if search_type == "semantic":
=======
        data = json.loads(self.request.get('BODY', '{}'))
        search_type = data.get('type', 'semantic')

        if search_type == 'semantic':
>>>>>>> fixing_linting_and_tests
            return self._semantic_search(data)
        elif search_type == "similarity":
            return self._similarity_search(data)
        elif search_type == "fulltext":
            return self._fulltext_search(data)
        else:
            self.request.response.setStatus(400)
            return {"error": "Invalid search type"}

    def _semantic_search(self, data):
        """Perform semantic search using embeddings."""
<<<<<<< HEAD
        query = data.get("query", "")
        limit = data.get("limit", 20)
        portal_types = data.get(
            "portal_types",
            ["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
        )
        filters = data.get("filters", {})

        if not query:
            self.request.response.setStatus(400)
            return {"error": "Query is required"}
=======
        query = data.get('query', '')
        limit = data.get('limit', 20)
        portal_types = data.get('portal_types', ['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus'])
        filters = data.get('filters', {})

        if not query:
            self.request.response.setStatus(400)
            return {'error': 'Query is required'}
>>>>>>> fixing_linting_and_tests

        # Get AI service
        ai_service = queryUtility(IAIService)
        if not ai_service:
            return self._fulltext_search(data)  # Fallback to fulltext

        # Generate embedding for query
        try:
            query_vector = ai_service.generate_embedding(query)
        except Exception:
            # Fallback to fulltext search
            return self._fulltext_search(data)

<<<<<<< HEAD
        catalog = api.portal.get_tool("portal_catalog")

        # Build query
        catalog_query = {"portal_type": portal_types}

        # Add filters
        if filters.get("review_state"):
            catalog_query["review_state"] = filters["review_state"]
        if filters.get("tags"):
            catalog_query["Subject"] = {"query": filters["tags"], "operator": "and"}
        if filters.get("date_range"):
            if filters["date_range"].get("start"):
                catalog_query["created"] = {
                    "query": filters["date_range"]["start"],
                    "range": "min",
                }
            if filters["date_range"].get("end"):
                catalog_query["created"] = {
                    "query": filters["date_range"]["end"],
                    "range": "max",
                }
=======
        catalog = api.portal.get_tool('portal_catalog')

        # Build query
        catalog_query = {
            'portal_type': portal_types
        }

        # Add filters
        if filters.get('review_state'):
            catalog_query['review_state'] = filters['review_state']
        if filters.get('tags'):
            catalog_query['Subject'] = {'query': filters['tags'], 'operator': 'and'}
        if filters.get('date_range'):
            if filters['date_range'].get('start'):
                catalog_query['created'] = {'query': filters['date_range']['start'], 'range': 'min'}
            if filters['date_range'].get('end'):
                catalog_query['created'] = {'query': filters['date_range']['end'], 'range': 'max'}
>>>>>>> fixing_linting_and_tests

        brains = catalog(**catalog_query)

        # Calculate similarities
        results = []
        for brain in brains:
            obj = brain.getObject()
            if hasattr(obj, "embedding_vector"):
                content_vector = getattr(obj, "embedding_vector", [])
                if content_vector:
                    similarity = self._calculate_similarity(
                        query_vector, content_vector
                    )
                    if similarity > 0.5:  # Threshold
<<<<<<< HEAD
                        results.append({"brain": brain, "similarity": similarity})
=======
                        results.append({
                            'brain': brain,
                            'similarity': similarity
                        })
>>>>>>> fixing_linting_and_tests

        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        # Format results
        items = []
        for result in results:
            brain = result["brain"]
            items.append({
                "uid": brain.UID,
                "title": brain.Title,
                "description": brain.Description,
                "url": brain.getURL(),
                "portal_type": brain.portal_type,
                "review_state": brain.review_state,
                "created": brain.created.ISO8601(),
                "modified": brain.modified.ISO8601(),
                "similarity_score": round(result["similarity"], 3),
                "tags": brain.Subject,
            })

        return {
            "items": items,
            "items_total": len(items),
            "query": query,
            "search_type": "semantic",
        }

    def _similarity_search(self, data):
        """Find similar items to a given item."""
<<<<<<< HEAD
        uid = data.get("uid")
        limit = data.get("limit", 10)
        threshold = data.get("threshold", 0.7)

        if not uid:
            self.request.response.setStatus(400)
            return {"error": "UID is required"}

        catalog = api.portal.get_tool("portal_catalog")
=======
        uid = data.get('uid')
        limit = data.get('limit', 10)
        threshold = data.get('threshold', 0.7)

        if not uid:
            self.request.response.setStatus(400)
            return {'error': 'UID is required'}

        catalog = api.portal.get_tool('portal_catalog')
>>>>>>> fixing_linting_and_tests
        brains = catalog(UID=uid)

        if not brains:
            self.request.response.setStatus(404)
<<<<<<< HEAD
            return {"error": "Item not found"}

        source_obj = brains[0].getObject()

        if not hasattr(source_obj, "embedding_vector"):
            return {"items": [], "message": "No embedding vector available"}

        source_vector = getattr(source_obj, "embedding_vector", [])

        if not source_vector:
            return {"items": [], "message": "No embedding vector available"}
=======
            return {'error': 'Item not found'}

        source_obj = brains[0].getObject()

        if not hasattr(source_obj, 'embedding_vector'):
            return {'items': [], 'message': 'No embedding vector available'}

        source_vector = getattr(source_obj, 'embedding_vector', [])

        if not source_vector:
            return {'items': [], 'message': 'No embedding vector available'}
>>>>>>> fixing_linting_and_tests

        # Search for similar items
        all_brains = catalog(
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"]
        )

        results = []

        for brain in all_brains:
            if uid == brain.UID:
                continue

            obj = brain.getObject()
            if hasattr(obj, "embedding_vector"):
                other_vector = getattr(obj, "embedding_vector", [])
                if other_vector:
                    similarity = self._calculate_similarity(source_vector, other_vector)
                    if similarity >= threshold:
<<<<<<< HEAD
                        results.append({"brain": brain, "similarity": similarity})
=======
                        results.append({
                            'brain': brain,
                            'similarity': similarity
                        })
>>>>>>> fixing_linting_and_tests

        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        # Format results
        items = []
        for result in results:
            brain = result["brain"]
            items.append({
                "uid": brain.UID,
                "title": brain.Title,
                "description": brain.Description,
                "url": brain.getURL(),
                "portal_type": brain.portal_type,
                "review_state": brain.review_state,
                "similarity_score": round(result["similarity"], 3),
                "tags": brain.Subject,
            })

        return {
            "items": items,
            "items_total": len(items),
            "source_uid": uid,
            "search_type": "similarity",
        }

    def _fulltext_search(self, data):
        """Perform traditional fulltext search."""
<<<<<<< HEAD
        query = data.get("query", "")
        limit = data.get("limit", 20)
        portal_types = data.get(
            "portal_types",
            ["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
        )
        filters = data.get("filters", {})

        if not query:
            self.request.response.setStatus(400)
            return {"error": "Query is required"}

        catalog = api.portal.get_tool("portal_catalog")
=======
        query = data.get('query', '')
        limit = data.get('limit', 20)
        portal_types = data.get('portal_types', ['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus'])
        filters = data.get('filters', {})

        if not query:
            self.request.response.setStatus(400)
            return {'error': 'Query is required'}

        catalog = api.portal.get_tool('portal_catalog')
>>>>>>> fixing_linting_and_tests

        # Build query
        catalog_query = {
            "SearchableText": query,
            "portal_type": portal_types,
            "sort_on": "modified",
            "sort_order": "descending",
            "b_size": limit,
        }

        # Add filters
<<<<<<< HEAD
        if filters.get("review_state"):
            catalog_query["review_state"] = filters["review_state"]
        if filters.get("tags"):
            catalog_query["Subject"] = {"query": filters["tags"], "operator": "and"}
        if filters.get("date_range"):
            if filters["date_range"].get("start"):
                catalog_query["created"] = {
                    "query": filters["date_range"]["start"],
                    "range": "min",
                }
            if filters["date_range"].get("end"):
                catalog_query["created"] = {
                    "query": filters["date_range"]["end"],
                    "range": "max",
                }
=======
        if filters.get('review_state'):
            catalog_query['review_state'] = filters['review_state']
        if filters.get('tags'):
            catalog_query['Subject'] = {'query': filters['tags'], 'operator': 'and'}
        if filters.get('date_range'):
            if filters['date_range'].get('start'):
                catalog_query['created'] = {'query': filters['date_range']['start'], 'range': 'min'}
            if filters['date_range'].get('end'):
                catalog_query['created'] = {'query': filters['date_range']['end'], 'range': 'max'}
>>>>>>> fixing_linting_and_tests

        brains = catalog(**catalog_query)

        # Format results
        items = []
        for brain in brains[:limit]:
            items.append({
                "uid": brain.UID,
                "title": brain.Title,
                "description": brain.Description,
                "url": brain.getURL(),
                "portal_type": brain.portal_type,
                "review_state": brain.review_state,
                "created": brain.created.ISO8601(),
                "modified": brain.modified.ISO8601(),
                "tags": brain.Subject,
            })

        return {
            "items": items,
            "items_total": len(brains),
            "query": query,
            "search_type": "fulltext",
        }

    def find_similar(self):
        """Find similar items to the current context."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
<<<<<<< HEAD
            return {"error": "Unauthorized"}

        limit = int(self.request.get("limit", 10))
        threshold = float(self.request.get("threshold", 0.7))
=======
            return {'error': 'Unauthorized'}

        limit = int(self.request.get('limit', 10))
        threshold = float(self.request.get('threshold', 0.7))
>>>>>>> fixing_linting_and_tests

        return self._similarity_search({
            "uid": api.content.get_uuid(self.context),
            "limit": limit,
            "threshold": threshold,
        })

    def semantic_search(self):
        """Perform semantic search from GET parameters."""
<<<<<<< HEAD
        query = self.request.get("q", "")
        limit = int(self.request.get("limit", 20))
        portal_types = (
            self.request.get("types", "").split(",")
            if self.request.get("types")
            else None
        )

        data = {"query": query, "limit": limit}

        if portal_types:
            data["portal_types"] = [pt.strip() for pt in portal_types if pt.strip()]
=======
        query = self.request.get('q', '')
        limit = int(self.request.get('limit', 20))
        portal_types = self.request.get('types', '').split(',') if self.request.get('types') else None

        data = {
            'query': query,
            'limit': limit
        }

        if portal_types:
            data['portal_types'] = [pt.strip() for pt in portal_types if pt.strip()]
>>>>>>> fixing_linting_and_tests

        return self._semantic_search(data)

    def _calculate_similarity(self, vector1, vector2):
        """Calculate cosine similarity between two vectors."""
        if len(vector1) != len(vector2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vector1, vector2, strict=False))
        magnitude1 = sum(a * a for a in vector1) ** 0.5
        magnitude2 = sum(b * b for b in vector2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
