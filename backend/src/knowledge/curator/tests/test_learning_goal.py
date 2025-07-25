"""Tests for Learning Goal content type."""

import unittest
from datetime import date
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
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_ct_learning_goal_schema(self):
        """Test that Learning Goal schema is correct."""
        fti = queryUtility(IDexterityFTI, name="LearningGoal")
        schema = fti.lookupSchema()
        self.assertEqual(ILearningGoal, schema)

    def test_ct_learning_goal_fti(self):
        """Test that Learning Goal FTI is properly installed."""
        fti = queryUtility(IDexterityFTI, name="LearningGoal")
        self.assertTrue(fti)

    def test_ct_learning_goal_factory(self):
        """Test that Learning Goal factory is properly set."""
        fti = queryUtility(IDexterityFTI, name="LearningGoal")
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
            ILearningGoal.providedBy(obj), f"ILearningGoal not provided by {obj}"
        )

    def test_ct_learning_goal_adding(self):
        """Test that Learning Goal can be added."""
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="learning-goal",
            title="Learn Python",
            description="Master Python programming",
            priority="high",
        )
        self.assertTrue(
            ILearningGoal.providedBy(obj), f"ILearningGoal not provided by {obj.id}"
        )
        # Check fields
        self.assertEqual(obj.title, "Learn Python")
        self.assertEqual(obj.priority, "high")
        self.assertEqual(obj.progress, 0)

    def test_ct_learning_goal_milestone_methods(self):
        """Test Learning Goal milestone methods."""
        obj = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-with-milestones",
        )

        # Test adding milestones
        m1 = obj.add_milestone(
            "Learn basics", "Complete Python tutorial", target_date=date(2024, 12, 31)
        )
        self.assertEqual(m1["title"], "Learn basics")
        self.assertEqual(m1["status"], "not_started")
        self.assertEqual(m1["progress_percentage"], 0)

        # Test updating milestone
        obj.update_milestone(m1["id"], status="completed", progress_percentage=100)
        updated = obj.milestones[0]
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["progress_percentage"], 100)
        self.assertIsNotNone(updated.get("completed_date"))

        # Test progress calculation
        obj.add_milestone("Advanced topics", "Learn advanced Python")
        progress = obj.calculate_progress()
        self.assertEqual(progress, 50)  # 1 of 2 completed (100% + 0% / 2)

        obj.update_progress()
        self.assertEqual(obj.progress, 50)

    def test_ct_learning_goal_overdue(self):
        """Test Learning Goal overdue check."""
        obj = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="overdue-goal",
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
            type="LearningGoal",
            id="goal-with-notes",
        )

        # Test adding related notes
        obj.add_related_note("note-uid-1")
        self.assertIn("note-uid-1", obj.related_notes)

        # Test duplicate prevention
        obj.add_related_note("note-uid-1")
        self.assertEqual(len(obj.related_notes), 1)

        # Test removing
        obj.remove_related_note("note-uid-1")
        self.assertEqual(len(obj.related_notes), 0)
    
    def test_ct_learning_goal_milestone_migration(self):
        """Test migration of legacy milestones."""
        obj = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-legacy-milestones",
        )
        
        # Simulate legacy milestones
        from persistent.list import PersistentList
        obj.milestones = PersistentList([
            "Complete chapter 1",
            "Finish exercises",
            {"title": "Final exam", "completed": True}
        ])
        
        # Run migration
        migrated = obj.migrate_legacy_milestones()
        self.assertTrue(migrated)
        
        # Check migrated milestones
        self.assertEqual(len(obj.milestones), 3)
        self.assertEqual(obj.milestones[0]["title"], "Complete chapter 1")
        self.assertEqual(obj.milestones[0]["status"], "not_started")
        self.assertEqual(obj.milestones[1]["title"], "Finish exercises")
        self.assertEqual(obj.milestones[2]["title"], "Final exam")
        self.assertEqual(obj.milestones[2]["status"], "completed")
        self.assertEqual(obj.milestones[2]["progress_percentage"], 100)
    
    def test_validate_learning_path_missing_fields(self):
        """Test validate_learning_path with missing required fields."""
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-missing-fields",
            title="Test Goal"
        )
        
        # Test with no starting item
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertIn("No starting knowledge item defined", result['errors'][0])
        
        # Test with starting item but no targets
        goal.starting_knowledge_item = "test-uid"
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertIn("No target knowledge items defined", result['errors'][0])
        
        # Test with starting and targets but no connections
        goal.target_knowledge_items = ["target-uid"]
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertIn("No connections defined", result['errors'][0])
    
    def test_validate_learning_path_cycle_detection(self):
        """Test cycle detection in learning path validation."""
        # Create knowledge items
        from plone.app.textfield.value import RichTextValue
        
        item1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item1",
            title="Item 1",
            description="Test item 1",
            content=RichTextValue("Content 1", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["concept1"]
        )
        item2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item2",
            title="Item 2",
            description="Test item 2",
            content=RichTextValue("Content 2", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["concept2"]
        )
        item3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item3",
            title="Item 3",
            description="Test item 3",
            content=RichTextValue("Content 3", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["concept3"]
        )
        
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-with-cycle",
            title="Goal with Cycle"
        )
        
        goal.starting_knowledge_item = item1.UID()
        goal.target_knowledge_items = [item3.UID()]
        
        # Create a cycle: item1 -> item2 -> item3 -> item1
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            PersistentMapping({
                'source_item_uid': item2.UID(),
                'target_item_uid': item3.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            PersistentMapping({
                'source_item_uid': item3.UID(),
                'target_item_uid': item1.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            })
        ])
        
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertTrue(any("Cycle detected" in error for error in result['errors']))
    
    def test_validate_learning_path_connectivity(self):
        """Test connectivity validation in learning paths."""
        # Create knowledge items
        from plone.app.textfield.value import RichTextValue
        
        item1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item-start",
            title="Starting Item",
            description="Starting item description",
            content=RichTextValue("Starting content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["start_concept"]
        )
        item2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item-middle",
            title="Middle Item",
            description="Middle item description",
            content=RichTextValue("Middle content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["middle_concept"]
        )
        item3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item-target",
            title="Target Item",
            description="Target item description",
            content=RichTextValue("Target content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["target_concept"]
        )
        item4 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="item-unreachable",
            title="Unreachable Item",
            description="Unreachable item description",
            content=RichTextValue("Unreachable content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["unreachable_concept"]
        )
        
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-connectivity",
            title="Goal Connectivity Test"
        )
        
        goal.starting_knowledge_item = item1.UID()
        goal.target_knowledge_items = [item3.UID(), item4.UID()]
        
        # Create connections that don't reach item4
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            PersistentMapping({
                'source_item_uid': item2.UID(),
                'target_item_uid': item3.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            })
        ])
        
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertTrue(any("not reachable from starting item" in error for error in result['errors']))
    
    def test_validate_learning_path_orphaned_items(self):
        """Test orphaned items detection in learning paths."""
        # Create knowledge items
        from plone.app.textfield.value import RichTextValue
        
        item1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="orphan-start",
            title="Start",
            description="Start description",
            content=RichTextValue("Start content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["start"]
        )
        item2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="orphan-middle",
            title="Middle",
            description="Middle description",
            content=RichTextValue("Middle content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["middle"]
        )
        item3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="orphan-target",
            title="Target",
            description="Target description",
            content=RichTextValue("Target content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["target"]
        )
        item4 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="orphan-isolated",
            title="Orphaned Item",
            description="Orphaned description",
            content=RichTextValue("Orphaned content", "text/plain", "text/html"),
            knowledge_type="factual",
            atomic_concepts=["orphan1"]
        )
        item5 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="orphan-other",
            title="Another Orphan",
            description="Another orphan description",
            content=RichTextValue("Another orphan content", "text/plain", "text/html"),
            knowledge_type="factual",
            atomic_concepts=["orphan2"]
        )
        
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-orphans",
            title="Goal with Orphans"
        )
        
        goal.starting_knowledge_item = item1.UID()
        goal.target_knowledge_items = [item3.UID()]
        
        # Create connections with orphaned items
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            PersistentMapping({
                'source_item_uid': item2.UID(),
                'target_item_uid': item3.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            # Orphaned connection
            PersistentMapping({
                'source_item_uid': item4.UID(),
                'target_item_uid': item5.UID(),
                'connection_type': 'builds_on',
                'strength': 0.5,
                'mastery_requirement': 0.6
            })
        ])
        
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertTrue(any("orphaned" in error for error in result['errors']))
    
    def test_validate_learning_path_strength_consistency(self):
        """Test connection strength and mastery requirement consistency."""
        # Create knowledge items
        from plone.app.textfield.value import RichTextValue
        
        item1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="strength-item1",
            title="Item 1",
            description="Item 1 description",
            content=RichTextValue("Item 1 content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["strength1"]
        )
        item2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="strength-item2",
            title="Item 2",
            description="Item 2 description",
            content=RichTextValue("Item 2 content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["strength2"]
        )
        item3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="strength-item3",
            title="Item 3",
            description="Item 3 description",
            content=RichTextValue("Item 3 content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["strength3"]
        )
        
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-strength",
            title="Goal Strength Test"
        )
        
        goal.starting_knowledge_item = item1.UID()
        goal.target_knowledge_items = [item3.UID()]
        
        # Create connections with inconsistent strengths
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            # Prerequisite with low mastery requirement
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.3,  # Too low for prerequisite
                'mastery_requirement': 0.5  # Too low for prerequisite
            }),
            # Builds-on with inappropriate strength
            PersistentMapping({
                'source_item_uid': item2.UID(),
                'target_item_uid': item3.UID(),
                'connection_type': 'builds_on',
                'strength': 0.9,  # Too high for builds-on
                'mastery_requirement': 0.6
            })
        ])
        
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertTrue(any("low mastery requirement" in error for error in result['errors']))
        self.assertTrue(any("low strength" in error for error in result['errors']))
        self.assertTrue(any("inappropriate strength" in error for error in result['errors']))
    
    def test_validate_learning_path_duplicate_connections(self):
        """Test duplicate connection detection."""
        # Create knowledge items
        from plone.app.textfield.value import RichTextValue
        
        item1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="dup-item1",
            title="Item 1",
            description="Item 1 description",
            content=RichTextValue("Item 1 content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["dup1"]
        )
        item2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="dup-item2",
            title="Item 2",
            description="Item 2 description",
            content=RichTextValue("Item 2 content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["dup2"]
        )
        
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-duplicates",
            title="Goal with Duplicates"
        )
        
        goal.starting_knowledge_item = item1.UID()
        goal.target_knowledge_items = [item2.UID()]
        
        # Create duplicate connections
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            # Duplicate connection with different parameters
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'builds_on',
                'strength': 0.5,
                'mastery_requirement': 0.6
            })
        ])
        
        result = goal.validate_learning_path()
        self.assertFalse(result['valid'])
        self.assertTrue(any("Duplicate connection" in error for error in result['errors']))
    
    def test_validate_learning_path_valid_graph(self):
        """Test validation of a valid learning path graph."""
        # Create knowledge items
        from plone.app.textfield.value import RichTextValue
        
        item1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="valid-item1",
            title="Basic Concepts",
            description="Basic concepts description",
            content=RichTextValue("Basic concepts content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["basic1", "basic2"]
        )
        item2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="valid-item2",
            title="Intermediate Concepts",
            description="Intermediate concepts description",
            content=RichTextValue("Intermediate concepts content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["intermediate1", "intermediate2"]
        )
        item3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="valid-item3",
            title="Advanced Concepts",
            description="Advanced concepts description",
            content=RichTextValue("Advanced concepts content", "text/plain", "text/html"),
            knowledge_type="metacognitive",
            atomic_concepts=["advanced1", "advanced2"]
        )
        
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-valid",
            title="Valid Learning Path"
        )
        
        goal.starting_knowledge_item = item1.UID()
        goal.target_knowledge_items = [item3.UID()]
        
        # Create valid connections
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            PersistentMapping({
                'source_item_uid': item1.UID(),
                'target_item_uid': item2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            }),
            PersistentMapping({
                'source_item_uid': item2.UID(),
                'target_item_uid': item3.UID(),
                'connection_type': 'builds_on',
                'strength': 0.6,
                'mastery_requirement': 0.7
            })
        ])
        
        result = goal.validate_learning_path()
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_calculate_overall_progress(self):
        """Test overall progress calculation with various mastery levels."""
        # Create a learning path with multiple knowledge items
        from plone.app.textfield.value import RichTextValue
        
        # Create knowledge items
        start_item = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="progress-start",
            title="Starting Knowledge",
            description="Starting knowledge description",
            content=RichTextValue("Starting content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["start"]
        )
        
        prereq1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="progress-prereq1",
            title="Prerequisite 1",
            description="First prerequisite",
            content=RichTextValue("Prereq 1 content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["prereq1"]
        )
        
        prereq2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="progress-prereq2",
            title="Prerequisite 2",
            description="Second prerequisite",
            content=RichTextValue("Prereq 2 content", "text/plain", "text/html"),
            knowledge_type="factual",
            atomic_concepts=["prereq2"]
        )
        
        intermediate = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="progress-intermediate",
            title="Intermediate Knowledge",
            description="Intermediate level knowledge",
            content=RichTextValue("Intermediate content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["intermediate"]
        )
        
        advanced = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="progress-advanced",
            title="Advanced Knowledge",
            description="Advanced level knowledge",
            content=RichTextValue("Advanced content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["advanced"]
        )
        
        target = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="progress-target",
            title="Target Knowledge",
            description="Target knowledge to achieve",
            content=RichTextValue("Target content", "text/plain", "text/html"),
            knowledge_type="metacognitive",
            atomic_concepts=["target"]
        )
        
        # Create learning goal
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-progress",
            title="Learning Goal with Progress"
        )
        
        goal.starting_knowledge_item = start_item.UID()
        goal.target_knowledge_items = [target.UID()]
        
        # Create connections forming a learning graph
        from persistent.mapping import PersistentMapping
        from persistent.list import PersistentList
        
        goal.knowledge_item_connections = PersistentList([
            # From start to prerequisites
            PersistentMapping({
                'source_item_uid': start_item.UID(),
                'target_item_uid': prereq1.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.7
            }),
            PersistentMapping({
                'source_item_uid': start_item.UID(),
                'target_item_uid': prereq2.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.7,
                'mastery_requirement': 0.7
            }),
            # Prerequisites to intermediate
            PersistentMapping({
                'source_item_uid': prereq1.UID(),
                'target_item_uid': intermediate.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.9,
                'mastery_requirement': 0.8
            }),
            PersistentMapping({
                'source_item_uid': prereq2.UID(),
                'target_item_uid': intermediate.UID(),
                'connection_type': 'builds_on',
                'strength': 0.5,
                'mastery_requirement': 0.6
            }),
            # Intermediate to advanced
            PersistentMapping({
                'source_item_uid': intermediate.UID(),
                'target_item_uid': advanced.UID(),
                'connection_type': 'builds_on',
                'strength': 0.6,
                'mastery_requirement': 0.7
            }),
            # Advanced to target
            PersistentMapping({
                'source_item_uid': advanced.UID(),
                'target_item_uid': target.UID(),
                'connection_type': 'prerequisite',
                'strength': 0.8,
                'mastery_requirement': 0.8
            })
        ])
        
        # Test 1: No mastery
        result = goal.calculate_overall_progress()
        self.assertEqual(result['overall_percentage'], 0)
        self.assertEqual(result['items_mastered'], 0)
        self.assertEqual(result['total_items'], 6)
        self.assertEqual(result['prerequisite_satisfaction'], 0.0)
        self.assertEqual(len(result['bottlenecks']), 0)  # No bottlenecks when nothing started
        self.assertEqual(len(result['next_milestones']), 0)
        
        # Test 2: Partial mastery
        mastery_levels = {
            start_item.UID(): 1.0,  # Fully mastered
            prereq1.UID(): 0.8,     # Mastered
            prereq2.UID(): 0.6,     # Partially mastered
            intermediate.UID(): 0.3, # Started
            advanced.UID(): 0.0,     # Not started
            target.UID(): 0.0        # Not started
        }
        
        result = goal.calculate_overall_progress(mastery_levels)
        self.assertGreater(result['overall_percentage'], 0)
        self.assertLess(result['overall_percentage'], 100)
        self.assertEqual(result['items_mastered'], 2)  # start_item and prereq1
        self.assertEqual(result['total_items'], 6)
        
        # Check bottlenecks - advanced should be a bottleneck since it's prerequisite for target
        bottleneck_uids = [b['item_uid'] for b in result['bottlenecks']]
        self.assertIn(advanced.UID(), bottleneck_uids)
        
        # Check next milestones - prereq2 should be a next milestone
        milestone_uids = [m['item_uid'] for m in result['next_milestones']]
        self.assertIn(prereq2.UID(), milestone_uids)
        
        # Check prerequisite satisfaction
        # We have 3 prerequisite connections, 1 is satisfied (start->prereq1)
        self.assertGreater(result['prerequisite_satisfaction'], 0)
        self.assertLess(result['prerequisite_satisfaction'], 100)
        
        # Test 3: Full mastery
        full_mastery = {uid: 1.0 for uid in mastery_levels.keys()}
        result = goal.calculate_overall_progress(full_mastery)
        self.assertEqual(result['overall_percentage'], 100)
        self.assertEqual(result['items_mastered'], 6)
        self.assertEqual(result['prerequisite_satisfaction'], 100.0)
        self.assertEqual(len(result['bottlenecks']), 0)
        self.assertEqual(len(result['next_milestones']), 0)
        
        # Test 4: Check visualization data
        result = goal.calculate_overall_progress(mastery_levels)
        
        # Check nodes
        self.assertEqual(len(result['visualization_data']['nodes']), 6)
        node_ids = [n['id'] for n in result['visualization_data']['nodes']]
        self.assertIn(start_item.UID(), node_ids)
        self.assertIn(target.UID(), node_ids)
        
        # Check edges
        self.assertEqual(len(result['visualization_data']['edges']), 6)
        
        # Check progress by level
        progress_by_level = result['visualization_data']['progress_by_level']
        self.assertIn(0, progress_by_level)  # Starting level
        self.assertGreater(len(progress_by_level), 1)  # Multiple levels
        
        # Check path segments
        self.assertGreater(len(result['path_segments']), 0)
        first_segment = result['path_segments'][0]
        self.assertEqual(first_segment['description'], 'Starting Knowledge')
        
        # Test 5: Test with missing connections (edge case)
        goal_empty = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-empty-progress",
            title="Empty Goal"
        )
        result = goal_empty.calculate_overall_progress()
        self.assertEqual(result['overall_percentage'], 0)
        self.assertEqual(result['total_items'], 0)
    
    def test_get_next_knowledge_items(self):
        """Test get_next_knowledge_items method returns properly ordered items."""
        from plone.app.textfield.value import RichTextValue
        
        # Create knowledge items with different mastery levels
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="next-item-1",
            title="Basic Math",
            description="Basic mathematics concepts",
            content=RichTextValue("Basic math content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.8,  # Already mastered
            atomic_concepts=["addition", "subtraction"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="next-item-2",
            title="Algebra Basics",
            description="Introduction to algebra",
            content=RichTextValue("Algebra content", "text/plain", "text/html"),
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.3,  # Not mastered
            atomic_concepts=["variables", "equations"]
        )
        
        ki3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="next-item-3",
            title="Advanced Calculus",
            description="Advanced calculus concepts",
            content=RichTextValue("Calculus content", "text/plain", "text/html"),
            knowledge_type="procedural",
            difficulty_level="advanced",
            mastery_threshold=0.9,
            learning_progress=0.1,  # Just started
            atomic_concepts=["derivatives", "integrals"]
        )
        
        # Create learning goal
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-next-items",
            title="Mathematics Learning Path",
            target_knowledge_items=[ki1.UID(), ki2.UID(), ki3.UID()],
            goal_type="mastery"
        )
        
        # Set up prerequisites: ki1 -> ki2 -> ki3
        ki2.prerequisite_items = [ki1.UID()]
        ki3.prerequisite_items = [ki2.UID()]
        
        # Test get_next_knowledge_items
        next_items = goal.get_next_knowledge_items()
        
        # Should return ki2 (ki1 is mastered, ki2 is available)
        # and not ki3 (ki2 prerequisite not mastered)
        self.assertEqual(len(next_items), 1)
        self.assertEqual(next_items[0]['uid'], ki2.UID())
        self.assertEqual(next_items[0]['title'], "Algebra Basics")
        self.assertTrue(next_items[0]['prerequisites_met'])
        self.assertEqual(next_items[0]['mastery_gap'], 0.5)  # 0.8 - 0.3
        
        # Test with limit parameter
        next_items_limited = goal.get_next_knowledge_items(limit=0)
        self.assertEqual(len(next_items_limited), 0)
        
        # Test after mastering ki2
        ki2.learning_progress = 0.9  # Now mastered
        next_items = goal.get_next_knowledge_items()
        
        # Should now return ki3
        self.assertEqual(len(next_items), 1)
        self.assertEqual(next_items[0]['uid'], ki3.UID())
        self.assertEqual(next_items[0]['title'], "Advanced Calculus")
        
        # Test with no available items (all mastered)
        ki3.learning_progress = 1.0
        next_items = goal.get_next_knowledge_items()
        self.assertEqual(len(next_items), 0)
    
    def test_target_knowledge_items_validation(self):
        """Test validation of target_knowledge_items field."""
        from knowledge.curator.content.validators import validate_target_knowledge_items
        from zope.interface import Invalid
        
        # Create valid Knowledge Items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="valid-target-1",
            title="Valid Target 1",
            knowledge_type="conceptual",
            atomic_concepts=["concept1"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="valid-target-2",
            title="Valid Target 2",
            knowledge_type="procedural",
            atomic_concepts=["procedure1"]
        )
        
        # Test with valid UIDs
        result = validate_target_knowledge_items([ki1.UID(), ki2.UID()])
        self.assertTrue(result)
        
        # Test with empty list - should fail
        with self.assertRaises(Invalid) as cm:
            validate_target_knowledge_items([])
        self.assertIn("at least one target Knowledge Item", str(cm.exception))
        
        # Test with invalid UID - should fail
        with self.assertRaises(Invalid) as cm:
            validate_target_knowledge_items(["invalid-uid"])
        self.assertIn("do not reference valid Knowledge Items", str(cm.exception))
        
        # Test with duplicate UIDs - should fail
        with self.assertRaises(Invalid) as cm:
            validate_target_knowledge_items([ki1.UID(), ki1.UID()])
        self.assertIn("Duplicate", str(cm.exception))
        
        # Create non-Knowledge Item content
        research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            id="not-a-ki-target",
            title="Not a KI",
            annotated_knowledge_items=[ki1.UID()],
            annotation_type="general",
            evidence_type="empirical",
            confidence_level="medium"
        )
        
        # Test with wrong content type - should fail
        with self.assertRaises(Invalid) as cm:
            validate_target_knowledge_items([research_note.UID()])
        self.assertIn("do not reference valid Knowledge Items", str(cm.exception))
    
    def test_knowledge_item_connection_management(self):
        """Test Knowledge Item connection management methods."""
        from plone.app.textfield.value import RichTextValue
        
        # Create knowledge items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="conn-item-1",
            title="Foundation Knowledge",
            description="Foundation concepts",
            content=RichTextValue("Foundation content", "text/plain", "text/html"),
            knowledge_type="conceptual",
            atomic_concepts=["foundation"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="conn-item-2",
            title="Building Knowledge",
            description="Building on foundation",
            content=RichTextValue("Building content", "text/plain", "text/html"),
            knowledge_type="procedural",
            atomic_concepts=["building"]
        )
        
        ki3 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="conn-item-3",
            title="Advanced Knowledge",
            description="Advanced concepts",
            content=RichTextValue("Advanced content", "text/plain", "text/html"),
            knowledge_type="metacognitive",
            atomic_concepts=["advanced"]
        )
        
        # Create learning goal
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-connections",
            title="Connection Management Test",
            target_knowledge_items=[ki1.UID(), ki2.UID(), ki3.UID()]
        )
        
        # Test add_knowledge_item_connection
        success = goal.add_knowledge_item_connection(
            source_uid=ki1.UID(),
            target_uid=ki2.UID(),
            connection_type="prerequisite",
            strength=0.8,
            mastery_requirement=0.7
        )
        self.assertTrue(success)
        self.assertEqual(len(goal.knowledge_item_connections), 1)
        
        # Test duplicate connection prevention
        success = goal.add_knowledge_item_connection(
            source_uid=ki1.UID(),
            target_uid=ki2.UID(),
            connection_type="builds_on",  # Different type, same items
            strength=0.5,
            mastery_requirement=0.6
        )
        self.assertFalse(success)  # Should prevent duplicate
        self.assertEqual(len(goal.knowledge_item_connections), 1)
        
        # Test add another valid connection
        success = goal.add_knowledge_item_connection(
            source_uid=ki2.UID(),
            target_uid=ki3.UID(),
            connection_type="builds_on",
            strength=0.6,
            mastery_requirement=0.8
        )
        self.assertTrue(success)
        self.assertEqual(len(goal.knowledge_item_connections), 2)
        
        # Test remove_knowledge_item_connection
        success = goal.remove_knowledge_item_connection(
            source_uid=ki1.UID(),
            target_uid=ki2.UID()
        )
        self.assertTrue(success)
        self.assertEqual(len(goal.knowledge_item_connections), 1)
        
        # Test remove non-existent connection
        success = goal.remove_knowledge_item_connection(
            source_uid=ki1.UID(),
            target_uid=ki3.UID()
        )
        self.assertFalse(success)
        self.assertEqual(len(goal.knowledge_item_connections), 1)
        
        # Test get_knowledge_item_connections_for_item
        connections = goal.get_knowledge_item_connections_for_item(ki2.UID())
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0]['source_item_uid'], ki2.UID())
        self.assertEqual(connections[0]['target_item_uid'], ki3.UID())
        
        # Test update_connection_strength
        success = goal.update_connection_strength(
            source_uid=ki2.UID(),
            target_uid=ki3.UID(),
            new_strength=0.9,
            new_mastery_requirement=0.85
        )
        self.assertTrue(success)
        
        # Verify update
        connections = goal.get_knowledge_item_connections_for_item(ki2.UID())
        self.assertEqual(connections[0]['strength'], 0.9)
        self.assertEqual(connections[0]['mastery_requirement'], 0.85)
    
    def test_learning_goal_knowledge_item_synchronization(self):
        """Test synchronization between Learning Goal and Knowledge Item fields."""
        from plone.app.textfield.value import RichTextValue
        
        # Create knowledge items
        ki1 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="sync-item-1",
            title="Synchronized Item 1",
            content=RichTextValue("Sync content 1", "text/plain", "text/html"),
            knowledge_type="conceptual",
            difficulty_level="beginner",
            mastery_threshold=0.7,
            learning_progress=0.3,
            atomic_concepts=["sync1"]
        )
        
        ki2 = api.content.create(
            container=self.portal,
            type="KnowledgeItem",
            id="sync-item-2",
            title="Synchronized Item 2",
            content=RichTextValue("Sync content 2", "text/plain", "text/html"),
            knowledge_type="procedural",
            difficulty_level="intermediate",
            mastery_threshold=0.8,
            learning_progress=0.6,
            atomic_concepts=["sync2"]
        )
        
        # Create learning goal
        goal = api.content.create(
            container=self.portal,
            type="LearningGoal",
            id="goal-sync",
            title="Synchronization Test Goal",
            target_knowledge_items=[ki1.UID(), ki2.UID()],
            goal_type="mastery",
            difficulty_level="intermediate"
        )
        
        # Test sync_with_knowledge_items method
        changes = goal.sync_with_knowledge_items()
        
        # Should detect changes and update goal
        self.assertGreater(len(changes), 0)
        
        # Check that goal properties were updated based on Knowledge Items
        # Difficulty should be updated to match the highest KI difficulty
        self.assertEqual(goal.difficulty_level, "intermediate")
        
        # Test get_knowledge_items_summary
        summary = goal.get_knowledge_items_summary()
        self.assertEqual(summary['total_items'], 2)
        self.assertEqual(summary['conceptual_items'], 1)
        self.assertEqual(summary['procedural_items'], 1)
        self.assertEqual(summary['average_progress'], 0.45)  # (0.3 + 0.6) / 2
        self.assertEqual(summary['mastered_items'], 0)
        
        # Test after mastering one item
        ki1.learning_progress = 0.8  # Above mastery threshold
        summary = goal.get_knowledge_items_summary()
        self.assertEqual(summary['mastered_items'], 1)
        self.assertEqual(summary['average_progress'], 0.7)  # (0.8 + 0.6) / 2
        
        # Test validate_knowledge_item_references
        is_valid, errors = goal.validate_knowledge_item_references()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test with invalid reference
        goal.target_knowledge_items.append("invalid-uid")
        is_valid, errors = goal.validate_knowledge_item_references()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("invalid-uid", errors[0])
