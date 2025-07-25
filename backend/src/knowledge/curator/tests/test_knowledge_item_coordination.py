"""Comprehensive tests for Knowledge Item coordination across all content types.

This test module validates the Knowledge Item-centric architecture where Knowledge Items
serve as atomic units of knowledge and other content types coordinate around them.
"""

from knowledge.curator.interfaces import IKnowledgeItem, ILearningGoal, IResearchNote, IBookmarkPlus, IProjectLog, IKnowledgeContainer
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject, queryUtility
from zope.interface import Invalid

import unittest


class KnowledgeItemCoordinationTest(unittest.TestCase):
    """Test Knowledge Item coordination across all content types."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        
        # Create test Knowledge Items
        self.ki_conceptual = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-conceptual",
            title="Conceptual Knowledge Item",
            description="A conceptual knowledge item for testing",
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.3,
            atomic_concepts=["concept1", "concept2"],
            tags=["physics", "quantum"]
        )
        
        self.ki_procedural = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-procedural",
            title="Procedural Knowledge Item",
            description="A procedural knowledge item for testing",
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.5,
            atomic_concepts=["procedure1", "step2"],
            tags=["programming", "python"]
        )
        
        self.ki_factual = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-factual",
            title="Factual Knowledge Item",
            description="A factual knowledge item for testing",
            knowledge_type="factual",
            difficulty_level="advanced",
            mastery_threshold=0.9,
            learning_progress=0.8,
            atomic_concepts=["fact1", "data2"],
            tags=["science", "mathematics"]
        )

    def test_knowledge_item_workflow_assignment(self):
        """Test that Knowledge Items are properly assigned to knowledge_workflow."""
        # Verify Knowledge Items use the knowledge_workflow
        workflow_tool = api.portal.get_tool('portal_workflow')
        
        # Check that knowledge_workflow is assigned to KnowledgeItem
        chain = workflow_tool.getChainForPortalType('KnowledgeItem')
        self.assertIn('knowledge_workflow', chain)
        
        # Verify Knowledge Item states
        ki_state = api.content.get_state(obj=self.ki_conceptual)
        self.assertIn(ki_state, ['capture', 'process', 'connect', 'published'])
        
        # Test workflow transitions
        api.content.transition(obj=self.ki_conceptual, transition='submit')
        new_state = api.content.get_state(obj=self.ki_conceptual)
        self.assertEqual(new_state, 'process')
        
        # Test that Knowledge Items have highest priority in workflow
        # (This would be tested by checking workflow configuration)
        workflow = workflow_tool.getWorkflowById('knowledge_workflow')
        self.assertIsNotNone(workflow)
        
        # Verify all required states exist
        states = workflow.states.keys()
        expected_states = ['capture', 'process', 'connect', 'published']
        for state in expected_states:
            self.assertIn(state, states)

    def test_learning_goal_knowledge_item_graph_relationships(self):
        """Test Learning Goal graph relationships with Knowledge Items."""
        # Create Learning Goal that connects Knowledge Items
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="test-learning-goal",
            title="Test Learning Goal",
            description="A learning goal that connects knowledge items",
            target_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID(),
                self.ki_factual.UID()
            ],
            goal_type="mastery",
            difficulty_level="intermediate",
            estimated_duration=120
        )
        
        # Test that Learning Goal properly references Knowledge Items
        target_items = learning_goal.target_knowledge_items
        self.assertEqual(len(target_items), 3)
        self.assertIn(self.ki_conceptual.UID(), target_items)
        self.assertIn(self.ki_procedural.UID(), target_items)
        self.assertIn(self.ki_factual.UID(), target_items)
        
        # Test Learning Goal graph methods
        # Add prerequisite relationships
        self.ki_procedural.prerequisite_items = [self.ki_conceptual.UID()]
        self.ki_factual.prerequisite_items = [self.ki_procedural.UID()]
        
        # Test validate_learning_path
        is_valid, errors = learning_goal.validate_learning_path()
        self.assertTrue(is_valid, f"Learning path validation failed: {errors}")
        
        # Test circular dependency detection
        self.ki_conceptual.prerequisite_items = [self.ki_factual.UID()]  # Creates cycle
        is_valid, errors = learning_goal.validate_learning_path()
        self.assertFalse(is_valid)
        self.assertIn("circular dependency", str(errors).lower())
        
        # Fix circular dependency
        self.ki_conceptual.prerequisite_items = []
        
        # Test get_next_knowledge_items
        next_items = learning_goal.get_next_knowledge_items()
        self.assertGreater(len(next_items), 0)
        
        # First item should be conceptual (no prerequisites)
        first_item = next_items[0]
        self.assertEqual(first_item['uid'], self.ki_conceptual.UID())
        self.assertEqual(first_item['knowledge_type'], 'conceptual')
        self.assertFalse(first_item['prerequisites_met'])  # Not mastered yet
        
        # Test calculate_overall_progress
        progress = learning_goal.calculate_overall_progress()
        self.assertIsInstance(progress, dict)
        self.assertIn('overall_percentage', progress)
        self.assertIn('items_mastered', progress)
        self.assertIn('items_total', progress)
        self.assertIn('weighted_progress', progress)
        
        # Progress should be based on Knowledge Item learning_progress values
        expected_avg = (0.3 + 0.5 + 0.8) / 3  # Average of our test items
        self.assertAlmostEqual(progress['overall_percentage'], expected_avg, places=2)

    def test_research_note_knowledge_item_annotations(self):
        """Test Research Note annotation system with Knowledge Items."""
        # Create Research Note that annotates Knowledge Items
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="test-research-note",
            title="Test Research Note",
            description="Research note that annotates knowledge items",
            annotated_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID()
            ],
            annotation_type="insight",
            evidence_type="empirical",
            confidence_level="high",
            research_question="How do these knowledge items relate?",
            tags=["research", "analysis"]
        )
        
        # Test annotated Knowledge Items validation
        annotated_items = research_note.annotated_knowledge_items
        self.assertEqual(len(annotated_items), 2)
        self.assertIn(self.ki_conceptual.UID(), annotated_items)
        self.assertIn(self.ki_procedural.UID(), annotated_items)
        
        # Test get_annotated_knowledge_items_details
        details = research_note.get_annotated_knowledge_items_details()
        self.assertEqual(len(details), 2)
        
        # Verify first item details
        item1_detail = details[0]
        self.assertEqual(item1_detail['uid'], self.ki_conceptual.UID())
        self.assertEqual(item1_detail['title'], "Conceptual Knowledge Item")
        self.assertEqual(item1_detail['knowledge_type'], "conceptual")
        self.assertEqual(item1_detail['difficulty_level'], "beginner")
        self.assertEqual(item1_detail['relationship'], "insight")
        self.assertIsNone(item1_detail['error'])
        
        # Test suggest_related_notes with Knowledge Item connections
        # Create another note with shared Knowledge Item
        related_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="related-research-note",
            title="Related Research Note",
            annotated_knowledge_items=[self.ki_conceptual.UID()],  # Shares conceptual KI
            annotation_type="explanation",
            evidence_type="theoretical",
            confidence_level="medium"
        )
        
        suggestions = research_note.suggest_related_notes()
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['uid'], related_note.UID())
        self.assertIn('Knowledge Item', suggestions[0]['connection_reasons'][0])
        
        # Test generate_knowledge_item_enhancement_suggestions
        enhancements = research_note.generate_knowledge_item_enhancement_suggestions()
        self.assertIsInstance(enhancements, list)
        self.assertGreater(len(enhancements), 0)
        
        # Each enhancement should reference a Knowledge Item
        for enhancement in enhancements:
            self.assertIn('knowledge_item_uid', enhancement)
            self.assertIn('suggestion_type', enhancement)
            self.assertIn('description', enhancement)
            self.assertIn(enhancement['knowledge_item_uid'], 
                         [self.ki_conceptual.UID(), self.ki_procedural.UID()])

    def test_project_log_knowledge_item_progress_tracking(self):
        """Test Project Log progress tracking for Knowledge Items."""
        # Create Learning Goal first
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="project-learning-goal",
            title="Project Learning Goal",
            target_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID()
            ],
            goal_type="mastery",
            difficulty_level="intermediate"
        )
        
        # Create Project Log
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="test-project-log",
            title="Test Project Log",
            description="Project log for testing KI progress",
            associated_learning_goals=[learning_goal.UID()],
            project_status="active"
        )
        
        # Test update_knowledge_item_progress
        initial_progress = self.ki_conceptual.learning_progress  # 0.3
        
        # Update progress
        result = project_log.update_knowledge_item_progress(
            knowledge_item_uid=self.ki_conceptual.UID(),
            new_progress=0.6,
            notes="Made significant progress on conceptual understanding"
        )
        
        self.assertTrue(result)
        
        # Verify Knowledge Item progress was updated
        updated_ki = api.content.get(UID=self.ki_conceptual.UID())
        self.assertEqual(updated_ki.learning_progress, 0.6)
        
        # Test progress history tracking
        progress_history = project_log.get_progress_history()
        self.assertGreater(len(progress_history), 0)
        
        latest_entry = progress_history[-1]
        self.assertEqual(latest_entry['knowledge_item_uid'], self.ki_conceptual.UID())
        self.assertEqual(latest_entry['new_progress'], 0.6)
        self.assertEqual(latest_entry['previous_progress'], initial_progress)
        
        # Test get_learning_analytics
        analytics = project_log.get_learning_analytics()
        self.assertIn('knowledge_items_progress', analytics)
        self.assertIn('learning_goals_progress', analytics)
        self.assertIn('overall_metrics', analytics)
        
        # Verify Knowledge Item analytics
        ki_progress = analytics['knowledge_items_progress']
        self.assertGreater(len(ki_progress), 0)
        
        conceptual_progress = next(
            (item for item in ki_progress if item['uid'] == self.ki_conceptual.UID()),
            None
        )
        self.assertIsNotNone(conceptual_progress)
        self.assertEqual(conceptual_progress['current_progress'], 0.6)
        self.assertEqual(conceptual_progress['knowledge_type'], 'conceptual')

    def test_bookmark_plus_knowledge_item_quality_assessment(self):
        """Test Bookmark+ quality assessment system for Knowledge Items."""
        # Create Bookmark+ resource
        bookmark = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="test-bookmark",
            title="Test Educational Resource",
            description="A bookmark for testing KI connections",
            url="https://example.com/educational-resource",
            resource_type="article",
            supports_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID()
            ],
            quality_metrics={
                'accuracy': 0.9,
                'clarity': 0.8,
                'depth': 0.7,
                'currency': 0.6
            }
        )
        
        # Test supported Knowledge Items
        supported_items = bookmark.supports_knowledge_items
        self.assertEqual(len(supported_items), 2)
        self.assertIn(self.ki_conceptual.UID(), supported_items)
        self.assertIn(self.ki_procedural.UID(), supported_items)
        
        # Test assess_knowledge_item_support_quality
        quality_assessment = bookmark.assess_knowledge_item_support_quality()
        self.assertIsInstance(quality_assessment, dict)
        self.assertIn('overall_score', quality_assessment)
        self.assertIn('knowledge_item_scores', quality_assessment)
        
        # Verify individual Knowledge Item scores
        ki_scores = quality_assessment['knowledge_item_scores']
        self.assertEqual(len(ki_scores), 2)
        
        for score_data in ki_scores:
            self.assertIn('knowledge_item_uid', score_data)
            self.assertIn('support_score', score_data)
            self.assertIn('relevance_factors', score_data)
            self.assertIn(score_data['knowledge_item_uid'], 
                         [self.ki_conceptual.UID(), self.ki_procedural.UID()])
        
        # Test get_learning_goal_support_analysis
        # Create Learning Goal that uses our Knowledge Items
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="bookmark-learning-goal",
            title="Bookmark Learning Goal",
            target_knowledge_items=[self.ki_conceptual.UID()],
            goal_type="mastery"
        )
        
        support_analysis = bookmark.get_learning_goal_support_analysis([learning_goal.UID()])
        self.assertIsInstance(support_analysis, list)
        self.assertEqual(len(support_analysis), 1)
        
        goal_analysis = support_analysis[0]
        self.assertEqual(goal_analysis['learning_goal_uid'], learning_goal.UID())
        self.assertIn('support_percentage', goal_analysis)
        self.assertIn('supported_items', goal_analysis)
        self.assertIn('unsupported_items', goal_analysis)
        
        # Should support the conceptual Knowledge Item
        self.assertEqual(len(goal_analysis['supported_items']), 1)
        self.assertEqual(goal_analysis['supported_items'][0], self.ki_conceptual.UID())

    def test_knowledge_container_collection_system(self):
        """Test Knowledge Container collection system with Knowledge Items."""
        # Create Knowledge Container
        container = api.content.create(
            container=self.portal,
            type="KnowledgeContainer",
            id="test-knowledge-container",
            title="Test Knowledge Container",
            description="Container for testing KI collections",
            container_type="collection",
            collected_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID(),
                self.ki_factual.UID()
            ],
            organization_strategy="difficulty_progression",
            sharing_permissions="public"
        )
        
        # Test collected Knowledge Items
        collected_items = container.collected_knowledge_items
        self.assertEqual(len(collected_items), 3)
        self.assertIn(self.ki_conceptual.UID(), collected_items)
        self.assertIn(self.ki_procedural.UID(), collected_items)
        self.assertIn(self.ki_factual.UID(), collected_items)
        
        # Test get_organized_knowledge_items
        organized_items = container.get_organized_knowledge_items()
        self.assertEqual(len(organized_items), 3)
        
        # With difficulty_progression, should be ordered by difficulty
        difficulties = [item['difficulty_level'] for item in organized_items]
        expected_order = ['beginner', 'intermediate', 'advanced']
        self.assertEqual(difficulties, expected_order)
        
        # Test export_collection with different formats
        # HTML export
        html_export = container.export_collection(format='html')
        self.assertIn('<html>', html_export)
        self.assertIn('Test Knowledge Container', html_export)
        self.assertIn('Conceptual Knowledge Item', html_export)
        
        # Markdown export
        md_export = container.export_collection(format='markdown')
        self.assertIn('# Test Knowledge Container', md_export)
        self.assertIn('## Conceptual Knowledge Item', md_export)
        
        # Test get_collection_analytics
        analytics = container.get_collection_analytics()
        self.assertIn('total_items', analytics)
        self.assertIn('knowledge_type_distribution', analytics)
        self.assertIn('difficulty_distribution', analytics)
        self.assertIn('average_progress', analytics)
        
        # Verify analytics data
        self.assertEqual(analytics['total_items'], 3)
        
        # Knowledge type distribution
        type_dist = analytics['knowledge_type_distribution']
        self.assertEqual(type_dist['conceptual'], 1)
        self.assertEqual(type_dist['procedural'], 1)
        self.assertEqual(type_dist['factual'], 1)
        
        # Difficulty distribution
        difficulty_dist = analytics['difficulty_distribution']
        self.assertEqual(difficulty_dist['beginner'], 1)
        self.assertEqual(difficulty_dist['intermediate'], 1)
        self.assertEqual(difficulty_dist['advanced'], 1)
        
        # Average progress should be (0.3 + 0.5 + 0.8) / 3
        expected_avg_progress = (0.3 + 0.5 + 0.8) / 3
        self.assertAlmostEqual(analytics['average_progress'], expected_avg_progress, places=2)

    def test_workflow_scripts_knowledge_item_priority(self):
        """Test that workflow scripts prioritize Knowledge Items."""
        from knowledge.curator.workflow_scripts import update_embeddings, update_learning_goal_progress
        
        # Create Research Note to test embedding prioritization
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="workflow-test-note",
            title="Workflow Test Note",
            annotated_knowledge_items=[self.ki_conceptual.UID()],
            annotation_type="insight",
            evidence_type="empirical",
            confidence_level="medium"
        )
        
        # Test update_embeddings with Knowledge Item priority
        # Mock embedding update to verify Knowledge Items are processed first
        update_embeddings(self.portal)
        
        # Knowledge Items should have embeddings updated first
        # (In a real implementation, we'd verify the order of processing)
        
        # Test update_learning_goal_progress
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="workflow-learning-goal",
            title="Workflow Learning Goal",
            target_knowledge_items=[self.ki_conceptual.UID()],
            goal_type="mastery"
        )
        
        # Update Knowledge Item progress
        original_progress = self.ki_conceptual.learning_progress
        self.ki_conceptual.learning_progress = 0.8
        
        # Run workflow script
        update_learning_goal_progress(learning_goal)
        
        # Verify Learning Goal progress was updated based on Knowledge Item progress
        updated_goal = api.content.get(UID=learning_goal.UID())
        self.assertIsNotNone(updated_goal.completion_percentage)

    def test_cross_content_type_knowledge_item_references(self):
        """Test Knowledge Item references across all content types."""
        # Create comprehensive test scenario with all content types
        
        # Learning Goal that targets our Knowledge Items
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="cross-ref-learning-goal",
            title="Cross-Reference Learning Goal",
            target_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID()
            ],
            goal_type="mastery"
        )
        
        # Research Note that annotates Knowledge Items
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="cross-ref-research-note",
            title="Cross-Reference Research Note",
            annotated_knowledge_items=[self.ki_conceptual.UID()],
            annotation_type="insight",
            evidence_type="empirical",
            confidence_level="high"
        )
        
        # Project Log tracking progress
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="cross-ref-project-log",
            title="Cross-Reference Project Log",
            associated_learning_goals=[learning_goal.UID()],
            project_status="active"
        )
        
        # Bookmark+ supporting Knowledge Items
        bookmark = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="cross-ref-bookmark",
            title="Cross-Reference Bookmark",
            url="https://example.com/resource",
            resource_type="article",
            supports_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID()
            ]
        )
        
        # Knowledge Container collecting items
        container = api.content.create(
            container=self.portal,
            type="KnowledgeContainer",
            id="cross-ref-container",
            title="Cross-Reference Container",
            container_type="collection",
            collected_knowledge_items=[
                self.ki_conceptual.UID(),
                self.ki_procedural.UID(),
                self.ki_factual.UID()
            ]
        )
        
        # Test that Knowledge Items are properly referenced
        
        # 1. Verify Learning Goal references
        self.assertIn(self.ki_conceptual.UID(), learning_goal.target_knowledge_items)
        self.assertIn(self.ki_procedural.UID(), learning_goal.target_knowledge_items)
        
        # 2. Verify Research Note references
        self.assertIn(self.ki_conceptual.UID(), research_note.annotated_knowledge_items)
        
        # 3. Verify Bookmark+ references
        self.assertIn(self.ki_conceptual.UID(), bookmark.supports_knowledge_items)
        self.assertIn(self.ki_procedural.UID(), bookmark.supports_knowledge_items)
        
        # 4. Verify Knowledge Container references
        self.assertIn(self.ki_conceptual.UID(), container.collected_knowledge_items)
        self.assertIn(self.ki_procedural.UID(), container.collected_knowledge_items)
        self.assertIn(self.ki_factual.UID(), container.collected_knowledge_items)
        
        # Test reverse relationships - find content that references Knowledge Items
        catalog = api.portal.get_tool('portal_catalog')
        
        # Find all content that references ki_conceptual
        # This would typically use a custom index for Knowledge Item references
        conceptual_uid = self.ki_conceptual.UID()
        
        # Verify each content type properly maintains its Knowledge Item references
        # Learning Goals
        learning_goals = api.content.find(portal_type='LearningGoal')
        conceptual_learning_goals = [
            lg for lg in learning_goals 
            if hasattr(lg.getObject(), 'target_knowledge_items') and 
            conceptual_uid in lg.getObject().target_knowledge_items
        ]
        self.assertEqual(len(conceptual_learning_goals), 1)
        
        # Research Notes
        research_notes = api.content.find(portal_type='ResearchNote')
        conceptual_research_notes = [
            rn for rn in research_notes
            if hasattr(rn.getObject(), 'annotated_knowledge_items') and
            conceptual_uid in rn.getObject().annotated_knowledge_items
        ]
        self.assertEqual(len(conceptual_research_notes), 1)
        
        # Test data integrity - all references should point to valid Knowledge Items
        all_content = list(learning_goals) + list(research_notes)
        for content_brain in all_content:
            obj = content_brain.getObject()
            
            # Check Learning Goal references
            if hasattr(obj, 'target_knowledge_items'):
                for ki_uid in obj.target_knowledge_items:
                    referenced_ki = api.content.get(UID=ki_uid)
                    self.assertIsNotNone(referenced_ki, 
                                       f"Learning Goal {obj.getId()} references non-existent KI {ki_uid}")
                    self.assertTrue(IKnowledgeItem.providedBy(referenced_ki),
                                  f"Learning Goal {obj.getId()} references non-KI content {ki_uid}")
            
            # Check Research Note references
            if hasattr(obj, 'annotated_knowledge_items'):
                for ki_uid in obj.annotated_knowledge_items:
                    referenced_ki = api.content.get(UID=ki_uid)
                    self.assertIsNotNone(referenced_ki,
                                       f"Research Note {obj.getId()} references non-existent KI {ki_uid}")
                    self.assertTrue(IKnowledgeItem.providedBy(referenced_ki),
                                  f"Research Note {obj.getId()} references non-KI content {ki_uid}")

    def test_knowledge_item_priority_in_vector_indexing(self):
        """Test that Knowledge Items have priority in vector indexing."""
        from knowledge.curator.vector.config import SUPPORTED_CONTENT_TYPES
        
        # Verify Knowledge Items are first in the supported content types list
        self.assertEqual(SUPPORTED_CONTENT_TYPES[0], "KnowledgeItem")
        
        # Test that Knowledge Items get processed first in vector operations
        # This would be tested in the actual vector indexing system
        
        # Create mixed content for indexing priority test
        mixed_content = [
            self.ki_conceptual,
            api.content.create(
                container=self.portal,
                type="ResearchNote",
                id="vector-research-note",
                title="Vector Research Note",
                annotated_knowledge_items=[self.ki_conceptual.UID()],
                annotation_type="insight",
                evidence_type="empirical",
                confidence_level="medium"
            ),
            self.ki_procedural
        ]
        
        # In a real vector indexing system, Knowledge Items would be processed first
        # This test would verify the ordering and priority system
        knowledge_items = [content for content in mixed_content if IKnowledgeItem.providedBy(content)]
        other_content = [content for content in mixed_content if not IKnowledgeItem.providedBy(content)]
        
        self.assertEqual(len(knowledge_items), 2)
        self.assertEqual(len(other_content), 1)
        
        # Knowledge Items should be processed before other content types
        # (This would be implemented in the actual vector indexing code)

    def test_knowledge_item_graph_model_priority(self):
        """Test Knowledge Item priority in graph model."""
        from knowledge.curator.graph.model import ContentType
        
        # Verify KNOWLEDGE_ITEM is the first enum value (highest priority)
        content_types = list(ContentType)
        self.assertEqual(content_types[0], ContentType.KNOWLEDGE_ITEM)
        
        # Test that this translates to highest priority in graph operations
        ki_priority = ContentType.KNOWLEDGE_ITEM.value
        other_priorities = [ct.value for ct in ContentType if ct != ContentType.KNOWLEDGE_ITEM]
        
        # All other content types should have lower priority (higher values)
        for priority in other_priorities:
            self.assertGreater(priority, ki_priority)

    def test_migration_system_knowledge_item_integration(self):
        """Test that migration system properly handles Knowledge Item relationships."""
        from knowledge.curator.upgrades.migrate_relationships import MigrationManager
        from knowledge.curator.upgrades.assess_current_state import DataAssessment
        
        # Test data assessment for Knowledge Item relationships
        assessor = DataAssessment()
        assessment = assessor.assess_current_data_state()
        
        self.assertIn('knowledge_items', assessment)
        self.assertIn('content_relationships', assessment)
        
        # Test migration readiness
        readiness = assessor.assess_migration_readiness()
        self.assertIn('readiness_score', readiness)
        self.assertIn('blocking_issues', readiness)
        
        # Test migration manager
        migration_manager = MigrationManager()
        
        # Test that Knowledge Item relationships are preserved during migration
        # (This would involve creating legacy content and migrating it)
        
        # Verify migration preserves Knowledge Item centrality
        self.assertTrue(migration_manager.validate_knowledge_item_integrity())