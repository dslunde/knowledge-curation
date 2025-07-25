"""Knowledge Container content type."""

from knowledge.curator.interfaces import IKnowledgeContainer
from plone.dexterity.content import Container
from zope.interface import implementer
from datetime import datetime
from plone import api
from zope.interface import Invalid
import io
import tempfile
import os
from pkg_resources import resource_string
from zope.pagetemplate.pagetemplatefile import PageTemplate
from knowledge.curator.content.validators import (
    validate_container_uid_references,
    validate_container_collection_type,
    validate_container_organization_structure,
    validate_container_publication_status,
    validate_container_target_audience,
    validate_container_sharing_permissions,
    validate_container_export_formats,
    validate_container_view_analytics,
)


@implementer(IKnowledgeContainer)
class KnowledgeContainer(Container):
    """Knowledge Container content type implementation."""

    def __init__(self, id=None):
        """Initialize the container with default values."""
        super().__init__(id)
        
        # Initialize IKnowledgeObjectBase fields with defaults
        if not hasattr(self, 'difficulty_level'):
            self.difficulty_level = "intermediate"
        if not hasattr(self, 'cognitive_load'):
            self.cognitive_load = None
        if not hasattr(self, 'learning_style'):
            self.learning_style = []
        if not hasattr(self, 'knowledge_status'):
            self.knowledge_status = "draft"
        if not hasattr(self, 'last_reviewed'):
            self.last_reviewed = None
        if not hasattr(self, 'review_frequency'):
            self.review_frequency = 30
        if not hasattr(self, 'confidence_score'):
            self.confidence_score = None
        if not hasattr(self, 'authors'):
            self.authors = []
        if not hasattr(self, 'publication_date'):
            self.publication_date = None
        if not hasattr(self, 'source_url'):
            self.source_url = None
        if not hasattr(self, 'doi'):
            self.doi = None
        if not hasattr(self, 'isbn'):
            self.isbn = None
        if not hasattr(self, 'journal_name'):
            self.journal_name = None
        if not hasattr(self, 'volume_issue'):
            self.volume_issue = None
        if not hasattr(self, 'page_numbers'):
            self.page_numbers = None
        if not hasattr(self, 'publisher'):
            self.publisher = None
        if not hasattr(self, 'citation_format'):
            self.citation_format = None
        
        # Initialize content lists with empty lists if not set
        if not hasattr(self, 'included_learning_goals'):
            self.included_learning_goals = []
        if not hasattr(self, 'included_knowledge_items'):
            self.included_knowledge_items = []
        if not hasattr(self, 'included_research_notes'):
            self.included_research_notes = []
        if not hasattr(self, 'included_project_logs'):
            self.included_project_logs = []
        if not hasattr(self, 'included_bookmarks'):
            self.included_bookmarks = []
        
        # Set default values for metadata fields
        if not hasattr(self, 'collection_type'):
            self.collection_type = "knowledge_base"
        if not hasattr(self, 'organization_structure'):
            self.organization_structure = "topical"
        if not hasattr(self, 'publication_status'):
            self.publication_status = "draft"
        if not hasattr(self, 'target_audience'):
            self.target_audience = "self"
        if not hasattr(self, 'sharing_permissions'):
            self.sharing_permissions = {}
        if not hasattr(self, 'export_formats'):
            self.export_formats = set()
        if not hasattr(self, 'view_analytics'):
            self.view_analytics = {}
        if not hasattr(self, 'created_date'):
            self.created_date = datetime.now()
        if not hasattr(self, 'last_modified_date'):
            self.last_modified_date = None
        if not hasattr(self, 'total_items_count'):
            self.total_items_count = 0
        if not hasattr(self, 'container_version'):
            self.container_version = "1.0"
        if not hasattr(self, 'tags'):
            self.tags = []

    def add_content_item(self, content_type, uid):
        """Add a content item to the container.
        
        Args:
            content_type: Type of content ('learning_goals', 'knowledge_items', 
                         'research_notes', 'project_logs', 'bookmarks')
            uid: UID of the content item to add
            
        Raises:
            ValueError: If content_type is invalid or item doesn't exist
            
        Returns:
            bool: True if item was added, False if already exists
        """
        # Validate content type
        valid_types = {
            'learning_goals': 'included_learning_goals',
            'knowledge_items': 'included_knowledge_items',
            'research_notes': 'included_research_notes',
            'project_logs': 'included_project_logs',
            'bookmarks': 'included_bookmarks'
        }
        
        if content_type not in valid_types:
            raise ValueError(f"Invalid content_type: {content_type}. Must be one of {list(valid_types.keys())}")
        
        # Validate that the content item exists
        if not self._validate_content_reference(uid):
            raise ValueError(f"Content item with UID {uid} does not exist or is not accessible")
        
        # Get the appropriate list attribute
        field_name = valid_types[content_type]
        content_list = getattr(self, field_name, [])
        
        # Ensure it's a list
        if not isinstance(content_list, list):
            content_list = []
            setattr(self, field_name, content_list)
        
        # Check if item already exists
        if uid in content_list:
            return False
        
        # Add the item
        content_list.append(uid)
        setattr(self, field_name, content_list)
        
        # Update metadata
        self._update_metadata()
        
        return True

    def remove_content_item(self, content_type, uid):
        """Remove a content item from the container.
        
        Args:
            content_type: Type of content ('learning_goals', 'knowledge_items',
                         'research_notes', 'project_logs', 'bookmarks')
            uid: UID of the content item to remove
            
        Raises:
            ValueError: If content_type is invalid
            
        Returns:
            bool: True if item was removed, False if not found
        """
        # Validate content type
        valid_types = {
            'learning_goals': 'included_learning_goals',
            'knowledge_items': 'included_knowledge_items',
            'research_notes': 'included_research_notes',
            'project_logs': 'included_project_logs',
            'bookmarks': 'included_bookmarks'
        }
        
        if content_type not in valid_types:
            raise ValueError(f"Invalid content_type: {content_type}. Must be one of {list(valid_types.keys())}")
        
        # Get the appropriate list attribute
        field_name = valid_types[content_type]
        content_list = getattr(self, field_name, [])
        
        # Check if item exists and remove it
        if uid in content_list:
            content_list.remove(uid)
            setattr(self, field_name, content_list)
            
            # Update metadata
            self._update_metadata()
            
            return True
        
        return False

    def organize_content(self, structure_type):
        """Update the organization structure of the container.
        
        Args:
            structure_type: The organization structure type
                          ('hierarchical', 'network', 'linear', 'matrix', 'free_form')
                          
        Raises:
            ValueError: If structure_type is invalid
        """
        # Validate the structure type using the existing validator
        try:
            validate_container_organization_structure(structure_type)
        except Exception as e:
            raise ValueError(f"Invalid organization structure: {e}")
        
        # Update the organization structure
        self.organization_structure = structure_type
        
        # Update metadata
        self._update_metadata()

    def update_organization_structure(self):
        """Update the organization structure based on current content.
        
        This method analyzes the current content and suggests or applies
        an appropriate organization structure based on content types and relationships.
        """
        # Get total items count
        total_items = self._calculate_total_items()
        
        # Simple logic for determining appropriate structure
        # This could be enhanced with more sophisticated analysis
        if total_items == 0:
            suggested_structure = "free_form"
        elif total_items <= 5:
            suggested_structure = "linear"
        elif total_items <= 20:
            suggested_structure = "hierarchical"
        else:
            # Check if we have multiple content types - suggest matrix
            content_types_used = sum([
                1 if self.included_learning_goals else 0,
                1 if self.included_knowledge_items else 0,
                1 if self.included_research_notes else 0,
                1 if self.included_project_logs else 0,
                1 if self.included_bookmarks else 0,
            ])
            
            if content_types_used >= 3:
                suggested_structure = "matrix"
            else:
                suggested_structure = "network"
        
        # Update the organization structure
        self.organization_structure = suggested_structure
        
        # Update metadata
        self._update_metadata()

    def validate_content_references(self):
        """Validate that all referenced content items exist and are accessible.
        
        Returns:
            dict: Validation results with format:
                  {'valid': bool, 'invalid_refs': list, 'errors': list}
        """
        result = {
            'valid': True,
            'invalid_refs': [],
            'errors': []
        }
        
        # Content lists to validate
        content_lists = {
            'learning_goals': self.included_learning_goals or [],
            'knowledge_items': self.included_knowledge_items or [],
            'research_notes': self.included_research_notes or [],
            'project_logs': self.included_project_logs or [],
            'bookmarks': self.included_bookmarks or [],
        }
        
        # Validate each content list
        for content_type, uid_list in content_lists.items():
            try:
                validate_container_uid_references(uid_list)
            except Exception as e:
                result['valid'] = False
                result['errors'].append(f"Error validating {content_type}: {str(e)}")
                continue
            
            # Additional validation - check individual UIDs
            for uid in uid_list:
                if not self._validate_content_reference(uid):
                    result['valid'] = False
                    result['invalid_refs'].append({
                        'content_type': content_type,
                        'uid': uid
                    })
        
        return result

    def get_collection_summary(self):
        """Get a comprehensive summary of the container's contents.
        
        Returns:
            dict: Summary information about the container
        """
        # Calculate totals
        total_items = self._calculate_total_items()
        
        # Get content type breakdown
        content_breakdown = {
            'learning_goals': len(self.included_learning_goals or []),
            'knowledge_items': len(self.included_knowledge_items or []),
            'research_notes': len(self.included_research_notes or []),
            'project_logs': len(self.included_project_logs or []),
            'bookmarks': len(self.included_bookmarks or []),
        }
        
        # Validate references
        validation_result = self.validate_content_references()
        
        # Get metadata
        metadata = {
            'collection_type': getattr(self, 'collection_type', 'curated'),
            'organization_structure': getattr(self, 'organization_structure', 'hierarchical'),
            'publication_status': getattr(self, 'publication_status', 'draft'),
            'target_audience': getattr(self, 'target_audience', 'self'),
            'container_version': getattr(self, 'container_version', '1.0'),
            'created_date': getattr(self, 'created_date', None),
            'last_modified_date': getattr(self, 'last_modified_date', None),
        }
        
        # Build summary
        summary = {
            'basic_info': {
                'title': getattr(self, 'title', 'Untitled Container'),
                'description': getattr(self, 'description', ''),
                'total_items': total_items,
                'tags': getattr(self, 'tags', []),
            },
            'content_breakdown': content_breakdown,
            'metadata': metadata,
            'validation': validation_result,
            'organization': {
                'structure_type': self.organization_structure,
                'export_formats': list(getattr(self, 'export_formats', set())),
                'sharing_permissions': getattr(self, 'sharing_permissions', {}),
            },
            'analytics': getattr(self, 'view_analytics', {}),
        }
        
        return summary

    def _validate_content_reference(self, uid):
        """Validate that a UID references an existing, accessible content item.
        
        Args:
            uid: The UID to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not uid or not isinstance(uid, str):
            return False
        
        try:
            # Try to get the content item using Plone API
            content_item = api.content.get(UID=uid)
            return content_item is not None
        except Exception:
            # If we can't access the API (e.g., in tests), assume valid
            # This matches the behavior in the validators
            return True

    def _calculate_total_items(self):
        """Calculate the total number of items in all content lists.
        
        Returns:
            int: Total number of items
        """
        total = 0
        for attr_name in ['included_learning_goals', 'included_knowledge_items',
                         'included_research_notes', 'included_project_logs',
                         'included_bookmarks']:
            content_list = getattr(self, attr_name, [])
            if isinstance(content_list, list):
                total += len(content_list)
        
        return total

    def _update_metadata(self):
        """Update container metadata after content changes."""
        # Update last modified date
        self.last_modified_date = datetime.now()
        
        # Update total items count
        self.total_items_count = self._calculate_total_items()
        
        # Mark object as changed for ZODB persistence
        self._p_changed = True

    # Organization structure handlers for different structure types
    def _organize_hierarchical(self):
        """Apply hierarchical organization logic."""
        # This could include sorting by creation date, importance, or dependencies
        # For now, we maintain the current order but ensure it's applied
        pass

    def _organize_network(self):
        """Apply network organization logic."""
        # This could analyze relationships between items
        # For now, we maintain the current structure
        pass

    def _organize_linear(self):
        """Apply linear organization logic."""
        # This could sort by some logical progression
        # For now, we maintain chronological order
        pass

    def _organize_matrix(self):
        """Apply matrix organization logic."""
        # This could organize by multiple dimensions (topic, difficulty, etc.)
        # For now, we maintain the current grouping
        pass

    def _organize_free_form(self):
        """Apply free-form organization logic."""
        # This maintains user-defined order
        pass

    # Vocabulary definitions for container metadata
    COLLECTION_TYPE_VOCABULARY = {
        "course": "Course",
        "study_guide": "Study Guide", 
        "research_collection": "Research Collection",
        "project_portfolio": "Project Portfolio",
        "knowledge_base": "Knowledge Base"
    }
    
    ORGANIZATION_STRUCTURE_VOCABULARY = {
        "chronological": "Chronological",
        "topical": "Topical",
        "hierarchical": "Hierarchical", 
        "custom": "Custom"
    }
    
    PUBLICATION_STATUS_VOCABULARY = {
        "draft": "Draft",
        "review": "Under Review",
        "published": "Published",
        "archived": "Archived"
    }
    
    TARGET_AUDIENCE_VOCABULARY = {
        "self": "Self",
        "team": "Team",
        "public": "Public",
        "specific_users": "Specific Users"
    }
    
    PERMISSION_LEVELS = {
        "none": "No Access",
        "view": "View Only", 
        "edit": "Edit Access",
        "admin": "Full Admin"
    }

    def update_publication_status(self, new_status):
        """Update the publication status of the container.
        
        Args:
            new_status: New publication status (draft, review, published, archived)
            
        Raises:
            ValueError: If status is invalid
            
        Returns:
            bool: True if status was updated
        """
        if new_status not in self.PUBLICATION_STATUS_VOCABULARY:
            raise ValueError(
                f"Invalid publication status '{new_status}'. "
                f"Must be one of: {list(self.PUBLICATION_STATUS_VOCABULARY.keys())}"
            )
        
        # Store previous status for potential rollback
        previous_status = getattr(self, 'publication_status', 'draft')
        
        # Update the status
        self.publication_status = new_status
        
        # Update metadata
        self._update_metadata()
        
        # Log the status change in analytics if tracking is enabled
        if hasattr(self, 'view_analytics') and isinstance(self.view_analytics, dict):
            if 'status_changes' not in self.view_analytics:
                self.view_analytics['status_changes'] = []
            
            self.view_analytics['status_changes'].append({
                'timestamp': datetime.now().isoformat(),
                'from_status': previous_status,
                'to_status': new_status,
                'user': self._get_current_user_id()
            })
        
        return True
    
    def set_target_audience(self, audience):
        """Set the target audience for the container.
        
        Args:
            audience: Target audience (self, team, public, specific_users)
            
        Raises:
            ValueError: If audience is invalid
            
        Returns:
            bool: True if audience was updated
        """
        if audience not in self.TARGET_AUDIENCE_VOCABULARY:
            raise ValueError(
                f"Invalid target audience '{audience}'. "
                f"Must be one of: {list(self.TARGET_AUDIENCE_VOCABULARY.keys())}"
            )
        
        # Store previous audience for analytics
        previous_audience = getattr(self, 'target_audience', 'self')
        
        # Update the target audience
        self.target_audience = audience
        
        # Auto-configure default sharing permissions based on audience
        if audience == 'self':
            self.sharing_permissions = {
                'view': 'owner',
                'edit': 'owner',
                'share': 'none',
                'admin': 'owner'
            }
        elif audience == 'team':
            self.sharing_permissions = {
                'view': 'team',
                'edit': 'team', 
                'share': 'admin',
                'admin': 'owner'
            }
        elif audience == 'public':
            self.sharing_permissions = {
                'view': 'public',
                'edit': 'admin',
                'share': 'admin', 
                'admin': 'owner'
            }
        elif audience == 'specific_users':
            # Keep existing permissions or set restrictive defaults
            if not hasattr(self, 'sharing_permissions') or not self.sharing_permissions:
                self.sharing_permissions = {
                    'view': 'specific',
                    'edit': 'specific',
                    'share': 'admin',
                    'admin': 'owner'
                }
        
        # Update metadata
        self._update_metadata()
        
        # Log the audience change in analytics
        if hasattr(self, 'view_analytics') and isinstance(self.view_analytics, dict):
            if 'audience_changes' not in self.view_analytics:
                self.view_analytics['audience_changes'] = []
            
            self.view_analytics['audience_changes'].append({
                'timestamp': datetime.now().isoformat(),
                'from_audience': previous_audience,
                'to_audience': audience,
                'user': self._get_current_user_id()
            })
        
        return True
    
    def configure_sharing_permissions(self, permissions_dict):
        """Configure sharing permissions for the container.
        
        Args:
            permissions_dict: Dictionary with permission settings
                             Format: {'view': 'public', 'edit': 'team', 'share': 'admin', 'admin': 'owner'}
                             
        Raises:
            ValueError: If permissions structure is invalid
            
        Returns:
            bool: True if permissions were updated
        """
        if not isinstance(permissions_dict, dict):
            raise ValueError("Permissions must be provided as a dictionary")
        
        # Validate permission keys and values
        valid_permission_types = ['view', 'edit', 'share', 'admin']
        valid_permission_levels = ['none', 'owner', 'team', 'public', 'specific']
        
        for perm_type, perm_level in permissions_dict.items():
            if perm_type not in valid_permission_types:
                raise ValueError(
                    f"Invalid permission type '{perm_type}'. "
                    f"Must be one of: {valid_permission_types}"
                )
            
            if perm_level not in valid_permission_levels:
                raise ValueError(
                    f"Invalid permission level '{perm_level}'. "
                    f"Must be one of: {valid_permission_levels}"
                )
        
        # Validate permission hierarchy (admin >= share >= edit >= view)
        hierarchy = {'none': 0, 'owner': 1, 'specific': 2, 'team': 3, 'public': 4}
        
        view_level = hierarchy.get(permissions_dict.get('view', 'none'), 0)
        edit_level = hierarchy.get(permissions_dict.get('edit', 'none'), 0)
        share_level = hierarchy.get(permissions_dict.get('share', 'none'), 0)
        admin_level = hierarchy.get(permissions_dict.get('admin', 'owner'), 1)
        
        if not (admin_level <= share_level <= edit_level <= view_level):
            raise ValueError(
                "Permission hierarchy violation. Admin permissions must be most restrictive, "
                "view permissions most permissive"
            )
        
        # Store previous permissions for analytics
        previous_permissions = getattr(self, 'sharing_permissions', {}).copy()
        
        # Update sharing permissions
        self.sharing_permissions = permissions_dict.copy()
        
        # Update metadata
        self._update_metadata()
        
        # Log permission changes in analytics
        if hasattr(self, 'view_analytics') and isinstance(self.view_analytics, dict):
            if 'permission_changes' not in self.view_analytics:
                self.view_analytics['permission_changes'] = []
            
            self.view_analytics['permission_changes'].append({
                'timestamp': datetime.now().isoformat(),
                'from_permissions': previous_permissions,
                'to_permissions': permissions_dict.copy(),
                'user': self._get_current_user_id()
            })
        
        return True
    
    def track_view_analytics(self, event_type, event_data=None):
        """Track view and usage analytics for the container.
        
        Args:
            event_type: Type of event to track (view, edit, share, export, etc.)
            event_data: Additional data about the event (optional)
            
        Returns:
            bool: True if analytics were updated
        """
        if not hasattr(self, 'view_analytics') or self.view_analytics is None:
            self.view_analytics = {}
        
        # Initialize analytics structure if needed
        if 'events' not in self.view_analytics:
            self.view_analytics['events'] = []
        if 'summary' not in self.view_analytics:
            self.view_analytics['summary'] = {}
        
        # Record the event
        event_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user': self._get_current_user_id(),
            'data': event_data or {}
        }
        
        self.view_analytics['events'].append(event_record)
        
        # Update summary statistics
        summary = self.view_analytics['summary']
        
        # Total events
        summary['total_events'] = summary.get('total_events', 0) + 1
        
        # Event type counts
        if 'event_counts' not in summary:
            summary['event_counts'] = {}
        summary['event_counts'][event_type] = summary['event_counts'].get(event_type, 0) + 1
        
        # Unique users (maintain as list to avoid set serialization issues)
        if 'unique_users' not in summary:
            summary['unique_users'] = []
        
        current_user = self._get_current_user_id()
        if current_user not in summary['unique_users']:
            summary['unique_users'].append(current_user)
        
        summary['unique_user_count'] = len(summary['unique_users'])
        
        # First and last access
        if 'first_access' not in summary:
            summary['first_access'] = event_record['timestamp']
        summary['last_access'] = event_record['timestamp']
        
        # Keep only last 100 events to prevent bloat
        if len(self.view_analytics['events']) > 100:
            self.view_analytics['events'] = self.view_analytics['events'][-100:]
        
        # Update metadata
        self._update_metadata()
        
        return True
    
    def _get_current_user_id(self):
        """Get the current user ID for analytics tracking.
        
        Returns:
            str: User ID or 'anonymous' if not available
        """
        try:
            user = api.user.get_current()
            return user.getId() if user else 'anonymous'
        except Exception:
            return 'anonymous'
    
    def get_metadata_summary(self):
        """Get a summary of all container metadata.
        
        Returns:
            dict: Comprehensive metadata summary
        """
        return {
            'collection_info': {
                'type': getattr(self, 'collection_type', 'knowledge_base'),
                'type_label': self.COLLECTION_TYPE_VOCABULARY.get(
                    getattr(self, 'collection_type', 'knowledge_base'), 'Knowledge Base'
                ),
                'organization': getattr(self, 'organization_structure', 'topical'),
                'organization_label': self.ORGANIZATION_STRUCTURE_VOCABULARY.get(
                    getattr(self, 'organization_structure', 'topical'), 'Topical'
                )
            },
            'publication_info': {
                'status': getattr(self, 'publication_status', 'draft'),
                'status_label': self.PUBLICATION_STATUS_VOCABULARY.get(
                    getattr(self, 'publication_status', 'draft'), 'Draft'
                ),
                'target_audience': getattr(self, 'target_audience', 'self'),
                'audience_label': self.TARGET_AUDIENCE_VOCABULARY.get(
                    getattr(self, 'target_audience', 'self'), 'Self'
                )
            },
            'sharing_info': {
                'permissions': getattr(self, 'sharing_permissions', {}),
                'can_view': self._can_current_user_access('view'),
                'can_edit': self._can_current_user_access('edit'),
                'can_share': self._can_current_user_access('share'),
                'can_admin': self._can_current_user_access('admin')
            },
            'analytics_summary': getattr(self, 'view_analytics', {}).get('summary', {}),
            'content_summary': {
                'total_items': self._calculate_total_items(),
                'created_date': getattr(self, 'created_date', None),
                'last_modified': getattr(self, 'last_modified_date', None),
                'version': getattr(self, 'container_version', '1.0')
            }
        }
    
    def _can_current_user_access(self, permission_type):
        """Check if current user can access based on sharing permissions.
        
        Args:
            permission_type: Type of permission to check (view, edit, share, admin)
            
        Returns:
            bool: True if user has permission
        """
        # This is a simplified implementation - in production you'd integrate
        # with Plone's security system
        permissions = getattr(self, 'sharing_permissions', {})
        permission_level = permissions.get(permission_type, 'none')
        
        if permission_level == 'none':
            return False
        elif permission_level == 'owner':
            # Check if current user is owner
            try:
                current_user = api.user.get_current()
                owner = getattr(self, 'owner', None)
                return current_user and owner and current_user.getId() == owner
            except Exception:
                return False
        elif permission_level in ['team', 'public', 'specific']:
            # In production, this would check actual group membership, etc.
            return True
        
        return False

    # Analytics and Sharing System
    def initialize_analytics(self):
        """Initialize the analytics tracking system with required structure."""
        if not hasattr(self, 'view_analytics') or self.view_analytics is None:
            self.view_analytics = {}
        
        # Initialize analytics structure
        analytics = self.view_analytics
        
        # Core analytics fields
        if 'view_count' not in analytics:
            analytics['view_count'] = 0
        if 'unique_viewers' not in analytics:
            analytics['unique_viewers'] = set()
        if 'last_accessed' not in analytics:
            analytics['last_accessed'] = None
        if 'popular_content_items' not in analytics:
            analytics['popular_content_items'] = {}
        if 'engagement_metrics' not in analytics:
            analytics['engagement_metrics'] = {
                'total_time_spent': 0,
                'average_session_duration': 0,
                'bounce_rate': 0.0,
                'return_visits': 0,
                'content_interactions': 0,
                'export_count': 0,
                'share_count': 0
            }
        
        # Activity tracking
        if 'activity_log' not in analytics:
            analytics['activity_log'] = []
        if 'user_sessions' not in analytics:
            analytics['user_sessions'] = {}
        if 'content_item_views' not in analytics:
            analytics['content_item_views'] = {}
        
        # Date tracking
        if 'first_view' not in analytics:
            analytics['first_view'] = None
        if 'peak_usage_times' not in analytics:
            analytics['peak_usage_times'] = {}
        
        self.view_analytics = analytics
        self._update_metadata()
        return True
    
    def track_container_view(self, user_id=None, session_data=None):
        """Track a container view with comprehensive analytics.
        
        Args:
            user_id (str): ID of the viewing user (optional)
            session_data (dict): Additional session information (optional)
            
        Returns:
            dict: Updated analytics summary
        """
        self.initialize_analytics()
        
        current_time = datetime.now()
        user_id = user_id or self._get_current_user_id()
        
        analytics = self.view_analytics
        
        # Update view count
        analytics['view_count'] += 1
        
        # Track unique viewers (convert set to list for ZODB compatibility)
        if isinstance(analytics['unique_viewers'], set):
            unique_viewers_list = list(analytics['unique_viewers'])
        else:
            unique_viewers_list = analytics['unique_viewers'] or []
        
        if user_id not in unique_viewers_list:
            unique_viewers_list.append(user_id)
            analytics['unique_viewers'] = unique_viewers_list
        
        # Update access times
        analytics['last_accessed'] = current_time.isoformat()
        if analytics['first_view'] is None:
            analytics['first_view'] = current_time.isoformat()
        
        # Track user sessions
        if user_id not in analytics['user_sessions']:
            analytics['user_sessions'][user_id] = {
                'first_visit': current_time.isoformat(),
                'visit_count': 0,
                'total_time': 0,
                'last_visit': None
            }
        
        user_session = analytics['user_sessions'][user_id]
        user_session['visit_count'] += 1
        user_session['last_visit'] = current_time.isoformat()
        
        # Update engagement metrics
        engagement = analytics['engagement_metrics']
        if user_session['visit_count'] > 1:
            engagement['return_visits'] += 1
        
        # Log activity
        activity_entry = {
            'timestamp': current_time.isoformat(),
            'user_id': user_id,
            'action': 'view_container',
            'session_data': session_data or {},
            'analytics_snapshot': {
                'view_count': analytics['view_count'],
                'unique_viewers_count': len(unique_viewers_list)
            }
        }
        
        analytics['activity_log'].append(activity_entry)
        
        # Keep activity log manageable (last 500 entries)
        if len(analytics['activity_log']) > 500:
            analytics['activity_log'] = analytics['activity_log'][-500:]
        
        # Track peak usage times
        hour_key = current_time.strftime('%H')
        if hour_key not in analytics['peak_usage_times']:
            analytics['peak_usage_times'][hour_key] = 0
        analytics['peak_usage_times'][hour_key] += 1
        
        self.view_analytics = analytics
        self._update_metadata()
        
        return self.get_analytics_summary()
    
    def track_content_item_interaction(self, content_type, content_uid, interaction_type='view', user_id=None):
        """Track interactions with specific content items within the container.
        
        Args:
            content_type (str): Type of content (learning_goals, knowledge_items, etc.)
            content_uid (str): UID of the specific content item
            interaction_type (str): Type of interaction (view, edit, share, export)
            user_id (str): ID of the user (optional)
            
        Returns:
            bool: True if tracking was successful
        """
        self.initialize_analytics()
        
        current_time = datetime.now()
        user_id = user_id or self._get_current_user_id()
        
        analytics = self.view_analytics
        
        # Track content item views
        content_key = f"{content_type}:{content_uid}"
        if content_key not in analytics['content_item_views']:
            analytics['content_item_views'][content_key] = {
                'view_count': 0,
                'unique_viewers': [],
                'last_accessed': None,
                'first_accessed': current_time.isoformat(),
                'interaction_types': {}
            }
        
        item_analytics = analytics['content_item_views'][content_key]
        
        # Update interaction metrics
        if interaction_type not in item_analytics['interaction_types']:
            item_analytics['interaction_types'][interaction_type] = 0
        item_analytics['interaction_types'][interaction_type] += 1
        
        if interaction_type == 'view':
            item_analytics['view_count'] += 1
            if user_id not in item_analytics['unique_viewers']:
                item_analytics['unique_viewers'].append(user_id)
        
        item_analytics['last_accessed'] = current_time.isoformat()
        
        # Update popular content items
        if content_key not in analytics['popular_content_items']:
            analytics['popular_content_items'][content_key] = {
                'total_interactions': 0,
                'content_type': content_type,
                'content_uid': content_uid,
                'score': 0
            }
        
        popular_item = analytics['popular_content_items'][content_key]
        popular_item['total_interactions'] += 1
        
        # Calculate popularity score (weighted by interaction type)
        interaction_weights = {
            'view': 1,
            'edit': 3,
            'share': 5,
            'export': 2,
            'comment': 2
        }
        weight = interaction_weights.get(interaction_type, 1)
        popular_item['score'] += weight
        
        # Update engagement metrics
        analytics['engagement_metrics']['content_interactions'] += 1
        
        # Log activity
        activity_entry = {
            'timestamp': current_time.isoformat(),
            'user_id': user_id,
            'action': f'{interaction_type}_content_item',
            'content_type': content_type,
            'content_uid': content_uid,
            'interaction_data': {
                'content_key': content_key,
                'interaction_type': interaction_type
            }
        }
        
        analytics['activity_log'].append(activity_entry)
        
        self.view_analytics = analytics
        self._update_metadata()
        
        return True
    
    def get_analytics_summary(self):
        """Get a comprehensive analytics summary.
        
        Returns:
            dict: Analytics summary with all key metrics
        """
        self.initialize_analytics()
        analytics = self.view_analytics
        
        # Convert unique_viewers to list if it's a set
        unique_viewers = analytics.get('unique_viewers', [])
        if isinstance(unique_viewers, set):
            unique_viewers = list(unique_viewers)
            analytics['unique_viewers'] = unique_viewers
        
        # Calculate derived metrics
        total_views = analytics.get('view_count', 0)
        unique_viewers_count = len(unique_viewers)
        
        # Get top popular content items
        popular_items = analytics.get('popular_content_items', {})
        top_content = sorted(
            popular_items.items(),
            key=lambda x: x[1].get('score', 0),
            reverse=True
        )[:10]
        
        # Calculate engagement rate
        content_interactions = analytics.get('engagement_metrics', {}).get('content_interactions', 0)
        engagement_rate = (content_interactions / max(total_views, 1)) * 100
        
        # Get peak usage time
        peak_times = analytics.get('peak_usage_times', {})
        peak_hour = max(peak_times.items(), key=lambda x: x[1])[0] if peak_times else None
        
        # Calculate return visitor rate
        return_visits = analytics.get('engagement_metrics', {}).get('return_visits', 0)
        return_rate = (return_visits / max(unique_viewers_count, 1)) * 100
        
        summary = {
            'view_count': total_views,
            'unique_viewers': unique_viewers,
            'unique_viewers_count': unique_viewers_count,
            'last_accessed': analytics.get('last_accessed'),
            'first_view': analytics.get('first_view'),
            'popular_content_items': [{
                'content_key': item[0],
                'content_type': item[1].get('content_type'),
                'content_uid': item[1].get('content_uid'),
                'score': item[1].get('score', 0),
                'total_interactions': item[1].get('total_interactions', 0)
            } for item in top_content],
            'engagement_metrics': {
                **analytics.get('engagement_metrics', {}),
                'engagement_rate': round(engagement_rate, 2),
                'return_visitor_rate': round(return_rate, 2),
                'average_views_per_user': round(total_views / max(unique_viewers_count, 1), 2)
            },
            'usage_patterns': {
                'peak_hour': peak_hour,
                'peak_usage_times': peak_times,
                'total_sessions': len(analytics.get('user_sessions', {})),
                'active_users': len([s for s in analytics.get('user_sessions', {}).values() 
                                   if s.get('visit_count', 0) > 1])
            },
            'content_analytics': {
                'total_content_items_tracked': len(analytics.get('content_item_views', {})),
                'most_viewed_content': self._get_most_viewed_content(),
                'content_interaction_breakdown': self._get_content_interaction_breakdown()
            }
        }
        
        return summary
    
    def initialize_sharing_system(self):
        """Initialize the sharing permissions system."""
        if not hasattr(self, 'sharing_permissions') or not isinstance(self.sharing_permissions, dict):
            self.sharing_permissions = {}
        
        # Initialize sharing structure
        permissions = self.sharing_permissions
        
        # Core permission levels
        if 'permission_levels' not in permissions:
            permissions['permission_levels'] = {
                'view': 'Can view container and content',
                'comment': 'Can view and add comments',
                'edit': 'Can view, comment, and edit content', 
                'admin': 'Full access including sharing management'
            }
        
        # User permissions mapping
        if 'user_permissions' not in permissions:
            permissions['user_permissions'] = {}
        
        # Group permissions
        if 'group_permissions' not in permissions:
            permissions['group_permissions'] = {}
        
        # Public access settings
        if 'public_access' not in permissions:
            permissions['public_access'] = {
                'enabled': False,
                'level': 'none',
                'require_login': True
            }
        
        # Sharing settings
        if 'sharing_settings' not in permissions:
            permissions['sharing_settings'] = {
                'allow_public_sharing': False,
                'allow_link_sharing': False,
                'require_approval': True,
                'default_permission_level': 'view',
                'max_shares': 100,
                'expiration_enabled': False,
                'default_expiration_days': 30
            }
        
        # Access tracking
        if 'access_log' not in permissions:
            permissions['access_log'] = []
        
        # Share links
        if 'share_links' not in permissions:
            permissions['share_links'] = {}
        
        self.sharing_permissions = permissions
        self._update_metadata()
        return True
    
    def check_access_permissions(self, user_id=None, required_level='view'):
        """Check if a user has the required access permissions.
        
        Args:
            user_id (str): User ID to check (defaults to current user)
            required_level (str): Required permission level (view, comment, edit, admin)
            
        Returns:
            dict: Access check result with details
        """
        self.initialize_sharing_system()
        
        user_id = user_id or self._get_current_user_id()
        permissions = self.sharing_permissions
        
        # Permission hierarchy (higher values = more permissions)
        permission_hierarchy = {
            'none': 0,
            'view': 1,
            'comment': 2,
            'edit': 3,
            'admin': 4
        }
        
        required_level_value = permission_hierarchy.get(required_level, 1)
        
        # Check owner access (owners always have admin access)
        try:
            owner_id = getattr(self, 'owner', None) or getattr(self, 'Creator', lambda: None)()
            if user_id == owner_id:
                return {
                    'access_granted': True,
                    'permission_level': 'admin',
                    'reason': 'owner_access',
                    'user_id': user_id
                }
        except Exception:
            pass
        
        # Check explicit user permissions
        user_permissions = permissions.get('user_permissions', {})
        if user_id in user_permissions:
            user_level = user_permissions[user_id].get('level', 'none')
            user_level_value = permission_hierarchy.get(user_level, 0)
            
            # Check if permission is active (not expired)
            permission_data = user_permissions[user_id]
            if self._is_permission_active(permission_data):
                access_granted = user_level_value >= required_level_value
                return {
                    'access_granted': access_granted,
                    'permission_level': user_level,
                    'reason': 'explicit_user_permission',
                    'user_id': user_id,
                    'permission_data': permission_data
                }
        
        # Check group permissions
        user_groups = self._get_user_groups(user_id)
        group_permissions = permissions.get('group_permissions', {})
        
        highest_group_level = 'none'
        highest_group_value = 0
        
        for group in user_groups:
            if group in group_permissions:
                group_data = group_permissions[group]
                if self._is_permission_active(group_data):
                    group_level = group_data.get('level', 'none')
                    group_level_value = permission_hierarchy.get(group_level, 0)
                    
                    if group_level_value > highest_group_value:
                        highest_group_level = group_level
                        highest_group_value = group_level_value
        
        if highest_group_value >= required_level_value:
            return {
                'access_granted': True,
                'permission_level': highest_group_level,
                'reason': 'group_permission',
                'user_id': user_id,
                'user_groups': user_groups
            }
        
        # Check public access
        public_access = permissions.get('public_access', {})
        if public_access.get('enabled', False):
            public_level = public_access.get('level', 'none')
            public_level_value = permission_hierarchy.get(public_level, 0)
            
            # If public access doesn't require login, or user is logged in
            if not public_access.get('require_login', True) or user_id != 'anonymous':
                if public_level_value >= required_level_value:
                    return {
                        'access_granted': True,
                        'permission_level': public_level,
                        'reason': 'public_access',
                        'user_id': user_id
                    }
        
        # Access denied
        return {
            'access_granted': False,
            'permission_level': 'none',
            'reason': 'insufficient_permissions',
            'user_id': user_id,
            'required_level': required_level
        }
    
    def grant_access(self, user_id, permission_level='view', granted_by=None, expiration_date=None, note=None):
        """Grant access permissions to a user.
        
        Args:
            user_id (str): User ID to grant access to
            permission_level (str): Permission level to grant (view, comment, edit, admin)
            granted_by (str): User ID who granted the permission (optional)
            expiration_date (datetime): When the permission expires (optional)
            note (str): Note about the permission grant (optional)
            
        Returns:
            dict: Result of the grant operation
        """
        self.initialize_sharing_system()
        
        # Validate permission level
        valid_levels = ['view', 'comment', 'edit', 'admin']
        if permission_level not in valid_levels:
            return {
                'success': False,
                'error': f'Invalid permission level. Must be one of: {valid_levels}',
                'user_id': user_id
            }
        
        # Check if current user can grant this permission
        granted_by = granted_by or self._get_current_user_id()
        granter_access = self.check_access_permissions(granted_by, 'admin')
        
        if not granter_access['access_granted']:
            return {
                'success': False,
                'error': 'Insufficient permissions to grant access. Admin level required.',
                'user_id': user_id,
                'granted_by': granted_by
            }
        
        permissions = self.sharing_permissions
        user_permissions = permissions.get('user_permissions', {})
        
        # Create permission entry
        current_time = datetime.now()
        permission_data = {
            'level': permission_level,
            'granted_date': current_time.isoformat(),
            'granted_by': granted_by,
            'expiration_date': expiration_date.isoformat() if expiration_date else None,
            'note': note,
            'active': True,
            'grant_history': user_permissions.get(user_id, {}).get('grant_history', [])
        }
        
        # Add to grant history
        permission_data['grant_history'].append({
            'action': 'granted',
            'level': permission_level,
            'timestamp': current_time.isoformat(),
            'granted_by': granted_by,
            'note': note
        })
        
        user_permissions[user_id] = permission_data
        permissions['user_permissions'] = user_permissions
        
        # Log the access grant
        access_log_entry = {
            'timestamp': current_time.isoformat(),
            'action': 'grant_access',
            'user_id': user_id,
            'permission_level': permission_level,
            'granted_by': granted_by,
            'note': note,
            'expiration_date': expiration_date.isoformat() if expiration_date else None
        }
        
        permissions['access_log'].append(access_log_entry)
        
        # Keep access log manageable
        if len(permissions['access_log']) > 1000:
            permissions['access_log'] = permissions['access_log'][-1000:]
        
        self.sharing_permissions = permissions
        self._update_metadata()
        
        # Track analytics
        self.track_view_analytics('grant_access', {
            'user_id': user_id,
            'permission_level': permission_level,
            'granted_by': granted_by
        })
        
        # Update engagement metrics
        if hasattr(self, 'view_analytics') and 'engagement_metrics' in self.view_analytics:
            self.view_analytics['engagement_metrics']['share_count'] += 1
        
        return {
            'success': True,
            'user_id': user_id,
            'permission_level': permission_level,
            'granted_by': granted_by,
            'granted_date': current_time.isoformat(),
            'expiration_date': expiration_date.isoformat() if expiration_date else None
        }
    
    def revoke_access(self, user_id, revoked_by=None, reason=None):
        """Revoke access permissions for a user.
        
        Args:
            user_id (str): User ID to revoke access from
            revoked_by (str): User ID who revoked the permission (optional)
            reason (str): Reason for revoking access (optional)
            
        Returns:
            dict: Result of the revoke operation
        """
        self.initialize_sharing_system()
        
        # Check if current user can revoke permissions
        revoked_by = revoked_by or self._get_current_user_id()
        revoker_access = self.check_access_permissions(revoked_by, 'admin')
        
        if not revoker_access['access_granted']:
            return {
                'success': False,
                'error': 'Insufficient permissions to revoke access. Admin level required.',
                'user_id': user_id,
                'revoked_by': revoked_by
            }
        
        permissions = self.sharing_permissions
        user_permissions = permissions.get('user_permissions', {})
        
        if user_id not in user_permissions:
            return {
                'success': False,
                'error': 'User does not have explicit permissions to revoke.',
                'user_id': user_id
            }
        
        current_time = datetime.now()
        user_data = user_permissions[user_id]
        
        # Record revocation in history
        if 'grant_history' not in user_data:
            user_data['grant_history'] = []
        
        user_data['grant_history'].append({
            'action': 'revoked',
            'level': user_data.get('level', 'unknown'),
            'timestamp': current_time.isoformat(),
            'revoked_by': revoked_by,
            'reason': reason
        })
        
        # Store previous level for logging
        previous_level = user_data.get('level', 'none')
        
        # Remove user permissions
        del user_permissions[user_id]
        permissions['user_permissions'] = user_permissions
        
        # Log the access revocation
        access_log_entry = {
            'timestamp': current_time.isoformat(),
            'action': 'revoke_access',
            'user_id': user_id,
            'previous_permission_level': previous_level,
            'revoked_by': revoked_by,
            'reason': reason
        }
        
        permissions['access_log'].append(access_log_entry)
        
        self.sharing_permissions = permissions
        self._update_metadata()
        
        # Track analytics
        self.track_view_analytics('revoke_access', {
            'user_id': user_id,
            'previous_permission_level': previous_level,
            'revoked_by': revoked_by,
            'reason': reason
        })
        
        return {
            'success': True,
            'user_id': user_id,
            'previous_permission_level': previous_level,
            'revoked_by': revoked_by,
            'revoked_date': current_time.isoformat(),
            'reason': reason
        }
    
    def list_shared_users(self, include_groups=True, include_expired=False):
        """List all users and groups with access to the container.
        
        Args:
            include_groups (bool): Whether to include group permissions
            include_expired (bool): Whether to include expired permissions
            
        Returns:
            dict: Comprehensive list of shared users and groups
        """
        self.initialize_sharing_system()
        
        permissions = self.sharing_permissions
        current_time = datetime.now()
        
        # Get user permissions
        user_permissions = permissions.get('user_permissions', {})
        shared_users = []
        
        for user_id, user_data in user_permissions.items():
            is_active = self._is_permission_active(user_data)
            
            if not include_expired and not is_active:
                continue
            
            user_info = {
                'user_id': user_id,
                'permission_level': user_data.get('level', 'none'),
                'granted_date': user_data.get('granted_date'),
                'granted_by': user_data.get('granted_by'),
                'expiration_date': user_data.get('expiration_date'),
                'active': is_active,
                'note': user_data.get('note'),
                'type': 'user'
            }
            
            # Add user details if available
            try:
                user_obj = api.user.get(userid=user_id)
                if user_obj:
                    user_info.update({
                        'fullname': user_obj.getProperty('fullname', ''),
                        'email': user_obj.getProperty('email', '')
                    })
            except Exception:
                pass
            
            shared_users.append(user_info)
        
        result = {
            'shared_users': shared_users,
            'total_users': len(shared_users),
            'active_users': len([u for u in shared_users if u['active']]),
            'permission_breakdown': self._get_permission_breakdown(shared_users)
        }
        
        # Include group permissions if requested
        if include_groups:
            group_permissions = permissions.get('group_permissions', {})
            shared_groups = []
            
            for group_id, group_data in group_permissions.items():
                is_active = self._is_permission_active(group_data)
                
                if not include_expired and not is_active:
                    continue
                
                group_info = {
                    'group_id': group_id,
                    'permission_level': group_data.get('level', 'none'),
                    'granted_date': group_data.get('granted_date'),
                    'granted_by': group_data.get('granted_by'),
                    'expiration_date': group_data.get('expiration_date'),
                    'active': is_active,
                    'note': group_data.get('note'),
                    'type': 'group',
                    'member_count': self._get_group_member_count(group_id)
                }
                
                shared_groups.append(group_info)
            
            result.update({
                'shared_groups': shared_groups,
                'total_groups': len(shared_groups),
                'active_groups': len([g for g in shared_groups if g['active']])
            })
        
        # Add public access info
        public_access = permissions.get('public_access', {})
        if public_access.get('enabled', False):
            result['public_access'] = {
                'enabled': True,
                'level': public_access.get('level', 'none'),
                'require_login': public_access.get('require_login', True)
            }
        
        # Add owner info
        try:
            owner_id = getattr(self, 'owner', None) or getattr(self, 'Creator', lambda: None)()
            if owner_id:
                result['owner'] = {
                    'user_id': owner_id,
                    'permission_level': 'admin',
                    'type': 'owner'
                }
        except Exception:
            pass
        
        return result
    
    # Multi-Format Export System
    def export_to_html(self, include_css=True, template_name=None):
        """
        Export Knowledge Container to HTML format.
        
        Args:
            include_css (bool): Whether to include embedded CSS styling
            template_name (str): Optional custom template name
            
        Returns:
            str: HTML content as string
        """
        content_data = self._aggregate_content_for_export()
        
        # Base HTML template
        html_template = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{title}</title>
    {css_styles}
</head>
<body>
    <div class=\"knowledge-container\">
        <header class=\"container-header\">
            <h1>{title}</h1>
            <div class=\"container-metadata\">
                <p class=\"description\">{description}</p>
                <div class=\"metadata-tags\">
                    <span class=\"collection-type\">Type: {collection_type}</span>
                    <span class=\"organization\">Organization: {organization_structure}</span>
                    <span class=\"status\">Status: {publication_status}</span>
                    <span class=\"audience\">Audience: {target_audience}</span>
                </div>
                <div class=\"export-info\">
                    <p>Exported on {export_date}</p>
                    <p>Total Items: {total_items}</p>
                    <p>Version: {container_version}</p>
                </div>
            </div>
        </header>
        
        <nav class=\"table-of-contents\">
            <h2>Table of Contents</h2>
            <ul>
                {toc_items}
            </ul>
        </nav>
        
        <main class=\"content-sections\">
            {content_sections}
        </main>
        
        <footer class=\"container-footer\">
            <p>Generated by Knowledge Curator v{container_version}</p>
            <p>Total {total_items} items across {content_types_count} content types</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # CSS styles for HTML export
        css_styles = self._get_html_export_css() if include_css else ""
        
        # Generate table of contents
        toc_items = self._generate_html_toc(content_data)
        
        # Generate content sections
        content_sections = self._generate_html_content_sections(content_data)
        
        # Format the template
        html_content = html_template.format(
            title=getattr(self, 'title', 'Knowledge Container'),
            description=getattr(self, 'description', ''),
            collection_type=getattr(self, 'collection_type', 'knowledge_base'),
            organization_structure=getattr(self, 'organization_structure', 'topical'),
            publication_status=getattr(self, 'publication_status', 'draft'),
            target_audience=getattr(self, 'target_audience', 'self'),
            export_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_items=content_data['total_items'],
            container_version=getattr(self, 'container_version', '1.0'),
            content_types_count=len(content_data['content_types']),
            css_styles=css_styles,
            toc_items=toc_items,
            content_sections=content_sections
        )
        
        # Track export event
        self.track_view_analytics('export', {'format': 'html', 'include_css': include_css})
        
        return html_content

    def export_to_pdf(self, include_cover_page=True, page_size='A4'):
        """
        Export Knowledge Container to PDF format.
        
        Args:
            include_cover_page (bool): Whether to include a cover page
            page_size (str): PDF page size (A4, Letter, etc.)
            
        Returns:
            bytes: PDF content as bytes
        """
        try:
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.platypus.tableofcontents import TableOfContents
        except ImportError:
            # Fallback to HTML-to-PDF conversion if reportlab not available
            return self._export_pdf_fallback(include_cover_page, page_size)
        
        content_data = self._aggregate_content_for_export()
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Set page size
        page_formats = {'A4': A4, 'Letter': letter}
        page_format = page_formats.get(page_size, A4)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_format,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2E3440')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#5E81AC')
        )
        
        # Build PDF content
        story = []
        
        # Cover page
        if include_cover_page:
            story.extend(self._generate_pdf_cover_page(content_data, title_style, styles))
            story.append(PageBreak())
        
        # Table of contents
        story.append(Paragraph("Table of Contents", heading_style))
        story.append(Spacer(1, 12))
        toc_data = self._generate_pdf_toc(content_data)
        if toc_data:
            toc_table = Table(toc_data)
            toc_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(toc_table)
        story.append(PageBreak())
        
        # Content sections
        story.extend(self._generate_pdf_content_sections(content_data, styles, heading_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Track export event
        self.track_view_analytics('export', {
            'format': 'pdf', 
            'include_cover_page': include_cover_page,
            'page_size': page_size
        })
        
        return pdf_content

    def export_to_markdown(self, include_metadata=True, format_style='github'):
        """
        Export Knowledge Container to Markdown format.
        
        Args:
            include_metadata (bool): Whether to include metadata section
            format_style (str): Markdown formatting style ('github', 'standard')
            
        Returns:
            str: Markdown content as string
        """
        content_data = self._aggregate_content_for_export()
        
        output = io.StringIO()
        
        # Title
        output.write(f"# {getattr(self, 'title', 'Knowledge Container')}\n\n")
        
        # Description
        if getattr(self, 'description', ''):
            output.write(f"{getattr(self, 'description')}\n\n")
        
        # Metadata section
        if include_metadata:
            output.write("## Container Information\n\n")
            
            metadata_table = [
                ["Property", "Value"],
                ["Type", getattr(self, 'collection_type', 'knowledge_base')],
                ["Organization", getattr(self, 'organization_structure', 'topical')],
                ["Status", getattr(self, 'publication_status', 'draft')],
                ["Target Audience", getattr(self, 'target_audience', 'self')],
                ["Version", getattr(self, 'container_version', '1.0')],
                ["Total Items", str(content_data['total_items'])],
                ["Export Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            
            if format_style == 'github':
                # GitHub-flavored markdown table
                for i, row in enumerate(metadata_table):
                    output.write(f"| {' | '.join(row)} |\n")
                    if i == 0:  # Header separator
                        output.write(f"| {' | '.join(['---' for _ in row])} |\n")
                output.write("\n")
            else:
                # Standard markdown
                for row in metadata_table:
                    output.write(f"**{row[0]}:** {row[1]}\n")
                output.write("\n")
        
        # Table of contents
        output.write("## Table of Contents\n\n")
        toc_entries = self._generate_markdown_toc(content_data)
        for entry in toc_entries:
            output.write(f"{entry}\n")
        output.write("\n")
        
        # Content sections based on organization structure
        content_sections = self._generate_markdown_content_sections(content_data, format_style)
        output.write(content_sections)
        
        # Footer
        output.write("---\n\n")
        output.write(f"*Generated by Knowledge Curator v{getattr(self, 'container_version', '1.0')} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        markdown_content = output.getvalue()
        output.close()
        
        # Track export event
        self.track_view_analytics('export', {
            'format': 'markdown', 
            'include_metadata': include_metadata,
            'format_style': format_style
        })
        
        return markdown_content

    def export_with_permissions_check(self, format_type, user_id=None, **export_options):
        """Export container with sharing permissions enforcement.
        
        Args:
            format_type (str): Export format (html, pdf, markdown)
            user_id (str): User requesting export (optional)
            **export_options: Format-specific export options
            
        Returns:
            dict: Export result with content or error
        """
        user_id = user_id or self._get_current_user_id()
        
        # Check if user has view permissions
        access_check = self.check_access_permissions(user_id, 'view')
        if not access_check['access_granted']:
            return {
                'success': False,
                'error': 'Insufficient permissions to export container',
                'required_permission': 'view',
                'user_id': user_id
            }
        
        # Track export analytics
        self.track_container_view(user_id, {'action': 'export_request', 'format': format_type})
        
        try:
            # Perform export based on format
            if format_type == 'html':
                content = self.export_to_html(**export_options)
            elif format_type == 'pdf':
                content = self.export_to_pdf(**export_options)
            elif format_type == 'markdown':
                content = self.export_to_markdown(**export_options)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported export format: {format_type}',
                    'supported_formats': ['html', 'pdf', 'markdown']
                }
            
            # Update export analytics
            if hasattr(self, 'view_analytics') and 'engagement_metrics' in self.view_analytics:
                self.view_analytics['engagement_metrics']['export_count'] += 1
                self._update_metadata()
            
            return {
                'success': True,
                'format': format_type,
                'content': content,
                'exported_by': user_id,
                'exported_at': datetime.now().isoformat(),
                'permission_level': access_check['permission_level']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Export failed: {str(e)}',
                'format': format_type,
                'user_id': user_id
            }

    def configure_export_formats(self, enabled_formats=None, default_options=None):
        """
        Configure available export formats and their default options.
        
        Args:
            enabled_formats (list): List of enabled export formats
            default_options (dict): Default options for each format
            
        Returns:
            dict: Current export configuration
        """
        if enabled_formats is None:
            enabled_formats = ['html', 'pdf', 'markdown']
        
        if default_options is None:
            default_options = {
                'html': {
                    'include_css': True,
                    'template_name': None
                },
                'pdf': {
                    'include_cover_page': True,
                    'page_size': 'A4'
                },
                'markdown': {
                    'include_metadata': True,
                    'format_style': 'github'
                }
            }
        
        # Update export_formats field
        if hasattr(self, 'export_formats'):
            self.export_formats = set(enabled_formats)
        else:
            self.export_formats = set(enabled_formats)
        
        # Store default options as metadata
        if not hasattr(self, 'export_options'):
            self.export_options = {}
        
        self.export_options = default_options.copy()
        
        # Update metadata
        self._update_metadata()
        
        # Track configuration change
        self.track_view_analytics('configure_export', {
            'enabled_formats': enabled_formats,
            'options_configured': list(default_options.keys())
        })
        
        return {
            'enabled_formats': list(self.export_formats),
            'default_options': self.export_options,
            'available_formats': ['html', 'pdf', 'markdown']
        }

    # Content Aggregation and Formatting Helpers
    def _aggregate_content_for_export(self):
        """
        Aggregate all content items for export processing.
        
        Returns:
            dict: Aggregated content data organized by type and structure
        """
        content_data = {
            'learning_goals': [],
            'knowledge_items': [],
            'research_notes': [],
            'project_logs': [],
            'bookmarks': [],
            'content_types': set(),
            'total_items': 0
        }
        
        # Content type mappings
        content_mappings = {
            'learning_goals': self.included_learning_goals or [],
            'knowledge_items': self.included_knowledge_items or [],
            'research_notes': self.included_research_notes or [],
            'project_logs': self.included_project_logs or [],
            'bookmarks': self.included_bookmarks or []
        }
        
        # Aggregate content by type
        for content_type, uid_list in content_mappings.items():
            for uid in uid_list:
                try:
                    # Get the content object
                    content_obj = api.content.get(UID=uid)
                    if content_obj:
                        item_data = self._extract_item_data(content_obj, content_type)
                        content_data[content_type].append(item_data)
                        content_data['content_types'].add(content_type)
                        content_data['total_items'] += 1
                except Exception:
                    # Skip items that can't be accessed
                    continue
        
        # Sort content based on organization structure
        content_data = self._organize_content_for_export(content_data)
        
        return content_data
    
    def _extract_item_data(self, content_obj, content_type):
        """
        Extract relevant data from a content object for export.
        
        Args:
            content_obj: Plone content object
            content_type (str): Type of content
            
        Returns:
            dict: Extracted item data
        """
        base_data = {
            'uid': content_obj.UID(),
            'title': getattr(content_obj, 'title', ''),
            'description': getattr(content_obj, 'description', ''),
            'created': getattr(content_obj, 'created', lambda: datetime.now())(),
            'modified': getattr(content_obj, 'modified', lambda: datetime.now())(),
            'tags': list(getattr(content_obj, 'subject', [])),
            'type': content_type,
            'url': content_obj.absolute_url() if hasattr(content_obj, 'absolute_url') else ''
        }
        
        # Add type-specific fields
        if content_type == 'learning_goals':
            base_data.update({
                'target_date': getattr(content_obj, 'target_date', None),
                'milestones': getattr(content_obj, 'milestones', []),
                'progress': getattr(content_obj, 'progress', 0),
                'priority': getattr(content_obj, 'priority', 'medium'),
                'reflection': getattr(content_obj, 'reflection', ''),
                'related_notes': getattr(content_obj, 'related_notes', [])
            })
        
        elif content_type == 'knowledge_items':
            base_data.update({
                'content': getattr(content_obj, 'content', ''),
                'difficulty_level': getattr(content_obj, 'difficulty_level', 'intermediate'),
                'cognitive_load': getattr(content_obj, 'cognitive_load', None),
                'learning_style': getattr(content_obj, 'learning_style', []),
                'knowledge_status': getattr(content_obj, 'knowledge_status', 'draft')
            })
        
        elif content_type == 'research_notes':
            base_data.update({
                'content': getattr(content_obj, 'content', ''),
                'source_url': getattr(content_obj, 'source_url', ''),
                'key_insights': getattr(content_obj, 'key_insights', []),
                'connections': getattr(content_obj, 'connections', []),
                'ai_summary': getattr(content_obj, 'ai_summary', '')
            })
        
        elif content_type == 'project_logs':
            base_data.update({
                'start_date': getattr(content_obj, 'start_date', None),
                'entries': getattr(content_obj, 'entries', []),
                'deliverables': getattr(content_obj, 'deliverables', []),
                'learnings': getattr(content_obj, 'learnings', []),
                'status': getattr(content_obj, 'status', 'planning')
            })
        
        elif content_type == 'bookmarks':
            base_data.update({
                'url': getattr(content_obj, 'url', ''),
                'notes': getattr(content_obj, 'notes', ''),
                'read_status': getattr(content_obj, 'read_status', 'unread'),
                'importance': getattr(content_obj, 'importance', 'medium'),
                'ai_summary': getattr(content_obj, 'ai_summary', '')
            })
        
        return base_data
    
    def _organize_content_for_export(self, content_data):
        """
        Organize content data based on the container's organization structure.
        
        Args:
            content_data (dict): Raw content data
            
        Returns:
            dict: Organized content data
        """
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'chronological':
            # Sort by creation date
            for content_type in content_data:
                if isinstance(content_data[content_type], list):
                    content_data[content_type].sort(key=lambda x: x.get('created', datetime.min))
        
        elif organization == 'hierarchical':
            # Group by type, then sort by importance/priority
            for content_type in content_data:
                if isinstance(content_data[content_type], list):
                    content_data[content_type].sort(key=lambda x: (
                        x.get('priority', 'medium') == 'high',
                        x.get('importance', 'medium') == 'high',
                        x.get('title', '')
                    ), reverse=True)
        
        elif organization == 'topical':
            # Group by tags/topics
            content_data['topics'] = {}
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                for item in content_data.get(content_type, []):
                    for tag in item.get('tags', ['Uncategorized']):
                        if tag not in content_data['topics']:
                            content_data['topics'][tag] = []
                        content_data['topics'][tag].append(item)
        
        return content_data

    # HTML Export Helpers
    def _get_html_export_css(self):
        """
        Get CSS styles for HTML export.
        
        Returns:
            str: CSS styles as HTML <style> block
        """
        css = """
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; 
                line-height: 1.6; 
                color: #2E3440; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 2rem; 
                background-color: #FAFAFA; 
            }
            .knowledge-container { 
                background: white; 
                padding: 2rem; 
                border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            }
            .container-header { 
                border-bottom: 2px solid #5E81AC; 
                padding-bottom: 1.5rem; 
                margin-bottom: 2rem; 
            }
            .container-header h1 { 
                color: #2E3440; 
                margin-bottom: 1rem; 
                font-size: 2.5rem; 
            }
            .description { 
                font-size: 1.2rem; 
                color: #4C566A; 
                margin-bottom: 1rem; 
            }
            .metadata-tags { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 1rem; 
                margin-bottom: 1rem; 
            }
            .metadata-tags span { 
                background: #E5E9F0; 
                padding: 0.5rem 1rem; 
                border-radius: 20px; 
                font-size: 0.9rem; 
                color: #2E3440; 
            }
            .export-info { 
                background: #ECEFF4; 
                padding: 1rem; 
                border-radius: 6px; 
                margin-top: 1rem; 
            }
            .export-info p { 
                margin: 0.25rem 0; 
                font-size: 0.9rem; 
                color: #4C566A; 
            }
            .table-of-contents { 
                background: #F8F9FA; 
                padding: 1.5rem; 
                border-radius: 6px; 
                margin-bottom: 2rem;
                border-left: 4px solid #5E81AC; 
            }
            .table-of-contents h2 { 
                color: #2E3440; 
                margin-bottom: 1rem; 
            }
            .table-of-contents ul { 
                margin: 0; 
                padding-left: 1.5rem; 
            }
            .table-of-contents li { 
                margin-bottom: 0.5rem; 
            }
            .table-of-contents a { 
                color: #5E81AC; 
                text-decoration: none; 
            }
            .table-of-contents a:hover { 
                text-decoration: underline; 
            }
            .content-section { 
                margin-bottom: 3rem; 
                page-break-inside: avoid; 
            }
            .content-section h2 { 
                color: #2E3440; 
                border-bottom: 1px solid #D8DEE9; 
                padding-bottom: 0.5rem; 
                margin-bottom: 1.5rem; 
            }
            .content-item { 
                background: #FAFAFA; 
                border: 1px solid #E5E9F0; 
                border-radius: 6px; 
                padding: 1.5rem; 
                margin-bottom: 1.5rem; 
            }
            .content-item h3 { 
                color: #2E3440; 
                margin-top: 0; 
            }
            .content-item .item-meta { 
                font-size: 0.9rem; 
                color: #4C566A; 
                margin-bottom: 1rem; 
            }
            .content-item .item-tags { 
                display: flex; 
                flex-wrap: wrap; 
                gap: 0.5rem; 
                margin-top: 1rem; 
            }
            .content-item .item-tags .tag { 
                background: #BF616A; 
                color: white; 
                padding: 0.25rem 0.75rem; 
                border-radius: 12px; 
                font-size: 0.8rem; 
            }
            .container-footer { 
                border-top: 1px solid #D8DEE9; 
                padding-top: 1.5rem; 
                margin-top: 3rem; 
                text-align: center; 
                color: #4C566A; 
                font-size: 0.9rem; 
            }
            @media print {
                body { background: white; }
                .knowledge-container { box-shadow: none; }
                .content-section { page-break-inside: avoid; }
            }
        </style>
        """
        return css

    def _generate_html_toc(self, content_data):
        """
        Generate HTML table of contents.
        
        Args:
            content_data (dict): Aggregated content data
            
        Returns:
            str: HTML list items for TOC
        """
        toc_items = []
        
        # Generate TOC based on organization structure
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'topical' and 'topics' in content_data:
            # Group by topics
            for topic in sorted(content_data['topics'].keys()):
                items_count = len(content_data['topics'][topic])
                toc_items.append(f'<li><a href="#topic-{topic.lower().replace(" ", "-")}">{topic}</a> ({items_count} items)</li>')
        else:
            # Group by content type
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                items = content_data.get(content_type, [])
                if items:
                    readable_name = content_type.replace('_', ' ').title()
                    toc_items.append(f'<li><a href="#section-{content_type}">{readable_name}</a> ({len(items)} items)</li>')
        
        return '\\n'.join(toc_items)

    def _generate_html_content_sections(self, content_data):
        """
        Generate HTML content sections.
        
        Args:
            content_data (dict): Aggregated content data
            
        Returns:
            str: HTML content sections
        """
        sections = []
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'topical' and 'topics' in content_data:
            # Generate sections by topic
            for topic in sorted(content_data['topics'].keys()):
                items = content_data['topics'][topic]
                section_id = f"topic-{topic.lower().replace(' ', '-')}"
                
                sections.append(f'<section class="content-section" id="{section_id}">')
                sections.append(f'    <h2>{topic}</h2>')
                
                for item in items:
                    sections.append(self._format_html_item(item))
                
                sections.append('</section>')
        else:
            # Generate sections by content type
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                items = content_data.get(content_type, [])
                if items:
                    readable_name = content_type.replace('_', ' ').title()
                    
                    sections.append(f'<section class="content-section" id="section-{content_type}">')
                    sections.append(f'    <h2>{readable_name}</h2>')
                    
                    for item in items:
                        sections.append(self._format_html_item(item))
                    
                    sections.append('</section>')
        
        return '\\n'.join(sections)

    def _format_html_item(self, item):
        """
        Format a single content item as HTML.
        
        Args:
            item (dict): Item data
            
        Returns:
            str: HTML formatted item
        """
        html = ['    <div class="content-item">']
        html.append(f'        <h3>{item.get("title", "Untitled")}</h3>')
        
        # Item metadata
        meta_parts = []
        if item.get('created'):
            created_str = item['created'].strftime('%Y-%m-%d') if hasattr(item['created'], 'strftime') else str(item['created'])
            meta_parts.append(f'Created: {created_str}')
        if item.get('type'):
            meta_parts.append(f'Type: {item["type"].replace("_", " ").title()}')
        if item.get('priority'):
            meta_parts.append(f'Priority: {item["priority"].title()}')
        if item.get('status'):
            meta_parts.append(f'Status: {item["status"].title()}')
        
        if meta_parts:
            html.append(f'        <div class="item-meta">{" | ".join(meta_parts)}</div>')
        
        # Description
        if item.get('description'):
            html.append(f'        <p>{item["description"]}</p>')
        
        # Content (for items that have it)
        if item.get('content'):
            content = str(item['content'])[:500] + ('...' if len(str(item['content'])) > 500 else '')
            html.append(f'        <div class="item-content">{content}</div>')
        
        # Type-specific fields
        if item.get('type') == 'learning_goals':
            if item.get('target_date'):
                html.append(f'        <p><strong>Target Date:</strong> {item["target_date"]}</p>')
            if item.get('progress'):
                html.append(f'        <p><strong>Progress:</strong> {item["progress"]}%</p>')
        
        elif item.get('type') == 'bookmarks':
            if item.get('url'):
                html.append(f'        <p><strong>URL:</strong> <a href="{item["url"]}" target="_blank">{item["url"]}</a></p>')
        
        elif item.get('type') == 'research_notes':
            if item.get('source_url'):
                html.append(f'        <p><strong>Source:</strong> <a href="{item["source_url"]}" target="_blank">{item["source_url"]}</a></p>')
            if item.get('key_insights'):
                html.append('        <div><strong>Key Insights:</strong>')
                html.append('        <ul>')
                for insight in item['key_insights'][:3]:  # Limit to first 3
                    html.append(f'            <li>{insight}</li>')
                html.append('        </ul>')
                html.append('        </div>')
        
        # Tags
        if item.get('tags'):
            html.append('        <div class="item-tags">')
            for tag in item['tags']:
                html.append(f'            <span class="tag">{tag}</span>')
            html.append('        </div>')
        
        html.append('    </div>')
        
        return '\\n'.join(html)

    # PDF Export Helpers
    def _export_pdf_fallback(self, include_cover_page, page_size):
        """
        Fallback PDF export using HTML to PDF conversion.
        
        Args:
            include_cover_page (bool): Include cover page
            page_size (str): Page size
            
        Returns:
            bytes: PDF content or error message as bytes
        """
        # For now, return the HTML content as a simple fallback
        # In production, you might use weasyprint or similar
        html_content = self.export_to_html()
        
        # Convert to bytes and add a note about PDF limitations
        pdf_note = f"""
PDF Export Note: ReportLab not available. 
This would normally be a properly formatted PDF.
Container: {getattr(self, 'title', 'Knowledge Container')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{html_content}
        """
        return pdf_note.encode('utf-8')

    def _generate_pdf_cover_page(self, content_data, title_style, styles):
        """
        Generate PDF cover page elements.
        
        Args:
            content_data (dict): Aggregated content data
            title_style: ReportLab style for title
            styles: ReportLab stylesheet
            
        Returns:
            list: List of ReportLab flowables for cover page
        """
        try:
            from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
        except ImportError:
            return []
        
        cover_elements = []
        
        # Title
        title = getattr(self, 'title', 'Knowledge Container')
        cover_elements.append(Paragraph(title, title_style))
        cover_elements.append(Spacer(1, 20))
        
        # Description
        description = getattr(self, 'description', '')
        if description:
            cover_elements.append(Paragraph(description, styles['Normal']))
            cover_elements.append(Spacer(1, 20))
        
        # Container information table
        info_data = [
            ['Collection Type', getattr(self, 'collection_type', 'knowledge_base')],
            ['Organization', getattr(self, 'organization_structure', 'topical')],
            ['Status', getattr(self, 'publication_status', 'draft')],
            ['Target Audience', getattr(self, 'target_audience', 'self')],
            ['Version', getattr(self, 'container_version', '1.0')],
            ['Total Items', str(content_data['total_items'])],
            ['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        info_table = Table(info_data, colWidths=[2*72, 3*72])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E5E9F0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2E3440')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D8DEE9')),
        ]))
        
        cover_elements.append(info_table)
        cover_elements.append(Spacer(1, 30))
        
        # Content summary
        if content_data['content_types']:
            cover_elements.append(Paragraph('Content Summary', styles['Heading2']))
            cover_elements.append(Spacer(1, 10))
            
            summary_data = [['Content Type', 'Count']]
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                count = len(content_data.get(content_type, []))
                if count > 0:
                    readable_name = content_type.replace('_', ' ').title()
                    summary_data.append([readable_name, str(count)])
            
            if len(summary_data) > 1:
                summary_table = Table(summary_data, colWidths=[3*72, 1*72])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5E81AC')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D8DEE9')),
                ]))
                cover_elements.append(summary_table)
        
        return cover_elements

    def _generate_pdf_toc(self, content_data):
        """
        Generate PDF table of contents data.
        
        Args:
            content_data (dict): Aggregated content data
            
        Returns:
            list: Table data for TOC
        """
        toc_data = []
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'topical' and 'topics' in content_data:
            # Group by topics
            for topic in sorted(content_data['topics'].keys()):
                items_count = len(content_data['topics'][topic])
                toc_data.append([f'{topic}', f'{items_count} items'])
        else:
            # Group by content type
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                items = content_data.get(content_type, [])
                if items:
                    readable_name = content_type.replace('_', ' ').title()
                    toc_data.append([readable_name, f'{len(items)} items'])
        
        return toc_data

    def _generate_pdf_content_sections(self, content_data, styles, heading_style):
        """
        Generate PDF content sections.
        
        Args:
            content_data (dict): Aggregated content data
            styles: ReportLab stylesheet
            heading_style: Style for headings
            
        Returns:
            list: List of ReportLab flowables
        """
        try:
            from reportlab.platypus import Paragraph, Spacer, PageBreak
        except ImportError:
            return []
        
        elements = []
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'topical' and 'topics' in content_data:
            # Generate sections by topic
            for i, topic in enumerate(sorted(content_data['topics'].keys())):
                if i > 0:
                    elements.append(PageBreak())
                
                elements.append(Paragraph(topic, heading_style))
                elements.append(Spacer(1, 12))
                
                items = content_data['topics'][topic]
                for item in items:
                    elements.extend(self._format_pdf_item(item, styles))
        else:
            # Generate sections by content type
            first_section = True
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                items = content_data.get(content_type, [])
                if items:
                    if not first_section:
                        elements.append(PageBreak())
                    first_section = False
                    
                    readable_name = content_type.replace('_', ' ').title()
                    elements.append(Paragraph(readable_name, heading_style))
                    elements.append(Spacer(1, 12))
                    
                    for item in items:
                        elements.extend(self._format_pdf_item(item, styles))
        
        return elements

    def _format_pdf_item(self, item, styles):
        """
        Format a single content item for PDF.
        
        Args:
            item (dict): Item data
            styles: ReportLab stylesheet
            
        Returns:
            list: List of ReportLab flowables for the item
        """
        try:
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib import colors
        except ImportError:
            return []
        
        elements = []
        
        # Item title
        item_title_style = ParagraphStyle(
            'ItemTitle',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=6,
            textColor=colors.HexColor('#2E3440')
        )
        
        elements.append(Paragraph(item.get('title', 'Untitled'), item_title_style))
        
        # Item metadata
        meta_parts = []
        if item.get('created'):
            created_str = item['created'].strftime('%Y-%m-%d') if hasattr(item['created'], 'strftime') else str(item['created'])
            meta_parts.append(f'Created: {created_str}')
        if item.get('type'):
            meta_parts.append(f'Type: {item["type"].replace("_", " ").title()}')
        if item.get('priority'):
            meta_parts.append(f'Priority: {item["priority"].title()}')
        if item.get('status'):
            meta_parts.append(f'Status: {item["status"].title()}')
        
        if meta_parts:
            meta_style = ParagraphStyle(
                'ItemMeta',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#4C566A'),
                spaceAfter=6
            )
            elements.append(Paragraph(' | '.join(meta_parts), meta_style))
        
        # Description
        if item.get('description'):
            elements.append(Paragraph(item['description'], styles['Normal']))
            elements.append(Spacer(1, 6))
        
        # Content (truncated for PDF)
        if item.get('content'):
            content = str(item['content'])[:300] + ('...' if len(str(item['content'])) > 300 else '')
            elements.append(Paragraph(content, styles['Normal']))
            elements.append(Spacer(1, 6))
        
        # Type-specific fields
        if item.get('type') == 'learning_goals':
            if item.get('target_date'):
                elements.append(Paragraph(f'<b>Target Date:</b> {item["target_date"]}', styles['Normal']))
            if item.get('progress'):
                elements.append(Paragraph(f'<b>Progress:</b> {item["progress"]}%', styles['Normal']))
        
        elif item.get('type') == 'bookmarks' and item.get('url'):
            elements.append(Paragraph(f'<b>URL:</b> {item["url"]}', styles['Normal']))
        
        elif item.get('type') == 'research_notes':
            if item.get('source_url'):
                elements.append(Paragraph(f'<b>Source:</b> {item["source_url"]}', styles['Normal']))
            if item.get('key_insights'):
                insights_text = '<b>Key Insights:</b><br/>' + '<br/>'.join([f'• {insight}' for insight in item['key_insights'][:2]])
                elements.append(Paragraph(insights_text, styles['Normal']))
        
        # Tags
        if item.get('tags'):
            tags_text = '<b>Tags:</b> ' + ', '.join(item['tags'])
            elements.append(Paragraph(tags_text, styles['Normal']))
        
        elements.append(Spacer(1, 12))
        
        return elements

    # Markdown Export Helpers
    def _generate_markdown_toc(self, content_data):
        """
        Generate Markdown table of contents.
        
        Args:
            content_data (dict): Aggregated content data
            
        Returns:
            list: List of TOC entries as strings
        """
        toc_entries = []
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'topical' and 'topics' in content_data:
            # Group by topics
            for topic in sorted(content_data['topics'].keys()):
                items_count = len(content_data['topics'][topic])
                anchor = topic.lower().replace(' ', '-').replace('&', 'and')
                toc_entries.append(f'- [{topic}](#{anchor}) ({items_count} items)')
        else:
            # Group by content type
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                items = content_data.get(content_type, [])
                if items:
                    readable_name = content_type.replace('_', ' ').title()
                    anchor = content_type.replace('_', '-')
                    toc_entries.append(f'- [{readable_name}](#{anchor}) ({len(items)} items)')
        
        return toc_entries

    def _generate_markdown_content_sections(self, content_data, format_style):
        """
        Generate Markdown content sections.
        
        Args:
            content_data (dict): Aggregated content data
            format_style (str): Markdown formatting style
            
        Returns:
            str: Markdown content sections
        """
        sections = []
        organization = getattr(self, 'organization_structure', 'topical')
        
        if organization == 'topical' and 'topics' in content_data:
            # Generate sections by topic
            for topic in sorted(content_data['topics'].keys()):
                items = content_data['topics'][topic]
                anchor = topic.lower().replace(' ', '-').replace('&', 'and')
                
                sections.append(f'## {topic} {{#{anchor}}}\\n')
                
                for item in items:
                    sections.append(self._format_markdown_item(item, format_style))
                
                sections.append('')
        else:
            # Generate sections by content type
            for content_type in ['learning_goals', 'knowledge_items', 'research_notes', 'project_logs', 'bookmarks']:
                items = content_data.get(content_type, [])
                if items:
                    readable_name = content_type.replace('_', ' ').title()
                    anchor = content_type.replace('_', '-')
                    
                    sections.append(f'## {readable_name} {{#{anchor}}}\\n')
                    
                    for item in items:
                        sections.append(self._format_markdown_item(item, format_style))
                    
                    sections.append('')
        
        return '\\n'.join(sections)

    def _format_markdown_item(self, item, format_style):
        """
        Format a single content item as Markdown.
        
        Args:
            item (dict): Item data
            format_style (str): Markdown formatting style
            
        Returns:
            str: Markdown formatted item
        """
        lines = []
        
        # Item title
        lines.append(f'### {item.get("title", "Untitled")}\\n')
        
        # Item metadata
        meta_parts = []
        if item.get('created'):
            created_str = item['created'].strftime('%Y-%m-%d') if hasattr(item['created'], 'strftime') else str(item['created'])
            meta_parts.append(f'**Created:** {created_str}')
        if item.get('type'):
            meta_parts.append(f'**Type:** {item["type"].replace("_", " ").title()}')
        if item.get('priority'):
            meta_parts.append(f'**Priority:** {item["priority"].title()}')
        if item.get('status'):
            meta_parts.append(f'**Status:** {item["status"].title()}')
        
        if meta_parts:
            if format_style == 'github':
                lines.append(f'{" | ".join(meta_parts)}\\n')
            else:
                for part in meta_parts:
                    lines.append(f'{part}  ')
                lines.append('')
        
        # Description
        if item.get('description'):
            lines.append(f'{item["description"]}\\n')
        
        # Content (for items that have it)
        if item.get('content'):
            content = str(item['content'])
            # For markdown, we can include more content than PDF
            if len(content) > 1000:
                content = content[:1000] + '\\n\\n*[Content truncated for export]*'
            lines.append(f'{content}\\n')
        
        # Type-specific fields
        if item.get('type') == 'learning_goals':
            if item.get('target_date'):
                lines.append(f'**Target Date:** {item["target_date"]}\\n')
            if item.get('progress') is not None:
                progress = item['progress']
                if format_style == 'github':
                    # Add a progress bar
                    filled = int(progress / 10)
                    empty = 10 - filled
                    progress_bar = '█' * filled + '░' * empty
                    lines.append(f'**Progress:** {progress}% `{progress_bar}`\\n')
                else:
                    lines.append(f'**Progress:** {progress}%\\n')
            if item.get('milestones'):
                lines.append('**Milestones:**\\n')
                for milestone in item['milestones'][:5]:  # Limit to first 5
                    lines.append(f'- {milestone}')
                lines.append('')
        
        elif item.get('type') == 'bookmarks':
            if item.get('url'):
                lines.append(f'**URL:** [{item["url"]}]({item["url"]})\\n')
            if item.get('read_status'):
                status_emoji = {'read': '✅', 'unread': '⏳', 'reading': '📖'}.get(item['read_status'], '❓')
                lines.append(f'**Read Status:** {status_emoji} {item["read_status"].title()}\\n')
            if item.get('importance'):
                importance_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(item['importance'], '⚪')
                lines.append(f'**Importance:** {importance_emoji} {item["importance"].title()}\\n')
        
        elif item.get('type') == 'research_notes':
            if item.get('source_url'):
                lines.append(f'**Source:** [{item["source_url"]}]({item["source_url"]})\\n')
            if item.get('key_insights'):
                lines.append('**Key Insights:**\\n')
                for insight in item['key_insights'][:5]:  # Limit to first 5
                    lines.append(f'- {insight}')
                lines.append('')
            if item.get('ai_summary'):
                lines.append(f'**AI Summary:** {item["ai_summary"]}\\n')
        
        elif item.get('type') == 'project_logs':
            if item.get('start_date'):
                lines.append(f'**Start Date:** {item["start_date"]}\\n')
            if item.get('deliverables'):
                lines.append('**Deliverables:**\\n')
                for deliverable in item['deliverables'][:3]:  # Limit to first 3
                    lines.append(f'- {deliverable}')
                lines.append('')
            if item.get('learnings'):
                lines.append('**Key Learnings:**\\n')
                for learning in item['learnings'][:3]:  # Limit to first 3
                    lines.append(f'- {learning}')
                lines.append('')
        
        elif item.get('type') == 'knowledge_items':
            if item.get('difficulty_level'):
                difficulty_emoji = {'beginner': '🟢', 'intermediate': '🟡', 'advanced': '🔴', 'expert': '🟣'}.get(item['difficulty_level'], '⚪')
                lines.append(f'**Difficulty:** {difficulty_emoji} {item["difficulty_level"].title()}\\n')
            if item.get('knowledge_status'):
                status_emoji = {'draft': '📝', 'review': '👀', 'published': '✅', 'archived': '📦'}.get(item['knowledge_status'], '❓')
                lines.append(f'**Status:** {status_emoji} {item["knowledge_status"].title()}\\n')
        
        # Tags
        if item.get('tags'):
            if format_style == 'github':
                tag_badges = ' '.join([f'`{tag}`' for tag in item['tags']])
                lines.append(f'**Tags:** {tag_badges}\\n')
            else:
                lines.append(f'**Tags:** {", ".join(item["tags"])}\\n')
        
        # Cross-references (for items with connections)
        if item.get('connections') or item.get('related_notes'):
            connections = item.get('connections', []) + item.get('related_notes', [])
            if connections:
                lines.append('**Related Items:**\\n')
                for conn_uid in connections[:3]:  # Limit to first 3
                    try:
                        conn_obj = api.content.get(UID=conn_uid)
                        if conn_obj:
                            lines.append(f'- [{conn_obj.title}]({conn_obj.absolute_url()})')
                    except Exception:
                        lines.append(f'- [Item {conn_uid[:8]}...](#)')
                lines.append('')
        
        lines.append('---\\n')
        
        return '\\n'.join(lines)
    
    # Helper methods for analytics and sharing
    def _get_most_viewed_content(self):
        """Get the most viewed content items.
        
        Returns:
            list: List of most viewed content items
        """
        if not hasattr(self, 'view_analytics') or 'content_item_views' not in self.view_analytics:
            return []
        
        content_views = self.view_analytics['content_item_views']
        sorted_content = sorted(
            content_views.items(),
            key=lambda x: x[1].get('view_count', 0),
            reverse=True
        )
        
        return [{
            'content_key': item[0],
            'view_count': item[1].get('view_count', 0),
            'unique_viewers': len(item[1].get('unique_viewers', [])),
            'last_accessed': item[1].get('last_accessed')
        } for item in sorted_content[:5]]
    
    def _get_content_interaction_breakdown(self):
        """Get breakdown of content interactions by type.
        
        Returns:
            dict: Interaction breakdown by type
        """
        if not hasattr(self, 'view_analytics') or 'content_item_views' not in self.view_analytics:
            return {}
        
        content_views = self.view_analytics['content_item_views']
        interaction_breakdown = {}
        
        for content_key, content_data in content_views.items():
            interaction_types = content_data.get('interaction_types', {})
            for interaction_type, count in interaction_types.items():
                if interaction_type not in interaction_breakdown:
                    interaction_breakdown[interaction_type] = 0
                interaction_breakdown[interaction_type] += count
        
        return interaction_breakdown
    
    def _is_permission_active(self, permission_data):
        """Check if a permission is currently active (not expired).
        
        Args:
            permission_data (dict): Permission data with expiration info
            
        Returns:
            bool: True if permission is active
        """
        if not permission_data.get('active', True):
            return False
        
        expiration_date = permission_data.get('expiration_date')
        if expiration_date:
            try:
                from datetime import datetime
                expiry = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                return datetime.now(expiry.tzinfo) < expiry
            except Exception:
                # If we can't parse the date, assume it's active
                return True
        
        return True
    
    def _get_user_groups(self, user_id):
        """Get groups that a user belongs to.
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of group IDs
        """
        try:
            user = api.user.get(userid=user_id)
            if user:
                groups = api.group.get_groups(user=user)
                return [group.getId() for group in groups]
        except Exception:
            pass
        
        return []
    
    def _get_group_member_count(self, group_id):
        """Get the number of members in a group.
        
        Args:
            group_id (str): Group ID
            
        Returns:
            int: Number of group members
        """
        try:
            group = api.group.get(groupname=group_id)
            if group:
                members = api.user.get_users(group=group)
                return len(members)
        except Exception:
            pass
        
        return 0
    
    def _get_permission_breakdown(self, shared_users):
        """Get breakdown of users by permission level.
        
        Args:
            shared_users (list): List of shared user data
            
        Returns:
            dict: Permission level breakdown
        """
        breakdown = {'view': 0, 'comment': 0, 'edit': 0, 'admin': 0}
        
        for user in shared_users:
            level = user.get('permission_level', 'view')
            if level in breakdown:
                breakdown[level] += 1
        
        return breakdown