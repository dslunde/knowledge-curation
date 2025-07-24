"""Integration tests for the complete spaced repetition system."""

import unittest
from datetime import datetime, timedelta
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from knowledge.curator.repetition.utilities import ReviewUtilities


class TestSpacedRepetitionSystem(unittest.TestCase):
    """Test the complete spaced repetition system integration."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        # Create test content
        self.folder = api.content.create(
            container=self.portal,
            type='Folder',
            title='Test Folder'
        )

        # Create multiple items for testing
        self.items = []
        for i in range(5):
            item = api.content.create(
                container=self.folder,
                type='ResearchNote',
                title=f'Research Note {i+1}',
                description=f'Description for note {i+1}',
                key_findings=f'Key findings for note {i+1}'
            )
            self.items.append(item)

    def test_review_workflow(self):
        """Test complete review workflow."""
        # Get initial review queue
        due_items = ReviewUtilities.get_items_due_for_review()

        # All new items should be due
        self.assertEqual(len(due_items), 5)

        # Perform a review on first item
        first_item = self.items[0]
        result = first_item.update_review(quality=4, time_spent=60)

        # Check review was recorded
        self.assertEqual(first_item.repetitions, 1)
        self.assertEqual(first_item.interval, 1)
        self.assertIsNotNone(first_item.last_review)
        self.assertIsNotNone(first_item.next_review)

        # Check it's no longer in immediate review queue
        due_items = ReviewUtilities.get_items_due_for_review()
        due_uids = [item['uid'] for item in due_items]
        self.assertNotIn(first_item.UID(), due_uids)

    def test_review_scheduling(self):
        """Test review scheduling and intervals."""
        item = self.items[0]

        # First review - quality 4
        item.update_review(quality=4)
        self.assertEqual(item.interval, 1)

        # Simulate time passing and second review
        item.last_review = datetime.now() - timedelta(days=2)
        item.next_review = datetime.now() - timedelta(days=1)
        item.update_review(quality=4)
        self.assertEqual(item.interval, 6)  # Second interval

        # Third review with perfect score
        item.last_review = datetime.now() - timedelta(days=7)
        item.next_review = datetime.now() - timedelta(days=1)
        item.update_review(quality=5)
        self.assertGreater(item.interval, 6)  # Should increase

    def test_adaptive_scheduling(self):
        """Test adaptive scheduling based on performance."""
        # Create review history
        for i, item in enumerate(self.items[:3]):
            # Different performance levels
            quality = 3 + i  # 3, 4, 5
            item.update_review(quality=quality, time_spent=60)

        # Get adaptive schedule
        schedule = ReviewUtilities.get_adaptive_schedule()

        self.assertIn('performance', schedule)
        self.assertIn('workload_forecast', schedule)
        self.assertIn('optimal_times', schedule)
        self.assertIn('recommendations', schedule)

    def test_at_risk_detection(self):
        """Test detection of items at risk of being forgotten."""
        item = self.items[0]

        # Create an overdue item
        item.update_review(quality=4)
        item.last_review = datetime.now() - timedelta(days=20)
        item.next_review = datetime.now() - timedelta(days=10)
        item.interval = 5

        # Get at-risk items
        at_risk = ReviewUtilities.get_items_at_risk(retention_threshold=0.8)

        # Should include our overdue item
        at_risk_uids = [i['uid'] for i in at_risk]
        self.assertIn(item.UID(), at_risk_uids)

        # Check risk level
        risk_item = next(i for i in at_risk if i['uid'] == item.UID())
        self.assertIn(risk_item['risk_level'], ['high', 'critical'])

    def test_bulk_operations(self):
        """Test bulk rescheduling operations."""
        # Review all items
        for item in self.items:
            item.update_review(quality=3)

        # Bulk reschedule to optimal
        uids = [item.UID() for item in self.items]
        results = ReviewUtilities.bulk_reschedule(uids, strategy='optimal')

        self.assertEqual(len(results['success']), 5)
        self.assertEqual(len(results['failed']), 0)

        # Check all items have new review dates
        for item in self.items:
            self.assertIsNotNone(item.next_review)

    def test_performance_tracking(self):
        """Test performance tracking over time."""
        # Create review history with varying performance
        item = self.items[0]

        # Simulate multiple reviews
        qualities = [3, 4, 2, 4, 5, 4, 3, 5]
        for i, quality in enumerate(qualities):
            # Backdate the review
            item.update_review(quality=quality, time_spent=60 + i*10)
            if i < len(qualities) - 1:
                # Simulate time passing
                item.last_review = datetime.now() - timedelta(days=20-i*2)

        # Get performance stats
        stats = item.get_review_stats()

        self.assertEqual(stats['total_reviews'], len(qualities))
        self.assertGreater(stats['average_quality'], 3)
        self.assertGreater(stats['success_rate'], 70)

        # Check current streak (last 3 were successful)
        self.assertGreaterEqual(stats['current_streak'], 3)

    def test_review_interface_data(self):
        """Test data preparation for review interface."""
        # Prepare some items
        for i, item in enumerate(self.items[:3]):
            if i > 0:
                # Make some items have reviews
                item.update_review(quality=4)
                item.last_review = datetime.now() - timedelta(days=i+1)
                item.next_review = datetime.now() - timedelta(days=1)

        # Get queue data
        due_items = ReviewUtilities.get_items_due_for_review()

        # Check data structure
        for item_data in due_items:
            self.assertIn('uid', item_data)
            self.assertIn('title', item_data)
            self.assertIn('sr_data', item_data)
            self.assertIn('urgency_score', item_data)

            # Check SR data
            sr_data = item_data['sr_data']
            self.assertIn('retention_score', sr_data)
            self.assertIn('mastery_level', sr_data)

    def test_session_management(self):
        """Test learning session creation and management."""
        # Review some items to create variety
        self.items[0].update_review(quality=5)  # Easy
        self.items[1].update_review(quality=3)  # Hard
        self.items[2].update_review(quality=4)  # Medium

        # Make them due
        for item in self.items[:3]:
            item.next_review = datetime.now() - timedelta(days=1)

        # Get user settings (with defaults)
        user = api.user.get_current()
        member = api.user.get(user.getId())
        settings = {
            'daily_review_limit': 20,
            'review_order': 'urgency',
            'session_duration': 10,  # 10 minutes
            'break_interval': 5
        }

        # Create a session
        from knowledge.curator.repetition import ReviewScheduler
        items_data = ReviewUtilities.get_items_due_for_review()
        session = ReviewScheduler.create_learning_session(
            items_data, settings, 'mixed'
        )

        self.assertIn('items', session)
        self.assertIn('breaks', session)
        self.assertIn('metadata', session)
        self.assertEqual(session['type'], 'mixed')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSpacedRepetitionSystem))
    return suite
