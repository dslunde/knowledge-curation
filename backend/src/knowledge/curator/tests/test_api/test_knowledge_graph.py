"""Tests for Knowledge Graph API."""

import unittest
import transaction
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession
from plone import api

from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING


class TestKnowledgeGraphAPI(unittest.TestCase):
    """Test knowledge graph API endpoints."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Set up test environment."""
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        # Set up REST API session
        self.api_session = RelativeSession(self.portal.absolute_url())
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        # Create interconnected test content
        self.note1 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            title="Machine Learning Basics",
            tags=["ml", "basics"],
        )

        self.note2 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            title="Deep Learning Fundamentals",
            tags=["ml", "deep-learning"],
        )

        self.goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            title="Master Machine Learning",
            tags=["ml", "goal"],
        )

    def test_get_graph(self):
        """Test getting the complete knowledge graph."""
        response = self.api_session.get("/@knowledge-graph")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertIn("count", data)

        # Check nodes
        self.assertEqual(len(data["nodes"]), 3)
        node_titles = [node["title"] for node in data["nodes"]]
        self.assertIn("Machine Learning Basics", node_titles)
        self.assertIn("Deep Learning Fundamentals", node_titles)
        self.assertIn("Master Machine Learning", node_titles)

        # Check edges
        self.assertGreater(len(data["edges"]), 0)

        # Verify node structure
        node = data["nodes"][0]
        self.assertIn("id", node)
        self.assertIn("title", node)
        self.assertIn("type", node)
        self.assertIn("url", node)
        self.assertIn("review_state", node)

    def test_get_connections(self):
        """Test getting connections for a specific item."""
        response = self.api_session.get(
            f"{self.note1.absolute_url()}/@knowledge-graph/connections"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("connections", data)
        self.assertIn("count", data)

        # Check connections
        connections = data["connections"]
        self.assertGreater(len(connections), 0)

        # Find direct connection
        direct_conn = [c for c in connections if c["connection_type"] == "direct"]
        self.assertEqual(len(direct_conn), 1)
        self.assertEqual(direct_conn[0]["title"], "Deep Learning Fundamentals")

    def test_suggest_connections(self):
        """Test connection suggestions."""
        # Create embedding vectors for testing
        self.note1.embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.note2.embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.6]  # Similar

        # Create another note with different vector
        api.content.create(
            container=self.folder,
            type="ResearchNote",
            title="Unrelated Topic",
            embedding_vector=[0.9, 0.8, 0.7, 0.6, 0.5],  # Very different
        )

        transaction.commit()

        response = self.api_session.get(
            f"{self.note1.absolute_url()}/@knowledge-graph/suggest"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("suggestions", data)
        self.assertIn("count", data)

        # Suggestions should be ordered by similarity
        if data["suggestions"]:
            self.assertGreater(data["suggestions"][0]["similarity"], 0.7)

    def test_visualize_graph(self):
        """Test graph visualization endpoint."""
        response = self.api_session.get("/@knowledge-graph/visualize")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("graph", data)
        self.assertIn("visualization", data)

        # Check visualization config
        viz = data["visualization"]
        self.assertIn("width", viz)
        self.assertIn("height", viz)
        self.assertIn("force", viz)

        # Check node colors
        nodes = data["graph"]["nodes"]
        for node in nodes:
            self.assertIn("color", node)
            self.assertIn("size", node)

    def test_unauthorized_access(self):
        """Test unauthorized access to knowledge graph."""
        # Logout
        self.api_session.auth = None

        response = self.api_session.get("/@knowledge-graph")
        self.assertEqual(response.status_code, 401)

    def test_invalid_endpoint(self):
        """Test invalid knowledge graph endpoint."""
        response = self.api_session.get("/@knowledge-graph/invalid")
        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertIn("error", data)

    def test_empty_graph(self):
        """Test knowledge graph with no content."""
        # Create empty folder
        empty_folder = api.content.create(
            container=self.portal, type="Folder", id="empty-folder"
        )

        response = self.api_session.get(
            f"{empty_folder.absolute_url()}/@knowledge-graph"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data["nodes"]), 0)
        self.assertEqual(len(data["edges"]), 0)
        self.assertEqual(data["count"], 0)
