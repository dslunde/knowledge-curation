"""Knowledge Container validation systems for academic standards and integrity."""

import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from plone import api
from zope.interface import Invalid

logger = logging.getLogger(__name__)


class AcademicStandardsValidator:
    """Validator for academic standards compliance in Knowledge Containers."""
    
    def __init__(self):
        self.academic_standards = {
            'min_content_items': 3,  # Minimum items for academic rigor
            'required_metadata_fields': [
                'title', 'description', 'collection_type', 'publication_status'
            ],
            'max_collection_size': 500,  # Maximum items to maintain quality
            'academic_collection_types': [
                'course', 'study_guide', 'research_collection', 'knowledge_base'
            ]
        }
    
    def validate_academic_completeness(self, container) -> Dict[str, Any]:
        """Validate that container meets academic completeness standards."""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'academic_score': 0.0,
            'recommendations': []
        }
        
        try:
            # Check metadata completeness
            metadata_score = self._validate_metadata_completeness(container, validation_result)
            
            # Check content quality and diversity
            content_score = self._validate_content_quality(container, validation_result)
            
            # Check collection coherence
            coherence_score = self._validate_collection_coherence(container, validation_result)
            
            # Check academic formatting
            formatting_score = self._validate_academic_formatting(container, validation_result)
            
            # Calculate overall academic score
            validation_result['academic_score'] = (
                metadata_score * 0.25 + 
                content_score * 0.35 + 
                coherence_score * 0.25 + 
                formatting_score * 0.15
            )
            
            # Determine if container meets academic standards
            if validation_result['academic_score'] < 0.7:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"Academic score {validation_result['academic_score']:.2f} below threshold 0.7"
                )
                
        except Exception as e:
            logger.error(f"Error in academic validation: {e}")
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_metadata_completeness(self, container, validation_result) -> float:
        """Validate metadata completeness for academic standards."""
        score = 0.0
        total_fields = len(self.academic_standards['required_metadata_fields'])
        
        for field in self.academic_standards['required_metadata_fields']:
            value = getattr(container, field, None)
            if value and str(value).strip():
                score += 1.0
            else:
                validation_result['warnings'].append(f"Missing or empty required field: {field}")
        
        # Check for academic-specific metadata
        academic_fields = ['target_audience', 'container_version', 'created_date']
        academic_present = 0
        for field in academic_fields:
            if getattr(container, field, None):
                academic_present += 1
        
        # Bonus for academic metadata
        academic_bonus = academic_present / len(academic_fields) * 0.2
        
        return (score / total_fields) + academic_bonus
    
    def _validate_content_quality(self, container, validation_result) -> float:
        """Validate content quality and diversity."""
        # Calculate total items
        total_items = 0
        content_diversity = 0
        
        content_types = [
            'included_knowledge_items', 'included_research_notes', 
            'included_learning_goals', 'included_project_logs', 
            'included_bookmarks'
        ]
        
        for content_type in content_types:
            items = getattr(container, content_type, [])
            if items:
                total_items += len(items)
                content_diversity += 1
        
        # Check minimum content requirement
        if total_items < self.academic_standards['min_content_items']:
            validation_result['warnings'].append(
                f"Collection has {total_items} items, academic standard recommends minimum {self.academic_standards['min_content_items']}"
            )
        
        # Check maximum size for quality maintenance
        if total_items > self.academic_standards['max_collection_size']:
            validation_result['warnings'].append(
                f"Collection has {total_items} items, consider splitting for better academic focus"
            )
        
        # Calculate content quality score
        size_score = min(1.0, total_items / 10)  # Optimal around 10 items
        diversity_score = content_diversity / len(content_types)
        
        return (size_score * 0.6 + diversity_score * 0.4)
    
    def _validate_collection_coherence(self, container, validation_result) -> float:
        """Validate that collection has academic coherence and focus."""
        coherence_score = 0.8  # Default good score
        
        # Check if collection type is academic
        collection_type = getattr(container, 'collection_type', '')
        if collection_type in self.academic_standards['academic_collection_types']:
            coherence_score += 0.2
        
        # Check if target audience is appropriate for academic work
        target_audience = getattr(container, 'target_audience', '')
        if target_audience in ['academic', 'professional', 'public']:
            coherence_score += 0.1
        elif target_audience == 'self':
            validation_result['recommendations'].append(
                "Consider setting target audience to 'academic' for scholarly collections"
            )
        
        # Check publication status for academic rigor
        pub_status = getattr(container, 'publication_status', '')
        if pub_status in ['review', 'published']:
            coherence_score += 0.1
        elif pub_status == 'draft':
            validation_result['recommendations'].append(
                "Consider moving to 'review' status when collection is complete"
            )
        
        return min(1.0, coherence_score)
    
    def _validate_academic_formatting(self, container, validation_result) -> float:
        """Validate academic formatting and presentation standards."""
        formatting_score = 0.5  # Base score
        
        # Check title formatting (should be descriptive and professional)
        title = getattr(container, 'title', '')
        if title:
            if len(title) >= 10 and len(title) <= 100:  # Reasonable length
                formatting_score += 0.2
            if title[0].isupper():  # Proper capitalization
                formatting_score += 0.1
        
        # Check description quality
        description = getattr(container, 'description', '')
        if description:
            if len(description) >= 50:  # Substantial description
                formatting_score += 0.2
            if len(description.split()) >= 10:  # Adequate detail
                formatting_score += 0.1
        
        # Check for tags (academic categorization)
        tags = getattr(container, 'tags', [])
        if tags and len(tags) >= 2:
            formatting_score += 0.1
        elif not tags:
            validation_result['recommendations'].append(
                "Add tags for better academic categorization"
            )
        
        return min(1.0, formatting_score)


class ContainerIntegrityValidator:
    """Validator for Knowledge Container structural and referential integrity."""
    
    def validate_container_integrity(self, container) -> Dict[str, Any]:
        """Perform comprehensive integrity validation."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'integrity_score': 0.0,
            'broken_references': [],
            'orphaned_items': []
        }
        
        try:
            # Validate reference integrity
            ref_score = self._validate_reference_integrity(container, validation_result)
            
            # Validate content accessibility
            access_score = self._validate_content_accessibility(container, validation_result)
            
            # Validate collection consistency
            consistency_score = self._validate_collection_consistency(container, validation_result)
            
            # Calculate overall integrity score
            validation_result['integrity_score'] = (
                ref_score * 0.4 + access_score * 0.4 + consistency_score * 0.2
            )
            
            if validation_result['integrity_score'] < 0.8:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"Integrity score {validation_result['integrity_score']:.2f} below threshold 0.8"
                )
                
        except Exception as e:
            logger.error(f"Error in integrity validation: {e}")
            validation_result['valid'] = False
            validation_result['errors'].append(f"Integrity validation error: {str(e)}")
        
        return validation_result
    
    def _validate_reference_integrity(self, container, validation_result) -> float:
        """Validate that all UID references point to valid, accessible objects."""
        catalog = api.portal.get_tool('portal_catalog')
        total_refs = 0
        valid_refs = 0
        
        content_fields = [
            'included_knowledge_items', 'included_research_notes',
            'included_learning_goals', 'included_project_logs', 
            'included_bookmarks'
        ]
        
        for field_name in content_fields:
            uids = getattr(container, field_name, [])
            for uid in uids:
                total_refs += 1
                try:
                    brains = catalog(UID=uid)
                    if brains:
                        obj = brains[0].getObject()
                        if obj:
                            valid_refs += 1
                        else:
                            validation_result['broken_references'].append({
                                'field': field_name,
                                'uid': uid,
                                'error': 'Object not accessible'
                            })
                    else:
                        validation_result['broken_references'].append({
                            'field': field_name,
                            'uid': uid,
                            'error': 'UID not found in catalog'
                        })
                except Exception as e:
                    validation_result['broken_references'].append({
                        'field': field_name,
                        'uid': uid,
                        'error': str(e)
                    })
        
        if total_refs == 0:
            return 1.0  # No references to validate
        
        return valid_refs / total_refs
    
    def _validate_content_accessibility(self, container, validation_result) -> float:
        """Validate that referenced content is accessible to current user."""
        # This would check permissions, but for now we'll assume accessibility
        # In a full implementation, this would verify read permissions
        return 1.0
    
    def _validate_collection_consistency(self, container, validation_result) -> float:
        """Validate internal consistency of collection metadata."""
        consistency_score = 1.0
        
        # Check for logical consistency
        pub_status = getattr(container, 'publication_status', '')
        target_audience = getattr(container, 'target_audience', '')
        
        # Draft collections shouldn't be public
        if pub_status == 'draft' and target_audience == 'public':
            validation_result['warnings'].append(
                "Draft collections should not have public target audience"
            )
            consistency_score -= 0.2
        
        # Published collections should have substantial content
        if pub_status == 'published':
            total_items = sum(
                len(getattr(container, field, []))
                for field in ['included_knowledge_items', 'included_research_notes',
                             'included_learning_goals', 'included_project_logs',
                             'included_bookmarks']
            )
            if total_items < 5:
                validation_result['warnings'].append(
                    "Published collections should have substantial content (5+ items)"
                )
                consistency_score -= 0.3
        
        return max(0.0, consistency_score)


class KnowledgeSovereigntyValidator:
    """Validator for knowledge sovereignty compliance."""
    
    def validate_sovereignty_compliance(self, container) -> Dict[str, Any]:
        """Validate knowledge sovereignty principles."""
        validation_result = {
            'valid': True,
            'sovereignty_score': 0.0,
            'compliance_issues': [],
            'recommendations': []
        }
        
        try:
            # Check data portability
            portability_score = self._validate_data_portability(container, validation_result)
            
            # Check privacy settings
            privacy_score = self._validate_privacy_settings(container, validation_result)
            
            # Check user control
            control_score = self._validate_user_control(container, validation_result)
            
            validation_result['sovereignty_score'] = (
                portability_score * 0.4 + privacy_score * 0.4 + control_score * 0.2
            )
            
            if validation_result['sovereignty_score'] < 0.9:
                validation_result['compliance_issues'].append(
                    "Knowledge sovereignty score below recommended threshold"
                )
                
        except Exception as e:
            logger.error(f"Error in sovereignty validation: {e}")
            validation_result['valid'] = False
            validation_result['compliance_issues'].append(f"Sovereignty validation error: {str(e)}")
        
        return validation_result
    
    def _validate_data_portability(self, container, validation_result) -> float:
        """Validate data portability compliance."""
        score = 0.8  # Base score for Plone's open architecture
        
        # Check export formats availability
        export_formats = getattr(container, 'export_formats', set())
        open_formats = {'json', 'markdown', 'html'}
        
        if open_formats.intersection(export_formats):
            score += 0.2
        else:
            validation_result['recommendations'].append(
                "Add open export formats (JSON, Markdown, HTML) for data portability"
            )
        
        return min(1.0, score)
    
    def _validate_privacy_settings(self, container, validation_result) -> float:
        """Validate privacy-first settings."""
        score = 1.0
        
        # Check target audience for privacy
        target_audience = getattr(container, 'target_audience', '')
        if target_audience == 'public':
            validation_result['recommendations'].append(
                "Consider privacy implications of public sharing"
            )
            score -= 0.1
        
        # Check sharing permissions for granular control
        sharing_perms = getattr(container, 'sharing_permissions', {})
        if sharing_perms:
            score += 0.1  # Bonus for granular control
        
        return score
    
    def _validate_user_control(self, container, validation_result) -> float:
        """Validate user maintains control over their knowledge."""
        # In Plone, users have inherent control, so this is mostly informational
        return 1.0


def validate_knowledge_container(container) -> Dict[str, Any]:
    """Comprehensive validation of Knowledge Container."""
    final_result = {
        'timestamp': datetime.now().isoformat(),
        'container_uid': getattr(container, 'UID', lambda: 'unknown')(),
        'overall_valid': True,
        'validation_results': {}
    }
    
    # Run all validators
    validators = {
        'academic_standards': AcademicStandardsValidator(),
        'container_integrity': ContainerIntegrityValidator(),
        'knowledge_sovereignty': KnowledgeSovereigntyValidator()
    }
    
    for validator_name, validator in validators.items():
        try:
            if validator_name == 'academic_standards':
                result = validator.validate_academic_completeness(container)
            elif validator_name == 'container_integrity':
                result = validator.validate_container_integrity(container)
            elif validator_name == 'knowledge_sovereignty':
                result = validator.validate_sovereignty_compliance(container)
            
            final_result['validation_results'][validator_name] = result
            
            if not result.get('valid', True):
                final_result['overall_valid'] = False
                
        except Exception as e:
            logger.error(f"Error running {validator_name} validator: {e}")
            final_result['validation_results'][validator_name] = {
                'valid': False,
                'error': str(e)
            }
            final_result['overall_valid'] = False
    
    return final_result 