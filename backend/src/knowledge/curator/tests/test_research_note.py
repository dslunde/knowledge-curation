"""Tests for Research Note content type."""

from knowledge.curator.interfaces import IResearchNote
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class ResearchNoteIntegrationTest(unittest.TestCase):
    """Test Research Note content type."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_ct_research_note_schema(self):
        """Test that Research Note schema is correct."""
        fti = queryUtility(IDexterityFTI, name="ResearchNote")
        schema = fti.lookupSchema()
        self.assertEqual(IResearchNote, schema)

    def test_ct_research_note_fti(self):
        """Test that Research Note FTI is properly installed."""
        fti = queryUtility(IDexterityFTI, name="ResearchNote")
        self.assertTrue(fti)

    def test_ct_research_note_factory(self):
        """Test that Research Note factory is properly set."""
        fti = queryUtility(IDexterityFTI, name="ResearchNote")
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
<<<<<<< HEAD
            IResearchNote.providedBy(obj), f"IResearchNote not provided by {obj}"
=======
            IResearchNote.providedBy(obj),
            f'IResearchNote not provided by {obj}'
>>>>>>> fixing_linting_and_tests
        )

    def test_ct_research_note_adding(self):
        """Test that Research Note can be added."""
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="research-note",
            title="Test Research Note",
            description="A test research note",
        )
        self.assertTrue(
<<<<<<< HEAD
            IResearchNote.providedBy(obj), f"IResearchNote not provided by {obj.id}"
=======
            IResearchNote.providedBy(obj),
            f'IResearchNote not provided by {obj.id}'
>>>>>>> fixing_linting_and_tests
        )
        # Check that all fields are accessible
        self.assertEqual(obj.title, "Test Research Note")
        self.assertEqual(obj.description, "A test research note")
        self.assertEqual(obj.tags, [])
        self.assertEqual(obj.key_insights, [])
        self.assertEqual(obj.connections, [])

    def test_ct_research_note_globally_addable(self):
        """Test that Research Note is globally addable."""
        fti = queryUtility(IDexterityFTI, name="ResearchNote")
        self.assertTrue(fti.global_allow, "Research Note is not globally addable")

    def test_ct_research_note_methods(self):
        """Test Research Note methods."""
        obj = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="research-note-methods",
        )

        # Test embedding methods
        self.assertEqual(obj.get_embedding(), [])
        obj.update_embedding([0.1, 0.2, 0.3])
        self.assertEqual(obj.get_embedding(), [0.1, 0.2, 0.3])

        # Test connection methods
        obj.add_connection("uid-1")
        self.assertIn("uid-1", obj.get_connections())
        obj.add_connection("uid-2")
        self.assertEqual(len(obj.get_connections()), 2)
<<<<<<< HEAD
        obj.remove_connection("uid-1")
        self.assertNotIn("uid-1", obj.get_connections())

        # Test insight methods
        obj.add_insight("Important insight")
        self.assertIn("Important insight", obj.key_insights)
=======
        obj.remove_connection('uid-1')
        self.assertNotIn('uid-1', obj.get_connections())

        # Test insight methods
        obj.add_insight('Important insight')
        self.assertIn('Important insight', obj.key_insights)
>>>>>>> fixing_linting_and_tests
