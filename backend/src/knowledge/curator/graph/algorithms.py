"""Graph algorithms for analysis and traversal."""

from typing import Any
from collections import deque
import heapq
from .model import Graph
from .relationships import RelationshipType


class GraphAlgorithms:
    """Algorithms for analyzing the knowledge graph."""

    def __init__(self, graph: Graph):
        """Initialize graph algorithms.
        
        Args:
            graph: Graph instance to analyze
        """
        self.graph = graph

    def shortest_path(self, start_uid: str, end_uid: str,
                     relationship_types: list[str] | None = None) -> list[str] | None:
        """Find shortest path between two nodes using Dijkstra's algorithm.
        
        Args:
            start_uid: Starting node UID
            end_uid: Ending node UID
            relationship_types: Optional filter for relationship types
            
        Returns:
            List of node UIDs representing the path, or None if no path exists
        """
        if start_uid not in self.graph.nodes or end_uid not in self.graph.nodes:
            return None

        if start_uid == end_uid:
            return [start_uid]

        # Dijkstra's algorithm
        distances = {uid: float('inf') for uid in self.graph.nodes}
        distances[start_uid] = 0
        previous = {}
        pq = [(0, start_uid)]
        visited = set()

        while pq:
            current_dist, current_uid = heapq.heappop(pq)

            if current_uid in visited:
                continue

            visited.add(current_uid)

            if current_uid == end_uid:
                # Reconstruct path
                path = []
                while current_uid in previous:
                    path.append(current_uid)
                    current_uid = previous[current_uid]
                path.append(start_uid)
                return list(reversed(path))

            # Check neighbors
            edges = self.graph.get_edges_from_node(current_uid)
            for edge in edges:
                if relationship_types and edge.relationship_type not in relationship_types:
                    continue

                neighbor_uid = edge.target_uid
                if neighbor_uid not in visited:
                    # Use inverse of weight as distance (higher weight = shorter distance)
                    distance = current_dist + (1.0 / edge.weight if edge.weight > 0 else float('inf'))

                    if distance < distances[neighbor_uid]:
                        distances[neighbor_uid] = distance
                        previous[neighbor_uid] = current_uid
                        heapq.heappush(pq, (distance, neighbor_uid))

        return None

    def all_paths(self, start_uid: str, end_uid: str, max_length: int = 5) -> list[list[str]]:
        """Find all paths between two nodes up to a maximum length.
        
        Args:
            start_uid: Starting node UID
            end_uid: Ending node UID
            max_length: Maximum path length
            
        Returns:
            List of paths (each path is a list of node UIDs)
        """
        if start_uid not in self.graph.nodes or end_uid not in self.graph.nodes:
            return []

        if start_uid == end_uid:
            return [[start_uid]]

        paths = []

        def dfs(current_uid: str, target_uid: str, path: list[str], visited: set[str]):
            if len(path) > max_length:
                return

            if current_uid == target_uid:
                paths.append(path.copy())
                return

            visited.add(current_uid)

            for neighbor_uid in self.graph.get_neighbors(current_uid):
                if neighbor_uid not in visited:
                    path.append(neighbor_uid)
                    dfs(neighbor_uid, target_uid, path, visited.copy())
                    path.pop()

        dfs(start_uid, end_uid, [start_uid], set())

        return paths

    def degree_centrality(self) -> dict[str, float]:
        """Calculate degree centrality for all nodes.
        
        Returns:
            Dictionary mapping node UID to degree centrality score
        """
        centrality = {}
        n = len(self.graph.nodes)

        if n <= 1:
            return dict.fromkeys(self.graph.nodes, 0.0)

        for uid in self.graph.nodes:
            # Count both incoming and outgoing edges
            degree = len(self.graph.get_neighbors(uid)) + len(self.graph.get_incoming_neighbors(uid))
            # Normalize by maximum possible degree
            centrality[uid] = degree / (2 * (n - 1))

        return centrality

    def betweenness_centrality(self, normalized: bool = True) -> dict[str, float]:
        """Calculate betweenness centrality for all nodes.
        
        Args:
            normalized: Whether to normalize scores
            
        Returns:
            Dictionary mapping node UID to betweenness centrality score
        """
        centrality = dict.fromkeys(self.graph.nodes, 0.0)
        nodes = list(self.graph.nodes.keys())

        for i, start_uid in enumerate(nodes):
            # Single source shortest paths
            S = []  # Stack of nodes in order of distance
            P = {uid: [] for uid in nodes}  # Predecessors
            sigma = dict.fromkeys(nodes, 0.0)  # Number of shortest paths
            sigma[start_uid] = 1.0
            d = dict.fromkeys(nodes, -1)  # Distance
            d[start_uid] = 0
            Q = deque([start_uid])

            while Q:
                v = Q.popleft()
                S.append(v)

                for w in self.graph.get_neighbors(v):
                    # First time we reach w?
                    if d[w] < 0:
                        Q.append(w)
                        d[w] = d[v] + 1
                    # Shortest path to w via v?
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)

            # Accumulation
            delta = dict.fromkeys(nodes, 0.0)
            while S:
                w = S.pop()
                for v in P[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != start_uid:
                    centrality[w] += delta[w]

        # Normalize
        if normalized and len(nodes) > 2:
            scale = 1.0 / ((len(nodes) - 1) * (len(nodes) - 2))
            for uid in centrality:
                centrality[uid] *= scale

        return centrality

    def closeness_centrality(self) -> dict[str, float]:
        """Calculate closeness centrality for all nodes.
        
        Returns:
            Dictionary mapping node UID to closeness centrality score
        """
        centrality = {}

        for uid in self.graph.nodes:
            # Calculate sum of shortest path distances
            total_distance = 0
            reachable_nodes = 0

            for other_uid in self.graph.nodes:
                if uid != other_uid:
                    path = self.shortest_path(uid, other_uid)
                    if path:
                        total_distance += len(path) - 1
                        reachable_nodes += 1

            if reachable_nodes > 0:
                # Closeness is inverse of average distance
                centrality[uid] = reachable_nodes / total_distance
            else:
                centrality[uid] = 0.0

        return centrality

    def pagerank(self, damping_factor: float = 0.85, max_iterations: int = 100,
                tolerance: float = 1e-6) -> dict[str, float]:
        """Calculate PageRank scores for all nodes.
        
        Args:
            damping_factor: Probability of following links (vs random jump)
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance
            
        Returns:
            Dictionary mapping node UID to PageRank score
        """
        n = len(self.graph.nodes)
        if n == 0:
            return {}

        # Initialize scores
        scores = dict.fromkeys(self.graph.nodes, 1.0 / n)

        for iteration in range(max_iterations):
            new_scores = {}
            diff = 0.0

            for uid in self.graph.nodes:
                # Random jump probability
                score = (1 - damping_factor) / n

                # Incoming link contributions
                incoming = self.graph.get_incoming_neighbors(uid)
                for source_uid in incoming:
                    out_degree = len(self.graph.get_neighbors(source_uid))
                    if out_degree > 0:
                        score += damping_factor * scores[source_uid] / out_degree

                new_scores[uid] = score
                diff += abs(score - scores[uid])

            scores = new_scores

            # Check convergence
            if diff < tolerance:
                break

        return scores

    def find_communities(self, resolution: float = 1.0) -> dict[str, int]:
        """Find communities using Louvain algorithm.
        
        Args:
            resolution: Resolution parameter (higher finds smaller communities)
            
        Returns:
            Dictionary mapping node UID to community ID
        """
        # Simplified community detection using connected components
        # For production, consider using more sophisticated algorithms

        communities = {}
        community_id = 0
        visited = set()

        for uid in self.graph.nodes:
            if uid not in visited:
                # BFS to find connected component
                queue = deque([uid])
                component = []

                while queue:
                    current = queue.popleft()
                    if current not in visited:
                        visited.add(current)
                        component.append(current)

                        # Add neighbors
                        for neighbor in self.graph.get_neighbors(current):
                            if neighbor not in visited:
                                queue.append(neighbor)
                        for neighbor in self.graph.get_incoming_neighbors(current):
                            if neighbor not in visited:
                                queue.append(neighbor)

                # Assign community ID
                for node_uid in component:
                    communities[node_uid] = community_id
                community_id += 1

        return communities

    def detect_clusters(self, min_size: int = 3) -> list[set[str]]:
        """Detect dense clusters of nodes.
        
        Args:
            min_size: Minimum cluster size
            
        Returns:
            List of node UID sets representing clusters
        """
        clusters = []
        processed = set()

        for uid in self.graph.nodes:
            if uid in processed:
                continue

            # Find nodes within 2 hops
            cluster = {uid}

            # First hop
            for neighbor1 in self.graph.get_neighbors(uid):
                cluster.add(neighbor1)

                # Second hop
                for neighbor2 in self.graph.get_neighbors(neighbor1):
                    cluster.add(neighbor2)

            # Check density
            if len(cluster) >= min_size:
                # Count edges within cluster
                edge_count = 0
                for node1 in cluster:
                    for node2 in cluster:
                        if node1 != node2:
                            edges = self.graph.get_edges_from_node(node1)
                            if any(e.target_uid == node2 for e in edges):
                                edge_count += 1

                # Calculate density
                max_edges = len(cluster) * (len(cluster) - 1)
                density = edge_count / max_edges if max_edges > 0 else 0

                # Keep dense clusters
                if density > 0.3:  # Threshold for density
                    clusters.append(cluster)
                    processed.update(cluster)

        return clusters

    def find_knowledge_gaps(self, min_importance: float = 0.5) -> list[tuple[str, str, float]]:
        """Find potential missing connections (knowledge gaps).
        
        Args:
            min_importance: Minimum importance score for gaps
            
        Returns:
            List of (node1_uid, node2_uid, importance_score) tuples
        """
        gaps = []

        # Calculate node importance using PageRank
        importance = self.pagerank()

        # Find nodes that should probably be connected
        nodes = list(self.graph.nodes.keys())

        for i, uid1 in enumerate(nodes):
            for uid2 in nodes[i+1:]:
                # Skip if already connected
                if self.graph.get_edge(uid1, uid2, RelationshipType.RELATED_TO.value):
                    continue

                # Calculate gap importance based on:
                # 1. Node importance
                # 2. Common neighbors
                # 3. Path distance

                node1_importance = importance.get(uid1, 0)
                node2_importance = importance.get(uid2, 0)

                # Common neighbors
                neighbors1 = set(self.graph.get_neighbors(uid1))
                neighbors2 = set(self.graph.get_neighbors(uid2))
                common_neighbors = len(neighbors1.intersection(neighbors2))

                # Path distance
                path = self.shortest_path(uid1, uid2)
                path_distance = len(path) - 1 if path else 10  # Large value if no path

                # Calculate gap score
                if common_neighbors > 0 and path_distance > 2:
                    gap_score = (
                        (node1_importance + node2_importance) / 2 *
                        (common_neighbors / 10) *
                        (1 / path_distance)
                    )

                    if gap_score >= min_importance:
                        gaps.append((uid1, uid2, gap_score))

        # Sort by importance
        gaps.sort(key=lambda x: x[2], reverse=True)

        return gaps

    def calculate_knowledge_density(self, subgraph_nodes: set[str] | None = None) -> float:
        """Calculate knowledge density of the graph or subgraph.
        
        Args:
            subgraph_nodes: Optional set of node UIDs to calculate density for
            
        Returns:
            Density score between 0 and 1
        """
        if subgraph_nodes:
            nodes = subgraph_nodes
        else:
            nodes = set(self.graph.nodes.keys())

        if len(nodes) <= 1:
            return 0.0

        # Count edges within the node set
        edge_count = 0
        for edge in self.graph.edges:
            if edge.source_uid in nodes and edge.target_uid in nodes:
                edge_count += 1

        # Calculate density
        max_edges = len(nodes) * (len(nodes) - 1)
        density = edge_count / max_edges if max_edges > 0 else 0.0

        return density

    def find_central_concepts(self, top_n: int = 10) -> list[tuple[str, float]]:
        """Find the most central/important concepts in the graph.
        
        Args:
            top_n: Number of top concepts to return
            
        Returns:
            List of (node_uid, centrality_score) tuples
        """
        # Combine multiple centrality measures
        degree_scores = self.degree_centrality()
        betweenness_scores = self.betweenness_centrality()
        pagerank_scores = self.pagerank()

        # Normalize and combine scores
        combined_scores = {}

        for uid in self.graph.nodes:
            # Weight different centrality measures
            score = (
                0.3 * degree_scores.get(uid, 0) +
                0.4 * betweenness_scores.get(uid, 0) +
                0.3 * pagerank_scores.get(uid, 0)
            )
            combined_scores[uid] = score

        # Sort and return top N
        sorted_concepts = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_concepts[:top_n]

    def analyze_node_importance(self, uid: str) -> dict[str, Any]:
        """Analyze the importance of a specific node.
        
        Args:
            uid: Node UID
            
        Returns:
            Dictionary with various importance metrics
        """
        if uid not in self.graph.nodes:
            return {}

        # Calculate various metrics
        degree_scores = self.degree_centrality()
        betweenness_scores = self.betweenness_centrality()
        closeness_scores = self.closeness_centrality()
        pagerank_scores = self.pagerank()

        # Get node's connections
        outgoing = len(self.graph.get_neighbors(uid))
        incoming = len(self.graph.get_incoming_neighbors(uid))

        # Find communities
        communities = self.find_communities()

        return {
            'uid': uid,
            'metrics': {
                'degree_centrality': degree_scores.get(uid, 0),
                'betweenness_centrality': betweenness_scores.get(uid, 0),
                'closeness_centrality': closeness_scores.get(uid, 0),
                'pagerank': pagerank_scores.get(uid, 0)
            },
            'connections': {
                'outgoing': outgoing,
                'incoming': incoming,
                'total': outgoing + incoming
            },
            'community': communities.get(uid, -1),
            'node_info': self.graph.get_node(uid).to_dict()
        }
