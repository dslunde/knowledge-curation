"""Knowledge graph visualization view."""

from knowledge.curator.graph import GraphAlgorithms
from knowledge.curator.graph import GraphStorage
from plone import api
from Products.Five import BrowserView


class KnowledgeGraphView(BrowserView):
    """View for knowledge graph visualization."""

    def __call__(self):
        """Render the knowledge graph view."""
        # Check permissions
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.redirect(self.context.absolute_url())
            return

        return self.index()

    def get_graph_stats(self):
        """Get graph statistics."""
        storage = GraphStorage(self.context)
        stats = storage.get_statistics()

        # Add additional analysis
        graph = storage.load_graph()
        algorithms = GraphAlgorithms(graph)

        # Calculate density
        node_count = stats["total_nodes"]
        edge_count = stats["total_edges"]
        max_edges = node_count * (node_count - 1) if node_count > 1 else 0
        density = edge_count / max_edges if max_edges > 0 else 0

        stats['density'] = round(density, 4)

        # Get central nodes
        central_nodes = algorithms.find_central_concepts(top_n=5)
        stats['central_nodes'] = []

        for uid, score in central_nodes:
            node = graph.get_node(uid)
            if node:
                stats["central_nodes"].append({
                    "uid": uid,
                    "title": node.title,
                    "score": round(score, 3),
                    "type": node.node_type.value
                    if hasattr(node.node_type, "value")
                    else node.node_type,
                })

        # Find knowledge gaps
        gaps = algorithms.find_knowledge_gaps(min_importance=0.3)
        stats['knowledge_gaps'] = []

        for uid1, uid2, importance in gaps[:5]:
            node1 = graph.get_node(uid1)
            node2 = graph.get_node(uid2)
            if node1 and node2:
                stats["knowledge_gaps"].append({
                    "node1": {"uid": uid1, "title": node1.title},
                    "node2": {"uid": uid2, "title": node2.title},
                    "importance": round(importance, 3),
                })

        # Find clusters
        clusters = algorithms.find_communities()
        cluster_sizes = {}
        for _uid, cluster_id in clusters.items():
            cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1

        stats['clusters'] = {
            'count': len(cluster_sizes),
            'sizes': sorted(cluster_sizes.values(), reverse=True)
        }

        return stats

    def can_edit_graph(self):
        """Check if user can edit the graph."""
        return api.user.has_permission('Modify portal content', obj=self.context)
