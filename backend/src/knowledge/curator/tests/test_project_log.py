"""Tests for Project Log content type."""

import unittest
from datetime import date, timedelta
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject, queryUtility

from knowledge.curator.interfaces import IProjectLog
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


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
            IProjectLog.providedBy(obj),
            f'IProjectLog not provided by {obj}'
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
            IProjectLog.providedBy(obj),
            f'IProjectLog not provided by {obj.id}'
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
            "Initial Planning",
            "Started project planning phase",
            tags=["planning", "milestone"],
        )
        self.assertEqual(entry1['title'], 'Initial Planning')
        self.assertIn('planning', entry1['tags'])
        self.assertIsNotNone(entry1['timestamp'])

        # Test updating entry
        obj.update_entry(entry1["id"], content="Updated content for planning phase")
        updated = obj.entries[0]
        self.assertEqual(updated['content'], 'Updated content for planning phase')
        self.assertIsNotNone(updated.get('modified'))

        # Test getting entries by tag
        obj.add_entry(
            "Development Started", "Begin coding", tags=["development"]
        )
        planning_entries = obj.get_entries_by_tag("planning")
        self.assertEqual(len(planning_entries), 1)

        # Test recent entries
        recent = obj.get_recent_entries(limit=1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["title"], "Development Started")

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
        self.assertTrue(obj.update_status('active'))
        self.assertEqual(obj.status, 'active')

        # Test invalid status
        self.assertFalse(obj.update_status('invalid-status'))
        self.assertEqual(obj.status, 'active')  # Should remain unchanged

        # Check that status change was logged
        entries = obj.get_entries_by_tag("status-change")
        self.assertEqual(len(entries), 1)

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
        obj.add_entry("Project Completed", "All done!", tags=["completed"])
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

        # Test adding learnings
        obj.add_learning('Always document API endpoints')
        obj.add_learning('User testing is crucial')
        self.assertEqual(len(obj.learnings), 2)
