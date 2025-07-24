"""Core graph data model for knowledge graph."""

from datetime import datetime
from typing import Any
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""

    RESEARCH_NOTE = "ResearchNote"
    LEARNING_GOAL = "LearningGoal"
    PROJECT_LOG = "ProjectLog"
    BOOKMARK_PLUS = "BookmarkPlus"
    CONCEPT = "Concept"
    TAG = "Tag"
    PERSON = "Person"
    ORGANIZATION = "Organization"


class Node:
    """Represents a node in the knowledge graph."""

    def __init__(self, uid: str, title: str, node_type: NodeType, **kwargs):
        """Initialize a node.

        Args:
            uid: Unique identifier for the node
            title: Display title for the node
            node_type: Type of the node
            **kwargs: Additional properties
        """
        self.uid = uid
        self.title = title
        self.node_type = node_type
        self.properties = kwargs
        self.created = kwargs.get("created", datetime.now())
        self.modified = kwargs.get("modified", datetime.now())

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "uid": self.uid,
            "title": self.title,
            "type": self.node_type.value
            if isinstance(self.node_type, NodeType)
            else self.node_type,
            "created": self.created.isoformat()
            if isinstance(self.created, datetime)
            else self.created,
            "modified": self.modified.isoformat()
            if isinstance(self.modified, datetime)
            else self.modified,
            "properties": self.properties,
        }

    def update_property(self, key: str, value: Any):
        """Update a property of the node."""
        self.properties[key] = value
        self.modified = datetime.now()

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value."""
        return self.properties.get(key, default)

    def __repr__(self):
        return f"Node(uid='{self.uid}', title='{self.title}', type={self.node_type})"

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.uid == other.uid

    def __hash__(self):
        return hash(self.uid)


class Edge:
    """Represents an edge (relationship) in the knowledge graph."""

    def __init__(
        self,
        source_uid: str,
        target_uid: str,
        relationship_type: str,
        weight: float = 1.0,
        **kwargs,
    ):
        """Initialize an edge.

        Args:
            source_uid: UID of the source node
            target_uid: UID of the target node
            relationship_type: Type of relationship
            weight: Weight/strength of the relationship
            **kwargs: Additional properties
        """
        self.source_uid = source_uid
        self.target_uid = target_uid
        self.relationship_type = relationship_type
        self.weight = weight
        self.properties = kwargs
        self.created = kwargs.get("created", datetime.now())

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "source": self.source_uid,
            "target": self.target_uid,
            "type": self.relationship_type,
            "weight": self.weight,
            "created": self.created.isoformat()
            if isinstance(self.created, datetime)
            else self.created,
            "properties": self.properties,
        }

    def __repr__(self):
        return (
            f"Edge({self.source_uid} --[{self.relationship_type}]--> {self.target_uid})"
        )

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return (
            self.source_uid == other.source_uid
            and self.target_uid == other.target_uid
            and self.relationship_type == other.relationship_type
        )

    def __hash__(self):
        return hash((self.source_uid, self.target_uid, self.relationship_type))


class Graph:
    """Represents the knowledge graph."""

    def __init__(self):
        """Initialize an empty graph."""
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.adjacency_list: dict[str, set[str]] = {}
        self.reverse_adjacency_list: dict[str, set[str]] = {}
        self.edge_index: dict[tuple, Edge] = {}

    def add_node(self, node: Node) -> bool:
        """Add a node to the graph.

        Args:
            node: Node to add

        Returns:
            True if node was added, False if already exists
        """
        if node.uid in self.nodes:
            return False

        self.nodes[node.uid] = node
        self.adjacency_list[node.uid] = set()
        self.reverse_adjacency_list[node.uid] = set()
        return True

    def add_edge(self, edge: Edge) -> bool:
        """Add an edge to the graph.

        Args:
            edge: Edge to add

        Returns:
            True if edge was added, False if already exists or nodes don't exist
        """
        # Check if nodes exist
        if edge.source_uid not in self.nodes or edge.target_uid not in self.nodes:
            return False

        # Check if edge already exists
        edge_key = (edge.source_uid, edge.target_uid, edge.relationship_type)
        if edge_key in self.edge_index:
            return False

        # Add edge
        self.edges.append(edge)
        self.edge_index[edge_key] = edge

        # Update adjacency lists
        self.adjacency_list[edge.source_uid].add(edge.target_uid)
        self.reverse_adjacency_list[edge.target_uid].add(edge.source_uid)

        return True

    def remove_node(self, uid: str) -> bool:
        """Remove a node from the graph.

        Args:
            uid: UID of node to remove

        Returns:
            True if node was removed, False if not found
        """
        if uid not in self.nodes:
            return False

        # Remove all edges connected to this node
        edges_to_remove = []
        for edge in self.edges:
            if edge.source_uid == uid or edge.target_uid == uid:
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            self.remove_edge(edge.source_uid, edge.target_uid, edge.relationship_type)

        # Remove node
        del self.nodes[uid]
        del self.adjacency_list[uid]
        del self.reverse_adjacency_list[uid]

        return True

    def remove_edge(
        self, source_uid: str, target_uid: str, relationship_type: str
    ) -> bool:
        """Remove an edge from the graph.

        Args:
            source_uid: Source node UID
            target_uid: Target node UID
            relationship_type: Type of relationship

        Returns:
            True if edge was removed, False if not found
        """
        edge_key = (source_uid, target_uid, relationship_type)
        if edge_key not in self.edge_index:
            return False

        # Remove edge
        edge = self.edge_index[edge_key]
        self.edges.remove(edge)
        del self.edge_index[edge_key]

        # Update adjacency lists if no other edges exist between nodes
        has_other_edges = any(
            e
            for e in self.edges
            if e.source_uid == source_uid and e.target_uid == target_uid
        )
        if not has_other_edges:
            self.adjacency_list[source_uid].discard(target_uid)
            self.reverse_adjacency_list[target_uid].discard(source_uid)

        return True

    def get_node(self, uid: str) -> Node | None:
        """Get a node by its UID."""
        return self.nodes.get(uid)

    def get_edge(
        self, source_uid: str, target_uid: str, relationship_type: str
    ) -> Edge | None:
        """Get an edge by its endpoints and type."""
        return self.edge_index.get((source_uid, target_uid, relationship_type))

    def get_neighbors(
        self, uid: str, relationship_type: str | None = None
    ) -> list[str]:
        """Get neighboring nodes.

        Args:
            uid: Node UID
            relationship_type: Optional filter by relationship type

        Returns:
            List of neighbor UIDs
        """
        if uid not in self.nodes:
            return []

        if relationship_type is None:
            return list(self.adjacency_list.get(uid, set()))

        # Filter by relationship type
        neighbors = []
        for edge in self.edges:
            if edge.source_uid == uid and edge.relationship_type == relationship_type:
                neighbors.append(edge.target_uid)

        return neighbors

    def get_incoming_neighbors(
        self, uid: str, relationship_type: str | None = None
    ) -> list[str]:
        """Get nodes that point to this node.

        Args:
            uid: Node UID
            relationship_type: Optional filter by relationship type

        Returns:
            List of neighbor UIDs
        """
        if uid not in self.nodes:
            return []

        if relationship_type is None:
            return list(self.reverse_adjacency_list.get(uid, set()))

        # Filter by relationship type
        neighbors = []
        for edge in self.edges:
            if edge.target_uid == uid and (
                relationship_type is None or edge.relationship_type == relationship_type
            ):
                neighbors.append(edge.source_uid)

        return neighbors

    def get_edges_from_node(
        self, uid: str, relationship_type: str | None = None
    ) -> list[Edge]:
        """Get all edges originating from a node.

        Args:
            uid: Node UID
            relationship_type: Optional filter by relationship type

        Returns:
            List of edges
        """
        edges = []
        for edge in self.edges:
            if edge.source_uid == uid and (
                relationship_type is None or edge.relationship_type == relationship_type
            ):
                edges.append(edge)
        return edges

    def get_edges_to_node(
        self, uid: str, relationship_type: str | None = None
    ) -> list[Edge]:
        """Get all edges pointing to a node.

        Args:
            uid: Node UID
            relationship_type: Optional filter by relationship type

        Returns:
            List of edges
        """
        edges = []
        for edge in self.edges:
            if edge.target_uid == uid and (
                relationship_type is None or edge.relationship_type == relationship_type
            ):
                edges.append(edge)
        return edges

    def get_subgraph(self, node_uids: list[str]) -> "Graph":
        """Get a subgraph containing only specified nodes.

        Args:
            node_uids: List of node UIDs to include

        Returns:
            New graph containing only specified nodes and edges between them
        """
        subgraph = Graph()

        # Add nodes
        for uid in node_uids:
            if uid in self.nodes:
                subgraph.add_node(self.nodes[uid])

        # Add edges between included nodes
        for edge in self.edges:
            if edge.source_uid in node_uids and edge.target_uid in node_uids:
                subgraph.add_edge(edge)

        return subgraph

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "node_types": self._count_node_types(),
                "relationship_types": self._count_relationship_types(),
            },
        }

    def _count_node_types(self) -> dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in self.nodes.values():
            node_type = (
                node.node_type.value
                if isinstance(node.node_type, NodeType)
                else node.node_type
            )
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def _count_relationship_types(self) -> dict[str, int]:
        """Count edges by relationship type."""
        counts = {}
        for edge in self.edges:
            counts[edge.relationship_type] = counts.get(edge.relationship_type, 0) + 1
        return counts

    def __repr__(self):
        return f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)})"
