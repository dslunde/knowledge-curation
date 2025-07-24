"""Graph operations for content relationship management."""

from typing import Any
from datetime import datetime

from .model import Graph, Node, Edge, NodeType
from .relationships import RelationshipType, RelationshipMetadata, RelationshipManager


class GraphOperations:
    """Operations for manipulating the knowledge graph."""

    def __init__(self, graph: Graph):
        """Initialize graph operations.

        Args:
            graph: Graph instance to operate on
        """
        self.graph = graph
        self.relationship_manager = RelationshipManager()
        self.operation_history: list[dict[str, Any]] = []

    def add_content_node(
        self, uid: str, title: str, content_type: str, **properties
    ) -> bool:
        """Add a content node to the graph.

        Args:
            uid: Unique identifier
            title: Node title
            content_type: Type of content (ResearchNote, LearningGoal, etc.)
            **properties: Additional properties

        Returns:
            True if node was added successfully
        """
        # Map content type to NodeType
        type_mapping = {
            "ResearchNote": NodeType.RESEARCH_NOTE,
            "LearningGoal": NodeType.LEARNING_GOAL,
            "ProjectLog": NodeType.PROJECT_LOG,
            "BookmarkPlus": NodeType.BOOKMARK_PLUS,
        }

        node_type = type_mapping.get(content_type, NodeType.RESEARCH_NOTE)
        node = Node(uid, title, node_type, **properties)

        success = self.graph.add_node(node)
        if success:
            self._log_operation("add_node", {"node": node.to_dict()})

        return success

    def add_concept_node(self, concept_name: str, **properties) -> str:
        """Add a concept node to the graph.

        Args:
            concept_name: Name of the concept
            **properties: Additional properties

        Returns:
            UID of the created concept node
        """
        # Generate UID for concept
        uid = f"concept_{concept_name.lower().replace(' ', '_')}"

        node = Node(uid, concept_name, NodeType.CONCEPT, **properties)
        self.graph.add_node(node)
        self._log_operation("add_concept", {"node": node.to_dict()})

        return uid

    def add_tag_node(self, tag_name: str) -> str:
        """Add a tag node to the graph.

        Args:
            tag_name: Name of the tag

        Returns:
            UID of the created tag node
        """
        # Generate UID for tag
        uid = f"tag_{tag_name.lower().replace(' ', '_')}"

        node = Node(uid, tag_name, NodeType.TAG)
        self.graph.add_node(node)
        self._log_operation("add_tag", {"node": node.to_dict()})

        return uid

    def create_relationship(
        self,
        source_uid: str,
        target_uid: str,
        relationship_type: RelationshipType,
        weight: float = 1.0,
        **properties,
    ) -> bool:
        """Create a relationship between two nodes.

        Args:
            source_uid: Source node UID
            target_uid: Target node UID
            relationship_type: Type of relationship
            weight: Relationship weight/strength
            **properties: Additional properties

        Returns:
            True if relationship was created successfully
        """
        # Validate nodes exist
        source = self.graph.get_node(source_uid)
        target = self.graph.get_node(target_uid)

        if not source or not target:
            return False

        # Validate relationship is allowed
        source_type = (
            source.node_type.value
            if isinstance(source.node_type, NodeType)
            else source.node_type
        )
        target_type = (
            target.node_type.value
            if isinstance(target.node_type, NodeType)
            else target.node_type
        )

        if not self.relationship_manager.validate_relationship(
            source_type, target_type, relationship_type.value
        ):
            return False

        # Create edge
        edge = Edge(
            source_uid, target_uid, relationship_type.value, weight, **properties
        )
        success = self.graph.add_edge(edge)

        if success:
            self._log_operation("create_relationship", {"edge": edge.to_dict()})

            # Handle bidirectional relationships
            if RelationshipMetadata.is_bidirectional(relationship_type):
                reverse_edge = Edge(
                    target_uid,
                    source_uid,
                    relationship_type.value,
                    weight,
                    **properties,
                )
                self.graph.add_edge(reverse_edge)

        return success

    def remove_relationship(
        self, source_uid: str, target_uid: str, relationship_type: RelationshipType
    ) -> bool:
        """Remove a relationship between two nodes.

        Args:
            source_uid: Source node UID
            target_uid: Target node UID
            relationship_type: Type of relationship

        Returns:
            True if relationship was removed successfully
        """
        success = self.graph.remove_edge(
            source_uid, target_uid, relationship_type.value
        )

        if success:
            self._log_operation(
                "remove_relationship",
                {
                    "source": source_uid,
                    "target": target_uid,
                    "type": relationship_type.value,
                },
            )

            # Handle bidirectional relationships
            if RelationshipMetadata.is_bidirectional(relationship_type):
                self.graph.remove_edge(target_uid, source_uid, relationship_type.value)

        return success

    def update_node_properties(self, uid: str, properties: dict[str, Any]) -> bool:
        """Update properties of a node.

        Args:
            uid: Node UID
            properties: Properties to update

        Returns:
            True if node was updated successfully
        """
        node = self.graph.get_node(uid)
        if not node:
            return False

        old_properties = node.properties.copy()

        for key, value in properties.items():
            node.update_property(key, value)

        self._log_operation(
            "update_node",
            {
                "uid": uid,
                "old_properties": old_properties,
                "new_properties": node.properties,
            },
        )

        return True

    def merge_nodes(self, primary_uid: str, secondary_uid: str) -> bool:
        """Merge two nodes, keeping the primary and redirecting all relationships.

        Args:
            primary_uid: UID of node to keep
            secondary_uid: UID of node to merge into primary

        Returns:
            True if merge was successful
        """
        primary = self.graph.get_node(primary_uid)
        secondary = self.graph.get_node(secondary_uid)

        if not primary or not secondary:
            return False

        # Get all edges from/to secondary node
        outgoing_edges = self.graph.get_edges_from_node(secondary_uid)
        incoming_edges = self.graph.get_edges_to_node(secondary_uid)

        # Redirect outgoing edges
        for edge in outgoing_edges:
            if edge.target_uid != primary_uid:  # Avoid self-loops
                new_edge = Edge(
                    primary_uid,
                    edge.target_uid,
                    edge.relationship_type,
                    edge.weight,
                    **edge.properties,
                )
                self.graph.add_edge(new_edge)

        # Redirect incoming edges
        for edge in incoming_edges:
            if edge.source_uid != primary_uid:  # Avoid self-loops
                new_edge = Edge(
                    edge.source_uid,
                    primary_uid,
                    edge.relationship_type,
                    edge.weight,
                    **edge.properties,
                )
                self.graph.add_edge(new_edge)

        # Merge properties
        secondary_props = secondary.properties.copy()
        secondary_props.update(primary.properties)  # Primary properties take precedence
        primary.properties = secondary_props

        # Remove secondary node
        self.graph.remove_node(secondary_uid)

        self._log_operation(
            "merge_nodes",
            {
                "primary": primary_uid,
                "secondary": secondary_uid,
                "redirected_edges": len(outgoing_edges) + len(incoming_edges),
            },
        )

        return True

    def clone_subgraph(
        self,
        root_uid: str,
        max_depth: int = 2,
        relationship_types: list[RelationshipType] | None = None,
    ) -> Graph:
        """Clone a subgraph starting from a root node.

        Args:
            root_uid: UID of root node
            max_depth: Maximum depth to traverse
            relationship_types: Optional filter for relationship types

        Returns:
            New graph containing the cloned subgraph
        """
        if root_uid not in self.graph.nodes:
            return Graph()

        # Collect nodes to include
        nodes_to_include = set()
        nodes_to_process = [(root_uid, 0)]

        while nodes_to_process:
            current_uid, depth = nodes_to_process.pop(0)

            if current_uid in nodes_to_include or depth > max_depth:
                continue

            nodes_to_include.add(current_uid)

            if depth < max_depth:
                # Get neighbors
                neighbors = self.graph.get_neighbors(current_uid)
                for neighbor_uid in neighbors:
                    if neighbor_uid not in nodes_to_include:
                        # Check if connected by allowed relationship type
                        if relationship_types:
                            edges = self.graph.get_edges_from_node(current_uid)
                            for edge in edges:
                                if edge.target_uid == neighbor_uid and any(
                                    edge.relationship_type == rt.value
                                    for rt in relationship_types
                                ):
                                    nodes_to_process.append((neighbor_uid, depth + 1))
                                    break
                        else:
                            nodes_to_process.append((neighbor_uid, depth + 1))

        # Create subgraph
        return self.graph.get_subgraph(list(nodes_to_include))

    def batch_add_relationships(
        self, relationships: list[tuple[str, str, RelationshipType, float]]
    ) -> int:
        """Add multiple relationships in batch.

        Args:
            relationships: List of (source_uid, target_uid, relationship_type,
                                   weight) tuples

        Returns:
            Number of relationships successfully added
        """
        added = 0

        for source_uid, target_uid, rel_type, weight in relationships:
            if self.create_relationship(source_uid, target_uid, rel_type, weight):
                added += 1

        self._log_operation(
            "batch_add_relationships", {"attempted": len(relationships), "added": added}
        )

        return added

    def find_orphan_nodes(self) -> list[str]:
        """Find nodes with no relationships.

        Returns:
            List of orphan node UIDs
        """
        orphans = []

        for uid in self.graph.nodes:
            outgoing = self.graph.get_edges_from_node(uid)
            incoming = self.graph.get_edges_to_node(uid)

            if not outgoing and not incoming:
                orphans.append(uid)

        return orphans

    def prune_orphan_nodes(self) -> int:
        """Remove all orphan nodes from the graph.

        Returns:
            Number of nodes removed
        """
        orphans = self.find_orphan_nodes()

        for uid in orphans:
            self.graph.remove_node(uid)

        self._log_operation("prune_orphans", {"removed": len(orphans)})

        return len(orphans)

    def _find_connection_candidates(self, uid, existing_targets):
        """Find connection candidates based on shared connections."""
        connection_counts = {}
        for neighbor_uid in self.graph.get_neighbors(uid):
            for second_neighbor_uid in self.graph.get_neighbors(neighbor_uid):
                if second_neighbor_uid != uid and second_neighbor_uid not in existing_targets:
                    connection_counts[second_neighbor_uid] = connection_counts.get(second_neighbor_uid, 0) + 1
        return connection_counts

    def _score_and_suggest(self, node_type, candidates):
        """Score candidates and generate suggestions."""
        suggestions = []
        for candidate_uid, shared_connections in candidates.items():
            candidate = self.graph.get_node(candidate_uid)
            if not candidate:
                continue

            candidate_type = candidate.node_type.value if isinstance(candidate.node_type, NodeType) else candidate.node_type
            rel_suggestions = self.relationship_manager.suggest_relationship_type(node_type, candidate_type)

            if rel_suggestions:
                rel_type_str, rel_confidence = rel_suggestions[0]
                confidence = min(0.9, (shared_connections / 10.0) * rel_confidence)
                
                try:
                    rel_type = RelationshipType(rel_type_str)
                    suggestions.append((candidate_uid, rel_type, confidence))
                except ValueError:
                    continue
        return suggestions

    def suggest_connections(
        self, uid: str, limit: int = 10
    ) -> list[tuple[str, RelationshipType, float]]:
        """Suggest potential connections for a node."""
        node = self.graph.get_node(uid)
        if not node:
            return []

        node_type = node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type
        existing_targets = {edge.target_uid for edge in self.graph.get_edges_from_node(uid)}
        
        candidates = self._find_connection_candidates(uid, existing_targets)
        suggestions = self._score_and_suggest(node_type, candidates)
        
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions[:limit]

    def _log_operation(self, operation_type: str, details: dict[str, Any]):
        """Log a graph operation.

        Args:
            operation_type: Type of operation
            details: Operation details
        """
        self.operation_history.append({
            "type": operation_type,
            "timestamp": datetime.now(),
            "details": details,
        })

        # Keep only last 1000 operations
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-1000:]

    def get_operation_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent operation history.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of operation records
        """
        return self.operation_history[-limit:]
