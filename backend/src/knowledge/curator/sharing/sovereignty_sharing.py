"""Knowledge sovereignty-compliant sharing and permission system."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from plone import api
from zope.interface import Invalid
import uuid
import hashlib
import json

logger = logging.getLogger(__name__)


class SovereigntyLevel(Enum):
    """Knowledge sovereignty protection levels."""
    FULL_CONTROL = "full_control"  # Complete user control, no external dependencies
    FEDERATED = "federated"        # Controlled sharing with trusted institutions
    ACADEMIC_OPEN = "academic_open"  # Open to academic community with attribution
    PUBLIC_DOMAIN = "public_domain"  # Public sharing with sovereignty notices


class PermissionType(Enum):
    """Academic-grade permission types."""
    VIEW = "view"                # Read-only access
    COMMENT = "comment"          # Add annotations and comments
    CITE = "cite"                # Citation rights with proper attribution
    REFERENCE = "reference"      # Reference in academic work
    COLLABORATE = "collaborate"  # Co-author and edit
    CURATE = "curate"           # Add/remove content from collection
    MANAGE = "manage"           # Full management including sharing
    EXPORT = "export"           # Export rights for personal use


class ShareScope(Enum):
    """Academic sharing scopes."""
    INDIVIDUAL = "individual"    # Share with specific individuals
    INSTITUTION = "institution"  # Share within academic institution
    RESEARCH_GROUP = "research_group"  # Share with research collaborators
    ACADEMIC_PUBLIC = "academic_public"  # Public academic sharing
    CONTROLLED_PUBLIC = "controlled_public"  # Public with sovereignty controls


@dataclass
class SharingAgreement:
    """Represents a sharing agreement with sovereignty protections."""
    agreement_id: str
    container_uid: str
    grantor_id: str  # User granting access
    grantee_id: str  # User receiving access
    permissions: List[str]
    sovereignty_level: str
    share_scope: str
    
    # Academic requirements
    citation_required: bool = True
    attribution_text: Optional[str] = None
    academic_use_only: bool = True
    
    # Temporal controls
    created_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    access_count: int = 0
    max_access_count: Optional[int] = None
    
    # Sovereignty protections
    data_residency_required: bool = True
    export_restrictions: List[str] = None
    revocation_notice_period: int = 7  # Days
    
    # Tracking and analytics
    last_accessed: Optional[datetime] = None
    access_log: List[Dict] = None
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.access_log is None:
            self.access_log = []
        if self.export_restrictions is None:
            self.export_restrictions = []


class KnowledgeSovereigntyManager:
    """Manager for knowledge sovereignty-compliant sharing."""
    
    def __init__(self):
        self.sovereignty_policies = self._load_sovereignty_policies()
        self.academic_standards = self._load_academic_standards()
    
    def create_sharing_agreement(self, container_uid: str, grantee_id: str, 
                               permissions: List[str], sovereignty_level: SovereigntyLevel,
                               share_scope: ShareScope, **kwargs) -> SharingAgreement:
        """Create a new sharing agreement with sovereignty protections."""
        
        # Validate sovereignty compliance
        self._validate_sovereignty_compliance(sovereignty_level, permissions, share_scope)
        
        # Generate secure agreement ID
        agreement_id = self._generate_agreement_id(container_uid, grantee_id)
        
        # Get current user as grantor
        grantor_id = api.user.get_current().getId()
        
        # Create agreement with academic defaults
        agreement = SharingAgreement(
            agreement_id=agreement_id,
            container_uid=container_uid,
            grantor_id=grantor_id,
            grantee_id=grantee_id,
            permissions=permissions,
            sovereignty_level=sovereignty_level.value,
            share_scope=share_scope.value,
            **kwargs
        )
        
        # Apply sovereignty protections based on level
        self._apply_sovereignty_protections(agreement, sovereignty_level)
        
        # Apply academic standards
        self._apply_academic_standards(agreement, share_scope)
        
        # Store agreement
        self._store_sharing_agreement(agreement)
        
        # Create sovereignty audit log
        self._log_sovereignty_event("agreement_created", agreement)
        
        return agreement
    
    def revoke_sharing_agreement(self, agreement_id: str, reason: str = None) -> bool:
        """Revoke a sharing agreement with proper sovereignty notice."""
        
        agreement = self._get_sharing_agreement(agreement_id)
        if not agreement:
            return False
        
        # Check if current user can revoke
        current_user = api.user.get_current().getId()
        if current_user != agreement.grantor_id:
            raise PermissionError("Only the grantor can revoke sharing agreements")
        
        # Apply notice period for sovereignty compliance
        if agreement.revocation_notice_period > 0:
            self._schedule_revocation(agreement, reason)
            return True
        else:
            # Immediate revocation
            return self._execute_revocation(agreement, reason)
    
    def validate_access_request(self, agreement_id: str, requested_permission: str) -> Dict[str, Any]:
        """Validate an access request against sovereignty and academic standards."""
        
        agreement = self._get_sharing_agreement(agreement_id)
        if not agreement:
            return {'valid': False, 'reason': 'Agreement not found'}
        
        validation_result = {
            'valid': True,
            'agreement': agreement,
            'restrictions': [],
            'requirements': []
        }
        
        # Check temporal validity
        if agreement.expiry_date and datetime.now() > agreement.expiry_date:
            validation_result['valid'] = False
            validation_result['reason'] = 'Agreement has expired'
            return validation_result
        
        # Check access limits
        if (agreement.max_access_count and 
            agreement.access_count >= agreement.max_access_count):
            validation_result['valid'] = False
            validation_result['reason'] = 'Access limit exceeded'
            return validation_result
        
        # Check permission validity
        if requested_permission not in agreement.permissions:
            validation_result['valid'] = False
            validation_result['reason'] = f'Permission {requested_permission} not granted'
            return validation_result
        
        # Apply sovereignty restrictions
        sovereignty_restrictions = self._get_sovereignty_restrictions(agreement)
        validation_result['restrictions'].extend(sovereignty_restrictions)
        
        # Apply academic requirements
        academic_requirements = self._get_academic_requirements(agreement)
        validation_result['requirements'].extend(academic_requirements)
        
        return validation_result
    
    def log_access_event(self, agreement_id: str, access_type: str, details: Dict = None):
        """Log access events for sovereignty and academic compliance."""
        
        agreement = self._get_sharing_agreement(agreement_id)
        if not agreement:
            return
        
        # Create access log entry
        access_entry = {
            'timestamp': datetime.now().isoformat(),
            'access_type': access_type,
            'user_id': api.user.get_current().getId(),
            'details': details or {}
        }
        
        # Update agreement
        agreement.access_log.append(access_entry)
        agreement.access_count += 1
        agreement.last_accessed = datetime.now()
        
        # Store updated agreement
        self._store_sharing_agreement(agreement)
        
        # Log sovereignty event
        self._log_sovereignty_event("access_event", agreement, access_entry)
    
    def generate_sovereignty_report(self, container_uid: str) -> Dict[str, Any]:
        """Generate comprehensive sovereignty compliance report."""
        
        agreements = self._get_container_agreements(container_uid)
        
        report = {
            'container_uid': container_uid,
            'generated_at': datetime.now().isoformat(),
            'sovereignty_summary': {
                'total_agreements': len(agreements),
                'sovereignty_levels': {},
                'share_scopes': {},
                'academic_compliance': True
            },
            'access_analytics': {
                'total_accesses': 0,
                'unique_users': set(),
                'access_patterns': []
            },
            'compliance_status': {
                'data_sovereignty': True,
                'academic_standards': True,
                'export_controls': True,
                'privacy_compliance': True
            },
            'recommendations': []
        }
        
        # Analyze agreements
        for agreement in agreements:
            # Count sovereignty levels
            level = agreement.sovereignty_level
            report['sovereignty_summary']['sovereignty_levels'][level] = \
                report['sovereignty_summary']['sovereignty_levels'].get(level, 0) + 1
            
            # Count share scopes
            scope = agreement.share_scope
            report['sovereignty_summary']['share_scopes'][scope] = \
                report['sovereignty_summary']['share_scopes'].get(scope, 0) + 1
            
            # Analyze access patterns
            report['access_analytics']['total_accesses'] += agreement.access_count
            report['access_analytics']['unique_users'].add(agreement.grantee_id)
            
            # Check compliance issues
            if not agreement.citation_required and agreement.share_scope != ShareScope.INDIVIDUAL.value:
                report['compliance_status']['academic_standards'] = False
                report['recommendations'].append(
                    f"Agreement {agreement.agreement_id} should require citations for {agreement.share_scope} sharing"
                )
        
        # Convert set to count
        report['access_analytics']['unique_users'] = len(report['access_analytics']['unique_users'])
        
        return report
    
    def _validate_sovereignty_compliance(self, sovereignty_level: SovereigntyLevel, 
                                       permissions: List[str], share_scope: ShareScope):
        """Validate that sharing request complies with sovereignty principles."""
        
        # Full control level restrictions
        if sovereignty_level == SovereigntyLevel.FULL_CONTROL:
            if share_scope not in [ShareScope.INDIVIDUAL, ShareScope.RESEARCH_GROUP]:
                raise Invalid("FULL_CONTROL sovereignty requires limited sharing scope")
            if PermissionType.EXPORT.value in permissions:
                raise Invalid("FULL_CONTROL sovereignty restricts export permissions")
        
        # Public domain requirements
        if sovereignty_level == SovereigntyLevel.PUBLIC_DOMAIN:
            if PermissionType.MANAGE.value in permissions:
                raise Invalid("PUBLIC_DOMAIN sovereignty cannot grant management permissions")
        
        # Academic open restrictions
        if sovereignty_level == SovereigntyLevel.ACADEMIC_OPEN:
            if share_scope == ShareScope.CONTROLLED_PUBLIC:
                raise Invalid("ACADEMIC_OPEN sovereignty requires academic-only sharing")
    
    def _apply_sovereignty_protections(self, agreement: SharingAgreement, 
                                     sovereignty_level: SovereigntyLevel):
        """Apply sovereignty protections based on level."""
        
        if sovereignty_level == SovereigntyLevel.FULL_CONTROL:
            agreement.data_residency_required = True
            agreement.export_restrictions = ["no_external_systems", "local_only"]
            agreement.revocation_notice_period = 1  # Immediate
            
        elif sovereignty_level == SovereigntyLevel.FEDERATED:
            agreement.data_residency_required = True
            agreement.export_restrictions = ["institutional_only"]
            agreement.revocation_notice_period = 3
            
        elif sovereignty_level == SovereigntyLevel.ACADEMIC_OPEN:
            agreement.citation_required = True
            agreement.academic_use_only = True
            agreement.export_restrictions = ["academic_use_only"]
            
        elif sovereignty_level == SovereigntyLevel.PUBLIC_DOMAIN:
            agreement.citation_required = True
            agreement.academic_use_only = False
            agreement.data_residency_required = False
    
    def _apply_academic_standards(self, agreement: SharingAgreement, share_scope: ShareScope):
        """Apply academic standards to sharing agreement."""
        
        # Generate attribution text if not provided
        if not agreement.attribution_text:
            container = api.content.get(UID=agreement.container_uid)
            grantor = api.user.get(agreement.grantor_id)
            agreement.attribution_text = f"{container.title} by {grantor.getProperty('fullname', grantor.getId())}"
        
        # Set appropriate expiry for academic sharing
        if share_scope in [ShareScope.ACADEMIC_PUBLIC, ShareScope.CONTROLLED_PUBLIC]:
            if not agreement.expiry_date:
                # Academic sharing expires after 2 years by default
                agreement.expiry_date = datetime.now() + timedelta(days=730)
        
        # Set access limits for large-scale sharing
        if share_scope == ShareScope.CONTROLLED_PUBLIC and not agreement.max_access_count:
            agreement.max_access_count = 1000  # Reasonable limit for public sharing
    
    def _generate_agreement_id(self, container_uid: str, grantee_id: str) -> str:
        """Generate a secure, unique agreement ID."""
        timestamp = datetime.now().isoformat()
        source_string = f"{container_uid}:{grantee_id}:{timestamp}:{uuid.uuid4()}"
        return hashlib.sha256(source_string.encode()).hexdigest()[:16]
    
    def _store_sharing_agreement(self, agreement: SharingAgreement):
        """Store sharing agreement with sovereignty protections."""
        # In a full implementation, this would store in a secure, sovereignty-compliant storage
        # For now, we'll use Plone's annotation storage
        
        container = api.content.get(UID=agreement.container_uid)
        if not container:
            raise ValueError(f"Container {agreement.container_uid} not found")
        
        from zope.annotation.interfaces import IAnnotations
        annotations = IAnnotations(container)
        
        if 'knowledge.curator.sharing_agreements' not in annotations:
            annotations['knowledge.curator.sharing_agreements'] = {}
        
        # Store agreement as JSON (in practice, would use more secure storage)
        annotations['knowledge.curator.sharing_agreements'][agreement.agreement_id] = asdict(agreement)
    
    def _get_sharing_agreement(self, agreement_id: str) -> Optional[SharingAgreement]:
        """Retrieve sharing agreement by ID."""
        # This would query the sovereignty-compliant storage
        # For now, search through container annotations
        
        catalog = api.portal.get_tool('portal_catalog')
        containers = catalog(portal_type='KnowledgeContainer')
        
        for brain in containers:
            container = brain.getObject()
            from zope.annotation.interfaces import IAnnotations
            annotations = IAnnotations(container)
            
            agreements = annotations.get('knowledge.curator.sharing_agreements', {})
            if agreement_id in agreements:
                agreement_data = agreements[agreement_id]
                # Convert back to dataclass
                return SharingAgreement(**agreement_data)
        
        return None
    
    def _get_container_agreements(self, container_uid: str) -> List[SharingAgreement]:
        """Get all sharing agreements for a container."""
        container = api.content.get(UID=container_uid)
        if not container:
            return []
        
        from zope.annotation.interfaces import IAnnotations
        annotations = IAnnotations(container)
        
        agreements_data = annotations.get('knowledge.curator.sharing_agreements', {})
        agreements = []
        
        for agreement_data in agreements_data.values():
            agreements.append(SharingAgreement(**agreement_data))
        
        return agreements
    
    def _log_sovereignty_event(self, event_type: str, agreement: SharingAgreement, 
                             extra_data: Dict = None):
        """Log sovereignty-related events for audit and compliance."""
        
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'agreement_id': agreement.agreement_id,
            'container_uid': agreement.container_uid,
            'user_id': api.user.get_current().getId(),
            'sovereignty_level': agreement.sovereignty_level,
            'extra_data': extra_data or {}
        }
        
        # In practice, this would log to a sovereignty-compliant audit system
        logger.info(f"Sovereignty event: {json.dumps(event_data)}")
    
    def _load_sovereignty_policies(self) -> Dict:
        """Load sovereignty policies (placeholder for external policy system)."""
        return {
            'data_residency_countries': ['US', 'EU', 'CA'],
            'academic_export_allowed': True,
            'max_public_sharing_size': 100,  # MB
            'required_notice_periods': {
                'full_control': 1,
                'federated': 3,
                'academic_open': 7,
                'public_domain': 14
            }
        }
    
    def _load_academic_standards(self) -> Dict:
        """Load academic standards for sharing."""
        return {
            'citation_formats': ['apa', 'mla', 'chicago', 'ieee'],
            'required_attribution_fields': ['title', 'author', 'date', 'institution'],
            'academic_use_definitions': [
                'research', 'education', 'scholarly_analysis', 'peer_review'
            ],
            'prohibited_commercial_uses': [
                'resale', 'commercial_training', 'proprietary_products'
            ]
        }
    
    def _get_sovereignty_restrictions(self, agreement: SharingAgreement) -> List[str]:
        """Get sovereignty restrictions for an agreement."""
        restrictions = []
        
        if agreement.data_residency_required:
            restrictions.append("Data must remain within approved jurisdictions")
        
        if agreement.export_restrictions:
            restrictions.extend([
                f"Export restriction: {restriction}" 
                for restriction in agreement.export_restrictions
            ])
        
        if agreement.academic_use_only:
            restrictions.append("Academic use only - no commercial applications")
        
        return restrictions
    
    def _get_academic_requirements(self, agreement: SharingAgreement) -> List[str]:
        """Get academic requirements for an agreement."""
        requirements = []
        
        if agreement.citation_required:
            requirements.append(f"Citation required: {agreement.attribution_text}")
        
        if agreement.sovereignty_level in [SovereigntyLevel.ACADEMIC_OPEN.value, 
                                         SovereigntyLevel.PUBLIC_DOMAIN.value]:
            requirements.append("Proper academic attribution must be maintained")
        
        return requirements 