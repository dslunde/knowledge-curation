"""Tests for workflow functionality."""

<<<<<<< HEAD
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
=======
import unittest

>>>>>>> fixing_linting_and_tests
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.annotation.interfaces import IAnnotations
<<<<<<< HEAD

import unittest
=======
>>>>>>> fixing_linting_and_tests


class TestKnowledgeWorkflow(unittest.TestCase):
    """Test knowledge workflow functionality."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Set up test environment."""
<<<<<<< HEAD
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        setRoles(self.portal, TEST_USER_ID, ["Manager"])
=======
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
>>>>>>> fixing_linting_and_tests

        # Create test content
        self.research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            title="Test Research Note",
            description="A test research note",
            text="Some research content",
            tags=["test", "research"],
        )

    def tearDown(self):
        """Clean up test environment."""
        api.content.delete(self.research_note)

    def test_initial_state(self):
        """Test that content starts in capture state."""
<<<<<<< HEAD
        self.assertEqual(api.content.get_state(self.research_note), "capture")
=======
        self.assertEqual(
            api.content.get_state(self.research_note),
            'capture'
        )
>>>>>>> fixing_linting_and_tests

    def test_capture_to_process_transition(self):
        """Test transition from capture to process state."""
        # Transition to process state
<<<<<<< HEAD
        api.content.transition(obj=self.research_note, transition="start_processing")

        self.assertEqual(api.content.get_state(self.research_note), "process")
=======
        api.content.transition(
            obj=self.research_note,
            transition='start_processing'
        )

        self.assertEqual(
            api.content.get_state(self.research_note),
            'process'
        )
>>>>>>> fixing_linting_and_tests

    def test_process_to_connect_transition(self):
        """Test transition from process to connect state."""
        # First move to process
<<<<<<< HEAD
        api.content.transition(obj=self.research_note, transition="start_processing")

        # Add AI summary (required for connect transition)
        self.research_note.ai_summary = "AI generated summary"

        # Then to connect
        api.content.transition(obj=self.research_note, transition="start_connecting")

        self.assertEqual(api.content.get_state(self.research_note), "connect")
=======
        api.content.transition(
            obj=self.research_note,
            transition='start_processing'
        )

        # Add AI summary (required for connect transition)
        self.research_note.ai_summary = 'AI generated summary'

        # Then to connect
        api.content.transition(
            obj=self.research_note,
            transition='start_connecting'
        )

        self.assertEqual(
            api.content.get_state(self.research_note),
            'connect'
        )
>>>>>>> fixing_linting_and_tests

    def test_connect_to_publish_transition(self):
        """Test transition from connect to published state."""
        # Move through states
<<<<<<< HEAD
        api.content.transition(obj=self.research_note, transition="start_processing")

        self.research_note.ai_summary = "AI generated summary"

        api.content.transition(obj=self.research_note, transition="start_connecting")

        # Publish
        api.content.transition(obj=self.research_note, transition="ready_to_publish")

        self.assertEqual(api.content.get_state(self.research_note), "published")
=======
        api.content.transition(
            obj=self.research_note,
            transition='start_processing'
        )

        self.research_note.ai_summary = 'AI generated summary'

        api.content.transition(
            obj=self.research_note,
            transition='start_connecting'
        )

        # Publish
        api.content.transition(
            obj=self.research_note,
            transition='ready_to_publish'
        )

        self.assertEqual(
            api.content.get_state(self.research_note),
            'published'
        )
>>>>>>> fixing_linting_and_tests

    def test_transition_guards(self):
        """Test workflow transition guards."""
        # Try to transition without required fields
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            title="",  # Empty title
        )

        # Should fail due to guard
        with self.assertRaises(WorkflowException):
<<<<<<< HEAD
            api.content.transition(obj=research_note, transition="start_processing")
=======
            api.content.transition(
                obj=research_note,
                transition='start_processing'
            )
>>>>>>> fixing_linting_and_tests

        api.content.delete(research_note)

    def test_workflow_history(self):
        """Test workflow history tracking."""
        # Make a transition with comment
        api.content.transition(
            obj=self.research_note,
            transition="start_processing",
            comment="Starting processing phase",
        )

<<<<<<< HEAD
        workflow_tool = api.portal.get_tool("portal_workflow")
        history = workflow_tool.getInfoFor(self.research_note, "review_history")

        self.assertTrue(len(history) > 0)
        last_entry = history[-1]
        self.assertEqual(last_entry["action"], "start_processing")
        self.assertEqual(last_entry["comments"], "Starting processing phase")
        self.assertEqual(last_entry["actor"], TEST_USER_ID)
=======
        workflow_tool = api.portal.get_tool('portal_workflow')
        history = workflow_tool.getInfoFor(self.research_note, 'review_history')

        self.assertTrue(len(history) > 0)
        last_entry = history[-1]
        self.assertEqual(last_entry['action'], 'start_processing')
        self.assertEqual(last_entry['comments'], 'Starting processing phase')
        self.assertEqual(last_entry['actor'], TEST_USER_ID)
>>>>>>> fixing_linting_and_tests

    def test_permissions_by_state(self):
        """Test permissions change with workflow state."""
        # In capture state, owner can modify
        self.assertTrue(
            api.user.has_permission("Modify portal content", obj=self.research_note)
        )

        # Move to published state
<<<<<<< HEAD
        api.content.transition(obj=self.research_note, transition="start_processing")
        self.research_note.ai_summary = "Summary"
        api.content.transition(obj=self.research_note, transition="start_connecting")
        api.content.transition(obj=self.research_note, transition="ready_to_publish")
=======
        api.content.transition(
            obj=self.research_note,
            transition='start_processing'
        )
        self.research_note.ai_summary = 'Summary'
        api.content.transition(
            obj=self.research_note,
            transition='start_connecting'
        )
        api.content.transition(
            obj=self.research_note,
            transition='ready_to_publish'
        )
>>>>>>> fixing_linting_and_tests

        # Anonymous can view published content
        setRoles(self.portal, TEST_USER_ID, ["Anonymous"])
        self.assertTrue(api.user.has_permission("View", obj=self.research_note))


class TestLearningGoalWorkflow(unittest.TestCase):
    """Test learning goal workflow functionality."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Set up test environment."""
<<<<<<< HEAD
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        setRoles(self.portal, TEST_USER_ID, ["Manager"])
=======
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
>>>>>>> fixing_linting_and_tests

        # Create test learning goal
        self.learning_goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            title="Test Learning Goal",
            description="Learn something new",
            milestones=[
                {"title": "Milestone 1", "completed": False},
                {"title": "Milestone 2", "completed": False},
            ],
        )

    def tearDown(self):
        """Clean up test environment."""
        api.content.delete(self.learning_goal)

    def test_initial_state_planning(self):
        """Test that learning goals start in planning state."""
<<<<<<< HEAD
        self.assertEqual(api.content.get_state(self.learning_goal), "planning")

    def test_activate_learning_goal(self):
        """Test activating a learning goal."""
        api.content.transition(obj=self.learning_goal, transition="activate")

        self.assertEqual(api.content.get_state(self.learning_goal), "active")

        # Check that start time was recorded
        annotations = IAnnotations(self.learning_goal)
        timeline = annotations.get("knowledge.curator.learning_timeline", {})
        self.assertIn("started_at", timeline)
=======
        self.assertEqual(
            api.content.get_state(self.learning_goal),
            'planning'
        )

    def test_activate_learning_goal(self):
        """Test activating a learning goal."""
        api.content.transition(
            obj=self.learning_goal,
            transition='activate'
        )

        self.assertEqual(
            api.content.get_state(self.learning_goal),
            'active'
        )

        # Check that start time was recorded
        annotations = IAnnotations(self.learning_goal)
        timeline = annotations.get('knowledge.curator.learning_timeline', {})
        self.assertIn('started_at', timeline)
>>>>>>> fixing_linting_and_tests

    def test_pause_and_resume(self):
        """Test pausing and resuming a learning goal."""
        # Activate first
<<<<<<< HEAD
        api.content.transition(obj=self.learning_goal, transition="activate")

        # Pause
        api.content.transition(obj=self.learning_goal, transition="pause")

        self.assertEqual(api.content.get_state(self.learning_goal), "paused")

        # Resume
        api.content.transition(obj=self.learning_goal, transition="resume")

        self.assertEqual(api.content.get_state(self.learning_goal), "active")
=======
        api.content.transition(
            obj=self.learning_goal,
            transition='activate'
        )

        # Pause
        api.content.transition(
            obj=self.learning_goal,
            transition='pause'
        )

        self.assertEqual(
            api.content.get_state(self.learning_goal),
            'paused'
        )

        # Resume
        api.content.transition(
            obj=self.learning_goal,
            transition='resume'
        )

        self.assertEqual(
            api.content.get_state(self.learning_goal),
            'active'
        )
>>>>>>> fixing_linting_and_tests

    def test_complete_learning_goal(self):
        """Test completing a learning goal."""
        # Activate
<<<<<<< HEAD
        api.content.transition(obj=self.learning_goal, transition="activate")

        # Start review
        api.content.transition(obj=self.learning_goal, transition="start_review")

        # Set progress and reflection
        self.learning_goal.progress = 85.0
        self.learning_goal.reflection = "I learned a lot!"

        # Complete
        api.content.transition(obj=self.learning_goal, transition="complete")

        self.assertEqual(api.content.get_state(self.learning_goal), "completed")
=======
        api.content.transition(
            obj=self.learning_goal,
            transition='activate'
        )

        # Start review
        api.content.transition(
            obj=self.learning_goal,
            transition='start_review'
        )

        # Set progress and reflection
        self.learning_goal.progress = 85.0
        self.learning_goal.reflection = 'I learned a lot!'

        # Complete
        api.content.transition(
            obj=self.learning_goal,
            transition='complete'
        )

        self.assertEqual(
            api.content.get_state(self.learning_goal),
            'completed'
        )
>>>>>>> fixing_linting_and_tests

        # Check completion was recorded
        annotations = IAnnotations(self.learning_goal)
        timeline = annotations.get("knowledge.curator.learning_timeline", {})
        self.assertIn("completed_at", timeline)
        self.assertEqual(self.learning_goal.progress, 100.0)

    def test_abandon_learning_goal(self):
        """Test abandoning a learning goal."""
        # Activate
<<<<<<< HEAD
        api.content.transition(obj=self.learning_goal, transition="activate")

        # Abandon
        api.content.transition(obj=self.learning_goal, transition="abandon")

        self.assertEqual(api.content.get_state(self.learning_goal), "abandoned")

        # Check abandonment was recorded
        annotations = IAnnotations(self.learning_goal)
        self.assertIn("knowledge.curator.abandoned", annotations)
=======
        api.content.transition(
            obj=self.learning_goal,
            transition='activate'
        )

        # Abandon
        api.content.transition(
            obj=self.learning_goal,
            transition='abandon'
        )

        self.assertEqual(
            api.content.get_state(self.learning_goal),
            'abandoned'
        )

        # Check abandonment was recorded
        annotations = IAnnotations(self.learning_goal)
        self.assertIn('knowledge.curator.abandoned', annotations)
>>>>>>> fixing_linting_and_tests

    def test_completion_guard(self):
        """Test that completion requires minimum progress."""
        # Activate and review
<<<<<<< HEAD
        api.content.transition(obj=self.learning_goal, transition="activate")
        api.content.transition(obj=self.learning_goal, transition="start_review")
=======
        api.content.transition(
            obj=self.learning_goal,
            transition='activate'
        )
        api.content.transition(
            obj=self.learning_goal,
            transition='start_review'
        )
>>>>>>> fixing_linting_and_tests

        # Try to complete with low progress
        self.learning_goal.progress = 50.0

        with self.assertRaises(WorkflowException):
            api.content.transition(obj=self.learning_goal, transition="complete")


class TestWorkflowViews(unittest.TestCase):
    """Test workflow-related views."""

    layer = PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING

    def setUp(self):
        """Set up test environment."""
<<<<<<< HEAD
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        setRoles(self.portal, TEST_USER_ID, ["Manager"])
=======
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
>>>>>>> fixing_linting_and_tests

        self.research_note = api.content.create(
            container=self.portal, type="ResearchNote", title="Test Note", tags=["test"]
        )

    def tearDown(self):
        """Clean up test environment."""
        api.content.delete(self.research_note)

    def test_workflow_history_view(self):
        """Test workflow history view."""
        # Make some transitions
        api.content.transition(
            obj=self.research_note,
            transition="start_processing",
            comment="Test comment",
        )

        # Access history view
        view = api.content.get_view(
            name="workflow-history", context=self.research_note, request=self.request
        )

        view.update()
        self.assertTrue(len(view.history) > 0)

        # Check history entry
        entry = view.history[0]
<<<<<<< HEAD
        self.assertEqual(entry["action"], "start_processing")
        self.assertEqual(entry["comments"], "Test comment")
=======
        self.assertEqual(entry['action'], 'start_processing')
        self.assertEqual(entry['comments'], 'Test comment')
>>>>>>> fixing_linting_and_tests

    def test_bulk_workflow_view(self):
        """Test bulk workflow operations."""
        # Create multiple items
        note2 = api.content.create(
            container=self.portal,
            type="ResearchNote",
            title="Test Note 2",
            tags=["test"],
        )

        # Prepare request for bulk view
<<<<<<< HEAD
        self.request["uids"] = [self.research_note.UID(), note2.UID()]
=======
        self.request['uids'] = [
            self.research_note.UID(),
            note2.UID()
        ]
>>>>>>> fixing_linting_and_tests

        view = api.content.get_view(
            name="bulk-workflow", context=self.portal, request=self.request
        )

        # Get available transitions
        transitions = view.get_available_transitions()
        self.assertTrue(len(transitions) > 0)

        # Clean up
        api.content.delete(note2)
