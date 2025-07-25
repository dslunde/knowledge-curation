"""Tests for BookmarkPlus status tracking and timestamp updates."""

import unittest
from datetime import datetime
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from knowledge.curator.testing import KNOWLEDGE_CURATOR_INTEGRATION_TESTING
from zope.lifecycleevent import modified


class TestBookmarkStatusTracking(unittest.TestCase):
    """Test suite for BookmarkPlus read status and date tracking."""

    layer = KNOWLEDGE_CURATOR_INTEGRATION_TESTING

    def setUp(self):
        """Set up test fixtures."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        
        # Create a test BookmarkPlus
        self.bookmark = api.content.create(
            container=self.portal,
            type='BookmarkPlus',
            title='Test Bookmark',
            url='https://example.com',
            related_knowledge_items=['dummy-uid'],  # Required field
            resource_type='article',
            content_quality='medium',
        )

    def test_initial_status_and_dates(self):
        """Test that new bookmarks have correct initial values."""
        self.assertEqual(self.bookmark.read_status, 'unread')
        self.assertIsNotNone(self.bookmark.access_date)  # Should be set on creation
        self.assertIsNone(self.bookmark.last_reviewed_date)

    def test_update_read_status_method(self):
        """Test the update_read_status method."""
        # Test changing to in_progress
        self.bookmark.update_read_status('in_progress')
        self.assertEqual(self.bookmark.read_status, 'in_progress')
        self.assertIsNotNone(self.bookmark.access_date)
        self.assertIsNone(self.bookmark.last_reviewed_date)
        
        # Test changing to completed
        self.bookmark.update_read_status('completed')
        self.assertEqual(self.bookmark.read_status, 'completed')
        self.assertIsNotNone(self.bookmark.last_reviewed_date)
        
        # Test invalid status
        with self.assertRaises(ValueError):
            self.bookmark.update_read_status('invalid_status')

    def test_backwards_compatibility_methods(self):
        """Test that old methods still work correctly."""
        # Test mark_as_reading
        self.bookmark.mark_as_reading()
        self.assertEqual(self.bookmark.read_status, 'in_progress')
        
        # Test mark_as_read
        self.bookmark.mark_as_read()
        self.assertEqual(self.bookmark.read_status, 'completed')
        self.assertIsNotNone(self.bookmark.last_reviewed_date)

    def test_event_handler_timestamp_updates(self):
        """Test that the event handler updates timestamps correctly."""
        # Create a fresh bookmark
        bookmark2 = api.content.create(
            container=self.portal,
            type='BookmarkPlus',
            title='Test Bookmark 2',
            url='https://example2.com',
            related_knowledge_items=['dummy-uid'],
            resource_type='video',
            content_quality='high',
        )
        
        # Clear access_date to simulate it not being set
        bookmark2.access_date = None
        
        # Change status through attribute assignment (simulating UI change)
        bookmark2.read_status = 'in_progress'
        # Trigger the modified event
        modified(bookmark2)
        
        # The event handler should have set access_date
        self.assertIsNotNone(bookmark2.access_date)
        
        # Change to completed
        bookmark2.read_status = 'completed'
        modified(bookmark2)
        
        # The event handler should have set last_reviewed_date
        self.assertIsNotNone(bookmark2.last_reviewed_date)

    def test_archived_status(self):
        """Test that archived status updates last_reviewed_date."""
        self.bookmark.update_read_status('archived')
        self.assertEqual(self.bookmark.read_status, 'archived')
        self.assertIsNotNone(self.bookmark.last_reviewed_date)

    def test_status_transitions(self):
        """Test various status transitions."""
        # unread -> in_progress
        self.bookmark.update_read_status('in_progress')
        access_date_1 = self.bookmark.access_date
        
        # in_progress -> unread (shouldn't change access_date)
        self.bookmark.update_read_status('unread')
        self.assertEqual(self.bookmark.access_date, access_date_1)
        
        # unread -> completed (should set both dates)
        self.bookmark.update_read_status('completed')
        self.assertIsNotNone(self.bookmark.access_date)
        self.assertIsNotNone(self.bookmark.last_reviewed_date)

    def test_date_field_validation(self):
        """Test that date fields are properly validated."""
        # Dates should be datetime objects
        self.assertIsInstance(self.bookmark.access_date, datetime)
        
        # Update status and check new dates
        self.bookmark.update_read_status('completed')
        self.assertIsInstance(self.bookmark.last_reviewed_date, datetime)
        
        # Ensure dates are reasonable (not in the future)
        now = datetime.now()
        self.assertLessEqual(self.bookmark.access_date, now)
        self.assertLessEqual(self.bookmark.last_reviewed_date, now)