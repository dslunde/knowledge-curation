"""Graph storage implementation using Plone's catalog and relationship fields."""

from .model import Edge
from .model import Graph
from .model import Node
from .model import NodeType
from .relationships import RelationshipType
from BTrees.OOBTree import OOBTree
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from BTrees.OOBTree import OOBTree
from zope.annotation.interfaces import IAnnotations
from typing import Any
import json


GRAPH_ANNOTATION_KEY = "knowledge.curator.graph"


class GraphStorage:
    """Storage backend for the knowledge graph using Plone's infrastructure."""

    def __init__(self, context=None):
        """Initialize graph storage.

        Args:
            context: Plone context (defaults to portal)
        """
        self.context = context or api.portal.get()
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure annotation storage exists."""
        annotations = IAnnotations(self.context)
        if GRAPH_ANNOTATION_KEY not in annotations:
            annotations[GRAPH_ANNOTATION_KEY] = OOBTree()
            annotations[GRAPH_ANNOTATION_KEY]['nodes'] = OOBTree()
            annotations[GRAPH_ANNOTATION_KEY]['edges'] = PersistentList()
            annotations[GRAPH_ANNOTATION_KEY]['indexes'] = OOBTree()
            annotations[GRAPH_ANNOTATION_KEY]['metadata'] = PersistentDict()

    def _get_storage(self):
        """Get the annotation storage."""
        annotations = IAnnotations(self.context)
        return annotations[GRAPH_ANNOTATION_KEY]

    def save_graph(self, graph: Graph):
        """Save a graph to persistent storage.

        Args:
            graph: Graph instance to save
        """
        storage = self._get_storage()

        # Clear existing data
        storage['nodes'].clear()
        storage['edges'][:] = []

        # Save nodes
        for uid, node in graph.nodes.items():
            node_data = {
                "uid": node.uid,
                "title": node.title,
                "type": node.node_type.value
                if hasattr(node.node_type, "value")
                else node.node_type,
                "properties": dict(node.properties),
                "created": node.created.isoformat()
                if hasattr(node.created, "isoformat")
                else node.created,
                "modified": node.modified.isoformat()
                if hasattr(node.modified, "isoformat")
                else node.modified,
            }
            storage['nodes'][uid] = PersistentDict(node_data)

        # Save edges
        for edge in graph.edges:
            edge_data = {
                "source": edge.source_uid,
                "target": edge.target_uid,
                "type": edge.relationship_type,
                "weight": edge.weight,
                "properties": dict(edge.properties),
                "created": edge.created.isoformat()
                if hasattr(edge.created, "isoformat")
                else edge.created,
            }
            storage['edges'].append(PersistentDict(edge_data))

        # Update indexes
        self._rebuild_indexes()

        # Update metadata
        storage['metadata']['last_modified'] = api.portal.get_localized_time()
        storage['metadata']['node_count'] = len(graph.nodes)
        storage['metadata']['edge_count'] = len(graph.edges)

    def load_graph(self) -> Graph:
        """Load graph from persistent storage.

        Returns:
            Graph instance
        """
        storage = self._get_storage()
        graph = Graph()

        # Load nodes
        for _uid, node_data in storage["nodes"].items():
            # Convert node type string to NodeType enum if possible
            node_type = node_data["type"]
            for nt in NodeType:
                if nt.value == node_type:
                    node_type = nt
                    break

            node = Node(
                uid=node_data["uid"],
                title=node_data["title"],
                node_type=node_type,
                created=node_data.get("created"),
                modified=node_data.get("modified"),
                **dict(node_data.get("properties", {})),
            )
            graph.add_node(node)

        # Load edges
        for edge_data in storage["edges"]:
            edge = Edge(
                source_uid=edge_data["source"],
                target_uid=edge_data["target"],
                relationship_type=edge_data["type"],
                weight=edge_data.get("weight", 1.0),
                created=edge_data.get("created"),
                **dict(edge_data.get("properties", {})),
            )
            graph.add_edge(edge)

        return graph

    def sync_with_catalog(self):
        """Synchronize graph with Plone catalog content."""
        catalog = api.portal.get_tool("portal_catalog")
        graph = self.load_graph()

        # Get all knowledge content
        brains = catalog(
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"]
        )

        # Track existing nodes
        existing_uids = set()

        for brain in brains:
            uid = brain.UID
            existing_uids.add(uid)

            # Update or create node
            node = graph.get_node(uid)
            if node:
                # Update existing node
                node.title = brain.Title
                node.update_property("url", brain.getURL())
                node.update_property("description", brain.Description)
                node.update_property("review_state", brain.review_state)
                node.update_property("portal_type", brain.portal_type)
            else:
                # Create new node
                node_type_map = {
                    "ResearchNote": NodeType.RESEARCH_NOTE,
                    "LearningGoal": NodeType.LEARNING_GOAL,
                    "ProjectLog": NodeType.PROJECT_LOG,
                    "BookmarkPlus": NodeType.BOOKMARK_PLUS,
                }

                node = Node(
                    uid=uid,
                    title=brain.Title,
                    node_type=node_type_map.get(
                        brain.portal_type, NodeType.RESEARCH_NOTE
                    ),
                    url=brain.getURL(),
                    description=brain.Description,
                    review_state=brain.review_state,
                    portal_type=brain.portal_type,
                    created=brain.created,
                    modified=brain.modified,
                )
                graph.add_node(node)

            # Sync relationships from content
            try:
                obj = brain.getObject()
                self._sync_content_relationships(graph, obj, uid)
            except (AttributeError, Unauthorized):
                # Object might be inaccessible
                pass

        # Remove nodes for deleted content
        nodes_to_remove = []
        for uid in graph.nodes:
            if uid not in existing_uids and not uid.startswith(("concept_", "tag_")):
                nodes_to_remove.append(uid)

        for uid in nodes_to_remove:
            graph.remove_node(uid)

        # Save updated graph
        self.save_graph(graph)

    def _sync_content_relationships(self, graph: Graph, obj, uid: str):
        """Sync relationships from content object to graph.

        Args:
            graph: Graph instance
            obj: Content object
            uid: Object UID
        """
        # Handle standard connections field
        if hasattr(obj, "connections"):
            for target_uid in getattr(obj, "connections", []):
                edge = Edge(uid, target_uid, RelationshipType.RELATED_TO.value)
                graph.add_edge(edge)

        # Handle related_notes field (for LearningGoal)
        if hasattr(obj, "related_notes"):
            for target_uid in getattr(obj, "related_notes", []):
                edge = Edge(uid, target_uid, RelationshipType.RELATED_TO.value)
                graph.add_edge(edge)

        # Handle tags
        if hasattr(obj, "tags"):
            for tag in getattr(obj, "tags", []):
                tag_uid = f"tag_{tag.lower().replace(' ', '_')}"

                # Create tag node if needed
                if not graph.get_node(tag_uid):
                    tag_node = Node(tag_uid, tag, NodeType.TAG)
                    graph.add_node(tag_node)

                # Create tagging relationship
                edge = Edge(uid, tag_uid, RelationshipType.TAGGED_WITH.value)
                graph.add_edge(edge)

        # Handle RelatedItems behavior
        if IRelatedItems.providedBy(obj):
            for rel in getattr(obj, "relatedItems", []):
                if hasattr(rel, "to_object"):
                    target = rel.to_object
                    if target:
                        edge = Edge(uid, api.content.get_uuid(target),
                                  RelationshipType.RELATED_TO.value)
                        graph.add_edge(edge)

    def _rebuild_indexes(self):
        """Rebuild graph indexes for efficient querying."""
        storage = self._get_storage()
        indexes = storage['indexes']

        # Clear existing indexes
        indexes.clear()

        # Node type index
        indexes['by_type'] = OOBTree()
        for uid, node_data in storage['nodes'].items():
            node_type = node_data['type']
            if node_type not in indexes['by_type']:
                indexes['by_type'][node_type] = PersistentList()
            indexes['by_type'][node_type].append(uid)

        # Relationship type index
        indexes['by_relationship'] = OOBTree()
        for edge_data in storage['edges']:
            rel_type = edge_data['type']
            if rel_type not in indexes['by_relationship']:
                indexes['by_relationship'][rel_type] = PersistentList()
            indexes['by_relationship'][rel_type].append(
                (edge_data['source'], edge_data['target'])
            )

        # Tag index
        indexes['by_tag'] = OOBTree()
        for edge_data in storage['edges']:
            if edge_data['type'] == RelationshipType.TAGGED_WITH.value:
                tag_uid = edge_data['target']
                if tag_uid not in indexes['by_tag']:
                    indexes['by_tag'][tag_uid] = PersistentList()
                indexes['by_tag'][tag_uid].append(edge_data['source'])

    def query_nodes(self, node_type: str | None = None,
                   properties: dict[str, Any] | None = None) -> list[Node]:
        """Query nodes by type and properties.

        Args:
            node_type: Optional node type filter
            properties: Optional property filters

        Returns:
            List of matching nodes
        """
        graph = self.load_graph()
        results = []

        # Get candidates by type
        if node_type:
            storage = self._get_storage()
            if (
                "by_type" in storage["indexes"]
                and node_type in storage["indexes"]["by_type"]
            ):
                candidates = storage["indexes"]["by_type"][node_type]
            else:
                candidates = []
        else:
            candidates = graph.nodes.keys()

        # Filter by properties
        for uid in candidates:
            node = graph.get_node(uid)
            if not node:
                continue

            if properties:
                match = True
                for key, value in properties.items():
                    if node.get_property(key) != value:
                        match = False
                        break
                if not match:
                    continue

            results.append(node)

        return results

    def query_relationships(self, relationship_type: str | None = None,
                          source_uid: str | None = None,
                          target_uid: str | None = None) -> list[Edge]:
        """Query relationships by type and endpoints.

        Args:
            relationship_type: Optional relationship type filter
            source_uid: Optional source node filter
            target_uid: Optional target node filter

        Returns:
            List of matching edges
        """
        graph = self.load_graph()
        results = []

        for edge in graph.edges:
            # Apply filters
            if relationship_type and edge.relationship_type != relationship_type:
                continue
            if source_uid and edge.source_uid != source_uid:
                continue
            if target_uid and edge.target_uid != target_uid:
                continue

            results.append(edge)

        return results

    def get_nodes_by_tag(self, tag: str) -> list[Node]:
        """Get all nodes tagged with a specific tag.

        Args:
            tag: Tag name

        Returns:
            List of nodes
        """
        tag_uid = f"tag_{tag.lower().replace(' ', '_')}"
        storage = self._get_storage()
        graph = self.load_graph()

        if 'by_tag' in storage['indexes'] and tag_uid in storage['indexes']['by_tag']:
            node_uids = storage['indexes']['by_tag'][tag_uid]
            return [graph.get_node(uid) for uid in node_uids if graph.get_node(uid)]

        return []

    def export_graph(self, format: str = 'json') -> str:
        """Export graph to various formats.

        Args:
            format: Export format ('json', 'gexf', 'graphml')

        Returns:
            Exported graph data as string
        """
        graph = self.load_graph()

        if format == 'json':
            return json.dumps(graph.to_dict(), indent=2)

        elif format == 'gexf':
            # GEXF format for Gephi
            gexf = ['<?xml version="1.0" encoding="UTF-8"?>']
            gexf.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
            gexf.append('  <graph mode="static" defaultedgetype="directed">')

            # Nodes
            gexf.append("    <nodes>")
            for node in graph.nodes.values():
                gexf.append(f'      <node id="{node.uid}" label="{node.title}" />')
            gexf.append('    </nodes>')

            # Edges
            gexf.append("    <edges>")
            for i, edge in enumerate(graph.edges):
                gexf.append(f'      <edge id="{i}" source="{edge.source_uid}" '
                          f'target="{edge.target_uid}" weight="{edge.weight}" />')
            gexf.append('    </edges>')

            gexf.append('  </graph>')
            gexf.append('</gexf>')

            return '\n'.join(gexf)

        elif format == 'graphml':
            # GraphML format
            graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
            graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
            graphml.append('  <graph id="G" edgedefault="directed">')

            # Nodes
            for node in graph.nodes.values():
                graphml.append(f'    <node id="{node.uid}">')
                graphml.append(f'      <data key="title">{node.title}</data>')
                graphml.append(f'      <data key="type">{node.node_type}</data>')
                graphml.append('    </node>')

            # Edges
            for edge in graph.edges:
                graphml.append(
                    f'    <edge source="{edge.source_uid}" target="{edge.target_uid}">'
                )
                graphml.append(
                    f'      <data key="type">{edge.relationship_type}</data>'
                )
                graphml.append(f'      <data key="weight">{edge.weight}</data>')
                graphml.append('    </edge>')

            graphml.append('  </graph>')
            graphml.append('</graphml>')

            return '\n'.join(graphml)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_graph(self, data: str, format: str = 'json', merge: bool = True):
        """Import graph from various formats.

        Args:
            data: Graph data as string
            format: Import format ('json')
            merge: Whether to merge with existing graph
        """
        if output_format == "json":
            import_data = json.loads(data)

            if merge:
                graph = self.load_graph()
            else:
                graph = Graph()

            # Import nodes
            for node_data in import_data.get("nodes", []):
                node_type = node_data["type"]
                for nt in NodeType:
                    if nt.value == node_type:
                        node_type = nt
                        break

                properties = node_data.get('properties', {})
                properties['created'] = node_data.get('created')
                properties['modified'] = node_data.get('modified')

                node = Node(
                    uid=node_data["uid"],
                    title=node_data["title"],
                    node_type=node_type,
                    **properties,
                )
                graph.add_node(node)

            # Import edges
            for edge_data in import_data.get("edges", []):
                edge = Edge(
                    source_uid=edge_data["source"],
                    target_uid=edge_data["target"],
                    relationship_type=edge_data["type"],
                    weight=edge_data.get("weight", 1.0),
                    **edge_data.get("properties", {}),
                )
                graph.add_edge(edge)

            self.save_graph(graph)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_statistics(self) -> dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        storage = self._get_storage()
        graph = self.load_graph()

        # Count by node type
        node_types = {}
        for node in graph.nodes.values():
            node_type = (
                node.node_type.value
                if hasattr(node.node_type, "value")
                else node.node_type
            )
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # Count by relationship type
        rel_types = {}
        for edge in graph.edges:
            rel_types[edge.relationship_type] = rel_types.get(edge.relationship_type, 0) + 1

        return {
            'total_nodes': len(graph.nodes),
            'total_edges': len(graph.edges),
            'node_types': node_types,
            'relationship_types': rel_types,
            'last_modified': storage['metadata'].get('last_modified'),
            'average_degree': len(graph.edges) * 2 / len(graph.nodes) if graph.nodes else 0
        }
