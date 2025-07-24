"""Tests for BookmarkPlus content type."""

from knowledge.curator.interfaces import IBookmarkPlus
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility

import unittest


class BookmarkPlusIntegrationTest(unittest.TestCase):
    """Test BookmarkPlus content type."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_ct_bookmark_plus_schema(self):
        """Test that BookmarkPlus schema is correct."""
        fti = queryUtility(IDexterityFTI, name="BookmarkPlus")
        schema = fti.lookupSchema()
        self.assertEqual(IBookmarkPlus, schema)

    def test_ct_bookmark_plus_fti(self):
        """Test that BookmarkPlus FTI is properly installed."""
        fti = queryUtility(IDexterityFTI, name="BookmarkPlus")
        self.assertTrue(fti)

    def test_ct_bookmark_plus_factory(self):
        """Test that BookmarkPlus factory is properly set."""
        fti = queryUtility(IDexterityFTI, name="BookmarkPlus")
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
            IBookmarkPlus.providedBy(obj), f"IBookmarkPlus not provided by {obj}"
        )

    def test_ct_bookmark_plus_adding(self):
        """Test that BookmarkPlus can be added."""
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-plus",
            title="Python Documentation",
            url="https://docs.python.org",
            description="Official Python documentation",
            read_status="unread",
            importance="high",
        )
        self.assertTrue(
            IBookmarkPlus.providedBy(obj), f"IBookmarkPlus not provided by {obj.id}"
        )
        # Check fields
        self.assertEqual(obj.title, "Python Documentation")
        self.assertEqual(obj.url, "https://docs.python.org")
        self.assertEqual(obj.read_status, "unread")
        self.assertEqual(obj.importance, "high")

    def test_ct_bookmark_plus_read_status_methods(self):
        """Test BookmarkPlus read status methods."""
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-status-test",
            url="https://example.com",
            read_status="unread",
        )

        # Test marking as reading
        obj.mark_as_reading()
        self.assertEqual(obj.read_status, "reading")
        self.assertIsNotNone(obj.get_reading_started_date())

        # Test marking as read
        obj.mark_as_read()
        self.assertEqual(obj.read_status, "read")
        self.assertIsNotNone(obj.get_read_date())

    def test_ct_bookmark_plus_importance_methods(self):
        """Test BookmarkPlus importance methods."""
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-importance-test",
            url="https://example.com",
            importance="medium",
            read_status="unread",
        )

        # Test updating importance
        self.assertTrue(obj.update_importance("critical"))
        self.assertEqual(obj.importance, "critical")

        # Test invalid importance
        self.assertFalse(obj.update_importance("invalid"))
        self.assertEqual(obj.importance, "critical")  # Should remain unchanged

        # Test high priority check
        self.assertTrue(obj.is_high_priority())  # unread + critical

        obj.read_status = "read"
        self.assertFalse(obj.is_high_priority())  # read + critical

    def test_ct_bookmark_plus_tag_methods(self):
        """Test BookmarkPlus tag methods."""
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-tags-test",
            url="https://example.com",
        )

        # Test adding tags
        obj.add_tag("python")
        self.assertIn("python", obj.tags)

        # Test duplicate prevention
        obj.add_tag("python")
        self.assertEqual(len(obj.tags), 1)

        # Test removing tags
        obj.add_tag("documentation")
        obj.remove_tag("python")
        self.assertNotIn("python", obj.tags)
        self.assertIn("documentation", obj.tags)

    def test_ct_bookmark_plus_embedding_methods(self):
        """Test BookmarkPlus embedding methods."""
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-embedding-test",
            url="https://example.com",
        )

        # Test embedding methods
        self.assertEqual(obj.get_embedding(), [])
        obj.update_embedding([0.5, 0.6, 0.7])
        self.assertEqual(obj.get_embedding(), [0.5, 0.6, 0.7])

    def test_ct_bookmark_plus_summary_text(self):
        """Test BookmarkPlus summary text generation."""
        from plone.app.textfield.value import RichTextValue

        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-summary-test",
            title="Test Bookmark",
            url="https://example.com",
            description="A test bookmark",
        )

        # Test without notes
        summary = obj.get_summary_text()
        self.assertIn("Test Bookmark", summary)
        self.assertIn("A test bookmark", summary)

        # Test with notes
        obj.notes = RichTextValue("Important notes about this resource")
        summary = obj.get_summary_text()
        self.assertIn("Important notes", summary)
