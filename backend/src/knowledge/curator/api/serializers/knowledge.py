"""Custom serializers for knowledge content types."""

from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from zope.component import adapter
from zope.interface import implementer, Interface
from knowledge.curator.interfaces import (
    IResearchNote, ILearningGoal, IProjectLog, IBookmarkPlus
)
from plone import api


@implementer(ISerializeToJson)
@adapter(IResearchNote, Interface)
class ResearchNoteSerializer(SerializeFolderToJson):
    """Serializer for Research Note content type."""
    
    def __call__(self, version=None, include_items=True):
        result = super(ResearchNoteSerializer, self).__call__(version, include_items)
        
        # Add custom fields
        obj = self.context
        
        # Include embedding vector if requested
        include_embeddings = self.request.get('include_embeddings', 'false').lower() == 'true'
        
        result['content'] = obj.content.raw if hasattr(obj, 'content') else ''
        result['source_url'] = getattr(obj, 'source_url', '')
        result['key_insights'] = getattr(obj, 'key_insights', [])
        result['connections'] = getattr(obj, 'connections', [])
        result['ai_summary'] = getattr(obj, 'ai_summary', '')
        
        if include_embeddings and hasattr(obj, 'embedding_vector'):
            result['embedding_vector'] = getattr(obj, 'embedding_vector', [])
        
        # Add connection details
        if result['connections']:
            catalog = api.portal.get_tool('portal_catalog')
            connection_details = []
            
            for uid in result['connections']:
                brains = catalog(UID=uid)
                if brains:
                    brain = brains[0]
                    connection_details.append({
                        'uid': uid,
                        'title': brain.Title,
                        'portal_type': brain.portal_type,
                        'url': brain.getURL()
                    })
            
            result['connection_details'] = connection_details
        
        # Add spaced repetition data if available
        if hasattr(obj, '_sr_data'):
            sr_data = obj._sr_data
            result['spaced_repetition'] = {
                'interval': sr_data.get('interval'),
                'repetitions': sr_data.get('repetitions'),
                'ease_factor': sr_data.get('ease_factor'),
                'last_review': sr_data.get('last_review', '').isoformat() if sr_data.get('last_review') else None,
                'next_review': sr_data.get('next_review', '').isoformat() if sr_data.get('next_review') else None
            }
        
        return result


@implementer(ISerializeToJson)
@adapter(ILearningGoal, Interface)
class LearningGoalSerializer(SerializeFolderToJson):
    """Serializer for Learning Goal content type."""
    
    def __call__(self, version=None, include_items=True):
        result = super(LearningGoalSerializer, self).__call__(version, include_items)
        
        obj = self.context
        
        result['target_date'] = getattr(obj, 'target_date', None)
        if result['target_date']:
            result['target_date'] = result['target_date'].isoformat()
        
        result['milestones'] = getattr(obj, 'milestones', [])
        result['progress'] = getattr(obj, 'progress', 0)
        result['priority'] = getattr(obj, 'priority', 'medium')
        result['reflection'] = getattr(obj, 'reflection', '')
        result['related_notes'] = getattr(obj, 'related_notes', [])
        
        # Add related note details
        if result['related_notes']:
            catalog = api.portal.get_tool('portal_catalog')
            note_details = []
            
            for uid in result['related_notes']:
                brains = catalog(UID=uid)
                if brains:
                    brain = brains[0]
                    note_details.append({
                        'uid': uid,
                        'title': brain.Title,
                        'portal_type': brain.portal_type,
                        'url': brain.getURL()
                    })
            
            result['related_note_details'] = note_details
        
        # Calculate time to target
        if result['target_date']:
            from datetime import datetime, date
            target = datetime.fromisoformat(result['target_date']).date()
            today = date.today()
            days_remaining = (target - today).days
            result['days_remaining'] = days_remaining
            result['is_overdue'] = days_remaining < 0
        
        return result


@implementer(ISerializeToJson)
@adapter(IProjectLog, Interface)
class ProjectLogSerializer(SerializeFolderToJson):
    """Serializer for Project Log content type."""
    
    def __call__(self, version=None, include_items=True):
        result = super(ProjectLogSerializer, self).__call__(version, include_items)
        
        obj = self.context
        
        result['start_date'] = getattr(obj, 'start_date', None)
        if result['start_date']:
            result['start_date'] = result['start_date'].isoformat()
        
        result['entries'] = getattr(obj, 'entries', [])
        result['deliverables'] = getattr(obj, 'deliverables', [])
        result['learnings'] = getattr(obj, 'learnings', [])
        result['status'] = getattr(obj, 'status', 'planning')
        
        # Calculate project duration
        if result['start_date']:
            from datetime import datetime, date
            start = datetime.fromisoformat(result['start_date']).date()
            today = date.today()
            result['duration_days'] = (today - start).days
        
        # Add entry count and latest entry
        result['entry_count'] = len(result['entries'])
        if result['entries']:
            # Sort entries by date (assuming they have a 'date' field)
            sorted_entries = sorted(
                result['entries'],
                key=lambda x: x.get('date', ''),
                reverse=True
            )
            result['latest_entry'] = sorted_entries[0]
        
        return result


@implementer(ISerializeToJson)
@adapter(IBookmarkPlus, Interface)
class BookmarkPlusSerializer(SerializeFolderToJson):
    """Serializer for BookmarkPlus content type."""
    
    def __call__(self, version=None, include_items=True):
        result = super(BookmarkPlusSerializer, self).__call__(version, include_items)
        
        obj = self.context
        
        # Include embedding vector if requested
        include_embeddings = self.request.get('include_embeddings', 'false').lower() == 'true'
        
        result['url'] = getattr(obj, 'url', '')
        result['notes'] = obj.notes.raw if hasattr(obj, 'notes') else ''
        result['read_status'] = getattr(obj, 'read_status', 'unread')
        result['importance'] = getattr(obj, 'importance', 'medium')
        result['ai_summary'] = getattr(obj, 'ai_summary', '')
        
        if include_embeddings and hasattr(obj, 'embedding_vector'):
            result['embedding_vector'] = getattr(obj, 'embedding_vector', [])
        
        # Add spaced repetition data if available
        if hasattr(obj, '_sr_data'):
            sr_data = obj._sr_data
            result['spaced_repetition'] = {
                'interval': sr_data.get('interval'),
                'repetitions': sr_data.get('repetitions'),
                'ease_factor': sr_data.get('ease_factor'),
                'last_review': sr_data.get('last_review', '').isoformat() if sr_data.get('last_review') else None,
                'next_review': sr_data.get('next_review', '').isoformat() if sr_data.get('next_review') else None
            }
        
        # Add domain info from URL
        if result['url']:
            from urllib.parse import urlparse
            parsed = urlparse(result['url'])
            result['domain'] = parsed.netloc
        
        return result