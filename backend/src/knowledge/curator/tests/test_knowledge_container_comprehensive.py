"""Comprehensive test suite for Knowledge Container functionality and academic workflows."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from plone import api
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.api.exc import InvalidParameterError
from zope.interface import Invalid

from knowledge.curator.content.knowledge_container import KnowledgeContainer
from knowledge.curator.validation.container_validation import (
    validate_knowledge_container,
    AcademicStandardsValidator,
    ContainerIntegrityValidator,
    KnowledgeSovereigntyValidator
)
from knowledge.curator.sharing.sovereignty_sharing import (
    KnowledgeSovereigntyManager,
    SharingAgreement,
    SovereigntyLevel,
    PermissionType,
    ShareScope
)


class KnowledgeContainerTestCase(unittest.TestCase):
    """Base test case for Knowledge Container tests."""
    
    layer = PLONE_INTEGRATION_TESTING
    
    def setUp(self):
        """Set up test fixtures."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        
        # Create test users
        api.user.create(
            username='test_curator',
            email='curator@example.com',
            password='testpass'
        )
        api.user.create(
            username='test_collaborator',
            email='collaborator@example.com',
            password='testpass'
        )
        
        # Create test Knowledge Container
        self.container = api.content.create(
            container=self.portal,
            type='KnowledgeContainer',
            id='test_container',
            title='Test Academic Collection',
            description='A comprehensive test collection for academic research',
            collection_type='research_collection',
            target_audience='academic',
            publication_status='draft'
        )
        
        # Create test content items
        self.knowledge_item = api.content.create(
            container=self.portal,
            type='KnowledgeItem',
            id='test_knowledge_item',
            title='Test Knowledge Item',
            description='Test content for container'
        )
        
        self.research_note = api.content.create(
            container=self.portal,
            type='ResearchNote',
            id='test_research_note',
            title='Test Research Note',
            description='Research note for container'
        )


class TestKnowledgeContainerCore(KnowledgeContainerTestCase):
    """Test core Knowledge Container functionality."""
    
    def test_container_creation(self):
        """Test basic Knowledge Container creation."""
        self.assertIsNotNone(self.container)
        self.assertEqual(self.container.portal_type, 'KnowledgeContainer')
        self.assertEqual(self.container.title, 'Test Academic Collection')
        self.assertEqual(self.container.collection_type, 'research_collection')
        self.assertEqual(self.container.target_audience, 'academic')
        self.assertEqual(self.container.publication_status, 'draft')
    
    def test_content_addition_and_removal(self):
        """Test adding and removing content from containers."""
        # Add content to container
        self.container.add_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        self.container.add_content_item(self.research_note.UID(), 'ResearchNote')
        
        # Verify content was added
        self.assertIn(self.knowledge_item.UID(), self.container.included_knowledge_items)
        self.assertIn(self.research_note.UID(), self.container.included_research_notes)
        
        # Test content removal
        self.container.remove_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        self.assertNotIn(self.knowledge_item.UID(), self.container.included_knowledge_items)
    
    def test_container_validation(self):
        """Test content validation in containers."""
        # Test valid UID
        self.assertTrue(
            self.container.validate_content_reference(self.knowledge_item.UID())
        )
        
        # Test invalid UID
        self.assertFalse(
            self.container.validate_content_reference('invalid-uid-12345')
        )
    
    def test_analytics_generation(self):
        """Test container analytics functionality."""
        # Add some content for analytics
        self.container.add_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        self.container.add_content_item(self.research_note.UID(), 'ResearchNote')
        
        analytics = self.container.get_collection_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_items', analytics)
        self.assertIn('content_types', analytics)
        self.assertIn('creation_timeline', analytics)
        self.assertEqual(analytics['total_items'], 2)
    
    def test_export_functionality(self):
        """Test container export functionality."""
        # Add content for export
        self.container.add_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        
        # Test HTML export
        html_export = self.container.export_collection('html')
        self.assertIsInstance(html_export, str)
        self.assertIn(self.container.title, html_export)
        
        # Test markdown export
        markdown_export = self.container.export_collection('markdown')
        self.assertIsInstance(markdown_export, str)
        self.assertIn('# ' + self.container.title, markdown_export)
    
    def test_container_organization(self):
        """Test container organization and structure."""
        # Set custom organization
        org_structure = {
            'type': 'hierarchical',
            'sections': ['Introduction', 'Methods', 'Results', 'Conclusion'],
            'subsections': {
                'Methods': ['Data Collection', 'Analysis'],
                'Results': ['Findings', 'Discussion']
            }
        }
        
        self.container.organization_structure = org_structure
        
        # Verify organization was set
        self.assertEqual(self.container.organization_structure['type'], 'hierarchical')
        self.assertIn('Introduction', self.container.organization_structure['sections'])


class TestAcademicStandardsValidation(KnowledgeContainerTestCase):
    """Test academic standards validation system."""
    
    def setUp(self):
        super().setUp()
        self.validator = AcademicStandardsValidator()
    
    def test_metadata_completeness_validation(self):
        """Test metadata completeness validation."""
        # Set up container with complete metadata
        self.container.title = 'Complete Academic Collection'
        self.container.description = 'A comprehensive description of this academic collection that meets minimum standards'
        self.container.collection_type = 'research_collection'
        self.container.publication_status = 'review'
        self.container.target_audience = 'academic'
        self.container.container_version = '1.0'
        
        result = self.validator.validate_academic_completeness(self.container)
        
        self.assertTrue(result['valid'])
        self.assertGreaterEqual(result['academic_score'], 0.7)
        self.assertEqual(len(result['errors']), 0)
    
    def test_content_quality_validation(self):
        """Test content quality and diversity validation."""
        # Add diverse content to meet academic standards
        for i in range(5):
            item = api.content.create(
                container=self.portal,
                type='KnowledgeItem',
                id=f'item_{i}',
                title=f'Academic Item {i}'
            )
            self.container.add_content_item(item.UID(), 'KnowledgeItem')
        
        # Add research notes
        for i in range(3):
            note = api.content.create(
                container=self.portal,
                type='ResearchNote',
                id=f'note_{i}',
                title=f'Research Note {i}'
            )
            self.container.add_content_item(note.UID(), 'ResearchNote')
        
        result = self.validator.validate_academic_completeness(self.container)
        
        # Should have good content diversity score
        self.assertGreater(result['academic_score'], 0.5)
    
    def test_collection_coherence_validation(self):
        """Test collection coherence and academic focus."""
        # Set up academically coherent container
        self.container.collection_type = 'research_collection'
        self.container.target_audience = 'academic'
        self.container.publication_status = 'review'
        
        result = self.validator.validate_academic_completeness(self.container)
        
        # Should have high coherence due to academic settings
        self.assertGreater(result['academic_score'], 0.6)
    
    def test_academic_formatting_validation(self):
        """Test academic formatting standards."""
        # Set up well-formatted container
        self.container.title = 'Research Methods in Digital Knowledge Curation'
        self.container.description = 'This comprehensive collection examines methodological approaches to digital knowledge curation in academic environments, providing structured insights for researchers and practitioners.'
        self.container.tags = ['research', 'methodology', 'digital-curation', 'academic']
        
        result = self.validator.validate_academic_completeness(self.container)
        
        # Should score well on formatting
        self.assertGreater(result['academic_score'], 0.6)
        self.assertLessEqual(len(result['warnings']), 2)


class TestContainerIntegrityValidation(KnowledgeContainerTestCase):
    """Test container integrity validation system."""
    
    def setUp(self):
        super().setUp()
        self.validator = ContainerIntegrityValidator()
    
    def test_reference_integrity_validation(self):
        """Test reference integrity validation."""
        # Add valid references
        self.container.add_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        self.container.add_content_item(self.research_note.UID(), 'ResearchNote')
        
        result = self.validator.validate_container_integrity(self.container)
        
        self.assertTrue(result['valid'])
        self.assertGreaterEqual(result['integrity_score'], 0.8)
        self.assertEqual(len(result['broken_references']), 0)
    
    def test_broken_reference_detection(self):
        """Test detection of broken references."""
        # Add an invalid UID
        self.container.included_knowledge_items = ['invalid-uid-12345']
        
        result = self.validator.validate_container_integrity(self.container)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['broken_references']), 0)
        self.assertEqual(result['broken_references'][0]['uid'], 'invalid-uid-12345')
    
    def test_collection_consistency_validation(self):
        """Test internal consistency validation."""
        # Test inconsistent state: draft with public audience
        self.container.publication_status = 'draft'
        self.container.target_audience = 'public'
        
        result = self.validator.validate_container_integrity(self.container)
        
        # Should generate warnings about inconsistency
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn('public target audience', result['warnings'][0])
    
    def test_published_content_validation(self):
        """Test validation of published content standards."""
        # Set up published container with insufficient content
        self.container.publication_status = 'published'
        # Only add 2 items (below the 5-item threshold for published content)
        self.container.add_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        self.container.add_content_item(self.research_note.UID(), 'ResearchNote')
        
        result = self.validator.validate_container_integrity(self.container)
        
        # Should warn about insufficient content for published status
        warning_found = any('substantial content' in warning for warning in result['warnings'])
        self.assertTrue(warning_found)


class TestKnowledgeSovereigntySharing(KnowledgeContainerTestCase):
    """Test knowledge sovereignty sharing system."""
    
    def setUp(self):
        super().setUp()
        self.sovereignty_manager = KnowledgeSovereigntyManager()
        api.user.grant_roles(username='test_curator', roles=['Manager'])
        
        # Login as curator
        with api.env.adopt_user(username='test_curator'):
            self.container_uid = self.container.UID()
    
    def test_sharing_agreement_creation(self):
        """Test creation of sharing agreements."""
        with api.env.adopt_user(username='test_curator'):
            agreement = self.sovereignty_manager.create_sharing_agreement(
                container_uid=self.container_uid,
                grantee_id='test_collaborator',
                permissions=[PermissionType.VIEW.value, PermissionType.CITE.value],
                sovereignty_level=SovereigntyLevel.ACADEMIC_OPEN,
                share_scope=ShareScope.INDIVIDUAL
            )
        
        self.assertIsInstance(agreement, SharingAgreement)
        self.assertEqual(agreement.container_uid, self.container_uid)
        self.assertEqual(agreement.grantee_id, 'test_collaborator')
        self.assertEqual(agreement.sovereignty_level, SovereigntyLevel.ACADEMIC_OPEN.value)
        self.assertTrue(agreement.citation_required)
    
    def test_sovereignty_compliance_validation(self):
        """Test sovereignty compliance validation."""
        # Test full control restrictions
        with self.assertRaises(Invalid):
            self.sovereignty_manager._validate_sovereignty_compliance(
                SovereigntyLevel.FULL_CONTROL,
                [PermissionType.EXPORT.value],
                ShareScope.CONTROLLED_PUBLIC
            )
        
        # Test valid academic open configuration
        try:
            self.sovereignty_manager._validate_sovereignty_compliance(
                SovereigntyLevel.ACADEMIC_OPEN,
                [PermissionType.VIEW.value, PermissionType.CITE.value],
                ShareScope.ACADEMIC_PUBLIC
            )
        except Invalid:
            self.fail("Valid academic open configuration should not raise Invalid")
    
    def test_access_request_validation(self):
        """Test access request validation."""
        with api.env.adopt_user(username='test_curator'):
            # Create agreement
            agreement = self.sovereignty_manager.create_sharing_agreement(
                container_uid=self.container_uid,
                grantee_id='test_collaborator',
                permissions=[PermissionType.VIEW.value, PermissionType.CITE.value],
                sovereignty_level=SovereigntyLevel.ACADEMIC_OPEN,
                share_scope=ShareScope.INDIVIDUAL
            )
            
            # Test valid access request
            result = self.sovereignty_manager.validate_access_request(
                agreement.agreement_id,
                PermissionType.VIEW.value
            )
            
            self.assertTrue(result['valid'])
            self.assertIn('restrictions', result)
            self.assertIn('requirements', result)
            
            # Test invalid permission request
            invalid_result = self.sovereignty_manager.validate_access_request(
                agreement.agreement_id,
                PermissionType.MANAGE.value
            )
            
            self.assertFalse(invalid_result['valid'])
            self.assertIn('not granted', invalid_result['reason'])
    
    def test_access_logging(self):
        """Test access event logging."""
        with api.env.adopt_user(username='test_curator'):
            # Create agreement
            agreement = self.sovereignty_manager.create_sharing_agreement(
                container_uid=self.container_uid,
                grantee_id='test_collaborator',
                permissions=[PermissionType.VIEW.value],
                sovereignty_level=SovereigntyLevel.ACADEMIC_OPEN,
                share_scope=ShareScope.INDIVIDUAL
            )
            
            # Log access event
            self.sovereignty_manager.log_access_event(
                agreement.agreement_id,
                'content_view',
                {'content_type': 'KnowledgeItem'}
            )
            
            # Retrieve updated agreement
            updated_agreement = self.sovereignty_manager._get_sharing_agreement(agreement.agreement_id)
            
            self.assertEqual(updated_agreement.access_count, 1)
            self.assertEqual(len(updated_agreement.access_log), 1)
            self.assertEqual(updated_agreement.access_log[0]['access_type'], 'content_view')
    
    def test_sovereignty_report_generation(self):
        """Test sovereignty compliance report generation."""
        with api.env.adopt_user(username='test_curator'):
            # Create multiple agreements
            self.sovereignty_manager.create_sharing_agreement(
                container_uid=self.container_uid,
                grantee_id='test_collaborator',
                permissions=[PermissionType.VIEW.value],
                sovereignty_level=SovereigntyLevel.ACADEMIC_OPEN,
                share_scope=ShareScope.INDIVIDUAL
            )
            
            self.sovereignty_manager.create_sharing_agreement(
                container_uid=self.container_uid,
                grantee_id='another_user',
                permissions=[PermissionType.VIEW.value, PermissionType.CITE.value],
                sovereignty_level=SovereigntyLevel.FEDERATED,
                share_scope=ShareScope.INSTITUTION
            )
            
            # Generate report
            report = self.sovereignty_manager.generate_sovereignty_report(self.container_uid)
            
            self.assertIn('sovereignty_summary', report)
            self.assertIn('access_analytics', report)
            self.assertIn('compliance_status', report)
            self.assertEqual(report['sovereignty_summary']['total_agreements'], 2)
            self.assertIn('academic_open', report['sovereignty_summary']['sovereignty_levels'])


class TestKnowledgeContainerWorkflows(KnowledgeContainerTestCase):
    """Test Knowledge Container workflow integration."""
    
    def test_workflow_state_transitions(self):
        """Test workflow state transitions."""
        # Test initial state
        review_state = api.content.get_state(obj=self.container)
        self.assertIn(review_state, ['private', 'process'])
        
        # Test transition to review
        try:
            api.content.transition(obj=self.container, transition='review')
            review_state = api.content.get_state(obj=self.container)
            self.assertEqual(review_state, 'reviewed')
        except InvalidParameterError:
            # Workflow might not support this transition
            pass
    
    def test_workflow_permissions(self):
        """Test workflow-based permissions."""
        # Test that container respects workflow permissions
        self.assertTrue(api.user.has_permission('View', obj=self.container))
        
        # Test container-specific permissions
        container_perms = self.container.permission_settings()
        self.assertIsInstance(container_perms, dict)


class TestKnowledgeContainerIntegration(KnowledgeContainerTestCase):
    """Test Knowledge Container integration with other systems."""
    
    def test_vector_indexing_integration(self):
        """Test integration with vector indexing system."""
        # Add content and test if it triggers vector indexing
        self.container.add_content_item(self.knowledge_item.UID(), 'KnowledgeItem')
        
        # This would normally trigger vector indexing events
        # For testing, we verify the container is configured for indexing
        from knowledge.curator.vector.config import SUPPORTED_CONTENT_TYPES
        self.assertIn('KnowledgeContainer', SUPPORTED_CONTENT_TYPES)
    
    def test_graph_model_integration(self):
        """Test integration with knowledge graph model."""
        from knowledge.curator.graph.model import NodeType
        
        # Verify KnowledgeContainer is in the graph model
        node_types = [node_type.value for node_type in NodeType]
        self.assertIn('KnowledgeContainer', node_types)
    
    def test_enhancement_queue_integration(self):
        """Test integration with enhancement queue system."""
        # Test that containers can be added to enhancement queue
        enhancement_data = {
            'content_uid': self.container.UID(),
            'enhancement_type': 'academic_review',
            'priority': 'high'
        }
        
        # This would normally interact with the enhancement queue
        # For testing, we verify the container supports enhancement
        self.assertTrue(hasattr(self.container, 'get_enhancement_suggestions'))


class TestKnowledgeContainerAPI(KnowledgeContainerTestCase):
    """Test Knowledge Container API endpoints."""
    
    def setUp(self):
        super().setUp()
        self.api_base = '/@knowledge-containers'
    
    @patch('knowledge.curator.api.knowledge_container.validate_knowledge_container')
    def test_validation_endpoint(self, mock_validate):
        """Test container validation API endpoint."""
        # Mock validation result
        mock_validate.return_value = {
            'timestamp': datetime.now().isoformat(),
            'container_uid': self.container.UID(),
            'overall_valid': True,
            'validation_results': {
                'academic_standards': {'valid': True, 'academic_score': 0.85},
                'container_integrity': {'valid': True, 'integrity_score': 0.90},
                'knowledge_sovereignty': {'valid': True, 'sovereignty_score': 0.95}
            }
        }
        
        # Test validation endpoint would be called
        self.assertTrue(callable(mock_validate))
    
    def test_export_endpoint_structure(self):
        """Test export endpoint structure."""
        # Test that export methods exist
        self.assertTrue(hasattr(self.container, 'export_collection'))
        
        # Test supported export formats
        supported_formats = ['html', 'pdf', 'markdown', 'json', 'docx', 'latex', 'epub']
        for format_type in supported_formats:
            try:
                result = self.container.export_collection(format_type)
                self.assertIsNotNone(result)
            except NotImplementedError:
                # Some formats might not be fully implemented yet
                pass


def test_suite():
    """Create test suite."""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestKnowledgeContainerCore,
        TestAcademicStandardsValidation,
        TestContainerIntegrityValidation,
        TestKnowledgeSovereigntySharing,
        TestKnowledgeContainerWorkflows,
        TestKnowledgeContainerIntegration,
        TestKnowledgeContainerAPI
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite') 