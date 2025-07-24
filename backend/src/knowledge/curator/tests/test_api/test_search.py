"""Tests for Search API."""

import unittest
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from plone.restapi.testing import RelativeSession
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING
from datetime import datetime, timedelta


class TestSearchAPI(unittest.TestCase):
    """Test Search API endpoints."""

    layer = PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({'Accept': 'application/json'})
        self.api_session.auth = (TEST_USER_ID, 'secret')

        # Create test content
        self.folder = api.content.create(
            container=self.portal,
            type='Folder',
            id='knowledge-base',
            title='Knowledge Base'
        )

        # Create research notes with different content
        self.note1 = api.content.create(
            container=self.folder,
            type='ResearchNote',
            title='Python Programming Guide',
            description='Comprehensive guide to Python',
            content='Python is a high-level programming language...',
            tags=['python', 'programming', 'tutorial']
        )

        self.note2 = api.content.create(
            container=self.folder,
            type='ResearchNote',
            title='Machine Learning with Python',
            description='ML implementation in Python',
            content='Machine learning algorithms in Python using scikit-learn...',
            tags=['python', 'machine-learning', 'data-science']
        )

        self.note3 = api.content.create(
            container=self.folder,
            type='ResearchNote',
            title='JavaScript Fundamentals',
            description='Learn JavaScript basics',
            content='JavaScript is a dynamic programming language...',
            tags=['javascript', 'programming', 'web']
        )

        # Create bookmark
        self.bookmark = api.content.create(
            container=self.folder,
            type='BookmarkPlus',
            title='Python Official Documentation',
            url='https://docs.python.org',
            description='Official Python documentation',
            tags=['python', 'documentation', 'reference']
        )

        # Add embedding vectors for similarity testing
        self.note1.embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.note2.embedding_vector = [0.1, 0.2, 0.3, 0.5, 0.6]  # Similar to note1
        self.note3.embedding_vector = [0.9, 0.8, 0.7, 0.6, 0.5]  # Different

        import transaction
        transaction.commit()

    def test_semantic_search_post(self):
        """Test semantic search via POST."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'semantic',
                'query': 'python programming',
                'limit': 10,
                'portal_types': ['ResearchNote', 'BookmarkPlus']
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('items', data)
        self.assertIn('items_total', data)
        self.assertIn('query', data)
        self.assertEqual(data['search_type'], 'semantic')

    def test_fulltext_search(self):
        """Test fulltext search."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'fulltext',
                'query': 'Python',
                'limit': 20
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('items', data)
        self.assertEqual(data['search_type'], 'fulltext')

        # Should find Python-related content
        titles = [item['title'] for item in data['items']]
        python_items = [t for t in titles if 'Python' in t]
        self.assertGreater(len(python_items), 0)

    def test_similarity_search(self):
        """Test similarity search."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'similarity',
                'uid': self.note1.UID(),
                'limit': 5,
                'threshold': 0.5
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('items', data)
        self.assertEqual(data['source_uid'], self.note1.UID())
        self.assertEqual(data['search_type'], 'similarity')

        # Should find similar items (note2 is similar to note1)
        if data['items']:
            # First result should be the most similar
            self.assertGreater(data['items'][0]['similarity_score'], 0.5)

    def test_search_with_filters(self):
        """Test search with filters."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'fulltext',
                'query': 'programming',
                'filters': {
                    'tags': ['python'],
                    'review_state': ['private']
                }
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # All results should have 'python' tag
        for item in data['items']:
            self.assertIn('python', item['tags'])

    def test_search_with_date_filter(self):
        """Test search with date range filter."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()

        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'fulltext',
                'query': 'programming',
                'filters': {
                    'date_range': {
                        'start': yesterday,
                        'end': tomorrow
                    }
                }
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should find recently created items
        self.assertGreater(len(data['items']), 0)

    def test_semantic_search_get(self):
        """Test semantic search via GET."""
        response = self.api_session.get(
            '/@knowledge-search/semantic?q=python&limit=5'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('items', data)
        self.assertEqual(data['query'], 'python')

    def test_find_similar_get(self):
        """Test find similar via GET on specific item."""
        response = self.api_session.get(
            f'{self.note1.absolute_url()}/@knowledge-search/similar?limit=3'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('items', data)
        self.assertEqual(data['source_uid'], self.note1.UID())

    def test_search_invalid_type(self):
        """Test search with invalid type."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'invalid',
                'query': 'test'
            }
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_search_missing_query(self):
        """Test search without query."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'fulltext'
            }
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_similarity_search_missing_uid(self):
        """Test similarity search without UID."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'similarity',
                'limit': 5
            }
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_similarity_search_invalid_uid(self):
        """Test similarity search with invalid UID."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'similarity',
                'uid': 'invalid-uid',
                'limit': 5
            }
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('error', data)

    def test_search_portal_type_filter(self):
        """Test search with portal type filter."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'fulltext',
                'query': 'python',
                'portal_types': ['BookmarkPlus']
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # All results should be BookmarkPlus
        for item in data['items']:
            self.assertEqual(item['portal_type'], 'BookmarkPlus')

    def test_search_limit(self):
        """Test search result limit."""
        response = self.api_session.post(
            '/@knowledge-search',
            json={
                'type': 'fulltext',
                'query': 'programming',
                'limit': 2
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertLessEqual(len(data['items']), 2)
