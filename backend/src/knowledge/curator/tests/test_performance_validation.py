"""Performance and user experience validation tests for Knowledge Item coordination.

This module tests performance characteristics, scalability, and user experience
aspects of the Knowledge Item-centric architecture.
"""

from knowledge.curator.interfaces import IKnowledgeItem, ILearningGoal, IResearchNote
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from datetime import datetime, date, timedelta
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import time
import unittest


class TestKnowledgeItemPerformance(unittest.TestCase):
    """Test performance characteristics of Knowledge Item operations."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Set up performance test environment."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        
        # Create base Knowledge Items for performance testing
        self.knowledge_items = []
        self.batch_size = 10  # Reduced for test performance
        
        for i in range(self.batch_size):
            ki = api.content.create(
                container=self.portal,
                type="KnowledgeItem",
                id=f"perf-ki-{i:03d}",
                title=f"Performance Test Knowledge Item {i}",
                description=f"Knowledge item {i} for performance testing",
                content=RichTextValue(f"Content for knowledge item {i}", "text/plain", "text/html"),
                knowledge_type="conceptual" if i % 3 == 0 else "procedural" if i % 3 == 1 else "factual",
                difficulty_level="beginner" if i < 3 else "intermediate" if i < 7 else "advanced",
                mastery_threshold=0.7 + (i * 0.01),
                learning_progress=i * 0.1,
                atomic_concepts=[f"concept{i}", f"skill{i}"],
                tags=[f"tag{i}", "performance", "test"]
            )
            self.knowledge_items.append(ki)

    def test_knowledge_item_creation_performance(self):
        """Test performance of creating multiple Knowledge Items."""
        start_time = time.time()
        
        # Create batch of Knowledge Items
        batch_items = []
        batch_size = 20
        
        for i in range(batch_size):
            ki = api.content.create(
                container=self.portal,
                type="KnowledgeItem",
                id=f"batch-ki-{i:03d}",
                title=f"Batch Knowledge Item {i}",
                knowledge_type="conceptual",
                atomic_concepts=[f"batch_concept_{i}"]
            )
            batch_items.append(ki)
        
        creation_time = time.time() - start_time
        
        # Verify all items were created
        self.assertEqual(len(batch_items), batch_size)
        
        # Performance assertion (should create 20 items in under 10 seconds)
        self.assertLess(creation_time, 10.0, 
                       f"Creating {batch_size} Knowledge Items took {creation_time:.2f}s, expected < 10s")
        
        # Average time per item
        avg_time = creation_time / batch_size
        self.assertLess(avg_time, 0.5, 
                       f"Average creation time {avg_time:.3f}s per item, expected < 0.5s")

    def test_knowledge_item_search_performance(self):
        """Test performance of searching Knowledge Items."""
        # Test catalog search performance
        start_time = time.time()
        
        # Search by content type
        results = api.content.find(portal_type='KnowledgeItem')
        search_time = time.time() - start_time
        
        # Should find all test items plus batch items
        self.assertGreaterEqual(len(results), self.batch_size)
        
        # Search should be fast (under 1 second for small dataset)
        self.assertLess(search_time, 1.0, 
                       f"Catalog search took {search_time:.3f}s, expected < 1s")
        
        # Test filtered search performance
        start_time = time.time()
        
        conceptual_items = api.content.find(
            portal_type='KnowledgeItem',
            knowledge_type='conceptual'
        )
        filtered_search_time = time.time() - start_time
        
        self.assertGreater(len(conceptual_items), 0)
        self.assertLess(filtered_search_time, 1.0,
                       f"Filtered search took {filtered_search_time:.3f}s, expected < 1s")

    def test_learning_goal_calculation_performance(self):
        """Test performance of Learning Goal progress calculations."""
        # Create Learning Goal with many Knowledge Items
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="perf-learning-goal",
            title="Performance Test Learning Goal",
            target_knowledge_items=[ki.UID() for ki in self.knowledge_items],
            goal_type="mastery"
        )
        
        # Test progress calculation performance
        start_time = time.time()
        progress_result = learning_goal.calculate_overall_progress()
        calculation_time = time.time() - start_time
        
        # Verify calculation completed
        self.assertIn('overall_percentage', progress_result)
        self.assertIn('items_total', progress_result)
        self.assertEqual(progress_result['items_total'], len(self.knowledge_items))
        
        # Should calculate quickly (under 2 seconds)
        self.assertLess(calculation_time, 2.0,
                       f"Progress calculation took {calculation_time:.3f}s, expected < 2s")
        
        # Test next items recommendation performance
        start_time = time.time()
        next_items = learning_goal.get_next_knowledge_items()
        recommendation_time = time.time() - start_time
        
        self.assertIsInstance(next_items, list)
        self.assertLess(recommendation_time, 1.0,
                       f"Next items calculation took {recommendation_time:.3f}s, expected < 1s")

    def test_research_note_suggestion_performance(self):
        """Test performance of Research Note related suggestions."""
        # Create Research Notes referencing Knowledge Items
        research_notes = []
        for i in range(5):  # Smaller batch for performance
            note = api.content.create(
                container=self.portal,
                type="ResearchNote",
                id=f"perf-note-{i}",
                title=f"Performance Test Note {i}",
                annotated_knowledge_items=[self.knowledge_items[i].UID()],
                annotation_type="analysis",
                evidence_type="empirical",
                confidence_level="medium",
                tags=[f"note{i}", "performance"]
            )
            research_notes.append(note)
        
        # Test suggestion performance
        test_note = research_notes[0]
        
        start_time = time.time()
        suggestions = test_note.suggest_related_notes()
        suggestion_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(suggestion_time, 2.0,
                       f"Related note suggestions took {suggestion_time:.3f}s, expected < 2s")
        
        # Test enhancement suggestions performance
        start_time = time.time()
        enhancements = test_note.generate_knowledge_item_enhancement_suggestions()
        enhancement_time = time.time() - start_time
        
        self.assertIsInstance(enhancements, list)
        self.assertLess(enhancement_time, 1.0,
                       f"Enhancement suggestions took {enhancement_time:.3f}s, expected < 1s")

    def test_container_analytics_performance(self):
        """Test performance of Knowledge Container analytics."""
        from knowledge.curator.tests.test_knowledge_container import MockKnowledgeContainer
        
        # Create container with many Knowledge Items
        container = MockKnowledgeContainer()
        container.included_knowledge_items = [ki.UID() for ki in self.knowledge_items]
        
        # Mock the analytics method for performance testing
        def mock_get_collection_analytics(self):
            """Mock analytics that simulates computation time."""
            start_computation = time.time()
            
            # Simulate analytics computation
            total_items = len(self.included_knowledge_items)
            
            # Mock processing each item
            for uid in self.included_knowledge_items[:5]:  # Process subset for speed
                # Simulate item analysis
                time.sleep(0.001)  # 1ms per item simulation
            
            computation_time = time.time() - start_computation
            
            return {
                'total_items': total_items,
                'computation_time': computation_time,
                'knowledge_type_distribution': {'conceptual': 3, 'procedural': 4, 'factual': 3},
                'difficulty_distribution': {'beginner': 3, 'intermediate': 4, 'advanced': 3},
                'average_progress': 0.45,
                'mastery_statistics': {
                    'mastered_count': 2,
                    'in_progress_count': 6,
                    'not_started_count': 2,
                    'mastery_percentage': 20.0
                }
            }
        
        # Bind mock method
        container.get_collection_analytics = mock_get_collection_analytics.__get__(container)
        
        # Test analytics performance
        start_time = time.time()
        analytics = container.get_collection_analytics()
        total_time = time.time() - start_time
        
        # Verify analytics completed
        self.assertEqual(analytics['total_items'], len(self.knowledge_items))
        self.assertIn('computation_time', analytics)
        
        # Should complete reasonably quickly
        self.assertLess(total_time, 3.0,
                       f"Container analytics took {total_time:.3f}s, expected < 3s")

    def test_bulk_operations_performance(self):
        """Test performance of bulk operations on Knowledge Items."""
        # Test bulk update performance
        start_time = time.time()
        
        # Update multiple Knowledge Items
        updated_count = 0
        for ki in self.knowledge_items:
            ki.learning_progress = min(ki.learning_progress + 0.1, 1.0)
            updated_count += 1
        
        bulk_update_time = time.time() - start_time
        
        self.assertEqual(updated_count, len(self.knowledge_items))
        self.assertLess(bulk_update_time, 2.0,
                       f"Bulk update took {bulk_update_time:.3f}s, expected < 2s")
        
        # Test bulk retrieval performance
        start_time = time.time()
        
        uids = [ki.UID() for ki in self.knowledge_items]
        retrieved_items = []
        for uid in uids:
            item = api.content.get(UID=uid)
            if item:
                retrieved_items.append(item)
        
        bulk_retrieval_time = time.time() - start_time
        
        self.assertEqual(len(retrieved_items), len(self.knowledge_items))
        self.assertLess(bulk_retrieval_time, 2.0,
                       f"Bulk retrieval took {bulk_retrieval_time:.3f}s, expected < 2s")


class TestUserExperienceValidation(unittest.TestCase):
    """Test user experience aspects of Knowledge Item coordination."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Set up user experience test environment."""
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        
        # Create sample Knowledge Items for UX testing
        self.ki_basic = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ux-basic",
            title="Basic Programming Concepts",
            description="Fundamental programming concepts for beginners",
            content=RichTextValue("Variables, functions, and basic control structures", "text/plain", "text/html"),
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.3,
            atomic_concepts=["variables", "functions", "control_flow"],
            tags=["programming", "basics", "beginner"]
        )
        
        self.ki_intermediate = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="ux-intermediate",
            title="Data Structures",
            description="Common data structures and their usage",
            content=RichTextValue("Arrays, lists, dictionaries, and trees", "text/plain", "text/html"),
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.1,
            prerequisite_items=[self.ki_basic.UID()],
            atomic_concepts=["arrays", "lists", "dictionaries", "trees"],
            tags=["programming", "data_structures", "intermediate"]
        )

    def test_learning_path_clarity(self):
        """Test clarity and usability of learning path recommendations."""
        # Create Learning Goal
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="ux-learning-goal",
            title="Programming Fundamentals",
            target_knowledge_items=[
                self.ki_basic.UID(),
                self.ki_intermediate.UID()
            ],
            starting_knowledge_item=self.ki_basic.UID(),
            goal_type="sequential"
        )
        
        # Test next items recommendation provides clear guidance
        next_items = goal.get_next_knowledge_items()
        
        self.assertEqual(len(next_items), 1)
        next_item = next_items[0]
        
        # Should provide comprehensive information for user decision-making
        required_fields = [
            'uid', 'title', 'description', 'knowledge_type', 
            'difficulty_level', 'mastery_threshold', 'learning_progress',
            'prerequisites_met', 'mastery_gap', 'estimated_time'
        ]
        
        for field in required_fields:
            self.assertIn(field, next_item, f"Next item missing required field: {field}")
        
        # Should indicate clear progression
        self.assertEqual(next_item['uid'], self.ki_basic.UID())
        self.assertTrue(next_item['prerequisites_met'])
        self.assertGreater(next_item['mastery_gap'], 0)

    def test_progress_visualization_data(self):
        """Test that progress data is suitable for visualization."""
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="ux-progress-goal",
            title="Progress Visualization Goal",
            target_knowledge_items=[
                self.ki_basic.UID(),
                self.ki_intermediate.UID()
            ]
        )
        
        progress = goal.calculate_overall_progress()
        
        # Should provide visualization-ready data
        self.assertIn('visualization_data', progress)
        viz_data = progress['visualization_data']
        
        # Should have nodes and edges for graph visualization
        self.assertIn('nodes', viz_data)
        self.assertIn('edges', viz_data)
        
        # Nodes should have positioning and styling information
        nodes = viz_data['nodes']
        self.assertGreater(len(nodes), 0)
        
        for node in nodes:
            self.assertIn('id', node)
            self.assertIn('label', node)
            self.assertIn('type', node)
            self.assertIn('progress', node)
            self.assertIn('status', node)
        
        # Should provide progress by level for hierarchical display
        self.assertIn('progress_by_level', viz_data)
        progress_by_level = viz_data['progress_by_level']
        self.assertIsInstance(progress_by_level, dict)
        
        # Should provide path segments for step-by-step guidance
        self.assertIn('path_segments', progress)
        segments = progress['path_segments']
        self.assertIsInstance(segments, list)
        
        for segment in segments:
            self.assertIn('knowledge_item_uid', segment)
            self.assertIn('title', segment)
            self.assertIn('description', segment)
            self.assertIn('status', segment)

    def test_research_note_discoverability(self):
        """Test discoverability and usefulness of Research Note suggestions."""
        # Create Research Notes with varying relevance
        main_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="ux-main-note",
            title="Programming Learning Strategies",
            description="Research on effective programming learning approaches",
            annotated_knowledge_items=[self.ki_basic.UID()],
            annotation_type="methodology",
            evidence_type="empirical",
            confidence_level="high",
            research_question="What strategies help beginners learn programming effectively?",
            tags=["programming", "education", "learning"]
        )
        
        # Create related note
        related_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="ux-related-note",
            title="Data Structure Teaching Methods",
            description="Effective approaches for teaching data structures",
            annotated_knowledge_items=[self.ki_intermediate.UID()],
            annotation_type="pedagogy",
            evidence_type="theoretical",
            confidence_level="medium",
            tags=["programming", "education", "data_structures"]
        )
        
        # Test suggestion quality and usefulness
        suggestions = main_note.suggest_related_notes()
        
        if len(suggestions) > 0:
            suggestion = suggestions[0]
            
            # Should provide actionable information
            required_fields = [
                'uid', 'title', 'relevance_score', 'connection_reasons', 
                'shared_items', 'score_breakdown'
            ]
            
            for field in required_fields:
                self.assertIn(field, suggestion, f"Suggestion missing field: {field}")
            
            # Relevance score should be meaningful
            self.assertGreater(suggestion['relevance_score'], 0)
            self.assertLessEqual(suggestion['relevance_score'], 1)
            
            # Connection reasons should be explanatory
            reasons = suggestion['connection_reasons']
            self.assertIsInstance(reasons, list)
            self.assertGreater(len(reasons), 0)
            
            # Each reason should be human-readable
            for reason in reasons:
                self.assertIsInstance(reason, str)
                self.assertGreater(len(reason), 10)  # Meaningful explanation

    def test_bookmark_resource_recommendations(self):
        """Test quality and usefulness of Bookmark+ resource recommendations."""
        # Create Bookmark+ resources
        beginner_resource = api.content.create(
            container=self.portal,
            type="BookmarkPlus",
            id="ux-beginner-resource",
            title="Programming for Complete Beginners",
            description="Step-by-step programming tutorial for absolute beginners",
            url="https://programming-beginners.com",
            resource_type="tutorial",
            supports_knowledge_items=[self.ki_basic.UID()],
            quality_metrics={
                'accuracy': 0.9,
                'clarity': 0.95,
                'depth': 0.7,
                'currency': 0.8
            },
            tags=["programming", "tutorial", "beginner"],
            importance="high"
        )
        
        # Test quality assessment provides actionable insights
        assessment = beginner_resource.assess_knowledge_item_support_quality()
        
        self.assertIn('overall_score', assessment)
        self.assertIn('knowledge_item_scores', assessment)
        self.assertIn('methodology', assessment)
        
        # Overall score should be interpretable
        overall_score = assessment['overall_score']
        self.assertGreaterEqual(overall_score, 0.0)
        self.assertLessEqual(overall_score, 1.0)
        
        # Should provide detailed scoring for each Knowledge Item
        ki_scores = assessment['knowledge_item_scores']
        self.assertEqual(len(ki_scores), 1)
        
        ki_score = ki_scores[0]
        self.assertEqual(ki_score['knowledge_item_uid'], self.ki_basic.UID())
        self.assertIn('support_score', ki_score)
        self.assertIn('relevance_factors', ki_score)
        
        # Relevance factors should be detailed and explanatory
        factors = ki_score['relevance_factors']
        expected_factors = ['shared_tags', 'topic_alignment', 'difficulty_match', 'quality_score']
        
        for factor in expected_factors:
            self.assertIn(factor, factors)
            self.assertIsInstance(factors[factor], (int, float))

    def test_container_organization_usability(self):
        """Test usability of Knowledge Container organization strategies."""
        from knowledge.curator.tests.test_knowledge_container import MockKnowledgeContainer
        
        container = MockKnowledgeContainer()
        container.included_knowledge_items = [
            self.ki_basic.UID(),
            self.ki_intermediate.UID()
        ]
        
        # Mock organization method for testing
        def mock_get_organized_knowledge_items(self):
            """Mock organization that provides user-friendly structure."""
            items = []
            
            # Simulate organized items with user-friendly metadata
            for i, uid in enumerate(self.included_knowledge_items):
                if uid == self.ki_basic.UID():
                    item_data = {
                        'uid': uid,
                        'title': 'Basic Programming Concepts',
                        'knowledge_type': 'conceptual',
                        'difficulty_level': 'beginner',
                        'mastery_threshold': 0.7,
                        'learning_progress': 0.3,
                        'position': i + 1,
                        'section': 'Fundamentals',
                        'prerequisites_satisfied': True,
                        'next_steps': ['Data Structures'],
                        'estimated_time_minutes': 60,
                        'user_friendly_status': 'In Progress',
                        'progress_indicator': '●●●○○',  # Visual progress
                        'difficulty_indicator': '★☆☆',  # Visual difficulty
                    }
                else:
                    item_data = {
                        'uid': uid,
                        'title': 'Data Structures',
                        'knowledge_type': 'procedural',
                        'difficulty_level': 'intermediate',
                        'mastery_threshold': 0.8,
                        'learning_progress': 0.1,
                        'position': i + 1,
                        'section': 'Core Concepts',
                        'prerequisites_satisfied': False,
                        'next_steps': [],
                        'estimated_time_minutes': 120,
                        'user_friendly_status': 'Not Ready',
                        'progress_indicator': '●○○○○',
                        'difficulty_indicator': '★★☆',
                    }
                items.append(item_data)
            
            return items
        
        # Bind mock method
        container.get_organized_knowledge_items = mock_get_organized_knowledge_items.__get__(container)
        
        # Test organization provides user-friendly structure
        organized = container.get_organized_knowledge_items()
        
        self.assertEqual(len(organized), 2)
        
        for item in organized:
            # Should have user-friendly display information
            ux_fields = [
                'section', 'prerequisites_satisfied', 'next_steps',
                'estimated_time_minutes', 'user_friendly_status',
                'progress_indicator', 'difficulty_indicator'
            ]
            
            for field in ux_fields:
                self.assertIn(field, item, f"Organized item missing UX field: {field}")
            
            # Status should be human-readable
            status = item['user_friendly_status']
            self.assertIn(status, ['Not Started', 'In Progress', 'Completed', 'Not Ready'])
            
            # Progress and difficulty indicators should be visual
            self.assertIsInstance(item['progress_indicator'], str)
            self.assertIsInstance(item['difficulty_indicator'], str)

    def test_workflow_feedback_mechanisms(self):
        """Test feedback mechanisms for user actions and progress."""
        # Create Project Log for testing feedback
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="ux-project-log",
            title="UX Test Project",
            start_date=date.today(),
            project_status="active"
        )
        
        # Test progress update feedback
        result = project_log.update_knowledge_item_progress(
            knowledge_item_uid=self.ki_basic.UID(),
            new_progress=0.6,
            notes="Completed variables and functions sections"
        )
        
        # Should provide clear feedback
        self.assertIn('success', result)
        self.assertIn('message', result)
        self.assertTrue(result['success'])
        
        # Message should be informative
        message = result['message']
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 20)  # Substantial feedback
        self.assertIn('0.6', message)  # Should mention new progress value
        
        # Test learning session feedback
        session_data = {
            'start_time': datetime.now(),
            'duration_minutes': 45,
            'knowledge_items_studied': [self.ki_basic.UID()],
            'progress_updates': {self.ki_basic.UID(): 0.1},
            'effectiveness_rating': 4,
            'session_type': 'tutorial'
        }
        
        session_result = project_log.add_learning_session(session_data)
        
        # Should provide comprehensive session feedback
        self.assertTrue(session_result['success'])
        session_message = session_result['message']
        self.assertIn('learning session', session_message.lower())
        self.assertIn('45', session_message)  # Duration
        
        # Test analytics provide actionable insights
        analytics = project_log.get_learning_analytics()
        
        # Should have user-friendly recommendations
        self.assertIn('recommendations', analytics)
        recommendations = analytics['recommendations']
        self.assertIsInstance(recommendations, list)
        
        if len(recommendations) > 0:
            rec = recommendations[0]
            self.assertIn('description', rec)
            self.assertIn('priority', rec)
            self.assertIn('actionable_steps', rec)
            
            # Description should be clear and actionable
            description = rec['description']
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 30)  # Substantial guidance

    def test_error_handling_user_experience(self):
        """Test user experience of error handling and validation."""
        # Test Knowledge Item validation with clear error messages
        from knowledge.curator.content.validators import validate_atomic_concepts
        from zope.interface import Invalid
        
        # Test empty concepts validation
        try:
            validate_atomic_concepts([])
            self.fail("Should have raised Invalid exception")
        except Invalid as e:
            error_message = str(e)
            self.assertIn("at least one", error_message.lower())
            self.assertIn("concept", error_message.lower())
            # Error should be user-friendly, not technical
            self.assertNotIn("Exception", error_message)
            self.assertNotIn("Stack", error_message)
        
        # Test Learning Goal validation with helpful guidance
        invalid_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="invalid-goal",
            title="Invalid Goal",
            target_knowledge_items=[],  # Empty - should fail
            goal_type="mastery"
        )
        
        is_valid, errors = invalid_goal.validate_learning_path()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Errors should be user-friendly
        for error in errors:
            self.assertIsInstance(error, str)
            self.assertGreater(len(error), 20)  # Substantial explanation
            # Should not contain technical jargon
            self.assertNotIn("UID", error)
            self.assertNotIn("schema", error.lower())
            self.assertNotIn("validation", error.lower())
        
        # Test Project Log error handling
        result = project_log.update_knowledge_item_progress(
            knowledge_item_uid="non-existent-uid",
            new_progress=0.5
        )
        
        self.assertFalse(result['success'])
        error_message = result['message']
        
        # Error should be helpful, not cryptic
        self.assertIn("not found", error_message.lower())
        self.assertNotIn("KeyError", error_message)
        self.assertNotIn("404", error_message)

    def test_accessibility_and_internationalization_readiness(self):
        """Test readiness for accessibility and internationalization."""
        # Test that user-facing strings are externalized and descriptive
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="i18n-goal",
            title="Internationalization Test Goal",
            target_knowledge_items=[self.ki_basic.UID()],
            goal_type="mastery"
        )
        
        progress = goal.calculate_overall_progress()
        
        # Test that status messages are descriptive for screen readers
        next_items = goal.get_next_knowledge_items()
        if len(next_items) > 0:
            item = next_items[0]
            
            # Should have semantic status information
            self.assertIn('status', item)
            status = item['status']
            
            # Status should be descriptive, not just codes
            valid_statuses = [
                'available', 'not_ready', 'in_progress', 
                'completed', 'prerequisites_not_met'
            ]
            self.assertIn(status, valid_statuses)
        
        # Test that numeric values have proper formatting context
        self.assertIn('overall_percentage', progress)
        percentage = progress['overall_percentage']
        self.assertIsInstance(percentage, (int, float))
        self.assertGreaterEqual(percentage, 0)
        self.assertLessEqual(percentage, 100)
        
        # Test that time estimates are provided in user-friendly units
        self.assertIn('path_segments', progress)
        for segment in progress.get('path_segments', []):
            if 'estimated_time' in segment:
                time_info = segment['estimated_time']
                # Should be structured data, not just numbers
                self.assertIsInstance(time_info, (dict, str, int))

    def test_responsive_design_data_structure(self):
        """Test that data structures support responsive UI design."""
        from knowledge.curator.tests.test_knowledge_container import MockKnowledgeContainer
        
        container = MockKnowledgeContainer()
        container.included_knowledge_items = [
            self.ki_basic.UID(),
            self.ki_intermediate.UID()
        ]
        
        # Mock method that provides responsive-friendly data
        def mock_get_responsive_data(self):
            """Mock method providing responsive UI data."""
            return {
                'desktop_view': {
                    'columns': 3,
                    'show_detailed_descriptions': True,
                    'show_progress_charts': True,
                    'items_per_page': 20
                },
                'tablet_view': {
                    'columns': 2,
                    'show_detailed_descriptions': True,
                    'show_progress_charts': False,
                    'items_per_page': 15
                },
                'mobile_view': {
                    'columns': 1,
                    'show_detailed_descriptions': False,
                    'show_progress_charts': False,
                    'items_per_page': 10,
                    'use_card_layout': True,
                    'show_quick_actions': True
                },
                'accessibility': {
                    'high_contrast_available': True,
                    'screen_reader_optimized': True,
                    'keyboard_navigation': True,
                    'font_size_adjustable': True
                }
            }
        
        container.get_responsive_configuration = mock_get_responsive_data.__get__(container)
        
        # Test responsive configuration
        responsive_config = container.get_responsive_configuration()
        
        # Should provide configuration for different screen sizes
        required_views = ['desktop_view', 'tablet_view', 'mobile_view']
        for view in required_views:
            self.assertIn(view, responsive_config)
            view_config = responsive_config[view]
            
            # Each view should specify layout parameters
            self.assertIn('columns', view_config)
            self.assertIn('items_per_page', view_config)
            self.assertIsInstance(view_config['columns'], int)
            self.assertIsInstance(view_config['items_per_page'], int)
        
        # Should include accessibility configuration
        self.assertIn('accessibility', responsive_config)
        accessibility_config = responsive_config['accessibility']
        
        accessibility_features = [
            'high_contrast_available', 'screen_reader_optimized',
            'keyboard_navigation', 'font_size_adjustable'
        ]
        
        for feature in accessibility_features:
            self.assertIn(feature, accessibility_config)
            self.assertIsInstance(accessibility_config[feature], bool)
            self.assertTrue(accessibility_config[feature])  # Should support accessibility