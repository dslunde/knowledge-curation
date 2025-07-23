"""Tests for Learning Goal content type."""

import unittest
from datetime import date, datetime
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject, queryUtility

from knowledge.curator.interfaces import ILearningGoal
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING


class LearningGoalIntegrationTest(unittest.TestCase):
    """Test Learning Goal content type."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_ct_learning_goal_schema(self):
        """Test that Learning Goal schema is correct."""
        fti = queryUtility(IDexterityFTI, name='LearningGoal')
        schema = fti.lookupSchema()
        self.assertEqual(ILearningGoal, schema)

    def test_ct_learning_goal_fti(self):
        """Test that Learning Goal FTI is properly installed."""
        fti = queryUtility(IDexterityFTI, name='LearningGoal')
        self.assertTrue(fti)

    def test_ct_learning_goal_factory(self):
        """Test that Learning Goal factory is properly set."""
        fti = queryUtility(IDexterityFTI, name='LearningGoal')
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
            ILearningGoal.providedBy(obj),
            'ILearningGoal not provided by {0}'.format(obj)
        )

    def test_ct_learning_goal_adding(self):
        """Test that Learning Goal can be added."""
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        obj = api.content.create(
            container=self.portal,
            type='LearningGoal',
            id='learning-goal',
            title='Learn Python',
            description='Master Python programming',
            priority='high',
        )
        self.assertTrue(
            ILearningGoal.providedBy(obj),
            'ILearningGoal not provided by {0}'.format(obj.id)
        )
        # Check fields
        self.assertEqual(obj.title, 'Learn Python')
        self.assertEqual(obj.priority, 'high')
        self.assertEqual(obj.progress, 0)

    def test_ct_learning_goal_milestone_methods(self):
        """Test Learning Goal milestone methods."""
        obj = api.content.create(
            container=self.portal,
            type='LearningGoal',
            id='goal-with-milestones',
        )
        
        # Test adding milestones
        m1 = obj.add_milestone(
            'Learn basics',
            'Complete Python tutorial',
            target_date=date(2024, 12, 31)
        )
        self.assertEqual(m1['title'], 'Learn basics')
        self.assertFalse(m1['completed'])
        
        # Test updating milestone
        obj.update_milestone(m1['id'], completed=True)
        updated = obj.milestones[0]
        self.assertTrue(updated['completed'])
        self.assertIsNotNone(updated['completed_date'])
        
        # Test progress calculation
        obj.add_milestone('Advanced topics', 'Learn advanced Python')
        progress = obj.calculate_progress()
        self.assertEqual(progress, 50)  # 1 of 2 completed
        
        obj.update_progress()
        self.assertEqual(obj.progress, 50)

    def test_ct_learning_goal_overdue(self):
        """Test Learning Goal overdue check."""
        obj = api.content.create(
            container=self.portal,
            type='LearningGoal',
            id='overdue-goal',
            target_date=date(2020, 1, 1),  # Past date
            progress=50,
        )
        self.assertTrue(obj.is_overdue())
        
        # Complete the goal
        obj.progress = 100
        self.assertFalse(obj.is_overdue())

    def test_ct_learning_goal_related_notes(self):
        """Test Learning Goal related notes methods."""
        obj = api.content.create(
            container=self.portal,
            type='LearningGoal',
            id='goal-with-notes',
        )
        
        # Test adding related notes
        obj.add_related_note('note-uid-1')
        self.assertIn('note-uid-1', obj.related_notes)
        
        # Test duplicate prevention
        obj.add_related_note('note-uid-1')
        self.assertEqual(len(obj.related_notes), 1)
        
        # Test removing
        obj.remove_related_note('note-uid-1')
        self.assertEqual(len(obj.related_notes), 0)