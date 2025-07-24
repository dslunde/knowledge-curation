"""Tests for vector database operations."""

from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from knowledge.curator.vector.adapter import QdrantAdapter
from knowledge.curator.vector.embeddings import EmbeddingGenerator
from knowledge.curator.vector.management import VectorCollectionManager
from knowledge.curator.vector.search import SimilaritySearch
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import Mock
from unittest.mock import patch

import unittest
    @patch('knowledge.curator.vector.adapter.QdrantClient')
    def test_adapter_initialization(self, mock_client_class):
        """Test adapter initialization."""
        mock_client_class.return_value = self.mock_client

        adapter = QdrantAdapter(host="localhost", port=6333)

        mock_client_class.assert_called_once_with(
            host="localhost", port=6333, api_key=None, https=False
        )
        self.assertEqual(adapter.collection_name, "plone_knowledge")
        self.assertEqual(adapter.vector_size, 384)

    @patch('knowledge.curator.vector.adapter.QdrantClient')
    def test_initialize_collection(self, mock_client_class):
        """Test collection initialization."""
        mock_client_class.return_value = self.mock_client

        # Mock get_collections response
        mock_collections = Mock()
        mock_collections.collections = []
        self.mock_client.get_collections.return_value = mock_collections

        adapter = QdrantAdapter()
        adapter.initialize_collection(vector_size=768)

        self.mock_client.create_collection.assert_called_once()
        self.assertEqual(adapter.vector_size, 768)

    @patch('knowledge.curator.vector.adapter.QdrantClient')
    def test_add_vectors(self, mock_client_class):
        """Test adding vectors to collection."""
        mock_client_class.return_value = self.mock_client

        adapter = QdrantAdapter()

        documents = [
            {
                "uid": "doc1",
                "title": "Document 1",
                "path": "/doc1",
                "content_type": "BookmarkPlus",
            },
            {
                "uid": "doc2",
                "title": "Document 2",
                "path": "/doc2",
                "content_type": "ResearchNote",
            },
        ]

        embeddings = [[0.1] * 384, [0.2] * 384]

        result = adapter.add_vectors(documents, embeddings)

        self.assertTrue(result)
        self.mock_client.upsert.assert_called()


class TestVectorCollectionManager(unittest.TestCase):
    """Test vector collection management."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    @patch('knowledge.curator.vector.management.QdrantAdapter')
    @patch('knowledge.curator.vector.management.EmbeddingGenerator')
    def test_update_content_vector(self, mock_embeddings_class, mock_adapter_class):
        """Test updating vector for content."""
        # Create mocks
        mock_adapter = Mock()
        mock_embeddings = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_embeddings_class.return_value = mock_embeddings

        # Configure mocks
        mock_embeddings.prepare_content_text.return_value = "Test content"
        mock_embeddings.generate_embedding.return_value = [0.1] * 384
        mock_adapter.update_vector.return_value = True

        # Create test content
        bookmark = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            title="Test Bookmark",
            description="Test description",
        )

        manager = VectorCollectionManager()
        result = manager.update_content_vector(bookmark)

        self.assertTrue(result)
        mock_embeddings.prepare_content_text.assert_called_once()
        mock_embeddings.generate_embedding.assert_called_once_with("Test content")
        mock_adapter.update_vector.assert_called_once()

    @patch('knowledge.curator.vector.management.QdrantAdapter')
    @patch('knowledge.curator.vector.management.EmbeddingGenerator')
    def test_health_check(self, mock_embeddings_class, mock_adapter_class):
        """Test health check functionality."""
        # Create mocks
        mock_adapter = Mock()
        mock_embeddings = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_embeddings_class.return_value = mock_embeddings

        # Configure mocks
        mock_collections = Mock()
        mock_collections.collections = [Mock(name="plone_knowledge")]
        mock_adapter.client.get_collections.return_value = mock_collections
        mock_adapter.get_collection_info.return_value = {"status": "green"}
        mock_adapter.collection_name = "plone_knowledge"

        mock_embeddings.generate_embedding.return_value = [0.1] * 384
        mock_embeddings.embedding_dimension = 384
        mock_embeddings.model_name = "test-model"

        manager = VectorCollectionManager()
        health = manager.health_check()

        self.assertTrue(health["healthy"])
        self.assertTrue(health["qdrant"]["healthy"])
        self.assertTrue(health["embeddings"]["healthy"])
        self.assertTrue(health["collection"]["exists"])


class TestSimilaritySearch(unittest.TestCase):
    """Test similarity search functionality."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    @patch('knowledge.curator.vector.search.QdrantAdapter')
    @patch('knowledge.curator.vector.search.EmbeddingGenerator')
    def test_search_by_text(self, mock_embeddings_class, mock_adapter_class):
        """Test text-based similarity search."""
        # Create mocks
        mock_adapter = Mock()
        mock_embeddings = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_embeddings_class.return_value = mock_embeddings

        # Configure mocks
        mock_embeddings.generate_embedding.return_value = [0.1] * 384
        mock_adapter.search_similar.return_value = [
            {
                "uid": "test-uid",
                "title": "Test Result",
                "score": 0.95,
                "path": "/test",
                "content_type": "BookmarkPlus",
            }
        ]

        # Create test content
        api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            title="Test Result",
            UID="test-uid",
        )

        search = SimilaritySearch()
        results = search.search_by_text("test query", limit=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["uid"], "test-uid")
        self.assertEqual(results[0]["score"], 0.95)
        mock_embeddings.generate_embedding.assert_called_once_with("test query")
        mock_adapter.search_similar.assert_called_once()

    @patch('knowledge.curator.vector.search.QdrantAdapter')
    @patch('knowledge.curator.vector.search.EmbeddingGenerator')
    def test_find_similar_content(self, mock_embeddings_class, mock_adapter_class):
        """Test finding similar content."""
        # Create mocks
        mock_adapter = Mock()
        mock_embeddings = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_embeddings_class.return_value = mock_embeddings

        # Create test content
        api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            title="Source Bookmark",
            UID="source-uid",
        )

        bookmark2 = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            title="Similar Bookmark",
            UID="similar-uid",
        )

        # Configure mocks
        mock_adapter.find_related_content.return_value = [
            {
                "uid": "similar-uid",
                "title": "Similar Bookmark",
                "score": 0.85,
                "path": "/similar",
                "content_type": "BookmarkPlus",
            }
        ]

        search = SimilaritySearch()
        results = search.find_similar_content("source-uid", limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["uid"], "similar-uid")
        self.assertEqual(results[0]["score"], 0.85)
        mock_adapter.find_related_content.assert_called_once_with(
            "source-uid", limit=3, score_threshold=0.6
        )
