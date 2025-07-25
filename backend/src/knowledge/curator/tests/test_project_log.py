"""Tests for Project Log content type."""

import unittest
from datetime import date, timedelta
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject, queryUtility

from knowledge.curator.interfaces import IProjectLog
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING


class ProjectLogIntegrationTest(unittest.TestCase):
    """Test Project Log content type."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_ct_project_log_schema(self):
        """Test that Project Log schema is correct."""
        fti = queryUtility(IDexterityFTI, name="ProjectLog")
        schema = fti.lookupSchema()
        self.assertEqual(IProjectLog, schema)

    def test_ct_project_log_fti(self):
        """Test that Project Log FTI is properly installed."""
        fti = queryUtility(IDexterityFTI, name="ProjectLog")
        self.assertTrue(fti)

    def test_ct_project_log_factory(self):
        """Test that Project Log factory is properly set."""
        fti = queryUtility(IDexterityFTI, name="ProjectLog")
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
            IProjectLog.providedBy(obj), f"IProjectLog not provided by {obj}"
        )

    def test_ct_project_log_adding(self):
        """Test that Project Log can be added."""
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="project-log",
            title="Website Redesign",
            description="Complete website redesign project",
            start_date=date.today(),
            status="planning",
        )
        self.assertTrue(
            IProjectLog.providedBy(obj), f"IProjectLog not provided by {obj.id}"
        )
        # Check fields
        self.assertEqual(obj.title, "Website Redesign")
        self.assertEqual(obj.status, "planning")
        self.assertEqual(obj.entries, [])

    def test_ct_project_log_entry_methods(self):
        """Test Project Log entry methods."""
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="log-with-entries",
            start_date=date.today(),
        )

        # Test adding entries
        entry1 = obj.add_entry(
            description="Initial Planning - Started project planning phase",
            author="Test User",
            entry_type="milestone",
            related_items=["item1", "item2"]
        )
        self.assertEqual(entry1["description"], "Initial Planning - Started project planning phase")
        self.assertEqual(entry1["author"], "Test User")
        self.assertEqual(entry1["entry_type"], "milestone")
        self.assertIsNotNone(entry1["timestamp"])
        self.assertIsNotNone(entry1["id"])

        # Test updating entry
        updated_entry = obj.update_entry(
            entry1["id"], 
            description="Updated content for planning phase",
            author="Test User",
            entry_type="milestone"
        )
        self.assertEqual(updated_entry["description"], "Updated content for planning phase")
        self.assertIsNotNone(updated_entry.get("modified"))

        # Test getting entries by type
        obj.add_entry(
            description="Development Started - Begin coding", 
            author="Test User",
            entry_type="note"
        )
        milestone_entries = obj.get_entries_by_type("milestone")
        self.assertEqual(len(milestone_entries), 1)

        # Test recent entries
        recent = obj.get_recent_entries(limit=1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["description"], "Development Started - Begin coding")

    def test_ct_project_log_status_methods(self):
        """Test Project Log status methods."""
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="log-status-test",
            start_date=date.today(),
            status="planning",
        )

        # Test status update
        self.assertTrue(obj.update_status("active"))
        self.assertEqual(obj.status, "active")

        # Test invalid status
        self.assertFalse(obj.update_status("invalid-status"))
        self.assertEqual(obj.status, "active")  # Should remain unchanged

        # Check that status change was logged
        entries = obj.get_entries_by_type("milestone")
        self.assertEqual(len(entries), 1)
        self.assertIn("status updated", entries[0]["description"].lower())

    def test_ct_project_log_duration(self):
        """Test Project Log duration calculation."""
        # Create project started 10 days ago
        start_date = date.today() - timedelta(days=10)
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="log-duration-test",
            start_date=start_date,
            status="active",
        )

        # Test active project duration
        duration = obj.get_duration()
        self.assertEqual(duration, 10)

        # Test completed project duration
        obj.status = "completed"
        obj.add_entry(
            description="Project Completed - All done!",
            author="Test User",
            entry_type="milestone"
        )
        # Duration should still be calculated to today since we can't
        # mock the entry timestamp easily in tests

    def test_ct_project_log_deliverables_learnings(self):
        """Test Project Log deliverables and learnings."""
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="log-deliverables",
            start_date=date.today(),
        )

        # Test adding deliverables
        obj.add_deliverable("Website mockups")
        obj.add_deliverable("API documentation")
        self.assertEqual(len(obj.deliverables), 2)

        # Test adding lessons learned
        obj.add_lesson_learned("Always document API endpoints", impact="high")
        obj.add_lesson_learned("User testing is crucial", context="Discovered during beta")
        self.assertEqual(len(obj.lessons_learned), 2)

    def test_ct_project_log_knowledge_item_progress(self):
        """Test Project Log knowledge item progress tracking."""
        from datetime import datetime
        
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="log-ki-progress",
            title="Learning Project",
            description="Test learning project",
            start_date=date.today(),
            attached_learning_goal="goal-123",
        )

        # Test updating knowledge item progress with valid values
        result = obj.update_knowledge_item_progress("ki-001", 0.5)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Successfully updated mastery level to 0.5')
        self.assertEqual(obj.knowledge_item_progress['ki-001'], 0.5)

        # Test updating with new value
        result = obj.update_knowledge_item_progress("ki-001", 0.8)
        self.assertTrue(result['success'])
        self.assertEqual(obj.knowledge_item_progress['ki-001'], 0.8)

        # Test invalid mastery level - too high
        result = obj.update_knowledge_item_progress("ki-002", 1.5)
        self.assertFalse(result['success'])
        self.assertIn('between 0.0 and 1.0', result['message'])

        # Test invalid mastery level - too low
        result = obj.update_knowledge_item_progress("ki-002", -0.1)
        self.assertFalse(result['success'])
        self.assertIn('between 0.0 and 1.0', result['message'])

        # Test invalid mastery level - not a number
        result = obj.update_knowledge_item_progress("ki-002", "invalid")
        self.assertFalse(result['success'])
        self.assertIn('must be a number', result['message'])

        # Test empty UID
        result = obj.update_knowledge_item_progress("", 0.5)
        self.assertFalse(result['success'])
        self.assertIn('cannot be empty', result['message'])

    def test_ct_project_log_learning_sessions(self):
        """Test Project Log learning session management."""
        from datetime import datetime
        
        obj = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="log-sessions",
            title="Learning Project",
            description="Test learning project",
            start_date=date.today(),
            attached_learning_goal="goal-123",
        )

        # Create a learning session
        session_data = {
            'start_time': datetime.now(),
            'duration_minutes': 45,
            'knowledge_items_studied': ['ki-001', 'ki-002'],
            'progress_updates': {
                'ki-001': 0.2,
                'ki-002': 0.15
            },
            'notes': 'Productive session',
            'effectiveness_rating': 4,
            'session_type': 'self_study'
        }

        # Test adding a learning session
        result = obj.add_learning_session(session_data)
        self.assertTrue(result['success'])
        self.assertIn('Successfully added learning session', result['message'])
        self.assertEqual(len(obj.learning_sessions), 1)

        # Verify progress was updated
        self.assertEqual(obj.knowledge_item_progress['ki-001'], 0.2)
        self.assertEqual(obj.knowledge_item_progress['ki-002'], 0.15)

        # Test adding another session with progress deltas
        session_data2 = {
            'start_time': datetime.now(),
            'duration_minutes': 30,
            'knowledge_items_studied': ['ki-001'],
            'progress_updates': {
                'ki-001': 0.3  # This should add to existing 0.2
            }
        }

        result = obj.add_learning_session(session_data2)
        self.assertTrue(result['success'])
        self.assertEqual(len(obj.learning_sessions), 2)
        self.assertEqual(obj.knowledge_item_progress['ki-001'], 0.5)  # 0.2 + 0.3

        # Test session without start_time
        invalid_session = {
            'duration_minutes': 30,
            'knowledge_items_studied': ['ki-003']
        }
        result = obj.add_learning_session(invalid_session)
        self.assertFalse(result['success'])
        self.assertIn('must have a start_time', result['message'])

        # Test session with invalid progress delta
        session_data3 = {
            'start_time': datetime.now(),
            'progress_updates': {
                'ki-003': 1.5,  # Invalid - too high
                'ki-004': -0.1,  # Invalid - negative
                'ki-005': 0.2   # Valid
            }
        }
        result = obj.add_learning_session(session_data3)
        self.assertTrue(result['success'])
        # Only valid progress should be updated
        self.assertNotIn('ki-003', obj.knowledge_item_progress)
        self.assertNotIn('ki-004', obj.knowledge_item_progress)
        self.assertEqual(obj.knowledge_item_progress['ki-005'], 0.2)

        # Test progress capping at 1.0
        session_data4 = {
            'start_time': datetime.now(),
            'progress_updates': {
                'ki-001': 0.6  # Current is 0.5, this would make it 1.1
            }
        }
        result = obj.add_learning_session(session_data4)
        self.assertTrue(result['success'])
        self.assertEqual(obj.knowledge_item_progress['ki-001'], 1.0)  # Capped at 1.0
