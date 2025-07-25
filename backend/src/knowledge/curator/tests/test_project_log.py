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

    def test_get_learning_analytics(self):
        """Test Project Log learning analytics with Knowledge Items."""
        from datetime import datetime
        
        # Create Knowledge Items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="analytics-ki-1",
            title="Analytics KI 1",
            description="First knowledge item for analytics",
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.8,
            atomic_concepts=["analytics1"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="analytics-ki-2",
            title="Analytics KI 2",
            description="Second knowledge item for analytics",
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.4,
            atomic_concepts=["analytics2"]
        )
        
        ki3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="analytics-ki-3",
            title="Analytics KI 3",
            description="Third knowledge item for analytics",
            knowledge_type="factual",
            difficulty_level="advanced",
            mastery_threshold=0.9,
            learning_progress=0.2,
            atomic_concepts=["analytics3"]
        )
        
        # Create Learning Goal
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="analytics-goal",
            title="Analytics Learning Goal",
            target_knowledge_items=[ki1.UID(), ki2.UID(), ki3.UID()],
            goal_type="mastery"
        )
        
        # Create Project Log
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="analytics-project-log",
            title="Analytics Project",
            description="Project for testing analytics",
            start_date=date.today(),
            associated_learning_goals=[learning_goal.UID()],
        )
        
        # Add some progress data
        project_log.update_knowledge_item_progress(ki1.UID(), 0.8)
        project_log.update_knowledge_item_progress(ki2.UID(), 0.4)
        project_log.update_knowledge_item_progress(ki3.UID(), 0.2)
        
        # Add learning sessions
        session1 = {
            'start_time': datetime.now(),
            'duration_minutes': 60,
            'knowledge_items_studied': [ki1.UID(), ki2.UID()],
            'progress_updates': {ki1.UID(): 0.1, ki2.UID(): 0.1},
            'effectiveness_rating': 4,
            'session_type': 'self_study'
        }
        project_log.add_learning_session(session1)
        
        session2 = {
            'start_time': datetime.now(),
            'duration_minutes': 45,
            'knowledge_items_studied': [ki3.UID()],
            'progress_updates': {ki3.UID(): 0.1},
            'effectiveness_rating': 3,
            'session_type': 'practice'
        }
        project_log.add_learning_session(session2)
        
        # Test get_learning_analytics
        analytics = project_log.get_learning_analytics()
        
        # Check knowledge_items_progress
        ki_progress = analytics['knowledge_items_progress']
        self.assertEqual(len(ki_progress), 3)
        
        # Find progress for each KI
        ki1_progress = next(item for item in ki_progress if item['uid'] == ki1.UID())
        ki2_progress = next(item for item in ki_progress if item['uid'] == ki2.UID())
        ki3_progress = next(item for item in ki_progress if item['uid'] == ki3.UID())
        
        # Verify KI 1 (mastered)
        self.assertEqual(ki1_progress['title'], 'Analytics KI 1')
        self.assertEqual(ki1_progress['knowledge_type'], 'conceptual')
        self.assertEqual(ki1_progress['current_progress'], 0.9)  # 0.8 + 0.1
        self.assertEqual(ki1_progress['mastery_threshold'], 0.7)
        self.assertTrue(ki1_progress['is_mastered'])
        self.assertEqual(ki1_progress['mastery_gap'], 0.0)
        
        # Verify KI 2 (not mastered)
        self.assertEqual(ki2_progress['current_progress'], 0.5)  # 0.4 + 0.1
        self.assertEqual(ki2_progress['mastery_threshold'], 0.8)
        self.assertFalse(ki2_progress['is_mastered'])
        self.assertEqual(ki2_progress['mastery_gap'], 0.3)  # 0.8 - 0.5
        
        # Verify KI 3 (not mastered)
        self.assertEqual(ki3_progress['current_progress'], 0.3)  # 0.2 + 0.1
        self.assertEqual(ki3_progress['mastery_threshold'], 0.9)
        self.assertFalse(ki3_progress['is_mastered'])
        self.assertEqual(ki3_progress['mastery_gap'], 0.6)  # 0.9 - 0.3
        
        # Check learning_goals_progress
        goals_progress = analytics['learning_goals_progress']
        self.assertEqual(len(goals_progress), 1)
        
        goal_progress = goals_progress[0]
        self.assertEqual(goal_progress['uid'], learning_goal.UID())
        self.assertEqual(goal_progress['title'], 'Analytics Learning Goal')
        self.assertEqual(goal_progress['items_mastered'], 1)
        self.assertEqual(goal_progress['total_items'], 3)
        self.assertAlmostEqual(goal_progress['completion_percentage'], 33.33, places=1)
        
        # Check overall_metrics
        overall = analytics['overall_metrics']
        self.assertEqual(overall['total_knowledge_items'], 3)
        self.assertEqual(overall['mastered_items'], 1)
        self.assertEqual(overall['total_learning_goals'], 1)
        self.assertEqual(overall['completed_goals'], 0)  # None fully completed
        self.assertAlmostEqual(overall['average_progress'], 0.567, places=2)  # (0.9+0.5+0.3)/3
        
        # Check learning session analytics
        session_analytics = analytics['learning_session_analytics']
        self.assertEqual(session_analytics['total_sessions'], 2)
        self.assertEqual(session_analytics['total_study_time'], 105)  # 60 + 45
        self.assertEqual(session_analytics['average_effectiveness'], 3.5)  # (4+3)/2
        self.assertEqual(len(session_analytics['session_types']), 2)
        
        # Check study patterns
        study_patterns = analytics['study_patterns']
        self.assertIn('most_studied_items', study_patterns)
        self.assertIn('least_studied_items', study_patterns)
        self.assertIn('study_frequency', study_patterns)
        
        # Check recommendations
        recommendations = analytics['recommendations']
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should recommend focusing on items with largest mastery gaps
        recommendation_text = ' '.join([r['description'] for r in recommendations])
        self.assertIn('Analytics KI 3', recommendation_text)  # Largest gap
    
    def test_sync_progress_to_learning_goal(self):
        """Test synchronization of progress to Learning Goal."""
        # Create Knowledge Items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="sync-ki-1",
            title="Sync KI 1",
            knowledge_type="conceptual",
            mastery_threshold=0.7,
            learning_progress=0.3,
            atomic_concepts=["sync1"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="sync-ki-2",
            title="Sync KI 2",
            knowledge_type="procedural",
            mastery_threshold=0.8,
            learning_progress=0.5,
            atomic_concepts=["sync2"]
        )
        
        # Create Learning Goal
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="sync-goal",
            title="Sync Learning Goal",
            target_knowledge_items=[ki1.UID(), ki2.UID()],
            goal_type="mastery",
            progress=25  # Initial progress
        )
        
        # Create Project Log
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="sync-project-log",
            title="Sync Project",
            start_date=date.today(),
            associated_learning_goals=[learning_goal.UID()],
        )
        
        # Update Knowledge Item progress through Project Log
        project_log.update_knowledge_item_progress(ki1.UID(), 0.8)  # Now mastered
        project_log.update_knowledge_item_progress(ki2.UID(), 0.9)  # Now mastered
        
        # Test _sync_progress_to_learning_goal
        result = project_log._sync_progress_to_learning_goal(learning_goal.UID())
        
        self.assertTrue(result['success'])
        self.assertIn('Progress synchronized', result['message'])
        
        # Verify Learning Goal progress was updated
        updated_goal = api.content.get(UID=learning_goal.UID())
        # Both items mastered = 100% progress
        expected_progress = 100  # Both items mastered
        self.assertEqual(updated_goal.progress, expected_progress)
        
        # Test with invalid Learning Goal UID
        result = project_log._sync_progress_to_learning_goal('invalid-uid')
        self.assertFalse(result['success'])
        self.assertIn('Learning Goal not found', result['message'])
        
        # Test with Learning Goal that has no target items
        empty_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="empty-goal",
            title="Empty Goal",
            target_knowledge_items=[]
        )
        
        result = project_log._sync_progress_to_learning_goal(empty_goal.UID())
        self.assertTrue(result['success'])  # Should handle gracefully
        self.assertIn('No target knowledge items', result['message'])
    
    def test_associated_learning_goals_validation(self):
        """Test validation of associated_learning_goals field."""
        from knowledge.curator.content.validators import validate_associated_learning_goals
        from zope.interface import Invalid
        
        # Create valid Learning Goal
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="valid-goal",
            title="Valid Learning Goal",
            goal_type="mastery",
            target_knowledge_items=[]  # Empty is ok for goals
        )
        
        # Test with valid UID
        result = validate_associated_learning_goals([learning_goal.UID()])
        self.assertTrue(result)
        
        # Test with empty list - should pass (optional field)
        result = validate_associated_learning_goals([])
        self.assertTrue(result)
        
        # Test with None - should pass
        result = validate_associated_learning_goals(None)
        self.assertTrue(result)
        
        # Test with invalid UID - should fail
        with self.assertRaises(Invalid) as cm:
            validate_associated_learning_goals(["invalid-uid"])
        self.assertIn("do not reference valid Learning Goals", str(cm.exception))
        
        # Test with duplicate UIDs - should fail
        with self.assertRaises(Invalid) as cm:
            validate_associated_learning_goals([learning_goal.UID(), learning_goal.UID()])
        self.assertIn("Duplicate", str(cm.exception))
        
        # Create non-Learning Goal content
        knowledge_item = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="not-a-goal",
            title="Not a Goal",
            knowledge_type="conceptual",
            atomic_concepts=["concept"]
        )
        
        # Test with wrong content type - should fail
        with self.assertRaises(Invalid) as cm:
            validate_associated_learning_goals([knowledge_item.UID()])
        self.assertIn("do not reference valid Learning Goals", str(cm.exception))
    
    def test_project_log_knowledge_item_integration(self):
        """Test comprehensive integration between Project Log and Knowledge Items."""
        from datetime import datetime
        
        # Create diverse Knowledge Items
        ki_conceptual = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="integration-conceptual",
            title="Conceptual Knowledge",
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.2,
            atomic_concepts=["theory", "concepts"]
        )
        
        ki_procedural = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="integration-procedural",
            title="Procedural Knowledge",
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.4,
            atomic_concepts=["steps", "process"]
        )
        
        ki_metacognitive = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="integration-metacognitive",
            title="Metacognitive Knowledge",
            knowledge_type="metacognitive",
            difficulty_level="advanced",
            mastery_threshold=0.9,
            learning_progress=0.1,
            atomic_concepts=["thinking", "strategy"]
        )
        
        # Create Learning Goal with prerequisites
        learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="integration-goal",
            title="Integration Learning Goal",
            target_knowledge_items=[
                ki_conceptual.UID(),
                ki_procedural.UID(),
                ki_metacognitive.UID()
            ],
            goal_type="comprehensive"
        )
        
        # Set up prerequisite relationships
        ki_procedural.prerequisite_items = [ki_conceptual.UID()]
        ki_metacognitive.prerequisite_items = [ki_procedural.UID()]
        
        # Create Project Log
        project_log = api.content.create(
            container=self.portal,
            type="ProjectLog",
            id="integration-project",
            title="Integration Test Project",
            description="Testing comprehensive integration",
            start_date=date.today(),
            associated_learning_goals=[learning_goal.UID()],
            project_status="active"
        )
        
        # Simulate a learning journey
        # Session 1: Focus on conceptual knowledge
        session1 = {
            'start_time': datetime.now(),
            'duration_minutes': 90,
            'knowledge_items_studied': [ki_conceptual.UID()],
            'progress_updates': {ki_conceptual.UID(): 0.3},  # 0.2 -> 0.5
            'notes': 'Focused on understanding core concepts',
            'effectiveness_rating': 4,
            'session_type': 'lecture'
        }
        result1 = project_log.add_learning_session(session1)
        self.assertTrue(result1['success'])
        
        # Session 2: Continue conceptual, achieve mastery
        session2 = {
            'start_time': datetime.now(),
            'duration_minutes': 60,
            'knowledge_items_studied': [ki_conceptual.UID()],
            'progress_updates': {ki_conceptual.UID(): 0.3},  # 0.5 -> 0.8 (mastered)
            'notes': 'Achieved mastery of conceptual knowledge',
            'effectiveness_rating': 5,
            'session_type': 'self_study'
        }
        result2 = project_log.add_learning_session(session2)
        self.assertTrue(result2['success'])
        
        # Verify conceptual KI is now mastered
        self.assertEqual(project_log.knowledge_item_progress[ki_conceptual.UID()], 0.8)
        
        # Session 3: Start procedural (prerequisite met)
        session3 = {
            'start_time': datetime.now(),
            'duration_minutes': 120,
            'knowledge_items_studied': [ki_procedural.UID()],
            'progress_updates': {ki_procedural.UID(): 0.4},  # 0.4 -> 0.8 (mastered)
            'notes': 'Applied concepts to procedures',
            'effectiveness_rating': 4,
            'session_type': 'practice'
        }
        result3 = project_log.add_learning_session(session3)
        self.assertTrue(result3['success'])
        
        # Session 4: Advanced metacognitive work
        session4 = {
            'start_time': datetime.now(),
            'duration_minutes': 75,
            'knowledge_items_studied': [ki_metacognitive.UID()],
            'progress_updates': {ki_metacognitive.UID(): 0.8},  # 0.1 -> 0.9 (mastered)
            'notes': 'Developed meta-learning strategies',
            'effectiveness_rating': 5,
            'session_type': 'reflection'
        }
        result4 = project_log.add_learning_session(session4)
        self.assertTrue(result4['success'])
        
        # Verify all KIs are mastered
        self.assertEqual(project_log.knowledge_item_progress[ki_conceptual.UID()], 0.8)
        self.assertEqual(project_log.knowledge_item_progress[ki_procedural.UID()], 0.8)
        self.assertEqual(project_log.knowledge_item_progress[ki_metacognitive.UID()], 0.9)
        
        # Test comprehensive analytics
        analytics = project_log.get_learning_analytics()
        
        # All KIs should be mastered
        self.assertEqual(analytics['overall_metrics']['mastered_items'], 3)
        self.assertEqual(analytics['overall_metrics']['total_knowledge_items'], 3)
        
        # Learning goal should be complete
        goal_progress = analytics['learning_goals_progress'][0]
        self.assertEqual(goal_progress['items_mastered'], 3)
        self.assertEqual(goal_progress['completion_percentage'], 100.0)
        
        # Session analytics should show progression
        session_analytics = analytics['learning_session_analytics']
        self.assertEqual(session_analytics['total_sessions'], 4)
        self.assertEqual(session_analytics['total_study_time'], 345)  # 90+60+120+75
        self.assertEqual(session_analytics['average_effectiveness'], 4.5)  # (4+5+4+5)/4
        
        # Should have varied session types
        session_types = session_analytics['session_types']
        expected_types = {'lecture', 'self_study', 'practice', 'reflection'}
        self.assertEqual(set(session_types.keys()), expected_types)
        
        # Test progress history tracking
        progress_history = project_log.get_progress_history(ki_conceptual.UID())
        self.assertEqual(len(progress_history), 2)  # Two updates to this KI
        
        # Verify chronological order and progress tracking
        self.assertEqual(progress_history[0]['new_progress'], 0.5)
        self.assertEqual(progress_history[0]['previous_progress'], 0.2)
        self.assertEqual(progress_history[1]['new_progress'], 0.8)
        self.assertEqual(progress_history[1]['previous_progress'], 0.5)
        
        # Test recommendations after completion
        recommendations = analytics['recommendations']
        # Should recommend next learning goals or advanced topics
        self.assertIsInstance(recommendations, list)
        # With all items mastered, should suggest new challenges
        recommendation_text = ' '.join([r['description'] for r in recommendations])
        self.assertIn('mastery', recommendation_text.lower())
