"""Graph traversal utilities for navigation and exploration."""

from typing import Any
from collections.abc import Callable
from collections import deque
from .model import Graph, Node
from .relationships import RelationshipType
from collections import deque
from collections.abc import Callable
from typing import Any


class GraphTraversal:
    """Utilities for traversing and navigating the knowledge graph."""

    def __init__(self, graph: Graph):
        """Initialize graph traversal.

        Args:
            graph: Graph instance to traverse
        """
        self.graph = graph

    def breadth_first_search(self, start_uid: str,
                           visit_func: Callable[[Node, int], bool] | None = None,
                           max_depth: int | None = None,
                           relationship_types: list[str] | None = None) -> list[tuple[Node, int]]:
        """Perform breadth-first search from a starting node.

        Args:
            start_uid: Starting node UID
            visit_func: Optional function called for each node (node, depth) -> continue
            max_depth: Maximum depth to traverse
            relationship_types: Optional filter for relationship types

        Returns:
            List of (node, depth) tuples in BFS order
        """
        if start_uid not in self.graph.nodes:
            return []

        visited = set()
        queue = deque([(start_uid, 0)])
        result = []

        while queue:
            current_uid, depth = queue.popleft()

            if current_uid in visited:
                continue

            if max_depth is not None and depth > max_depth:
                continue

            visited.add(current_uid)
            node = self.graph.get_node(current_uid)
            result.append((node, depth))

            # Call visit function if provided
            if visit_func and not visit_func(node, depth):
                continue

            # Add neighbors to queue
            edges = self.graph.get_edges_from_node(current_uid)
            for edge in edges:
                if (
                    relationship_types
                    and edge.relationship_type not in relationship_types
                ):
                    continue
                if edge.target_uid not in visited:
                    queue.append((edge.target_uid, depth + 1))

        return result

    def depth_first_search(self, start_uid: str,
                         visit_func: Callable[[Node, int], bool] | None = None,
                         max_depth: int | None = None,
                         relationship_types: list[str] | None = None) -> list[tuple[Node, int]]:
        """Perform depth-first search from a starting node.

        Args:
            start_uid: Starting node UID
            visit_func: Optional function called for each node (node, depth) -> continue
            max_depth: Maximum depth to traverse
            relationship_types: Optional filter for relationship types

        Returns:
            List of (node, depth) tuples in DFS order
        """
        if start_uid not in self.graph.nodes:
            return []

        visited = set()
        result = []

        def dfs(uid: str, depth: int):
            if uid in visited:
                return

            if max_depth is not None and depth > max_depth:
                return

            visited.add(uid)
            node = self.graph.get_node(uid)
            result.append((node, depth))

            # Call visit function if provided
            if visit_func and not visit_func(node, depth):
                return

            # Visit neighbors
            edges = self.graph.get_edges_from_node(uid)
            for edge in edges:
                if (
                    relationship_types
                    and edge.relationship_type not in relationship_types
                ):
                    continue
                dfs(edge.target_uid, depth + 1)

        dfs(start_uid, 0)
        return result

    def find_connected_component(self, start_uid: str) -> set[str]:
        """Find all nodes in the connected component containing the start node.

        Args:
            start_uid: Starting node UID

        Returns:
            Set of node UIDs in the connected component
        """
        if start_uid not in self.graph.nodes:
            return set()

        component = set()
        queue = deque([start_uid])

        while queue:
            current_uid = queue.popleft()

            if current_uid in component:
                continue

            component.add(current_uid)

            # Add all neighbors (both directions)
            for neighbor_uid in self.graph.get_neighbors(current_uid):
                if neighbor_uid not in component:
                    queue.append(neighbor_uid)

            for neighbor_uid in self.graph.get_incoming_neighbors(current_uid):
                if neighbor_uid not in component:
                    queue.append(neighbor_uid)

        return component

    def get_neighborhood(self, center_uid: str, radius: int = 1,
                        include_incoming: bool = True) -> dict[str, int]:
        """Get all nodes within a certain distance from center node.

        Args:
            center_uid: Center node UID
            radius: Maximum distance from center
            include_incoming: Whether to include incoming edges

        Returns:
            Dictionary mapping node UID to distance from center
        """
        if center_uid not in self.graph.nodes:
            return {}

        distances = {center_uid: 0}
        queue = deque([(center_uid, 0)])

        while queue:
            current_uid, dist = queue.popleft()

            if dist >= radius:
                continue

            # Outgoing neighbors
            for neighbor_uid in self.graph.get_neighbors(current_uid):
                if neighbor_uid not in distances or distances[neighbor_uid] > dist + 1:
                    distances[neighbor_uid] = dist + 1
                    queue.append((neighbor_uid, dist + 1))

            # Incoming neighbors
            if include_incoming:
                for neighbor_uid in self.graph.get_incoming_neighbors(current_uid):
                    if (
                        neighbor_uid not in distances
                        or distances[neighbor_uid] > dist + 1
                    ):
                        distances[neighbor_uid] = dist + 1
                        queue.append((neighbor_uid, dist + 1))

        return distances

    def find_all_paths(self, start_uid: str, end_uid: str,
                      max_length: int = 5,
                      relationship_types: list[str] | None = None) -> list[list[str]]:
        """Find all paths between two nodes.

        Args:
            start_uid: Starting node UID
            end_uid: Ending node UID
            max_length: Maximum path length
            relationship_types: Optional filter for relationship types

        Returns:
            List of paths (each path is a list of node UIDs)
        """
        if start_uid not in self.graph.nodes or end_uid not in self.graph.nodes:
            return []

        paths = []

        def dfs_paths(current: str, target: str, path: list[str], visited: set[str]):
            if len(path) > max_length:
                return

            if current == target:
                paths.append(path.copy())
                return

            visited.add(current)

            edges = self.graph.get_edges_from_node(current)
            for edge in edges:
                if (
                    relationship_types
                    and edge.relationship_type not in relationship_types
                ):
                    continue

                if edge.target_uid not in visited:
                    path.append(edge.target_uid)
                    dfs_paths(edge.target_uid, target, path, visited.copy())
                    path.pop()

        dfs_paths(start_uid, end_uid, [start_uid], set())

        return paths

    def get_learning_path(self, start_uid: str, goal_uid: str) -> list[str] | None:
        """Find optimal learning path from start to goal using prerequisite relationships.

        Args:
            start_uid: Starting knowledge node
            goal_uid: Goal knowledge node

        Returns:
            Ordered list of node UIDs representing learning path
        """
        # Use prerequisite relationships to find path
        paths = self.find_all_paths(
            start_uid,
            goal_uid,
            relationship_types=[
                RelationshipType.PREREQUISITE_OF.value,
                RelationshipType.BUILDS_ON.value,
            ],
        )

        if not paths:
            return None

        # Choose shortest path with highest aggregate weight
        best_path = None
        best_score = -1

        for path in paths:
            # Calculate path score based on edge weights
            score = 0
            for i in range(len(path) - 1):
                edge = self.graph.get_edge(
                    path[i], path[i+1],
                    RelationshipType.PREREQUISITE_OF.value
                )
                if not edge:
                    edge = self.graph.get_edge(
                        path[i], path[i + 1], RelationshipType.BUILDS_ON.value
                    )
                if edge:
                    score += edge.weight

            # Prefer shorter paths with higher weights
            score = score / len(path)

            if score > best_score:
                best_score = score
                best_path = path

        return best_path

    def explore_topic(self, topic_uid: str, max_nodes: int = 20) -> list[tuple[Node, float]]:
        """Explore nodes related to a topic, ranked by relevance.

        Args:
            topic_uid: Topic node UID
            max_nodes: Maximum number of nodes to return

        Returns:
            List of (node, relevance_score) tuples
        """
        if topic_uid not in self.graph.nodes:
            return []

        # Calculate relevance scores using distance and connection strength
        scores = {}

        # BFS with edge weights
        queue = deque([(topic_uid, 1.0, 0)])
        visited = set()

        while queue and len(scores) < max_nodes * 2:
            current_uid, score, depth = queue.popleft()

            if current_uid in visited or depth > 3:
                continue

            visited.add(current_uid)

            if current_uid != topic_uid:
                # Decay score by depth
                final_score = score * (0.7**depth)
                if current_uid in scores:
                    scores[current_uid] = max(scores[current_uid], final_score)
                else:
                    scores[current_uid] = final_score

            # Explore neighbors
            edges = self.graph.get_edges_from_node(current_uid)
            for edge in edges:
                if edge.target_uid not in visited:
                    queue.append((edge.target_uid, score * edge.weight, depth + 1))

        # Get top nodes by score
        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        result = []
        for uid, score in sorted_nodes[:max_nodes]:
            node = self.graph.get_node(uid)
            if node:
                result.append((node, score))

        return result

    def get_breadcrumb_path(self, target_uid: str, root_uid: str | None = None) -> list[str]:
        """Get breadcrumb navigation path from root to target.

        Args:
            target_uid: Target node UID
            root_uid: Optional root node UID (finds most relevant root if not provided)

        Returns:
            List of node UIDs representing breadcrumb path
        """
        if target_uid not in self.graph.nodes:
            return []

        if root_uid and root_uid not in self.graph.nodes:
            return []

        # If no root specified, find the most connected ancestor
        if not root_uid:
            # Look for nodes with no incoming edges or high centrality
            ancestors = []

            # BFS backwards to find potential roots
            queue = deque([target_uid])
            visited = set()

            while queue:
                current_uid = queue.popleft()
                if current_uid in visited:
                    continue

                visited.add(current_uid)
                incoming = self.graph.get_incoming_neighbors(current_uid)

                if not incoming:
                    ancestors.append(current_uid)
                else:
                    for ancestor_uid in incoming:
                        if ancestor_uid not in visited:
                            queue.append(ancestor_uid)

            # Choose ancestor with most connections
            if ancestors:
                root_uid = max(
                    ancestors, key=lambda uid: len(self.graph.get_neighbors(uid))
                )
            else:
                return [target_uid]

        # Find shortest path from root to target
        from ..algorithms import GraphAlgorithms

        algo = GraphAlgorithms(self.graph)
        path = algo.shortest_path(root_uid, target_uid)

        return path if path else [target_uid]

    def suggest_next_nodes(self, current_uid: str,
                          visited_uids: set[str],
                          limit: int = 5) -> list[tuple[Node, str, float]]:
        """Suggest next nodes to explore based on current position and history.

        Args:
            current_uid: Current node UID
            visited_uids: Set of already visited node UIDs
            limit: Maximum number of suggestions

        Returns:
            List of (node, reason, score) tuples
        """
        if current_uid not in self.graph.nodes:
            return []

        suggestions = []

        # Get direct neighbors not yet visited
        edges = self.graph.get_edges_from_node(current_uid)

        for edge in edges:
            if edge.target_uid not in visited_uids:
                node = self.graph.get_node(edge.target_uid)
                if node:
                    # Score based on edge weight and relationship type
                    score = edge.weight

                    # Boost score for certain relationship types
                    if edge.relationship_type == RelationshipType.BUILDS_ON.value:
                        score *= 1.5
                        reason = "Builds on current knowledge"
                    elif (
                        edge.relationship_type == RelationshipType.PREREQUISITE_OF.value
                    ):
                        score *= 1.3
                        reason = "Important prerequisite"
                    elif edge.relationship_type == RelationshipType.RELATED_TO.value:
                        score *= 1.0
                        reason = "Related topic"
                    else:
                        reason = f"Connected via {edge.relationship_type}"

                    suggestions.append((node, reason, score))

        # Sort by score and limit
        suggestions.sort(key=lambda x: x[2], reverse=True)

        return suggestions[:limit]

    def find_knowledge_clusters(self, min_size: int = 3) -> list[dict[str, Any]]:
        """Find clusters of closely related knowledge.

        Args:
            min_size: Minimum cluster size

        Returns:
            List of cluster information dictionaries
        """
        clusters = []
        processed = set()

        for uid in self.graph.nodes:
            if uid in processed:
                continue

            # Find connected component
            component = self.find_connected_component(uid)

            if len(component) >= min_size:
                # Calculate cluster properties
                cluster_edges = []
                internal_edges = 0

                for edge in self.graph.edges:
                    if edge.source_uid in component and edge.target_uid in component:
                        cluster_edges.append(edge)
                        internal_edges += 1

                # Calculate density
                max_edges = len(component) * (len(component) - 1)
                density = internal_edges / max_edges if max_edges > 0 else 0

                # Find central node
                degree_counts = {}
                for node_uid in component:
                    degree = (len(self.graph.get_neighbors(node_uid)) +
                             len(self.graph.get_incoming_neighbors(node_uid)))
                    degree_counts[node_uid] = degree

                central_uid = max(degree_counts.items(), key=lambda x: x[1])[0]
                central_node = self.graph.get_node(central_uid)

                # Determine cluster topic/theme
                # Could be enhanced with NLP analysis of node titles

                clusters.append({
                    "nodes": list(component),
                    "size": len(component),
                    "density": density,
                    "central_node": central_node.to_dict() if central_node else None,
                    "edge_count": internal_edges,
                })

                processed.update(component)

        # Sort by size
        clusters.sort(key=lambda x: x['size'], reverse=True)

        return clusters
