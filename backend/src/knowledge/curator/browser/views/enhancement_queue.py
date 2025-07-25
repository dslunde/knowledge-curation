"""Enhancement Queue Management Views."""

from Products.Five.browser import BrowserView
from plone import api
from knowledge.curator.workflow_scripts import (
    get_enhancement_queue,
    process_enhancement_queue,
    get_queue_statistics,
    queue_for_enhancement,
    calculate_enhancement_priority
)
from zope.annotation.interfaces import IAnnotations
import json


class EnhancementQueueView(BrowserView):
    """View for managing the enhancement queue."""
    
    def __call__(self):
        """Handle queue management requests."""
        # Check permissions
        if not api.user.has_permission('Manage portal', obj=self.context):
            self.request.response.setStatus(403)
            return "Unauthorized"
        
        # Handle different actions
        action = self.request.get('action', 'view')
        
        if action == 'view':
            return self.index()
        elif action == 'process':
            return self.process_queue()
        elif action == 'clear':
            return self.clear_queue()
        elif action == 'requeue':
            return self.requeue_item()
        elif action == 'stats':
            return self.get_stats()
        else:
            return self.index()
    
    def get_queue_items(self):
        """Get all items in the enhancement queue."""
        return get_enhancement_queue()
    
    def get_knowledge_items_queue(self):
        """Get only Knowledge Items from the queue."""
        items = get_enhancement_queue()
        return [item for item in items if item.get('portal_type') == 'KnowledgeItem']
    
    def process_queue(self):
        """Process items from the queue."""
        batch_size = int(self.request.get('batch_size', 10))
        content_type = self.request.get('content_type', None)
        
        # Process with Knowledge Items priority
        processed = process_enhancement_queue(
            batch_size=batch_size,
            content_type_filter=content_type
        )
        
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps({
            'processed': len(processed),
            'items': [{'uid': p['uid'], 'title': p['title']} for p in processed]
        })
    
    def clear_queue(self):
        """Clear the entire enhancement queue."""
        portal = api.portal.get()
        annotations = IAnnotations(portal)
        
        if 'knowledge.curator.enhancement_queue' in annotations:
            del annotations['knowledge.curator.enhancement_queue']
        
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps({'status': 'Queue cleared'})
    
    def requeue_item(self):
        """Requeue a specific item."""
        uid = self.request.get('uid')
        if not uid:
            self.request.response.setStatus(400)
            return json.dumps({'error': 'UID required'})
        
        try:
            obj = api.content.get(UID=uid)
            if obj:
                priority = calculate_enhancement_priority(obj)
                # Give Knowledge Items a boost when requeuing
                if obj.portal_type == 'KnowledgeItem':
                    priority *= 1.5
                    
                entry = queue_for_enhancement(obj, priority_override=priority)
                
                self.request.response.setHeader('Content-Type', 'application/json')
                return json.dumps({
                    'status': 'Requeued',
                    'uid': uid,
                    'priority': entry['priority']
                })
            else:
                self.request.response.setStatus(404)
                return json.dumps({'error': 'Object not found'})
        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({'error': str(e)})
    
    def get_stats(self):
        """Get queue statistics."""
        stats = get_queue_statistics()
        
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(stats)
    
    def format_priority(self, priority):
        """Format priority for display."""
        return f"{priority:.2f}"
    
    def get_priority_class(self, priority):
        """Get CSS class based on priority."""
        if priority >= 100:
            return 'priority-critical'
        elif priority >= 75:
            return 'priority-high'
        elif priority >= 50:
            return 'priority-medium'
        else:
            return 'priority-low'


class BatchEnhancementView(BrowserView):
    """View for batch enhancement operations."""
    
    def __call__(self):
        """Queue multiple items for enhancement."""
        if not api.user.has_permission('Manage portal', obj=self.context):
            self.request.response.setStatus(403)
            return "Unauthorized"
        
        # Get UIDs from request
        uids = self.request.get('uids', '').split(',')
        operation = self.request.get('operation', 'full')
        
        if not uids:
            self.request.response.setStatus(400)
            return json.dumps({'error': 'No UIDs provided'})
        
        queued = []
        errors = []
        
        # Sort UIDs by content type to process Knowledge Items first
        knowledge_items = []
        other_items = []
        
        for uid in uids:
            if uid:
                try:
                    obj = api.content.get(UID=uid)
                    if obj:
                        if obj.portal_type == 'KnowledgeItem':
                            knowledge_items.append(obj)
                        else:
                            other_items.append(obj)
                except Exception as e:
                    errors.append({'uid': uid, 'error': str(e)})
        
        # Queue Knowledge Items first with boosted priority
        for obj in knowledge_items:
            try:
                priority = calculate_enhancement_priority(obj) * 1.5
                entry = queue_for_enhancement(obj, operation=operation, 
                                            priority_override=priority)
                queued.append({
                    'uid': obj.UID(),
                    'title': obj.Title(),
                    'priority': entry['priority'],
                    'type': 'KnowledgeItem'
                })
            except Exception as e:
                errors.append({
                    'uid': obj.UID(),
                    'title': obj.Title(),
                    'error': str(e)
                })
        
        # Then queue other items
        for obj in other_items:
            try:
                entry = queue_for_enhancement(obj, operation=operation)
                queued.append({
                    'uid': obj.UID(),
                    'title': obj.Title(),
                    'priority': entry['priority'],
                    'type': obj.portal_type
                })
            except Exception as e:
                errors.append({
                    'uid': obj.UID(),
                    'title': obj.Title(),
                    'error': str(e)
                })
        
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps({
            'queued': queued,
            'errors': errors,
            'summary': {
                'total_queued': len(queued),
                'knowledge_items': len(knowledge_items),
                'other_items': len(other_items),
                'errors': len(errors)
            }
        })