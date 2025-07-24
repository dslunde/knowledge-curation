"""Knowledge Graph API endpoints."""

from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


@implementer(IPublishTraverse)
class KnowledgeGraphService(Service):
    """Service for knowledge graph operations."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if len(self.params) == 0:
            return self.get_graph()
        elif self.params[0] == "connections":
            return self.get_connections()
        elif self.params[0] == "suggest":
            return self.suggest_connections()
        elif self.params[0] == "visualize":
            return self.visualize_graph()
        else:
            self.request.response.setStatus(404)
            return {"error": "Not found"}

    def get_graph(self):
        """Get the knowledge graph for the current context."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")

        catalog = api.portal.get_tool("portal_catalog")

        # Get all knowledge items
        brains = catalog(
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
            path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
        )

        nodes = []
        edges = []

        for brain in brains:
            obj = brain.getObject()

            # Create node
            node = {
                "id": brain.UID,
                "title": brain.Title,
                "type": brain.portal_type,
                "url": brain.getURL(),
                "description": brain.Description,
                "review_state": brain.review_state,
                "created": brain.created.ISO8601(),
                "modified": brain.modified.ISO8601(),
            }

            # Add type-specific data
            if hasattr(obj, "tags"):
                node["tags"] = getattr(obj, "tags", [])

            if hasattr(obj, "progress"):
                node["progress"] = getattr(obj, "progress", 0)

            if hasattr(obj, "status"):
                node["status"] = getattr(obj, "status", "")

            nodes.append(node)

            # Create edges from connections
            if hasattr(obj, "connections"):
                for target_uid in getattr(obj, "connections", []):
                    edge = {
                        "source": brain.UID,
                        "target": target_uid,
                        "type": "connection",
                    }
                    edges.append(edge)

            # Create edges from related notes
            if hasattr(obj, "related_notes"):
                for target_uid in getattr(obj, "related_notes", []):
                    edge = {
                        "source": brain.UID,
                        "target": target_uid,
                        "type": "related",
                    }
                    edges.append(edge)

        return {"nodes": nodes, "edges": edges, "count": len(nodes)}

    def get_connections(self):
        """Get connections for a specific item."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        connections = []
        catalog = api.portal.get_tool("portal_catalog")

        # Get direct connections
        if hasattr(self.context, "connections"):
            for uid in getattr(self.context, "connections", []):
                brain = catalog(UID=uid)
                if brain:
                    brain = brain[0]
                    connections.append({
                        "uid": uid,
                        "title": brain.Title,
                        "type": brain.portal_type,
                        "url": brain.getURL(),
                        "connection_type": "direct",
                    })

        # Get related notes
        if hasattr(self.context, "related_notes"):
            for uid in getattr(self.context, "related_notes", []):
                brain = catalog(UID=uid)
                if brain:
                    brain = brain[0]
                    connections.append({
                        "uid": uid,
                        "title": brain.Title,
                        "type": brain.portal_type,
                        "url": brain.getURL(),
                        "connection_type": "related",
                    })

        # Find items that reference this item
        uid = api.content.get_uuid(self.context)
        referencing = catalog(
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
            SearchableText=uid,
        )

        for brain in referencing:
            if uid != brain.UID:
                connections.append({
                    "uid": brain.UID,
                    "title": brain.Title,
                    "type": brain.portal_type,
                    "url": brain.getURL(),
                    "connection_type": "reference",
                })

        return {"connections": connections, "count": len(connections)}

    def _get_existing_connections(self):
        """Get existing connections to exclude from suggestions."""
        existing = set()
        if hasattr(self.context, "connections"):
            existing.update(getattr(self.context, "connections", []))
        if hasattr(self.context, "related_notes"):
            existing.update(getattr(self.context, "related_notes", []))
        return existing

    def _find_similar_items(self, current_vector, existing_connections):
        """Find similar items based on embedding vector."""
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"]
        )
        similarities = []

        for brain in brains:
            if (
                api.content.get_uuid(self.context) == brain.UID
                or brain.UID in existing_connections
            ):
                continue

            obj = brain.getObject()
            if hasattr(obj, "embedding_vector"):
                other_vector = getattr(obj, "embedding_vector", [])
                if other_vector:
                    similarity = self._calculate_similarity(
                        current_vector, other_vector
                    )
                    if similarity > 0.7:
                        similarities.append({"brain": brain, "similarity": similarity})

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:10]

    def suggest_connections(self):
        """Suggest potential connections based on similarity."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        current_vector = getattr(self.context, "embedding_vector", [])
        if not current_vector:
            return {"suggestions": [], "message": "No embedding vector available"}

        existing_connections = self._get_existing_connections()
        similar_items = self._find_similar_items(current_vector, existing_connections)

        suggestions = [
            {
                "uid": item["brain"].UID,
                "title": item["brain"].Title,
                "type": item["brain"].portal_type,
                "url": item["brain"].getURL(),
                "similarity": round(item["similarity"], 3),
                "description": item["brain"].Description,
            }
            for item in similar_items
        ]

        return {"suggestions": suggestions, "count": len(suggestions)}

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

    def visualize_graph(self):
        """Get graph data optimized for visualization."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        graph_data = self.get_graph()

        # Add visualization-specific properties
        type_colors = {
            "ResearchNote": "#3498db",
            "LearningGoal": "#2ecc71",
            "ProjectLog": "#e74c3c",
            "BookmarkPlus": "#f39c12",
        }

        # Add colors and sizes to nodes
        for node in graph_data["nodes"]:
            node["color"] = type_colors.get(node["type"], "#95a5a6")
            # Size based on number of connections
            connections = len([
                e
                for e in graph_data["edges"]
                if e["source"] == node["id"] or e["target"] == node["id"]
            ])
            node["size"] = 10 + (connections * 2)

        # Add edge properties
        for edge in graph_data["edges"]:
            edge["color"] = "#bdc3c7" if edge["type"] == "connection" else "#ecf0f1"
            edge["width"] = 2 if edge["type"] == "connection" else 1

        return {
            "graph": graph_data,
            "visualization": {
                "width": 1200,
                "height": 800,
                "force": {"charge": -300, "linkDistance": 100, "gravity": 0.05},
            },
        }
