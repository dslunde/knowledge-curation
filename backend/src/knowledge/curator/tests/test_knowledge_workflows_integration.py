"""Integration tests for Knowledge Item workflows and cross-content type coordination.

This module tests the complete workflows and integration between different content types
with Knowledge Items serving as the central coordination point.
"""

from knowledge.curator.interfaces import (
    IKnowledgeItem, ILearningGoal, IResearchNote, 
    IBookmarkPlus, IProjectLog, IKnowledgeContainer
)
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from datetime import datetime, date
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

import unittest


class TestKnowledgeWorkflows(unittest.TestCase):
    """Integration tests for Knowledge Item workflows."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Set up comprehensive test environment."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        
        # Create Knowledge Items representing a learning domain
        self.ki_foundations = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-foundations",
            title="Programming Foundations",
            description="Basic programming concepts and principles",
            content=RichTextValue("Core programming concepts including variables, functions, and control structures", "text/plain", "text/html"),
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.0,
            atomic_concepts=["variables", "functions", "loops", "conditionals"],
            tags=["programming", "basics", "foundations"]
        )
        
        self.ki_oop = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-oop",
            title="Object-Oriented Programming",
            description="Object-oriented programming principles and patterns",
            content=RichTextValue("Classes, objects, inheritance, polymorphism, and encapsulation", "text/plain", "text/html"),
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.0,
            prerequisite_items=[self.ki_foundations.UID()],
            atomic_concepts=["classes", "objects", "inheritance", "polymorphism"],
            tags=["programming", "oop", "design"]
        )
        
        self.ki_patterns = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ki-patterns",
            title="Design Patterns",
            description="Common software design patterns and their applications",
            content=RichTextValue("Creational, structural, and behavioral design patterns", "text/plain", "text/html"),
            knowledge_type="metacognitive",
            difficulty_level="advanced",
            mastery_threshold=0.9,
            learning_progress=0.0,
            prerequisite_items=[self.ki_oop.UID()],
            atomic_concepts=["singleton", "factory", "observer", "strategy"],
            tags=["programming", "patterns", "architecture"]
        )
        
        # Create Learning Goal that connects these Knowledge Items
        self.learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="software-mastery-goal",
            title="Software Development Mastery",
            description="Master software development from foundations to advanced patterns",
            target_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID(),
                self.ki_patterns.UID()
            ],
            starting_knowledge_item=self.ki_foundations.UID(),
            goal_type="comprehensive",
            difficulty_level="progressive",
            estimated_duration=180  # 3 months
        )
        
        # Set up knowledge item connections in the learning goal
        self.learning_goal.knowledge_item_connections = PersistentList([
            PersistentMapping({
                'source_item_uid': self.ki_foundations.UID(),
                'target_item_uid': self.ki_oop.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.9,
                'mastery_requirement': 0.7
            }),
            PersistentMapping({
                'source_item_uid': self.ki_oop.UID(),
                'target_item_uid': self.ki_patterns.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            })
        ])

    def test_knowledge_item_workflow_states(self):
        """Test that Knowledge Items progress through workflow states correctly."""
        # Initially in 'capture' state
        initial_state = api.content.get_state(obj=self.ki_foundations)
        self.assertEqual(initial_state, 'capture')
        
        # Transition to 'process' state
        api.content.transition(obj=self.ki_foundations, transition='submit')
        process_state = api.content.get_state(obj=self.ki_foundations)
        self.assertEqual(process_state, 'process')
        
        # Transition to 'connect' state
        api.content.transition(obj=self.ki_foundations, transition='connect')
        connect_state = api.content.get_state(obj=self.ki_foundations)
        self.assertEqual(connect_state, 'connect')
        
        # Transition to 'published' state
        api.content.transition(obj=self.ki_foundations, transition='publish')
        published_state = api.content.get_state(obj=self.ki_foundations)
        self.assertEqual(published_state, 'published')
        
        # Test that workflow affects related content
        # Research Notes should be able to reference published Knowledge Items
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="test-research-note",
            title="Research on Programming Foundations",
            annotated_knowledge_items=[self.ki_foundations.UID()],
            annotation_type="insight",
            evidence_type="empirical",
            confidence_level="high"
        )
        
        # Should successfully create and reference the published Knowledge Item
        self.assertTrue(IResearchNote.providedBy(research_note))
        self.assertIn(self.ki_foundations.UID(), research_note.annotated_knowledge_items)

    def test_learning_goal_knowledge_item_coordination(self):
        """Test coordination between Learning Goals and Knowledge Items."""
        # Test learning path validation
        is_valid, errors = self.learning_goal.validate_learning_path()
        self.assertTrue(is_valid, f"Learning path should be valid: {errors}")
        
        # Test getting next Knowledge Items (should start with foundations)
        next_items = self.learning_goal.get_next_knowledge_items()
        self.assertEqual(len(next_items), 1)
        self.assertEqual(next_items[0]['uid'], self.ki_foundations.UID())
        self.assertEqual(next_items[0]['knowledge_type'], 'conceptual')
        self.assertEqual(next_items[0]['difficulty_level'], 'beginner')
        
        # Simulate mastering foundations
        self.ki_foundations.learning_progress = 0.8  # Above mastery threshold
        
        # Should now suggest OOP as next
        next_items = self.learning_goal.get_next_knowledge_items()
        self.assertEqual(len(next_items), 1)
        self.assertEqual(next_items[0]['uid'], self.ki_oop.UID())
        self.assertTrue(next_items[0]['prerequisites_met'])
        
        # Test overall progress calculation
        progress = self.learning_goal.calculate_overall_progress()
        self.assertIn('overall_percentage', progress)
        self.assertIn('items_mastered', progress)
        self.assertEqual(progress['items_mastered'], 1)  # Only foundations mastered
        self.assertEqual(progress['items_total'], 3)
        
        # Test prerequisite satisfaction
        self.assertGreater(progress['prerequisite_satisfaction'], 0)
        
        # Test bottleneck identification
        self.assertIn('bottlenecks', progress)
        bottlenecks = progress['bottlenecks']
        # OOP should be identified as next bottleneck
        bottleneck_uids = [b['item_uid'] for b in bottlenecks]
        self.assertIn(self.ki_oop.UID(), bottleneck_uids)

    def test_project_log_learning_integration(self):
        """Test Project Log integration with Knowledge Items and Learning Goals."""
        # Create Project Log associated with Learning Goal
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="software-learning-project",
            title="Software Development Learning Project",
            description="Tracking progress through software development mastery",
            start_date=date.today(),
            associated_learning_goals=[self.learning_goal.UID()],
            project_status="active"
        )
        
        # Test initial progress tracking
        initial_analytics = project_log.get_learning_analytics()
        
        self.assertIn('knowledge_items_progress', initial_analytics)
        self.assertIn('learning_goals_progress', initial_analytics)
        self.assertIn('overall_metrics', initial_analytics)
        
        # Should track all 3 Knowledge Items
        ki_progress = initial_analytics['knowledge_items_progress']
        self.assertEqual(len(ki_progress), 3)
        
        # Test learning session with progress updates
        session_data = {
            'start_time': datetime.now(),
            'duration_minutes': 120,
            'knowledge_items_studied': [self.ki_foundations.UID()],
            'progress_updates': {
                self.ki_foundations.UID(): 0.3  # 0.0 -> 0.3
            },
            'notes': 'Completed basic programming tutorial',
            'effectiveness_rating': 4,
            'session_type': 'self_study'
        }
        
        result = project_log.add_learning_session(session_data)
        self.assertTrue(result['success'])
        
        # Verify Knowledge Item progress was updated
        updated_foundations = api.content.get(UID=self.ki_foundations.UID())
        self.assertEqual(updated_foundations.learning_progress, 0.3)
        
        # Test another session reaching mastery
        mastery_session = {
            'start_time': datetime.now(),
            'duration_minutes': 90,
            'knowledge_items_studied': [self.ki_foundations.UID()],
            'progress_updates': {
                self.ki_foundations.UID(): 0.5  # 0.3 -> 0.8 (mastered)
            },
            'notes': 'Completed foundations assessment with high score',
            'effectiveness_rating': 5,
            'session_type': 'assessment'
        }
        
        result = project_log.add_learning_session(mastery_session)
        self.assertTrue(result['success'])
        
        # Verify mastery
        mastered_foundations = api.content.get(UID=self.ki_foundations.UID())
        self.assertEqual(mastered_foundations.learning_progress, 0.8)
        
        # Test Learning Goal synchronization
        sync_result = project_log._sync_progress_to_learning_goal(self.learning_goal.UID())
        self.assertTrue(sync_result['success'])
        
        # Verify Learning Goal progress was updated
        updated_goal = api.content.get(UID=self.learning_goal.UID())
        self.assertGreater(updated_goal.progress, 0)
        
        # Test updated analytics
        updated_analytics = project_log.get_learning_analytics()
        
        # Should show 1 mastered item
        overall_metrics = updated_analytics['overall_metrics']
        self.assertEqual(overall_metrics['mastered_items'], 1)
        
        # Should have session analytics
        session_analytics = updated_analytics['learning_session_analytics']
        self.assertEqual(session_analytics['total_sessions'], 2)
        self.assertEqual(session_analytics['total_study_time'], 210)  # 120 + 90

    def test_research_note_knowledge_annotation_workflow(self):
        """Test Research Note workflow with Knowledge Item annotations."""
        # Create Research Note that annotates multiple Knowledge Items
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="programming-research",
            title="Research on Programming Learning Effectiveness",
            description="Study of different approaches to learning programming",
            annotated_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID()
            ],
            annotation_type="analysis",
            evidence_type="empirical",
            confidence_level="high",
            research_question="What factors contribute to effective programming learning?",
            methodology="Comparative analysis of learning approaches",
            tags=["education", "programming", "research"]
        )
        
        # Test annotation details retrieval
        annotation_details = research_note.get_annotated_knowledge_items_details()
        self.assertEqual(len(annotation_details), 2)
        
        # Verify detailed information
        foundations_detail = next(
            detail for detail in annotation_details 
            if detail['uid'] == self.ki_foundations.UID()
        )
        self.assertEqual(foundations_detail['title'], "Programming Foundations")
        self.assertEqual(foundations_detail['knowledge_type'], "conceptual")
        self.assertEqual(foundations_detail['relationship'], "analysis")
        self.assertIsNone(foundations_detail['error'])
        
        # Test related note suggestions
        # Create another note with overlapping Knowledge Items
        related_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="oop-research",
            title="Object-Oriented Programming Pedagogy",
            annotated_knowledge_items=[self.ki_oop.UID(), self.ki_patterns.UID()],
            annotation_type="methodology",
            evidence_type="theoretical",
            confidence_level="medium",
            tags=["oop", "pedagogy", "research"]
        )
        
        # Test suggestion system
        suggestions = research_note.suggest_related_notes()
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]['uid'], related_note.UID())
        
        # Should identify shared Knowledge Item connection
        connection_reasons = suggestions[0]['connection_reasons']
        self.assertTrue(any('Knowledge Item' in reason for reason in connection_reasons))
        
        # Test Knowledge Item enhancement suggestions
        enhancements = research_note.generate_knowledge_item_enhancement_suggestions()
        self.assertIsInstance(enhancements, list)
        self.assertGreater(len(enhancements), 0)
        
        # Each enhancement should reference an annotated Knowledge Item
        for enhancement in enhancements:
            self.assertIn(enhancement['knowledge_item_uid'], 
                         [self.ki_foundations.UID(), self.ki_oop.UID()])
            self.assertIn('suggestion_type', enhancement)
            self.assertIn('description', enhancement)

    def test_bookmark_plus_learning_resource_workflow(self):
        """Test Bookmark+ workflow as learning resources for Knowledge Items."""
        # Create diverse Bookmark+ resources
        foundations_resource = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="foundations-tutorial",
            title="Programming Foundations Tutorial",
            description="Comprehensive tutorial covering programming basics",
            url="https://programming-tutorial.com/foundations",
            resource_type="tutorial",
            supports_knowledge_items=[self.ki_foundations.UID()],
            quality_metrics={
                'accuracy': 0.95,
                'clarity': 0.90,
                'depth': 0.80,
                'currency': 0.85
            },
            tags=["tutorial", "programming", "foundations"],
            importance="high",
            read_status="unread"
        )
        
        comprehensive_course = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="comprehensive-course",
            title="Complete Software Development Course",
            description="Full course covering foundations through advanced patterns",
            url="https://dev-course.com/complete",
            resource_type="course",
            supports_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID(),
                self.ki_patterns.UID()
            ],
            quality_metrics={
                'accuracy': 0.90,
                'clarity': 0.85,
                'depth': 0.95,
                'currency': 0.90
            },
            tags=["course", "comprehensive", "software"],
            importance="critical",
            read_status="reading"
        )
        
        # Test quality assessment for specific Knowledge Items
        foundations_assessment = foundations_resource.assess_knowledge_item_support_quality()
        
        self.assertIn('overall_score', foundations_assessment)
        self.assertIn('knowledge_item_scores', foundations_assessment)
        self.assertEqual(len(foundations_assessment['knowledge_item_scores']), 1)
        
        # Should have high support score due to good metrics and matching tags
        foundations_score = foundations_assessment['knowledge_item_scores'][0]
        self.assertEqual(foundations_score['knowledge_item_uid'], self.ki_foundations.UID())
        self.assertGreater(foundations_score['support_score'], 0.7)
        
        # Test Learning Goal support analysis
        goal_support = comprehensive_course.get_learning_goal_support_analysis([self.learning_goal.UID()])
        self.assertEqual(len(goal_support), 1)
        
        goal_analysis = goal_support[0]
        self.assertEqual(goal_analysis['learning_goal_uid'], self.learning_goal.UID())
        self.assertEqual(goal_analysis['support_percentage'], 100.0)  # Supports all 3 KIs
        self.assertEqual(len(goal_analysis['supported_items']), 3)
        self.assertEqual(len(goal_analysis['unsupported_items']), 0)
        
        # Test resource effectiveness calculation
        foundations_effectiveness = comprehensive_course.calculate_learning_effectiveness_for_item(
            self.ki_foundations.UID()
        )
        self.assertGreater(foundations_effectiveness, 0.6)
        
        patterns_effectiveness = comprehensive_course.calculate_learning_effectiveness_for_item(
            self.ki_patterns.UID()
        )
        self.assertGreater(patterns_effectiveness, 0.6)
        
        # Test resource discovery for learning path
        # When learner has mastered foundations, should recommend OOP resources
        self.ki_foundations.learning_progress = 0.8  # Mastered
        
        # Comprehensive course should still be highly effective for next step
        oop_effectiveness = comprehensive_course.calculate_learning_effectiveness_for_item(
            self.ki_oop.UID()
        )
        self.assertGreater(oop_effectiveness, 0.7)

    def test_knowledge_container_collection_workflow(self):
        """Test Knowledge Container workflow for organizing learning resources."""
        # Create Knowledge Container for the software development domain
        container = api.content.create(
            container=self.portal,
            type="KnowledgeContainer",
            id="software-dev-collection",
            title="Software Development Learning Collection",
            description="Curated collection for software development mastery",
            container_type="learning_path",
            collected_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID(),
                self.ki_patterns.UID()
            ],
            organization_strategy="difficulty_progression",
            sharing_permissions={"view": "public", "edit": "team"}
        )
        
        # Test Knowledge Item organization
        organized_items = container.get_organized_knowledge_items()
        self.assertEqual(len(organized_items), 3)
        
        # Should be ordered by difficulty: beginner -> intermediate -> advanced
        difficulties = [item['difficulty_level'] for item in organized_items]
        expected_order = ['beginner', 'intermediate', 'advanced']
        self.assertEqual(difficulties, expected_order)
        
        # Test collection analytics
        analytics = container.get_collection_analytics()
        
        self.assertEqual(analytics['total_items'], 3)
        
        # Check knowledge type distribution
        type_dist = analytics['knowledge_type_distribution']
        self.assertEqual(type_dist['conceptual'], 1)
        self.assertEqual(type_dist['procedural'], 1)
        self.assertEqual(type_dist['metacognitive'], 1)
        
        # Check difficulty distribution
        difficulty_dist = analytics['difficulty_distribution']
        self.assertEqual(difficulty_dist['beginner'], 1)
        self.assertEqual(difficulty_dist['intermediate'], 1)
        self.assertEqual(difficulty_dist['advanced'], 1)
        
        # Test export functionality
        # HTML export should include all Knowledge Items
        html_export = container.export_collection(format='html')
        
        self.assertIn('<html>', html_export)
        self.assertIn('Software Development Learning Collection', html_export)
        self.assertIn('Programming Foundations', html_export)
        self.assertIn('Object-Oriented Programming', html_export)
        self.assertIn('Design Patterns', html_export)
        
        # Markdown export should have structured sections
        md_export = container.export_collection(format='markdown')
        
        self.assertIn('# Software Development Learning Collection', md_export)
        self.assertIn('## Programming Foundations', md_export)
        self.assertIn('**Type:** conceptual', md_export)
        self.assertIn('**Difficulty:** beginner', md_export)
        
        # JSON export should preserve all data
        import json
        json_export = container.export_collection(format='json')
        export_data = json.loads(json_export)
        
        self.assertEqual(len(export_data['knowledge_items']), 3)
        
        # Verify each Knowledge Item is properly exported
        for ki_data in export_data['knowledge_items']:
            self.assertIn('uid', ki_data)
            self.assertIn('title', ki_data)
            self.assertIn('knowledge_type', ki_data)
            self.assertIn('difficulty_level', ki_data)
            self.assertIn('mastery_threshold', ki_data)
            self.assertIn('learning_progress', ki_data)

    def test_workflow_scripts_coordination(self):
        """Test that workflow scripts coordinate properly across content types."""
        from knowledge.curator.workflow_scripts import (
            update_embeddings, update_learning_goal_progress
        )
        
        # Create additional content to test prioritization
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="workflow-test-note",
            title="Workflow Test Research Note",
            annotated_knowledge_items=[self.ki_foundations.UID()],
            annotation_type="insight",
            evidence_type="empirical",
            confidence_level="medium"
        )
        
        bookmark = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="workflow-test-bookmark",
            title="Workflow Test Resource",
            url="https://example.com/resource",
            resource_type="article",
            supports_knowledge_items=[self.ki_foundations.UID()]
        )
        
        # Test embedding update workflow
        # Should prioritize Knowledge Items first
        update_embeddings(self.portal)
        
        # Knowledge Items should have been processed first
        # (In real implementation, this would check embedding timestamps)
        
        # Test Learning Goal progress update
        # Update Knowledge Item progress first
        self.ki_foundations.learning_progress = 0.8  # Mastered
        self.ki_oop.learning_progress = 0.5  # In progress
        
        # Run workflow script
        update_learning_goal_progress(self.learning_goal)
        
        # Verify Learning Goal progress was updated
        updated_goal = api.content.get(UID=self.learning_goal.UID())
        self.assertIsNotNone(updated_goal.completion_percentage)
        self.assertGreater(updated_goal.completion_percentage, 0)
        
        # Should reflect partial mastery (1 of 3 items fully mastered)
        expected_progress = (0.8 + 0.5 + 0.0) / 3  # Average progress
        self.assertAlmostEqual(updated_goal.completion_percentage, expected_progress * 100, places=1)

    def test_cross_content_type_validation(self):
        """Test validation of relationships across content types."""
        # Test that all content types properly reference valid Knowledge Items
        
        # Research Note validation
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="validation-test-note",
            title="Validation Test Note",
            annotated_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID()
            ],
            annotation_type="analysis",
            evidence_type="empirical",
            confidence_level="high"
        )
        
        # Should pass validation
        is_valid, error = research_note.validate_annotation_requirement()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Learning Goal validation
        is_valid, errors = self.learning_goal.validate_learning_path()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test Knowledge Item reference validation
        is_valid, errors = self.learning_goal.validate_knowledge_item_references()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test with invalid reference
        invalid_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="invalid-goal",
            title="Invalid Goal",
            target_knowledge_items=["non-existent-uid"],
            goal_type="mastery"
        )
        
        is_valid, errors = invalid_goal.validate_knowledge_item_references()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("non-existent-uid", errors[0])
        
        # Test Project Log validation
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="validation-project",
            title="Validation Project",
            associated_learning_goals=[self.learning_goal.UID()],
            start_date=date.today()
        )
        
        # Should successfully update Knowledge Item progress
        result = project_log.update_knowledge_item_progress(
            self.ki_foundations.UID(), 0.5
        )
        self.assertTrue(result['success'])
        
        # Should fail with invalid Knowledge Item UID
        result = project_log.update_knowledge_item_progress(
            "invalid-ki-uid", 0.5
        )
        self.assertFalse(result['success'])
        self.assertIn("not found", result['message'])

    def test_complete_learning_workflow_end_to_end(self):
        """Test complete end-to-end learning workflow across all content types."""
        # This is the comprehensive integration test for the entire system
        
        # Phase 1: Setup and Discovery
        # Create comprehensive learning environment
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="complete-workflow-project",
            title="Complete Learning Workflow Project",
            description="End-to-end software development learning",
            start_date=date.today(),
            associated_learning_goals=[self.learning_goal.UID()],
            project_status="active"
        )
        
        # Create supporting resources
        tutorial_resource = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="complete-tutorial",
            title="Complete Programming Tutorial",
            url="https://complete-programming.com",
            resource_type="tutorial",
            supports_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID()
            ],
            quality_metrics={
                'accuracy': 0.9,
                'clarity': 0.85,
                'depth': 0.8,
                'currency': 0.9
            },
            importance="high"
        )
        
        research_notes = []
        for i, (ki, topic) in enumerate([
            (self.ki_foundations, "Foundations Research"),
            (self.ki_oop, "OOP Research"),
            (self.ki_patterns, "Patterns Research")
        ]):
            note = api.content.create(
                container=self.portal,
                type="ResearchNote",
                id=f"research-note-{i+1}",
                title=topic,
                annotated_knowledge_items=[ki.UID()],
                annotation_type="analysis",
                evidence_type="empirical",
                confidence_level="high"
            )
            research_notes.append(note)
        
        container = api.content.create(
            container=self.portal,
            type="KnowledgeContainer",
            id="complete-workflow-container",
            title="Complete Workflow Container",
            collected_knowledge_items=[
                self.ki_foundations.UID(),
                self.ki_oop.UID(),
                self.ki_patterns.UID()
            ],
            organization_strategy="difficulty_progression"
        )
        
        # Phase 2: Learning Journey Simulation
        
        # Week 1: Study Foundations
        week1_session = {
            'start_time': datetime.now(),
            'duration_minutes': 240,  # 4 hours
            'knowledge_items_studied': [self.ki_foundations.UID()],
            'progress_updates': {
                self.ki_foundations.UID(): 0.4  # 0.0 -> 0.4
            },
            'notes': 'Studied variables, functions, and basic control structures',
            'effectiveness_rating': 4,
            'session_type': 'tutorial'
        }
        result = project_log.add_learning_session(week1_session)
        self.assertTrue(result['success'])
        
        # Verify progress tracking
        analytics = project_log.get_learning_analytics()
        ki_progress = analytics['knowledge_items_progress']
        foundations_progress = next(
            item for item in ki_progress 
            if item['uid'] == self.ki_foundations.UID()
        )
        self.assertEqual(foundations_progress['current_progress'], 0.4)
        self.assertFalse(foundations_progress['is_mastered'])
        
        # Week 2: Complete Foundations Mastery
        week2_session = {
            'start_time': datetime.now(),
            'duration_minutes': 180,  # 3 hours
            'knowledge_items_studied': [self.ki_foundations.UID()],
            'progress_updates': {
                self.ki_foundations.UID(): 0.4  # 0.4 -> 0.8 (mastered!)
            },
            'notes': 'Completed foundations assessment, ready for OOP',
            'effectiveness_rating': 5,
            'session_type': 'assessment'
        }
        result = project_log.add_learning_session(week2_session)
        self.assertTrue(result['success'])
        
        # Verify mastery achievement
        mastered_foundations = api.content.get(UID=self.ki_foundations.UID())
        self.assertEqual(mastered_foundations.learning_progress, 0.8)
        
        # Test Learning Goal next recommendations
        next_items = self.learning_goal.get_next_knowledge_items()
        self.assertEqual(len(next_items), 1)
        self.assertEqual(next_items[0]['uid'], self.ki_oop.UID())
        self.assertTrue(next_items[0]['prerequisites_met'])
        
        # Week 3-4: OOP Learning
        week3_session = {
            'start_time': datetime.now(),
            'duration_minutes': 300,  # 5 hours
            'knowledge_items_studied': [self.ki_oop.UID()],
            'progress_updates': {
                self.ki_oop.UID(): 0.5  # 0.0 -> 0.5
            },
            'notes': 'Studied classes, objects, and inheritance',
            'effectiveness_rating': 4,
            'session_type': 'tutorial'
        }
        result = project_log.add_learning_session(week3_session)
        self.assertTrue(result['success'])
        
        week4_session = {
            'start_time': datetime.now(),
            'duration_minutes': 240,  # 4 hours
            'knowledge_items_studied': [self.ki_oop.UID()],
            'progress_updates': {
                self.ki_oop.UID(): 0.3  # 0.5 -> 0.8 (mastered!)
            },
            'notes': 'Mastered polymorphism and encapsulation',
            'effectiveness_rating': 5,
            'session_type': 'practice'
        }
        result = project_log.add_learning_session(week4_session)
        self.assertTrue(result['success'])
        
        # Week 5-6: Design Patterns
        week5_session = {
            'start_time': datetime.now(),
            'duration_minutes': 360,  # 6 hours
            'knowledge_items_studied': [self.ki_patterns.UID()],
            'progress_updates': {
                self.ki_patterns.UID(): 0.6  # 0.0 -> 0.6
            },
            'notes': 'Studied creational and structural patterns',
            'effectiveness_rating': 4,
            'session_type': 'self_study'
        }
        result = project_log.add_learning_session(week5_session)
        self.assertTrue(result['success'])
        
        week6_session = {
            'start_time': datetime.now(),
            'duration_minutes': 300,  # 5 hours
            'knowledge_items_studied': [self.ki_patterns.UID()],
            'progress_updates': {
                self.ki_patterns.UID(): 0.3  # 0.6 -> 0.9 (mastered!)
            },
            'notes': 'Mastered behavioral patterns and applications',
            'effectiveness_rating': 5,
            'session_type': 'project'
        }
        result = project_log.add_learning_session(week6_session)
        self.assertTrue(result['success'])
        
        # Phase 3: Validation and Completion
        
        # Verify all Knowledge Items are mastered
        final_foundations = api.content.get(UID=self.ki_foundations.UID())
        final_oop = api.content.get(UID=self.ki_oop.UID())
        final_patterns = api.content.get(UID=self.ki_patterns.UID())
        
        self.assertEqual(final_foundations.learning_progress, 0.8)
        self.assertEqual(final_oop.learning_progress, 0.8)
        self.assertEqual(final_patterns.learning_progress, 0.9)
        
        # All should be above their mastery thresholds
        self.assertGreaterEqual(final_foundations.learning_progress, final_foundations.mastery_threshold)
        self.assertGreaterEqual(final_oop.learning_progress, final_oop.mastery_threshold)
        self.assertGreaterEqual(final_patterns.learning_progress, final_patterns.mastery_threshold)
        
        # Verify Learning Goal completion
        final_progress = self.learning_goal.calculate_overall_progress()
        self.assertEqual(final_progress['items_mastered'], 3)
        self.assertEqual(final_progress['items_total'], 3)
        self.assertEqual(final_progress['overall_percentage'], 100.0)
        
        # Verify Project Log analytics
        final_analytics = project_log.get_learning_analytics()
        
        # All items should be mastered
        overall_metrics = final_analytics['overall_metrics']
        self.assertEqual(overall_metrics['mastered_items'], 3)
        self.assertEqual(overall_metrics['total_knowledge_items'], 3)
        
        # Should have comprehensive session data
        session_analytics = final_analytics['learning_session_analytics']
        self.assertEqual(session_analytics['total_sessions'], 6)
        total_time = 240 + 180 + 300 + 240 + 360 + 300  # Sum of all sessions
        self.assertEqual(session_analytics['total_study_time'], total_time)
        
        # Verify resource effectiveness
        tutorial_assessment = tutorial_resource.assess_knowledge_item_support_quality()
        self.assertGreater(tutorial_assessment['overall_score'], 0.7)
        
        # Verify container analytics
        container_analytics = container.get_collection_analytics()
        self.assertEqual(container_analytics['total_items'], 3)
        # Should show high mastery rate
        mastery_stats = container_analytics['mastery_statistics']
        self.assertEqual(mastery_stats['mastered_count'], 3)
        self.assertEqual(mastery_stats['mastery_percentage'], 100.0)
        
        # Verify research notes captured insights
        for note in research_notes:
            details = note.get_annotated_knowledge_items_details()
            self.assertEqual(len(details), 1)
            self.assertIsNone(details[0]['error'])
        
        # Phase 4: Cross-Content Type Verification
        
        # All content should be properly coordinated
        # Learning Goal should show complete path
        next_items = self.learning_goal.get_next_knowledge_items()
        self.assertEqual(len(next_items), 0)  # No more items to learn
        
        # Container should export complete learning journey
        export_data = json.loads(container.export_collection(format='json'))
        self.assertEqual(len(export_data['knowledge_items']), 3)
        
        # All Knowledge Items should show mastery
        for ki_data in export_data['knowledge_items']:
            self.assertGreaterEqual(ki_data['learning_progress'], ki_data['mastery_threshold'])
        
        # Research notes should suggest no additional items (all covered)
        all_suggestions = []
        for note in research_notes:
            suggestions = note.suggest_related_notes()
            all_suggestions.extend(suggestions)
        
        # Should have cross-references between notes
        self.assertGreater(len(all_suggestions), 0)
        
        # Project log should show successful completion
        completion_rate = (final_analytics['overall_metrics']['mastered_items'] / 
                          final_analytics['overall_metrics']['total_knowledge_items']) * 100
        self.assertEqual(completion_rate, 100.0)
        
        # This completes the comprehensive end-to-end test
        # All content types are properly coordinated around Knowledge Items
        # Learning progression follows prerequisite chains
        # Progress tracking works across all systems
        # Export and analytics provide complete visibility
        self.assertTrue(True, "Complete learning workflow test passed!")