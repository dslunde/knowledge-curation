"""Knowledge Graph API endpoints."""

from datetime import datetime
from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from zope.component import getUtility
from knowledge.curator.behaviors.interfaces import IKnowledgeRelationship, ISuggestedRelationship
import json


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
        if self.request.method == 'GET':
            if len(self.params) == 0:
                return self.get_graph()
            elif self.params[0] == "connections":
                return self.get_connections()
            elif self.params[0] == "suggest":
                return self.suggest_connections()
            elif self.params[0] == "visualize":
                return self.visualize_graph()
            elif self.params[0] == "metrics":
                return self.get_graph_metrics()
            elif self.params[0] == "analysis":
                return self.get_graph_analysis()
            else:
                self.request.response.setStatus(404)
                return {"error": "Not found"}
        elif self.request.method == 'POST':
            if len(self.params) > 0:
                if self.params[0] == "relationship":
                    return self.create_relationship()
                elif self.params[0] == "accept-suggestion":
                    return self.accept_suggestion()
            self.request.response.setStatus(400)
            return {"error": "Invalid endpoint"}
        elif self.request.method == 'PUT':
            if len(self.params) > 0 and self.params[0] == "relationship":
                return self.update_relationship()
            self.request.response.setStatus(400)
            return {"error": "Invalid endpoint"}
        elif self.request.method == 'DELETE':
            if len(self.params) > 0 and self.params[0] == "relationship":
                return self.delete_relationship()
            self.request.response.setStatus(400)
            return {"error": "Invalid endpoint"}

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

            # Create edges from typed relationships
            if hasattr(obj, "relationships"):
                for rel in getattr(obj, "relationships", []):
                    edge = {
                        "source": brain.UID,
                        "target": rel.get("target_uid"),
                        "type": rel.get("relationship_type", "related"),
                        "strength": rel.get("strength", 0.5),
                        "metadata": rel.get("metadata", {}),
                        "created": rel.get("created"),
                        "confidence": rel.get("confidence", 1.0)
                    }
                    edges.append(edge)
            # Backwards compatibility with old connections field
            elif hasattr(obj, "connections"):
                for target_uid in getattr(obj, "connections", []):
                    edge = {
                        "source": brain.UID,
                        "target": target_uid,
                        "type": "connection",
                        "strength": 0.5,
                        "metadata": {},
                        "created": brain.created.ISO8601(),
                        "confidence": 1.0
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

        # Get typed relationships
        if hasattr(self.context, "relationships"):
            for rel in getattr(self.context, "relationships", []):
                target_uid = rel.get("target_uid")
                brain = catalog(UID=target_uid)
                if brain:
                    brain = brain[0]
                    connections.append({
                        "uid": target_uid,
                        "title": brain.Title,
                        "type": brain.portal_type,
                        "url": brain.getURL(),
                        "connection_type": rel.get("relationship_type", "related"),
                        "strength": rel.get("strength", 0.5),
                        "metadata": rel.get("metadata", {}),
                        "created": rel.get("created"),
                        "confidence": rel.get("confidence", 1.0)
                    })
        
        # Get suggested relationships
        suggested = []
        if hasattr(self.context, "suggested_relationships"):
            for sug in getattr(self.context, "suggested_relationships", []):
                if not sug.get("is_accepted", False):
                    target_uid = sug.get("target_uid")
                    brain = catalog(UID=target_uid)
                    if brain:
                        brain = brain[0]
                        suggested.append({
                            "uid": target_uid,
                            "title": brain.Title,
                            "type": brain.portal_type,
                            "url": brain.getURL(),
                            "connection_type": sug.get("relationship_type", "related"),
                            "strength": sug.get("strength", 0.5),
                            "suggestion_reason": sug.get("suggestion_reason", ""),
                            "similarity_score": sug.get("similarity_score", 0.0),
                            "confidence": sug.get("confidence", 0.7)
                        })

        return {
            "connections": connections, 
            "suggested": suggested,
            "count": len(connections),
            "suggested_count": len(suggested)
        }

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
    
    def create_relationship(self):
        """Create a typed relationship between content items."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        data = json.loads(self.request.body)
        source_uid = data.get("source_uid") or api.content.get_uuid(self.context)
        target_uid = data.get("target_uid")
        relationship_type = data.get("relationship_type", "related")
        strength = data.get("strength", 0.5)
        metadata = data.get("metadata", {})
        
        if not target_uid:
            self.request.response.setStatus(400)
            return {"error": "target_uid is required"}
        
        # Get source object
        catalog = api.portal.get_tool("portal_catalog")
        source_brain = catalog(UID=source_uid)
        if not source_brain:
            self.request.response.setStatus(404)
            return {"error": "Source content not found"}
        
        source_obj = source_brain[0].getObject()
        
        # Initialize relationships if not exists
        if not hasattr(source_obj, "relationships"):
            source_obj.relationships = []
        
        # Check if relationship already exists
        existing = [r for r in source_obj.relationships 
                   if r.get("target_uid") == target_uid 
                   and r.get("relationship_type") == relationship_type]
        
        if existing:
            self.request.response.setStatus(409)
            return {"error": "Relationship already exists"}
        
        # Create new relationship
        new_relationship = {
            "source_uid": source_uid,
            "target_uid": target_uid,
            "relationship_type": relationship_type,
            "strength": strength,
            "metadata": metadata,
            "created": datetime.now().isoformat(),
            "confidence": 1.0
        }
        
        source_obj.relationships.append(new_relationship)
        source_obj.reindexObject()
        
        return {
            "status": "created",
            "relationship": new_relationship
        }
    
    def update_relationship(self):
        """Update an existing relationship."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        data = json.loads(self.request.body)
        source_uid = data.get("source_uid") or api.content.get_uuid(self.context)
        target_uid = data.get("target_uid")
        relationship_type = data.get("relationship_type")
        
        if not target_uid or not relationship_type:
            self.request.response.setStatus(400)
            return {"error": "target_uid and relationship_type are required"}
        
        # Get source object
        catalog = api.portal.get_tool("portal_catalog")
        source_brain = catalog(UID=source_uid)
        if not source_brain:
            self.request.response.setStatus(404)
            return {"error": "Source content not found"}
        
        source_obj = source_brain[0].getObject()
        
        # Find and update relationship
        updated = False
        for rel in getattr(source_obj, "relationships", []):
            if (rel.get("target_uid") == target_uid and 
                rel.get("relationship_type") == relationship_type):
                # Update fields
                if "strength" in data:
                    rel["strength"] = data["strength"]
                if "metadata" in data:
                    rel["metadata"].update(data["metadata"])
                if "confidence" in data:
                    rel["confidence"] = data["confidence"]
                rel["modified"] = datetime.now().isoformat()
                updated = True
                break
        
        if not updated:
            self.request.response.setStatus(404)
            return {"error": "Relationship not found"}
        
        source_obj.reindexObject()
        return {"status": "updated"}
    
    def delete_relationship(self):
        """Delete a relationship."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        data = json.loads(self.request.body)
        source_uid = data.get("source_uid") or api.content.get_uuid(self.context)
        target_uid = data.get("target_uid")
        relationship_type = data.get("relationship_type")
        
        if not target_uid:
            self.request.response.setStatus(400)
            return {"error": "target_uid is required"}
        
        # Get source object
        catalog = api.portal.get_tool("portal_catalog")
        source_brain = catalog(UID=source_uid)
        if not source_brain:
            self.request.response.setStatus(404)
            return {"error": "Source content not found"}
        
        source_obj = source_brain[0].getObject()
        
        # Remove relationship
        if hasattr(source_obj, "relationships"):
            original_count = len(source_obj.relationships)
            source_obj.relationships = [
                r for r in source_obj.relationships
                if not (r.get("target_uid") == target_uid and
                       (not relationship_type or r.get("relationship_type") == relationship_type))
            ]
            
            if len(source_obj.relationships) < original_count:
                source_obj.reindexObject()
                return {"status": "deleted"}
        
        self.request.response.setStatus(404)
        return {"error": "Relationship not found"}
    
    def accept_suggestion(self):
        """Accept a suggested relationship."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        data = json.loads(self.request.body)
        source_uid = data.get("source_uid") or api.content.get_uuid(self.context)
        target_uid = data.get("target_uid")
        
        if not target_uid:
            self.request.response.setStatus(400)
            return {"error": "target_uid is required"}
        
        # Get source object
        catalog = api.portal.get_tool("portal_catalog")
        source_brain = catalog(UID=source_uid)
        if not source_brain:
            self.request.response.setStatus(404)
            return {"error": "Source content not found"}
        
        source_obj = source_brain[0].getObject()
        
        # Find suggested relationship
        suggestion = None
        if hasattr(source_obj, "suggested_relationships"):
            for sug in source_obj.suggested_relationships:
                if sug.get("target_uid") == target_uid and not sug.get("is_accepted"):
                    suggestion = sug
                    break
        
        if not suggestion:
            self.request.response.setStatus(404)
            return {"error": "Suggestion not found"}
        
        # Move to accepted relationships
        if not hasattr(source_obj, "relationships"):
            source_obj.relationships = []
        
        # Create accepted relationship
        new_relationship = {
            "source_uid": source_uid,
            "target_uid": target_uid,
            "relationship_type": suggestion.get("relationship_type", "related"),
            "strength": suggestion.get("strength", 0.5),
            "metadata": suggestion.get("metadata", {}),
            "created": datetime.now().isoformat(),
            "confidence": suggestion.get("confidence", 0.7),
            "accepted_from_suggestion": True
        }
        
        source_obj.relationships.append(new_relationship)
        
        # Mark suggestion as accepted
        suggestion["is_accepted"] = True
        suggestion["review_date"] = datetime.now().isoformat()
        
        source_obj.reindexObject()
        
        return {
            "status": "accepted",
            "relationship": new_relationship
        }
    
    def get_graph_metrics(self):
        """Calculate graph metrics for a node or the entire graph."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        node_uid = self.request.get("node_uid") or api.content.get_uuid(self.context)
        
        # Get graph data
        graph_data = self.get_graph()
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        # Build adjacency lists
        adjacency = {}
        for node in nodes:
            adjacency[node["id"]] = []
        
        for edge in edges:
            if edge["source"] in adjacency:
                adjacency[edge["source"]].append(edge["target"])
            if edge["target"] in adjacency:
                adjacency[edge["target"]].append(edge["source"])
        
        if node_uid:
            # Calculate metrics for specific node
            if node_uid not in adjacency:
                self.request.response.setStatus(404)
                return {"error": "Node not found"}
            
            degree = len(adjacency[node_uid])
            
            # Calculate local clustering coefficient
            neighbors = adjacency[node_uid]
            if degree < 2:
                clustering_coefficient = 0.0
            else:
                edges_between_neighbors = 0
                for i, n1 in enumerate(neighbors):
                    for n2 in neighbors[i+1:]:
                        if n2 in adjacency.get(n1, []):
                            edges_between_neighbors += 1
                
                possible_edges = degree * (degree - 1) / 2
                clustering_coefficient = edges_between_neighbors / possible_edges if possible_edges > 0 else 0
            
            # Calculate betweenness centrality (simplified)
            # For now, just use degree centrality as approximation
            centrality = degree / (len(nodes) - 1) if len(nodes) > 1 else 0
            
            return {
                "node_uid": node_uid,
                "degree": degree,
                "clustering_coefficient": round(clustering_coefficient, 3),
                "centrality_score": round(centrality, 3),
                "connections": neighbors
            }
        else:
            # Calculate overall graph metrics
            total_nodes = len(nodes)
            total_edges = len(edges)
            
            # Average degree
            avg_degree = (2 * total_edges) / total_nodes if total_nodes > 0 else 0
            
            # Density
            possible_edges = total_nodes * (total_nodes - 1) / 2
            density = total_edges / possible_edges if possible_edges > 0 else 0
            
            # Find connected components (simplified)
            visited = set()
            components = 0
            
            def dfs(node):
                visited.add(node)
                for neighbor in adjacency.get(node, []):
                    if neighbor not in visited:
                        dfs(neighbor)
            
            for node in nodes:
                if node["id"] not in visited:
                    dfs(node["id"])
                    components += 1
            
            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "average_degree": round(avg_degree, 2),
                "density": round(density, 3),
                "connected_components": components,
                "is_connected": components == 1
            }
    
    def get_graph_analysis(self):
        """Perform advanced graph analysis."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        # Get graph data
        graph_data = self.get_graph()
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        # Identify knowledge hubs (nodes with high degree)
        node_degrees = {}
        for edge in edges:
            node_degrees[edge["source"]] = node_degrees.get(edge["source"], 0) + 1
            node_degrees[edge["target"]] = node_degrees.get(edge["target"], 0) + 1
        
        # Sort by degree
        sorted_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
        
        # Knowledge hubs (top 10%)
        hub_count = max(1, len(sorted_nodes) // 10)
        hubs = []
        
        for node_id, degree in sorted_nodes[:hub_count]:
            node_info = next((n for n in nodes if n["id"] == node_id), None)
            if node_info:
                hubs.append({
                    "uid": node_id,
                    "title": node_info["title"],
                    "type": node_info["type"],
                    "degree": degree,
                    "url": node_info["url"]
                })
        
        # Find isolated nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])
        
        isolated = []
        for node in nodes:
            if node["id"] not in connected_nodes:
                isolated.append({
                    "uid": node["id"],
                    "title": node["title"],
                    "type": node["type"],
                    "url": node["url"]
                })
        
        # Analyze relationship types
        relationship_stats = {}
        for edge in edges:
            rel_type = edge.get("type", "unknown")
            if rel_type not in relationship_stats:
                relationship_stats[rel_type] = {
                    "count": 0,
                    "total_strength": 0,
                    "avg_confidence": 0
                }
            
            stats = relationship_stats[rel_type]
            stats["count"] += 1
            stats["total_strength"] += edge.get("strength", 0.5)
            stats["avg_confidence"] += edge.get("confidence", 1.0)
        
        # Calculate averages
        for rel_type, stats in relationship_stats.items():
            if stats["count"] > 0:
                stats["avg_strength"] = round(stats["total_strength"] / stats["count"], 3)
                stats["avg_confidence"] = round(stats["avg_confidence"] / stats["count"], 3)
                del stats["total_strength"]
        
        return {
            "knowledge_hubs": hubs,
            "isolated_nodes": isolated,
            "relationship_statistics": relationship_stats,
            "hub_count": len(hubs),
            "isolated_count": len(isolated),
            "analysis_timestamp": datetime.now().isoformat()
        }
