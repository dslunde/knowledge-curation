# -*- coding: utf-8 -*-
"""Browser views for Knowledge Curator."""

from plone import api
from plone.dexterity.browser.view import DefaultView
from Products.Five.browser import BrowserView


class KnowledgeCuratorView(DefaultView):
    """Default view for Knowledge Curator content."""

    def __call__(self):
        """Render the view."""
        return super(KnowledgeCuratorView, self).__call__()


class KnowledgeHomeView(BrowserView):
    """Custom home page view displaying Knowledge Items and learning content."""
    
    def __call__(self):
        """Render the home page with Knowledge Items."""
        return self.index()
    
    def get_knowledge_items(self):
        """Get all Knowledge Items for display."""
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(
            portal_type='KnowledgeItem',
            sort_on='created',
            sort_order='reverse'
        )
        
        items = []
        for brain in brains:
            try:
                obj = brain.getObject()
                items.append({
                    'title': brain.Title,
                    'description': brain.Description,
                    'url': brain.getURL(),
                    'knowledge_type': getattr(obj, 'knowledge_type', 'unknown'),
                    'difficulty_level': getattr(obj, 'difficulty_level', 'unknown'),
                    'created': brain.created,
                    'review_state': brain.review_state
                })
            except Exception:
                continue
                
        return items
    
    def get_content_summary(self):
        """Get summary of all content types."""
        catalog = api.portal.get_tool('portal_catalog')
        
        content_types = ['KnowledgeItem', 'LearningGoal', 'ResearchNote', 'ProjectLog', 'BookmarkPlus']
        summary = {}
        
        for content_type in content_types:
            brains = catalog(portal_type=content_type)
            summary[content_type] = {
                'count': len(brains),
                'items': [{'title': brain.Title, 'url': brain.getURL()} for brain in brains[:3]]
            }
            
        return summary
    
    def get_learning_stats(self):
        """Get learning progress statistics."""
        knowledge_items = self.get_knowledge_items()
        
        difficulty_counts = {}
        knowledge_type_counts = {}
        
        for item in knowledge_items:
            difficulty = item['difficulty_level']
            knowledge_type = item['knowledge_type']
            
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            knowledge_type_counts[knowledge_type] = knowledge_type_counts.get(knowledge_type, 0) + 1
            
        return {
            'total_items': len(knowledge_items),
            'difficulty_distribution': difficulty_counts,
            'knowledge_type_distribution': knowledge_type_counts
        } 