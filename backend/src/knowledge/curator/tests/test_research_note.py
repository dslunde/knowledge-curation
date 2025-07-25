"""Tests for Research Note content type."""

from knowledge.curator.interfaces import IResearchNote
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility
from zope.interface import Invalid
from knowledge.curator.content.validators import validate_annotated_knowledge_items

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
            IResearchNote.providedBy(obj), f"IResearchNote not provided by {obj}"
        )

    def test_ct_research_note_adding(self):
        """Test that Research Note can be added."""
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        
        # First create a Knowledge Item to annotate
        ki = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="test-ki",
            title="Test Knowledge Item",
            description="A knowledge item for testing",
            knowledge_type="conceptual",
        )
        
        obj = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="research-note",
            title="Test Research Note",
            description="A test research note",
            annotated_knowledge_items=[ki.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium",
        )
        self.assertTrue(
            IResearchNote.providedBy(obj), f"IResearchNote not provided by {obj.id}"
        )
        # Check that all fields are accessible
        self.assertEqual(obj.title, "Test Research Note")
        self.assertEqual(obj.description, "A test research note")
        self.assertEqual(obj.tags, [])
        self.assertEqual(obj.key_insights, [])
        self.assertEqual(obj.connections, [])
        self.assertEqual(len(obj.annotated_knowledge_items), 1)
        self.assertEqual(obj.annotated_knowledge_items[0], ki.UID())

    def test_ct_research_note_globally_addable(self):
        """Test that Research Note is globally addable."""
        fti = queryUtility(IDexterityFTI, name="ResearchNote")
        self.assertTrue(fti.global_allow, "Research Note is not globally addable")

    def test_ct_research_note_methods(self):
        """Test Research Note methods."""
        # Create a Knowledge Item first
        ki = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-for-methods",
            title="KI for Methods Test",
            description="Knowledge item for methods test",
            knowledge_type="conceptual",
        )
        
        obj = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="research-note-methods",
            annotated_knowledge_items=[ki.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium",
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
        obj.remove_connection("uid-1")
        self.assertNotIn("uid-1", obj.get_connections())

        # Test insight methods
        insight = obj.add_insight("Important insight", importance="high", evidence="Test data")
        self.assertEqual(len(obj.key_insights), 1)
        self.assertEqual(obj.key_insights[0]['text'], "Important insight")
        self.assertEqual(obj.key_insights[0]['importance'], "high")
        self.assertEqual(obj.key_insights[0]['evidence'], "Test data")

    def test_get_annotated_knowledge_items_details(self):
        """Test get_annotated_knowledge_items_details method."""
        # Create a Research Note
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="test-research-note",
            title="Test Research Note",
            annotation_type="explanation",
            annotated_knowledge_items=[]
        )
        
        # Test with no annotated items
        details = research_note.get_annotated_knowledge_items_details()
        self.assertEqual(details, [])
        
        # Create Knowledge Items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="knowledge-item-1",
            title="Knowledge Item 1",
            description="First test knowledge item",
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.3,
            tags=["test", "example"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="knowledge-item-2",
            title="Knowledge Item 2",
            description="Second test knowledge item",
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.5,
            tags=["demo", "sample"]
        )
        
        # Add knowledge items to research note
        research_note.annotated_knowledge_items = [ki1.UID(), ki2.UID()]
        
        # Test getting details
        details = research_note.get_annotated_knowledge_items_details()
        self.assertEqual(len(details), 2)
        
        # Check first item details
        item1_detail = details[0]
        self.assertEqual(item1_detail['uid'], ki1.UID())
        self.assertEqual(item1_detail['title'], "Knowledge Item 1")
        self.assertEqual(item1_detail['description'], "First test knowledge item")
        self.assertEqual(item1_detail['knowledge_type'], "conceptual")
        self.assertEqual(item1_detail['difficulty_level'], "beginner")
        self.assertEqual(item1_detail['mastery_threshold'], 0.7)
        self.assertEqual(item1_detail['learning_progress'], 0.3)
        self.assertEqual(item1_detail['tags'], ["test", "example"])
        self.assertEqual(item1_detail['relationship'], "explanation")
        self.assertIsNone(item1_detail['error'])
        
        # Check second item details
        item2_detail = details[1]
        self.assertEqual(item2_detail['uid'], ki2.UID())
        self.assertEqual(item2_detail['title'], "Knowledge Item 2")
        self.assertEqual(item2_detail['description'], "Second test knowledge item")
        self.assertEqual(item2_detail['knowledge_type'], "procedural")
        self.assertEqual(item2_detail['difficulty_level'], "intermediate")
        self.assertEqual(item2_detail['mastery_threshold'], 0.8)
        self.assertEqual(item2_detail['learning_progress'], 0.5)
        self.assertEqual(item2_detail['tags'], ["demo", "sample"])
        self.assertEqual(item2_detail['relationship'], "explanation")
        self.assertIsNone(item2_detail['error'])
        
        # Test with missing item
        research_note.annotated_knowledge_items.append("non-existent-uid")
        details = research_note.get_annotated_knowledge_items_details()
        self.assertEqual(len(details), 3)
        
        # Check missing item detail
        missing_detail = details[2]
        self.assertEqual(missing_detail['uid'], "non-existent-uid")
        self.assertIn("Missing", missing_detail['title'])
        self.assertEqual(missing_detail['status'], 'missing')
        self.assertEqual(missing_detail['error'], 'Knowledge Item not found')
        
        # Test with wrong content type
        wrong_type = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="wrong-type-item",
            title="Wrong Type Item"
        )
        research_note.annotated_knowledge_items = [wrong_type.UID()]
        details = research_note.get_annotated_knowledge_items_details()
        self.assertEqual(len(details), 1)
        
        wrong_detail = details[0]
        self.assertEqual(wrong_detail['uid'], wrong_type.UID())
        self.assertEqual(wrong_detail['title'], "Wrong Type Item")
        self.assertEqual(wrong_detail['status'], 'error')
        self.assertIn('Expected KnowledgeItem', wrong_detail['error'])
    
    def test_suggest_related_notes(self):
        """Test suggest_related_notes method."""
        # Create Knowledge Items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki1",
            title="Test Knowledge Item 1",
            knowledge_type="conceptual",
            tags=["physics", "quantum"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem", 
            id="ki2",
            title="Test Knowledge Item 2",
            knowledge_type="procedural",
            tags=["physics", "mechanics"]
        )
        
        ki3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki3",
            title="Test Knowledge Item 3",
            knowledge_type="factual",
            tags=["chemistry", "organic"]
        )
        
        # Create main Research Note
        main_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="main-note",
            title="Main Research Note",
            annotation_type="insight",
            annotated_knowledge_items=[ki1.UID(), ki2.UID()],
            research_question="How do quantum mechanics principles apply to everyday physics?",
            tags=["physics", "research", "quantum"]
        )
        
        # Add an author
        main_note.add_author(name="Dr. Smith", email="smith@example.com")
        
        # Test with no other notes
        suggestions = main_note.suggest_related_notes()
        self.assertEqual(len(suggestions), 0)
        
        # Create related note with shared knowledge items
        related_note1 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="related-note-1",
            title="Related Note 1",
            annotation_type="insight",  # Same type
            annotated_knowledge_items=[ki1.UID(), ki3.UID()],  # Shares ki1
            research_question="What are the quantum effects in chemical bonding?",
            tags=["quantum", "chemistry"]  # Shares "quantum" tag
        )
        
        # Create another related note with different connections
        related_note2 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="related-note-2",
            title="Related Note 2",
            annotation_type="question",  # Different type
            annotated_knowledge_items=[ki2.UID()],  # Shares ki2
            research_question="How do mechanics principles work in practice?",
            tags=["physics", "mechanics"]  # Shares "physics" tag
        )
        related_note2.add_author(name="Dr. Smith", email="smith@example.com")  # Same author
        
        # Create unrelated note
        unrelated_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="unrelated-note",
            title="Unrelated Note",
            annotation_type="example",
            annotated_knowledge_items=[ki3.UID()],  # No shared items
            research_question="What are the properties of organic compounds?",
            tags=["chemistry", "organic"]  # No shared tags
        )
        
        # Test suggestions
        suggestions = main_note.suggest_related_notes()
        
        # Should find 2 related notes, not the unrelated one
        self.assertGreaterEqual(len(suggestions), 2)
        
        # Check first suggestion (should be related_note1 - higher score)
        top_suggestion = suggestions[0]
        self.assertIn(top_suggestion['uid'], [related_note1.UID(), related_note2.UID()])
        self.assertGreater(top_suggestion['relevance_score'], 0)
        self.assertIn('connection_reasons', top_suggestion)
        self.assertIn('shared_items', top_suggestion)
        self.assertIn('score_breakdown', top_suggestion)
        
        # Verify connection reasons
        all_reasons = []
        for suggestion in suggestions:
            all_reasons.extend(suggestion['connection_reasons'])
        
        # Should have various connection reasons
        reasons_text = ' '.join(all_reasons)
        self.assertIn('Knowledge Item', reasons_text)  # Shared items
        
        # Test with research relationships
        main_note.add_builds_upon(related_note1.UID())
        related_note2.add_contradicts(main_note.UID())
        
        suggestions = main_note.suggest_related_notes()
        
        # Should still find related notes, now with additional connection reasons
        self.assertGreaterEqual(len(suggestions), 2)
        
        # Check for direct reference connections
        for suggestion in suggestions:
            if suggestion['uid'] in [related_note1.UID(), related_note2.UID()]:
                reasons_text = ' '.join(suggestion['connection_reasons'])
                if 'Direct research reference' in reasons_text:
                    # Found the direct reference connection
                    break
        else:
            self.fail("Expected to find direct research reference connection")
        
        # Test max_results parameter
        suggestions_limited = main_note.suggest_related_notes(max_results=1)
        self.assertEqual(len(suggestions_limited), 1)
        
    def test_suggest_related_notes_edge_cases(self):
        """Test edge cases for suggest_related_notes method."""
        # Create a Knowledge Item for minimal annotation
        ki_minimal = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-minimal",
            title="Minimal KI",
            description="For edge case testing",
            knowledge_type="factual",
        )
        
        # Create a note with minimal annotations
        minimal_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="minimal-note",
            title="Minimal Research Note",
            annotated_knowledge_items=[ki_minimal.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="low",
        )
        
        # Should return empty list when no other notes exist
        suggestions = minimal_note.suggest_related_notes()
        self.assertEqual(len(suggestions), 0)
        
        # Create another Knowledge Item
        ki_tagged = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-tagged",
            title="Tagged KI",
            description="For tagged notes",
            knowledge_type="conceptual",
        )
        
        # Create note with tags
        tagged_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="tagged-note",
            title="Tagged Note",
            tags=["physics", "quantum"],
            annotated_knowledge_items=[ki_tagged.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium",
        )
        
        # Create another note with same tags
        similar_tagged = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="similar-tagged",
            title="Similar Tagged Note",
            tags=["physics", "quantum", "mechanics"],
            annotated_knowledge_items=[ki_tagged.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium",
        )
        
        # Should find connection through tags
        suggestions = tagged_note.suggest_related_notes()
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['uid'], similar_tagged.UID())
        self.assertIn('tag', suggestions[0]['connection_reasons'][0].lower())
    
    def test_annotated_knowledge_items_validation(self):
        """Test validation of annotated_knowledge_items field."""
        # Test with empty list - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items([])
        self.assertIn("at least one Knowledge Item", str(cm.exception))
        
        # Test with None - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items(None)
        self.assertIn("at least one Knowledge Item", str(cm.exception))
        
        # Test with invalid type - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items("not-a-list")
        self.assertIn("must be a list", str(cm.exception))
        
        # Test with non-string UID - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items([123])
        self.assertIn("must be a string UID", str(cm.exception))
        
        # Test with empty string UID - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items([""])
        self.assertIn("Empty UID", str(cm.exception))
        
        # Test with non-existent UID - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items(["non-existent-uid"])
        self.assertIn("do not reference valid Knowledge Items", str(cm.exception))
        
        # Create a valid Knowledge Item
        ki = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="valid-ki",
            title="Valid Knowledge Item",
            description="A valid knowledge item",
            knowledge_type="conceptual",
        )
        
        # Test with valid UID - should pass
        result = validate_annotated_knowledge_items([ki.UID()])
        self.assertTrue(result)
        
        # Test with duplicate UIDs - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items([ki.UID(), ki.UID()])
        self.assertIn("Duplicate", str(cm.exception))
        
        # Create a non-Knowledge Item content
        note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="not-a-ki",
            title="Not a Knowledge Item",
            annotated_knowledge_items=[ki.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium",
        )
        
        # Test with UID pointing to wrong content type - should fail
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items([note.UID()])
        self.assertIn("do not reference valid Knowledge Items", str(cm.exception))
    
    def test_research_note_helper_methods(self):
        """Test Research Note helper methods for Knowledge Item management."""
        # Create Knowledge Items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-helper-1",
            title="Knowledge Item 1",
            description="First knowledge item",
            knowledge_type="conceptual",
            tags=["test", "helper"],
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-helper-2",
            title="Knowledge Item 2",
            description="Second knowledge item",
            knowledge_type="procedural",
            tags=["test"],
        )
        
        # Create Research Note
        note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="helper-test-note",
            title="Helper Test Note",
            annotated_knowledge_items=[ki1.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium",
        )
        
        # Test validate_annotation_requirement
        is_valid, error = note.validate_annotation_requirement()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Test get_available_knowledge_items_for_annotation
        available = note.get_available_knowledge_items_for_annotation()
        self.assertEqual(len(available), 2)
        
        # Check that already annotated items are marked
        for item in available:
            if item['uid'] == ki1.UID():
                self.assertTrue(item['already_annotated'])
            elif item['uid'] == ki2.UID():
                self.assertFalse(item['already_annotated'])
        
        # Test add_annotated_knowledge_item
        result = note.add_annotated_knowledge_item(ki2.UID())
        self.assertTrue(result)
        self.assertEqual(len(note.annotated_knowledge_items), 2)
        self.assertIn(ki2.UID(), note.annotated_knowledge_items)
        
        # Try adding the same item again - should fail
        result = note.add_annotated_knowledge_item(ki2.UID())
        self.assertFalse(result)
        self.assertEqual(len(note.annotated_knowledge_items), 2)
        
        # Try adding invalid UID - should fail
        result = note.add_annotated_knowledge_item("invalid-uid")
        self.assertFalse(result)
        self.assertEqual(len(note.annotated_knowledge_items), 2)
        
        # Test remove_annotated_knowledge_item
        result = note.remove_annotated_knowledge_item(ki2.UID())
        self.assertTrue(result)
        self.assertEqual(len(note.annotated_knowledge_items), 1)
        self.assertNotIn(ki2.UID(), note.annotated_knowledge_items)
        
        # Try removing the last item - should fail
        result = note.remove_annotated_knowledge_item(ki1.UID())
        self.assertFalse(result)
        self.assertEqual(len(note.annotated_knowledge_items), 1)
        
        # Test suggest_knowledge_items_for_annotation
        note.description = "This note is about conceptual knowledge and testing"
        suggestions = note.suggest_knowledge_items_for_annotation(limit=5)
        
        # Should suggest ki2 since ki1 is already annotated
        self.assertGreater(len(suggestions), 0)
        suggested_uids = [s['uid'] for s in suggestions]
        self.assertNotIn(ki1.UID(), suggested_uids)  # Already annotated
        
    def test_research_note_without_knowledge_items_fails(self):
        """Test that creating a Research Note without Knowledge Items fails."""
        # This test would fail at the form level in practice, but we test the validator
        note_data = {
            'title': 'Invalid Note',
            'description': 'This should fail',
            'annotated_knowledge_items': [],  # Empty list
            'annotation_type': 'general',
            'evidence_type': 'empirical',
            'confidence_level': 'medium',
        }
        
        # Validate the annotated_knowledge_items field
        with self.assertRaises(Invalid) as cm:
            validate_annotated_knowledge_items(note_data['annotated_knowledge_items'])
        
        self.assertIn("at least one Knowledge Item", str(cm.exception))
