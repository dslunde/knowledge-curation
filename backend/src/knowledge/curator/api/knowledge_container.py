"""Knowledge Container API endpoints for collection management and publication."""

from datetime import datetime
from plone import api
from plone.restapi.services import Service
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import ISerializeToJson
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
import json
import logging
from knowledge.curator.validation import validate_knowledge_container

logger = logging.getLogger(__name__)


class KnowledgeContainerService(Service):
    """Base service for Knowledge Container operations."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.portal = api.portal.get()


@implementer(IPublishTraverse)
class KnowledgeContainerCollectionService(KnowledgeContainerService):
    """Service for managing Knowledge Container collections."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        """Allow traversal to specific container operations."""
        self.params.append(name)
        return self

    def reply(self):
        """Handle various collection operations based on traversal."""
        if not self.params:
            if self.request.method == "GET":
                return self._list_containers()
            elif self.request.method == "POST":
                return self._create_container()
        
        # Handle specific container operations
        container_id = self.params[0]
        container = self._get_container(container_id)
        
        if len(self.params) == 1:
            if self.request.method == "GET":
                return self._get_container_details(container)
            elif self.request.method == "PUT":
                return self._update_container(container)
            elif self.request.method == "DELETE":
                return self._delete_container(container)
        
        elif len(self.params) == 2:
            operation = self.params[1]
            
            if operation == "content":
                if self.request.method == "GET":
                    return self._get_container_content(container)
                elif self.request.method == "POST":
                    return self._add_content_to_container(container)
                elif self.request.method == "DELETE":
                    return self._remove_content_from_container(container)
            
            elif operation == "export":
                return self._export_container(container)
            
            elif operation == "share":
                if self.request.method == "GET":
                    return self._get_sharing_settings(container)
                elif self.request.method == "POST":
                    return self._update_sharing_settings(container)
            
            elif operation == "analytics":
                return self._get_container_analytics(container)
            
            elif operation == "validate":
                return self._validate_container(container)
            
            elif operation == "organize":
                return self._organize_container(container)
        
        self.request.response.setStatus(404)
        return {"error": "Not found"}

    def _validate_container(self, container):
        """Validate container using comprehensive validation systems."""
        try:
            validation_result = validate_knowledge_container(container)
            
            # Return the comprehensive validation result
            return {
                'validation_complete': True,
                'timestamp': validation_result['timestamp'],
                'container_uid': validation_result['container_uid'],
                'overall_valid': validation_result['overall_valid'],
                'academic_standards': validation_result['validation_results'].get('academic_standards', {}),
                'container_integrity': validation_result['validation_results'].get('container_integrity', {}),
                'knowledge_sovereignty': validation_result['validation_results'].get('knowledge_sovereignty', {}),
                'summary': self._generate_validation_summary(validation_result)
            }
            
        except Exception as e:
            logger.error(f"Error validating container: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Validation failed: {str(e)}"}

    def _generate_validation_summary(self, validation_result) -> dict:
        """Generate a human-readable summary of validation results."""
        summary = {
            'overall_status': 'valid' if validation_result['overall_valid'] else 'invalid',
            'academic_score': 0.0,
            'integrity_score': 0.0,
            'sovereignty_score': 0.0,
            'total_warnings': 0,
            'total_errors': 0,
            'recommendations': []
        }
        
        # Extract scores and issues
        academic = validation_result['validation_results'].get('academic_standards', {})
        integrity = validation_result['validation_results'].get('container_integrity', {})
        sovereignty = validation_result['validation_results'].get('knowledge_sovereignty', {})
        
        summary['academic_score'] = academic.get('academic_score', 0.0)
        summary['integrity_score'] = integrity.get('integrity_score', 0.0)
        summary['sovereignty_score'] = sovereignty.get('sovereignty_score', 0.0)
        
        # Count warnings and errors
        for result in [academic, integrity, sovereignty]:
            summary['total_warnings'] += len(result.get('warnings', []))
            summary['total_errors'] += len(result.get('errors', []))
            summary['recommendations'].extend(result.get('recommendations', []))
        
        # Add specific compliance issues
        summary['recommendations'].extend(sovereignty.get('compliance_issues', []))
        
        return summary

    def _list_containers(self):
        """List all Knowledge Containers accessible to the current user."""
        try:
            catalog = api.portal.get_tool('portal_catalog')
            
            # Get query parameters
            query = {
                'portal_type': 'KnowledgeContainer',
                'sort_on': 'created',
                'sort_order': 'descending'
            }
            
            # Apply filters from request
            publication_status = self.request.get('publication_status')
            if publication_status:
                query['publication_status'] = publication_status
            
            collection_type = self.request.get('collection_type')
            if collection_type:
                query['collection_type'] = collection_type
            
            target_audience = self.request.get('target_audience')
            if target_audience:
                query['target_audience'] = target_audience
            
            # Execute search
            brains = catalog(**query)
            
            containers = []
            for brain in brains:
                try:
                    container = brain.getObject()
                    container_data = {
                        'uid': brain.UID,
                        'id': container.getId(),
                        'title': getattr(container, 'title', ''),
                        'description': getattr(container, 'description', ''),
                        'collection_type': getattr(container, 'collection_type', 'curated'),
                        'publication_status': getattr(container, 'publication_status', 'draft'),
                        'target_audience': getattr(container, 'target_audience', 'self'),
                        'total_items_count': getattr(container, 'total_items_count', 0),
                        'created_date': getattr(container, 'created_date', None),
                        'last_modified_date': getattr(container, 'last_modified_date', None),
                        'url': brain.getURL(),
                        'tags': getattr(container, 'tags', [])
                    }
                    containers.append(container_data)
                except Exception as e:
                    logger.error(f"Error processing container {brain.UID}: {e}")
                    continue
            
            return {
                'containers': containers,
                'total': len(containers)
            }
            
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Failed to list containers: {str(e)}"}

    def _create_container(self):
        """Create a new Knowledge Container."""
        try:
            data = json_body(self.request)
            
            # Validate required fields
            required_fields = ['title', 'description']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                self.request.response.setStatus(400)
                return {"error": f"Missing required fields: {missing_fields}"}
            
            # Create the container
            container_id = api.content.create(
                container=self.context,
                type='KnowledgeContainer',
                title=data['title'],
                description=data['description'],
                safe_id=True
            )
            
            container = api.content.get(UID=container_id.UID())
            
            # Set optional fields
            optional_fields = {
                'collection_type': 'curated',
                'organization_structure': 'hierarchical',
                'publication_status': 'draft',
                'target_audience': 'self',
                'tags': [],
                'export_formats': set(),
                'sharing_permissions': {}
            }
            
            for field, default_value in optional_fields.items():
                value = data.get(field, default_value)
                setattr(container, field, value)
            
            # Set creation metadata
            container.created_date = datetime.now()
            container.container_version = "1.0"
            
            # Add initial content if provided
            if 'included_content' in data:
                self._add_content_items(container, data['included_content'])
            
            self.request.response.setStatus(201)
            return {
                'uid': container.UID(),
                'id': container.getId(),
                'title': container.title,
                'url': container.absolute_url(),
                'created_date': container.created_date.isoformat() if container.created_date else None
            }
            
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Failed to create container: {str(e)}"}

    def _get_container(self, container_id):
        """Get a Knowledge Container by ID or UID."""
        try:
            # Try by UID first
            container = api.content.get(UID=container_id)
            if container and container.portal_type == 'KnowledgeContainer':
                return container
            
            # Try by path/ID
            if hasattr(self.context, container_id):
                container = getattr(self.context, container_id)
                if container.portal_type == 'KnowledgeContainer':
                    return container
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting container {container_id}: {e}")
            return None

    def _get_container_details(self, container):
        """Get detailed information about a Knowledge Container."""
        try:
            # Get comprehensive summary
            summary = container.get_collection_summary()
            
            # Add additional details
            details = {
                'uid': container.UID(),
                'id': container.getId(),
                'url': container.absolute_url(),
                'summary': summary,
                'content_details': self._get_detailed_content_info(container),
                'export_options': list(getattr(container, 'export_formats', set())),
                'sharing_info': self._get_sharing_info(container),
                'validation_status': container.validate_content_references()
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting container details: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Failed to get container details: {str(e)}"}

    def _get_detailed_content_info(self, container):
        """Get detailed information about content items in the container."""
        content_details = {}
        
        content_types = {
            'learning_goals': 'included_learning_goals',
            'knowledge_items': 'included_knowledge_items', 
            'research_notes': 'included_research_notes',
            'project_logs': 'included_project_logs',
            'bookmarks': 'included_bookmarks'
        }
        
        for content_type, field_name in content_types.items():
            uid_list = getattr(container, field_name, [])
            items = []
            
            for uid in uid_list:
                try:
                    item = api.content.get(UID=uid)
                    if item:
                        item_info = {
                            'uid': uid,
                            'title': getattr(item, 'title', ''),
                            'description': getattr(item, 'description', ''),
                            'url': item.absolute_url(),
                            'created': getattr(item, 'created', None),
                            'modified': getattr(item, 'modified', None)
                        }
                        
                        # Add type-specific information
                        if content_type == 'knowledge_items':
                            item_info['knowledge_type'] = getattr(item, 'knowledge_type', '')
                            item_info['difficulty_level'] = getattr(item, 'difficulty_level', '')
                        elif content_type == 'learning_goals':
                            item_info['progress'] = getattr(item, 'progress', 0)
                            item_info['priority'] = getattr(item, 'priority', '')
                        
                        items.append(item_info)
                        
                except Exception as e:
                    logger.warning(f"Could not get details for {content_type} item {uid}: {e}")
                    items.append({
                        'uid': uid,
                        'title': 'Item not accessible',
                        'error': str(e)
                    })
            
            content_details[content_type] = items
        
        return content_details

    def _export_container(self, container):
        """Export container in specified format."""
        try:
            export_format = self.request.get('format', 'html')
            
            # Validate export format
            available_formats = getattr(container, 'export_formats', set())
            if available_formats and export_format not in available_formats:
                self.request.response.setStatus(400)
                return {"error": f"Export format '{export_format}' not available for this container"}
            
            # Get export options
            options = {
                'include_metadata': self.request.get('include_metadata', True),
                'include_css': self.request.get('include_css', True),
                'template_name': self.request.get('template', None),
                'format_style': self.request.get('style', 'academic'),
                'citation_format': self.request.get('citation_format', 'apa')
            }
            
            # Check permissions
            user_id = api.user.get_current().getId()
            export_result = container.export_with_permissions_check(
                export_format, 
                user_id=user_id,
                **options
            )
            
            if 'error' in export_result:
                self.request.response.setStatus(403)
                return export_result
            
            # Set appropriate content type for download
            if export_format == 'pdf':
                self.request.response.setHeader('Content-Type', 'application/pdf')
            elif export_format == 'html':
                self.request.response.setHeader('Content-Type', 'text/html')
            elif export_format == 'markdown':
                self.request.response.setHeader('Content-Type', 'text/markdown')
            elif export_format == 'latex':
                self.request.response.setHeader('Content-Type', 'text/x-latex')
            
            # Set download filename
            filename = f"{container.getId()}.{export_format}"
            self.request.response.setHeader(
                'Content-Disposition', 
                f'attachment; filename="{filename}"'
            )
            
            return export_result
            
        except Exception as e:
            logger.error(f"Error exporting container: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Export failed: {str(e)}"}

    def _add_content_to_container(self, container):
        """Add content items to a container."""
        try:
            data = json_body(self.request)
            
            if 'items' not in data:
                self.request.response.setStatus(400)
                return {"error": "Missing 'items' field"}
            
            results = []
            
            for item in data['items']:
                content_type = item.get('content_type')
                uid = item.get('uid')
                
                if not content_type or not uid:
                    results.append({
                        'uid': uid,
                        'success': False,
                        'error': 'Missing content_type or uid'
                    })
                    continue
                
                try:
                    success = container.add_content_item(content_type, uid)
                    results.append({
                        'uid': uid,
                        'content_type': content_type,
                        'success': success,
                        'message': 'Added successfully' if success else 'Already exists'
                    })
                except Exception as e:
                    results.append({
                        'uid': uid,
                        'content_type': content_type,
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'results': results,
                'total_items': container._calculate_total_items()
            }
            
        except Exception as e:
            logger.error(f"Error adding content to container: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Failed to add content: {str(e)}"}

    def _get_sharing_info(self, container):
        """Get sharing information for a container."""
        return {
            'target_audience': getattr(container, 'target_audience', 'self'),
            'publication_status': getattr(container, 'publication_status', 'draft'),
            'sharing_permissions': getattr(container, 'sharing_permissions', {}),
            'can_share': getattr(container, 'target_audience', 'self') != 'self'
        }

    def _add_content_items(self, container, content_items):
        """Helper to add multiple content items during creation."""
        for content_type, uid_list in content_items.items():
            for uid in uid_list:
                try:
                    container.add_content_item(content_type, uid)
                except Exception as e:
                    logger.warning(f"Could not add {content_type} item {uid}: {e}")


@implementer(IPublishTraverse)
class KnowledgeContainerAnalyticsService(KnowledgeContainerService):
    """Service for Knowledge Container analytics and insights."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        """Handle analytics requests."""
        if self.request.method != "GET":
            self.request.response.setStatus(405)
            return {"error": "Method not allowed"}

        if not self.params:
            return self._get_global_analytics()
        
        container_id = self.params[0]
        container = self._get_container(container_id)
        
        if not container:
            self.request.response.setStatus(404)
            return {"error": "Container not found"}
        
        if len(self.params) == 1:
            return self._get_container_analytics(container)
        
        analytics_type = self.params[1]
        
        if analytics_type == "usage":
            return self._get_usage_analytics(container)
        elif analytics_type == "content":
            return self._get_content_analytics(container)
        elif analytics_type == "learning":
            return self._get_learning_analytics(container)
        
        self.request.response.setStatus(404)
        return {"error": "Analytics type not found"}

    def _get_container_analytics(self, container):
        """Get comprehensive analytics for a container."""
        try:
            analytics = {
                'basic_metrics': {
                    'total_items': container._calculate_total_items(),
                    'content_breakdown': self._get_content_breakdown(container),
                    'creation_date': getattr(container, 'created_date', None),
                    'last_modified': getattr(container, 'last_modified_date', None)
                },
                'usage_metrics': getattr(container, 'view_analytics', {}),
                'validation_status': container.validate_content_references(),
                'organization_info': {
                    'structure': getattr(container, 'organization_structure', 'hierarchical'),
                    'collection_type': getattr(container, 'collection_type', 'curated'),
                    'publication_status': getattr(container, 'publication_status', 'draft')
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting container analytics: {e}")
            self.request.response.setStatus(500)
            return {"error": f"Analytics failed: {str(e)}"}

    def _get_content_breakdown(self, container):
        """Get breakdown of content types in container."""
        return {
            'learning_goals': len(getattr(container, 'included_learning_goals', [])),
            'knowledge_items': len(getattr(container, 'included_knowledge_items', [])),
            'research_notes': len(getattr(container, 'included_research_notes', [])),
            'project_logs': len(getattr(container, 'included_project_logs', [])),
            'bookmarks': len(getattr(container, 'included_bookmarks', []))
        }

    def _get_container(self, container_id):
        """Helper method to get container by ID or UID."""
        try:
            container = api.content.get(UID=container_id)
            if container and container.portal_type == 'KnowledgeContainer':
                return container
            return None
        except:
            return None 