"""Tests for knowledge graph functionality."""

from knowledge.curator.graph import Edge
from knowledge.curator.graph import Graph
from knowledge.curator.graph import GraphAlgorithms
from knowledge.curator.graph import GraphOperations
from knowledge.curator.graph import GraphStorage
from knowledge.curator.graph import GraphTraversal
from knowledge.curator.graph import Node
from knowledge.curator.graph import NodeType
from knowledge.curator.graph import RelationshipManager
from knowledge.curator.graph import RelationshipType
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestGraphModel(unittest.TestCase):
    """Test graph data model."""

    def setUp(self):
        self.graph = Graph()

    def test_add_node(self):
        """Test adding nodes to graph."""
        node = Node("test1", "Test Node", NodeType.RESEARCH_NOTE)
        self.assertTrue(self.graph.add_node(node))
        self.assertEqual(len(self.graph.nodes), 1)

        # Adding same node again should fail
        self.assertFalse(self.graph.add_node(node))

    def test_add_edge(self):
        """Test adding edges to graph."""
        node1 = Node("test1", "Node 1", NodeType.RESEARCH_NOTE)
        node2 = Node("test2", "Node 2", NodeType.LEARNING_GOAL)

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        edge = Edge("test1", "test2", RelationshipType.RELATED_TO.value)
        self.assertTrue(self.graph.add_edge(edge))
        self.assertEqual(len(self.graph.edges), 1)

        # Adding edge without nodes should fail
        edge2 = Edge("test1", "test3", RelationshipType.RELATED_TO.value)
        self.assertFalse(self.graph.add_edge(edge2))

    def test_remove_node(self):
        """Test removing nodes from graph."""
        node1 = Node("test1", "Node 1", NodeType.RESEARCH_NOTE)
        node2 = Node("test2", "Node 2", NodeType.LEARNING_GOAL)

        self.graph.add_node(node1)
        self.graph.add_node(node2)

        edge = Edge("test1", "test2", RelationshipType.RELATED_TO.value)
        self.graph.add_edge(edge)

        # Remove node should also remove connected edges
        self.assertTrue(self.graph.remove_node("test1"))
        self.assertEqual(len(self.graph.nodes), 1)
        self.assertEqual(len(self.graph.edges), 0)

    def test_get_neighbors(self):
        """Test getting node neighbors."""
        # Create a small graph
        for i in range(4):
            node = Node(f"test{i}", f"Node {i}", NodeType.RESEARCH_NOTE)
            self.graph.add_node(node)

        # Add edges: 0->1, 0->2, 1->3
        self.graph.add_edge(Edge("test0", "test1", RelationshipType.RELATED_TO.value))
        self.graph.add_edge(Edge("test0", "test2", RelationshipType.RELATED_TO.value))
        self.graph.add_edge(Edge("test1", "test3", RelationshipType.RELATED_TO.value))

        # Test neighbors
        neighbors = self.graph.get_neighbors("test0")
        self.assertEqual(set(neighbors), {"test1", "test2"})

        # Test incoming neighbors
        incoming = self.graph.get_incoming_neighbors("test1")
        self.assertEqual(set(incoming), {"test0"})

    def test_get_subgraph(self):
        """Test getting subgraph."""
        # Create nodes
        for i in range(5):
            node = Node(f"test{i}", f"Node {i}", NodeType.RESEARCH_NOTE)
            self.graph.add_node(node)

        # Add edges
        edges = [
            ("test0", "test1"),
            ("test1", "test2"),
            ("test2", "test3"),
            ("test3", "test4"),
            ("test0", "test4"),
        ]

        for source, target in edges:
            self.graph.add_edge(Edge(source, target, RelationshipType.RELATED_TO.value))

        # Get subgraph with nodes 0, 1, 2
        subgraph = self.graph.get_subgraph(["test0", "test1", "test2"])

        self.assertEqual(len(subgraph.nodes), 3)
        self.assertEqual(len(subgraph.edges), 2)  # Only edges between included nodes


class TestRelationships(unittest.TestCase):
    """Test relationship management."""

    def setUp(self):
        self.manager = RelationshipManager()

    def test_validate_relationship(self):
        """Test relationship validation."""
        # Test valid relationships
        self.assertTrue(
            self.manager.validate_relationship(
                "ResearchNote", "ResearchNote", RelationshipType.RELATED_TO.value
            )
        )

        # Test constrained relationships
        self.assertTrue(
            self.manager.validate_relationship(
                "ResearchNote", "Tag", RelationshipType.TAGGED_WITH.value
            )
        )

        # Invalid relationship
        self.assertFalse(
            self.manager.validate_relationship(
                "Tag", "ResearchNote", RelationshipType.TAGGED_WITH.value
            )
        )

    def test_suggest_relationship_type(self):
        """Test relationship type suggestions."""
        suggestions = self.manager.suggest_relationship_type(
            "ResearchNote", "LearningGoal"
        )

        self.assertTrue(len(suggestions) > 0)

        # Check that suggestions are sorted by confidence
        confidences = [s[1] for s in suggestions]
        self.assertEqual(confidences, sorted(confidences, reverse=True))

    def test_custom_relationships(self):
        """Test custom relationship registration."""
        self.manager.register_custom_relationship(
            "mentions",
            {
                "bidirectional": False,
                "transitive": False,
                "weight_range": (0.0, 1.0),
                "description": "Mentions another item",
                "reverse_name": "mentioned_by",
            },
        )

        self.assertIn("mentions", self.manager.custom_relationships)


class TestGraphOperations(unittest.TestCase):
    """Test graph operations."""

    def setUp(self):
        self.graph = Graph()
        self.ops = GraphOperations(self.graph)

    def test_add_content_node(self):
        """Test adding content nodes."""
        self.assertTrue(
            self.ops.add_content_node(
                "uid1", "Research Note 1", "ResearchNote", tags=["python", "testing"]
            )
        )

        node = self.graph.get_node("uid1")
        self.assertIsNotNone(node)
        self.assertEqual(node.title, "Research Note 1")
        self.assertEqual(node.get_property("tags"), ["python", "testing"])

    def test_create_relationship(self):
        """Test creating relationships."""
        self.ops.add_content_node("uid1", "Note 1", "ResearchNote")
        self.ops.add_content_node("uid2", "Note 2", "ResearchNote")

        self.assertTrue(
            self.ops.create_relationship(
                "uid1", "uid2", RelationshipType.RELATED_TO, weight=0.8
            )
        )

        edge = self.graph.get_edge("uid1", "uid2", RelationshipType.RELATED_TO.value)
        self.assertIsNotNone(edge)
        self.assertEqual(edge.weight, 0.8)

    def test_merge_nodes(self):
        """Test merging nodes."""
        # Create nodes with edges
        self.ops.add_content_node("uid1", "Note 1", "ResearchNote")
        self.ops.add_content_node("uid2", "Note 2", "ResearchNote")
        self.ops.add_content_node("uid3", "Note 3", "ResearchNote")

        self.ops.create_relationship("uid1", "uid3", RelationshipType.RELATED_TO)
        self.ops.create_relationship("uid2", "uid3", RelationshipType.RELATED_TO)

        # Merge uid2 into uid1
        self.assertTrue(self.ops.merge_nodes("uid1", "uid2"))

        # Check results
        self.assertIsNone(self.graph.get_node("uid2"))
        self.assertEqual(len(self.graph.nodes), 2)

        # Check edges were redirected
        edges_from_uid1 = self.graph.get_edges_from_node("uid1")
        self.assertEqual(len(edges_from_uid1), 1)
        self.assertEqual(edges_from_uid1[0].target_uid, "uid3")

    def test_suggest_connections(self):
        """Test connection suggestions."""
        # Create a small graph
        self.ops.add_content_node("uid1", "Note 1", "ResearchNote")
        self.ops.add_content_node("uid2", "Note 2", "ResearchNote")
        self.ops.add_content_node("uid3", "Note 3", "ResearchNote")
        self.ops.add_content_node("uid4", "Note 4", "ResearchNote")

        # Create connections
        self.ops.create_relationship("uid1", "uid2", RelationshipType.RELATED_TO)
        self.ops.create_relationship("uid2", "uid3", RelationshipType.RELATED_TO)
        self.ops.create_relationship("uid3", "uid4", RelationshipType.RELATED_TO)

        # Get suggestions for uid1
        suggestions = self.ops.suggest_connections("uid1", limit=5)

        # Should suggest uid3 (connected through uid2)
        suggested_uids = [s[0] for s in suggestions]
        self.assertIn("uid3", suggested_uids)


class TestGraphAlgorithms(unittest.TestCase):
    """Test graph algorithms."""

    def setUp(self):
        self.graph = Graph()
        self.algo = GraphAlgorithms(self.graph)

        # Create a test graph
        for i in range(6):
            node = Node(f"node{i}", f"Node {i}", NodeType.RESEARCH_NOTE)
            self.graph.add_node(node)

    def test_shortest_path(self):
        """Test shortest path algorithm."""
        # Create edges
        edges = [
            ("node0", "node1", 1.0),
            ("node1", "node2", 1.0),
            ("node2", "node3", 1.0),
            ("node0", "node4", 1.0),
            ("node4", "node3", 1.0),
        ]

        for source, target, weight in edges:
            edge = Edge(source, target, RelationshipType.RELATED_TO.value, weight)
            self.graph.add_edge(edge)

        # Find shortest path
        path = self.algo.shortest_path("node0", "node3")
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3)  # node0 -> node4 -> node3

    def test_centrality_measures(self):
        """Test centrality algorithms."""
        # Create a star graph (node0 connected to all others)
        for i in range(1, 6):
            edge = Edge("node0", f"node{i}", RelationshipType.RELATED_TO.value)
            self.graph.add_edge(edge)

        # Test degree centrality
        degree_centrality = self.algo.degree_centrality()

        # node0 should have highest centrality
        max_centrality_node = max(degree_centrality.items(), key=lambda x: x[1])[0]
        self.assertEqual(max_centrality_node, "node0")

        # Test PageRank
        pagerank = self.algo.pagerank()
        max_pagerank_node = max(pagerank.items(), key=lambda x: x[1])[0]
        self.assertEqual(max_pagerank_node, "node0")

    def test_find_communities(self):
        """Test community detection."""
        # Create two connected components
        # Component 1: node0, node1, node2
        self.graph.add_edge(Edge("node0", "node1", RelationshipType.RELATED_TO.value))
        self.graph.add_edge(Edge("node1", "node2", RelationshipType.RELATED_TO.value))

        # Component 2: node3, node4, node5
        self.graph.add_edge(Edge("node3", "node4", RelationshipType.RELATED_TO.value))
        self.graph.add_edge(Edge("node4", "node5", RelationshipType.RELATED_TO.value))

        communities = self.algo.find_communities()

        # Should find 2 communities
        unique_communities = set(communities.values())
        self.assertEqual(len(unique_communities), 2)

        # Nodes in same component should have same community ID
        self.assertEqual(communities["node0"], communities["node1"])
        self.assertEqual(communities["node3"], communities["node4"])
        self.assertNotEqual(communities["node0"], communities["node3"])


class TestGraphStorage(unittest.TestCase):
    """Test graph storage with Plone."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.storage = GraphStorage(self.portal)

    def test_save_and_load_graph(self):
        """Test saving and loading graph."""
        # Create a graph
        graph = Graph()

        node1 = Node("test1", "Test Node 1", NodeType.RESEARCH_NOTE)
        node2 = Node("test2", "Test Node 2", NodeType.LEARNING_GOAL)
        graph.add_node(node1)
        graph.add_node(node2)

        edge = Edge("test1", "test2", RelationshipType.RELATED_TO.value, 0.8)
        graph.add_edge(edge)

        # Save graph
        self.storage.save_graph(graph)

        # Load graph
        loaded_graph = self.storage.load_graph()

        self.assertEqual(len(loaded_graph.nodes), 2)
        self.assertEqual(len(loaded_graph.edges), 1)

        # Check node properties
        loaded_node = loaded_graph.get_node("test1")
        self.assertEqual(loaded_node.title, "Test Node 1")

        # Check edge properties
        loaded_edge = loaded_graph.get_edge(
            "test1", "test2", RelationshipType.RELATED_TO.value
        )
        self.assertEqual(loaded_edge.weight, 0.8)

    def test_sync_with_catalog(self):
        """Test syncing graph with catalog content."""
        # Create some content
        note1 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="note1",
            title="Research Note 1",
            tags=["python", "testing"],
        )

        note2 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="note2",
            title="Research Note 2",
            connections=[api.content.get_uuid(note1)],
        )

        # Sync with catalog
        self.storage.sync_with_catalog()

        # Load and check graph
        graph = self.storage.load_graph()

        # Should have nodes for both notes
        self.assertEqual(
            len([
                n for n in graph.nodes.values() if n.node_type == NodeType.RESEARCH_NOTE
            ]),
            2,
        )

        # Should have tag nodes
        tag_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.TAG]
        self.assertEqual(len(tag_nodes), 2)  # python and testing

        # Should have connection edge
        uid1 = api.content.get_uuid(note1)
        uid2 = api.content.get_uuid(note2)
        edge = graph.get_edge(uid2, uid1, RelationshipType.RELATED_TO.value)
        self.assertIsNotNone(edge)

    def test_query_nodes(self):
        """Test querying nodes."""
        # Create and save a graph
        graph = Graph()

        for i in range(3):
            node = Node(
                f"note{i}",
                f"Note {i}",
                NodeType.RESEARCH_NOTE,
                status="published" if i < 2 else "draft",
            )
            graph.add_node(node)

        self.storage.save_graph(graph)

        # Query by type
        notes = self.storage.query_nodes(node_type="ResearchNote")
        self.assertEqual(len(notes), 3)

        # Query by properties
        published = self.storage.query_nodes(properties={"status": "published"})
        self.assertEqual(len(published), 2)

    def test_export_import(self):
        """Test export and import functionality."""
        # Create a graph
        graph = Graph()
        node = Node("test1", "Test Node", NodeType.RESEARCH_NOTE)
        graph.add_node(node)

        self.storage.save_graph(graph)

        # Export to JSON
        json_data = self.storage.export_graph(format="json")
        self.assertIn("nodes", json_data)
        self.assertIn("edges", json_data)

        # Clear and import
        empty_graph = Graph()
        self.storage.save_graph(empty_graph)

        self.storage.import_graph(json_data, format="json", merge=False)

        # Check imported graph
        imported_graph = self.storage.load_graph()
        self.assertEqual(len(imported_graph.nodes), 1)
        self.assertEqual(imported_graph.get_node("test1").title, "Test Node")


class TestGraphTraversal(unittest.TestCase):
    """Test graph traversal utilities."""

    def setUp(self):
        self.graph = Graph()
        self.traversal = GraphTraversal(self.graph)

        # Create a test graph
        for i in range(7):
            node = Node(f"node{i}", f"Node {i}", NodeType.RESEARCH_NOTE)
            self.graph.add_node(node)

    def test_breadth_first_search(self):
        """Test BFS traversal."""
        # Create edges
        edges = [
            ("node0", "node1"),
            ("node0", "node2"),
            ("node1", "node3"),
            ("node1", "node4"),
            ("node2", "node5"),
            ("node2", "node6"),
        ]

        for source, target in edges:
            edge = Edge(source, target, RelationshipType.RELATED_TO.value)
            self.graph.add_edge(edge)

        # Perform BFS
        result = self.traversal.breadth_first_search("node0", max_depth=2)

        # Check order and depth
        visited_nodes = [item[0].uid for item in result]
        depths = [item[1] for item in result]

        self.assertEqual(visited_nodes[0], "node0")  # Start node
        self.assertEqual(depths[0], 0)

        # All nodes should be visited within depth 2
        self.assertEqual(len(result), 7)
        self.assertTrue(all(d <= 2 for d in depths))

    def test_find_connected_component(self):
        """Test finding connected components."""
        # Create two separate components
        self.graph.add_edge(Edge("node0", "node1", RelationshipType.RELATED_TO.value))
        self.graph.add_edge(Edge("node1", "node2", RelationshipType.RELATED_TO.value))

        self.graph.add_edge(Edge("node3", "node4", RelationshipType.RELATED_TO.value))

        # Find components
        component1 = self.traversal.find_connected_component("node0")
        component2 = self.traversal.find_connected_component("node3")

        self.assertEqual(component1, {"node0", "node1", "node2"})
        self.assertEqual(component2, {"node3", "node4"})

    def test_get_learning_path(self):
        """Test finding learning paths."""
        # Create a learning hierarchy
        edges = [
            ("node0", "node1", RelationshipType.PREREQUISITE_OF),
            ("node1", "node2", RelationshipType.PREREQUISITE_OF),
            ("node0", "node3", RelationshipType.BUILDS_ON),
            ("node3", "node2", RelationshipType.PREREQUISITE_OF),
        ]

        for source, target, rel_type in edges:
            edge = Edge(source, target, rel_type.value, weight=0.9)
            self.graph.add_edge(edge)

        # Find learning path
        path = self.traversal.get_learning_path("node0", "node2")

        self.assertIsNotNone(path)
        self.assertEqual(path[0], "node0")
        self.assertEqual(path[-1], "node2")

    def test_suggest_next_nodes(self):
        """Test next node suggestions."""
        # Create edges with different types
        self.graph.add_edge(
            Edge("node0", "node1", RelationshipType.BUILDS_ON.value, 0.9)
        )
        self.graph.add_edge(
            Edge("node0", "node2", RelationshipType.RELATED_TO.value, 0.7)
        )
        self.graph.add_edge(
            Edge("node0", "node3", RelationshipType.PREREQUISITE_OF.value, 0.8)
        )

        # Get suggestions
        suggestions = self.traversal.suggest_next_nodes("node0", set())

        self.assertEqual(len(suggestions), 3)

        # Check that suggestions are sorted by score
        scores = [s[2] for s in suggestions]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # Check reasons are provided
        for _node, reason, _score in suggestions:
            self.assertIsNotNone(reason)
            self.assertGreater(len(reason), 0)


def test_suite():
    """Test suite."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGraphModel))
    suite.addTest(unittest.makeSuite(TestRelationships))
    suite.addTest(unittest.makeSuite(TestGraphOperations))
    suite.addTest(unittest.makeSuite(TestGraphAlgorithms))
    suite.addTest(unittest.makeSuite(TestGraphStorage))
    suite.addTest(unittest.makeSuite(TestGraphTraversal))
    return suite


if __name__ == "__main__":
    unittest.main()
