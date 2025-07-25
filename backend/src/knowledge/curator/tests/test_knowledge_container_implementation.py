"""Tests for Knowledge Container implementation."""

import unittest
from unittest.mock import patch, Mock
from datetime import datetime
from zope.interface.verify import verifyClass, verifyObject

from knowledge.curator.interfaces import IKnowledgeContainer
from knowledge.curator.content.knowledge_container import KnowledgeContainer


class TestKnowledgeContainerImplementation(unittest.TestCase):
    """Test the KnowledgeContainer class implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.container = KnowledgeContainer('test-container')

    def test_interface_compliance(self):
        """Test that the class implements the interface correctly."""
        # Test class implementation
        self.assertTrue(verifyClass(IKnowledgeContainer, KnowledgeContainer))
        
        # Add required fields for interface compliance
        self.container.title = "Test Container"
        self.container.description = "A test container"
        
        # Test instance implementation
        self.assertTrue(verifyObject(IKnowledgeContainer, self.container))

    def test_initialization_defaults(self):
        """Test that container is initialized with proper defaults."""
        container = KnowledgeContainer('test-id')
        
        # Test content lists are initialized as empty lists
        self.assertEqual(container.included_learning_goals, [])
        self.assertEqual(container.included_knowledge_items, [])
        self.assertEqual(container.included_research_notes, [])
        self.assertEqual(container.included_project_logs, [])
        self.assertEqual(container.included_bookmarks, [])
        
        # Test metadata defaults
        self.assertEqual(container.collection_type, "curated")
        self.assertEqual(container.organization_structure, "hierarchical")
        self.assertEqual(container.publication_status, "draft")
        self.assertEqual(container.target_audience, "self")
        self.assertEqual(container.sharing_permissions, {})
        self.assertEqual(container.export_formats, set())
        self.assertEqual(container.view_analytics, {})
        self.assertEqual(container.total_items_count, 0)
        self.assertEqual(container.container_version, "1.0")
        self.assertEqual(container.tags, [])
        self.assertIsInstance(container.created_date, datetime)

    def test_add_content_item_success(self):
        """Test successful content item addition."""
        # Mock validation to return True
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            # Test adding different content types
            result = self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.assertTrue(result)
            self.assertIn('lg-uid-1', self.container.included_learning_goals)
            
            result = self.container.add_content_item('knowledge_items', 'ki-uid-1')
            self.assertTrue(result)
            self.assertIn('ki-uid-1', self.container.included_knowledge_items)
            
            result = self.container.add_content_item('research_notes', 'rn-uid-1')
            self.assertTrue(result)
            self.assertIn('rn-uid-1', self.container.included_research_notes)
            
            result = self.container.add_content_item('project_logs', 'pl-uid-1')
            self.assertTrue(result)
            self.assertIn('pl-uid-1', self.container.included_project_logs)
            
            result = self.container.add_content_item('bookmarks', 'bm-uid-1')
            self.assertTrue(result)
            self.assertIn('bm-uid-1', self.container.included_bookmarks)
            
            # Check total items count is updated
            self.assertEqual(self.container.total_items_count, 5)

    def test_add_content_item_duplicate(self):
        """Test that adding duplicate content items returns False."""
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            # Add item first time
            result1 = self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.assertTrue(result1)
            
            # Try to add same item again
            result2 = self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.assertFalse(result2)
            
            # Check it's only in the list once
            self.assertEqual(self.container.included_learning_goals.count('lg-uid-1'), 1)

    def test_add_content_item_invalid_type(self):
        """Test that invalid content types raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.container.add_content_item('invalid_type', 'some-uid')
        
        self.assertIn("Invalid content_type: invalid_type", str(cm.exception))

    def test_add_content_item_invalid_reference(self):
        """Test that invalid content references raise ValueError."""
        with patch.object(self.container, '_validate_content_reference', return_value=False):
            with self.assertRaises(ValueError) as cm:
                self.container.add_content_item('learning_goals', 'invalid-uid')
            
            self.assertIn("does not exist or is not accessible", str(cm.exception))

    def test_remove_content_item_success(self):
        """Test successful content item removal."""
        # First add some items
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.container.add_content_item('knowledge_items', 'ki-uid-1')
        
        # Test removal
        result = self.container.remove_content_item('learning_goals', 'lg-uid-1')
        self.assertTrue(result)
        self.assertNotIn('lg-uid-1', self.container.included_learning_goals)
        
        result = self.container.remove_content_item('knowledge_items', 'ki-uid-1')
        self.assertTrue(result)
        self.assertNotIn('ki-uid-1', self.container.included_knowledge_items)
        
        # Check total items count is updated
        self.assertEqual(self.container.total_items_count, 0)

    def test_remove_content_item_not_found(self):
        """Test removing non-existent content item returns False."""
        result = self.container.remove_content_item('learning_goals', 'non-existent-uid')
        self.assertFalse(result)

    def test_remove_content_item_invalid_type(self):
        """Test that invalid content types raise ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.container.remove_content_item('invalid_type', 'some-uid')
        
        self.assertIn("Invalid content_type: invalid_type", str(cm.exception))

    def test_organize_content_valid_structures(self):
        """Test organizing content with valid structure types."""
        valid_structures = ["hierarchical", "network", "linear", "matrix", "free_form"]
        
        for structure in valid_structures:
            self.container.organize_content(structure)
            self.assertEqual(self.container.organization_structure, structure)

    def test_organize_content_invalid_structure(self):
        """Test that invalid organization structure raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            self.container.organize_content('invalid_structure')
        
        self.assertIn("Invalid organization structure", str(cm.exception))

    def test_update_organization_structure(self):
        """Test automatic organization structure update based on content."""
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            # Test with no items - should be free_form
            self.container.update_organization_structure()
            self.assertEqual(self.container.organization_structure, "free_form")
            
            # Test with few items - should be linear
            for i in range(3):
                self.container.add_content_item('learning_goals', f'lg-uid-{i}')
            self.container.update_organization_structure()
            self.assertEqual(self.container.organization_structure, "linear")
            
            # Test with medium number of items - should be hierarchical
            for i in range(3, 10):
                self.container.add_content_item('knowledge_items', f'ki-uid-{i}')
            self.container.update_organization_structure()
            self.assertEqual(self.container.organization_structure, "hierarchical")
            
            # Test with many items and multiple types - should be matrix
            for i in range(15):
                self.container.add_content_item('research_notes', f'rn-uid-{i}')
                self.container.add_content_item('project_logs', f'pl-uid-{i}')
                self.container.add_content_item('bookmarks', f'bm-uid-{i}')
            self.container.update_organization_structure()
            self.assertEqual(self.container.organization_structure, "matrix")

    def test_validate_content_references_all_valid(self):
        """Test validation with all valid content references."""
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            # Add some content
            self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.container.add_content_item('knowledge_items', 'ki-uid-1')
            
            result = self.container.validate_content_references()
            
            self.assertTrue(result['valid'])
            self.assertEqual(result['invalid_refs'], [])
            self.assertEqual(result['errors'], [])

    def test_validate_content_references_invalid_refs(self):
        """Test validation with invalid content references."""
        # Add some content directly (bypassing validation)
        self.container.included_learning_goals = ['lg-valid', 'lg-invalid']
        self.container.included_knowledge_items = ['ki-valid']
        
        # Mock validation to return different results for different UIDs
        def mock_validate(uid):
            return uid in ['lg-valid', 'ki-valid']
        
        with patch.object(self.container, '_validate_content_reference', side_effect=mock_validate):
            result = self.container.validate_content_references()
            
            self.assertFalse(result['valid'])
            self.assertEqual(len(result['invalid_refs']), 1)
            self.assertEqual(result['invalid_refs'][0]['uid'], 'lg-invalid')
            self.assertEqual(result['invalid_refs'][0]['content_type'], 'learning_goals')

    def test_get_collection_summary(self):
        """Test getting comprehensive collection summary."""
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            # Set up container with some content
            self.container.title = "Test Container"
            self.container.description = "A test container"
            self.container.tags = ["test", "demo"]
            
            # Add content
            self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.container.add_content_item('knowledge_items', 'ki-uid-1')
            self.container.add_content_item('knowledge_items', 'ki-uid-2')
            self.container.add_content_item('research_notes', 'rn-uid-1')
            
            # Get summary
            summary = self.container.get_collection_summary()
            
            # Test basic info
            self.assertEqual(summary['basic_info']['title'], "Test Container")
            self.assertEqual(summary['basic_info']['description'], "A test container")
            self.assertEqual(summary['basic_info']['total_items'], 4)
            self.assertEqual(summary['basic_info']['tags'], ["test", "demo"])
            
            # Test content breakdown
            self.assertEqual(summary['content_breakdown']['learning_goals'], 1)
            self.assertEqual(summary['content_breakdown']['knowledge_items'], 2)
            self.assertEqual(summary['content_breakdown']['research_notes'], 1)
            self.assertEqual(summary['content_breakdown']['project_logs'], 0)
            self.assertEqual(summary['content_breakdown']['bookmarks'], 0)
            
            # Test metadata
            self.assertEqual(summary['metadata']['collection_type'], "curated")
            self.assertEqual(summary['metadata']['organization_structure'], "hierarchical")
            self.assertEqual(summary['metadata']['publication_status'], "draft")
            self.assertEqual(summary['metadata']['target_audience'], "self")
            
            # Test validation results exist
            self.assertIn('validation', summary)
            self.assertTrue(summary['validation']['valid'])
            
            # Test organization info
            self.assertEqual(summary['organization']['structure_type'], "hierarchical")
            self.assertEqual(summary['organization']['export_formats'], [])
            self.assertEqual(summary['organization']['sharing_permissions'], {})
            
            # Test analytics
            self.assertEqual(summary['analytics'], {})

    def test_calculate_total_items(self):
        """Test total items calculation."""
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            # Initially should be 0
            self.assertEqual(self.container._calculate_total_items(), 0)
            
            # Add some items
            self.container.add_content_item('learning_goals', 'lg-uid-1')
            self.assertEqual(self.container._calculate_total_items(), 1)
            
            self.container.add_content_item('knowledge_items', 'ki-uid-1')
            self.container.add_content_item('knowledge_items', 'ki-uid-2')
            self.assertEqual(self.container._calculate_total_items(), 3)
            
            # Remove an item
            self.container.remove_content_item('learning_goals', 'lg-uid-1')
            self.assertEqual(self.container._calculate_total_items(), 2)

    def test_update_metadata(self):
        """Test metadata update functionality."""
        # Store initial values
        initial_modified = getattr(self.container, 'last_modified_date', None)
        initial_count = self.container.total_items_count
        
        # Add some content to change totals
        with patch.object(self.container, '_validate_content_reference', return_value=True):
            self.container.add_content_item('learning_goals', 'lg-uid-1')
        
        # Check that metadata was updated
        self.assertGreater(self.container.last_modified_date, initial_modified if initial_modified else datetime.min)
        self.assertGreater(self.container.total_items_count, initial_count)

    @patch('knowledge.curator.content.knowledge_container.api.content.get')
    def test_validate_content_reference_with_api(self, mock_get):
        """Test content reference validation using Plone API."""
        # Test valid reference
        mock_get.return_value = Mock()  # Mock content object
        self.assertTrue(self.container._validate_content_reference('valid-uid'))
        mock_get.assert_called_with(UID='valid-uid')
        
        # Test invalid reference
        mock_get.return_value = None
        self.assertFalse(self.container._validate_content_reference('invalid-uid'))
        
        # Test API exception (should return True for test environments)
        mock_get.side_effect = Exception("API not available")
        self.assertTrue(self.container._validate_content_reference('any-uid'))

    def test_validate_content_reference_edge_cases(self):
        """Test content reference validation edge cases."""
        # Test None reference
        self.assertFalse(self.container._validate_content_reference(None))
        
        # Test empty string
        self.assertFalse(self.container._validate_content_reference(''))
        
        # Test non-string reference
        self.assertFalse(self.container._validate_content_reference(123))


class TestKnowledgeContainerMethods(unittest.TestCase):
    """Test individual methods of KnowledgeContainer."""

    def setUp(self):
        """Set up test fixtures."""
        self.container = KnowledgeContainer('test-container')

    def test_organization_structure_methods(self):
        """Test that organization structure methods exist and are callable."""
        # These methods are currently stubs but should exist
        self.assertTrue(hasattr(self.container, '_organize_hierarchical'))
        self.assertTrue(hasattr(self.container, '_organize_network'))
        self.assertTrue(hasattr(self.container, '_organize_linear'))
        self.assertTrue(hasattr(self.container, '_organize_matrix'))
        self.assertTrue(hasattr(self.container, '_organize_free_form'))
        
        # Test they are callable without errors
        self.container._organize_hierarchical()
        self.container._organize_network()
        self.container._organize_linear()
        self.container._organize_matrix()
        self.container._organize_free_form()


if __name__ == '__main__':
    unittest.main()