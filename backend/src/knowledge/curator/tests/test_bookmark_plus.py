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

    def test_ct_bookmark_plus_personal_notes(self):
        """Test BookmarkPlus personal notes field."""
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-personal-notes-test",
            title="Test Resource",
            url="https://example.com",
        )
        
        # Test empty personal notes
        self.assertIsNone(obj.personal_notes)
        
        # Test setting personal notes
        test_notes = "This resource provides excellent insights into Python best practices. I found the section on decorators particularly enlightening."
        obj.personal_notes = test_notes
        self.assertEqual(obj.personal_notes, test_notes)
        
        # Test long personal notes (should be allowed up to 10,000 characters)
        long_notes = "A" * 9999
        obj.personal_notes = long_notes
        self.assertEqual(len(obj.personal_notes), 9999)

    def test_ct_bookmark_plus_key_quotes(self):
        """Test BookmarkPlus key quotes field."""
        obj = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="bookmark-key-quotes-test",
            title="Test Resource",
            url="https://example.com",
        )
        
        # Test empty key quotes
        self.assertEqual(obj.key_quotes, [])
        
        # Test adding key quotes
        quotes = [
            "Explicit is better than implicit.",
            "Simple is better than complex.",
            "Complex is better than complicated."
        ]
        obj.key_quotes = quotes
        self.assertEqual(len(obj.key_quotes), 3)
        self.assertIn("Explicit is better than implicit.", obj.key_quotes)
        
        # Test individual quote length (up to 2000 characters)
        long_quote = "B" * 1999
        obj.key_quotes = [long_quote]
        self.assertEqual(len(obj.key_quotes[0]), 1999)
        
        # Test multiple quotes (up to 20)
        many_quotes = [f"Quote number {i}: This is an important insight from the resource." for i in range(20)]
        obj.key_quotes = many_quotes
        self.assertEqual(len(obj.key_quotes), 20)
    
    def test_calculate_learning_effectiveness_for_item(self):
        """Test calculation of learning effectiveness for specific Knowledge Items."""
        # Create Knowledge Item
        ki = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="effectiveness-ki",
            title="Effectiveness Test KI",
            knowledge_type="procedural",
            difficulty_level="intermediate",
            atomic_concepts=["programming"],
            tags=["python", "programming"]
        )
        
        # Create Bookmark+ with matching characteristics
        bookmark = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="effectiveness-bookmark",
            title="Python Programming Guide",
            description="Comprehensive Python programming resource",
            url="https://python-guide.com",
            resource_type="tutorial",
            supports_knowledge_items=[ki.UID()],
            quality_metrics={
                'accuracy': 0.9,
                'clarity': 0.8,
                'depth': 0.85,
                'currency': 0.75
            },
            tags=["python", "programming", "tutorial"]
        )
        
        # Test effectiveness calculation
        effectiveness = bookmark.calculate_learning_effectiveness_for_item(ki.UID())
        
        # Should return a score between 0 and 1
        self.assertGreaterEqual(effectiveness, 0.0)
        self.assertLessEqual(effectiveness, 1.0)
        
        # Should be relatively high due to good matches
        self.assertGreater(effectiveness, 0.6)
        
        # Test with non-supported KI
        non_supported_ki = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="non-supported-ki",
            title="Non-supported KI",
            knowledge_type="factual",
            atomic_concepts=["chemistry"],
            tags=["chemistry"]
        )
        
        non_supported_effectiveness = bookmark.calculate_learning_effectiveness_for_item(non_supported_ki.UID())
        # Should be 0 since KI is not in supports_knowledge_items
        self.assertEqual(non_supported_effectiveness, 0.0)
