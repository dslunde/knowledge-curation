"""Views for Research Note content type."""

import logging

from plone import api
from Products.Five.browser import BrowserView

logger = logging.getLogger(__name__)


class ResearchNoteView(BrowserView):
    """Default view for Research Note."""

    def __call__(self):
        """Render the view."""
        return self.index()

    def get_connections(self):
        """Get connected content items."""
        connections = []
        if self.context.connections:
            for uid in self.context.connections:
                try:
                    brain = api.content.find(UID=uid)
                    if brain:
                        connections.append(brain[0])
                except Exception:
                    logger.exception("Error finding connection with UID: %s", uid)
        return connections

    def get_key_insights_formatted(self):
        """Get key insights as a formatted list."""
        return self.context.key_insights or []

    def has_embedding(self):
        """Check if this note has an embedding vector."""
        return bool(self.context.embedding_vector)

    def get_similar_notes(self, limit=5):
        """Get similar research notes based on embeddings."""
        # This would use the AI service to find similar content
        # For now, return empty list
        return []

    def get_annotated_knowledge_items_details(self):
        """Get detailed information about annotated Knowledge Items.
        
        Returns:
            list: List of dicts with Knowledge Item details including error handling
        """
        return self.context.get_annotated_knowledge_items_details()

    def has_annotated_knowledge_items(self):
        """Check if this research note has any annotated knowledge items."""
        return bool(getattr(self.context, 'annotated_knowledge_items', []))

    def get_annotation_type_title(self):
        """Get human-readable title for the annotation type."""
        annotation_type = getattr(self.context, 'annotation_type', None)
        if not annotation_type:
            return "General Annotation"
        
        # Convert snake_case to Title Case
        return annotation_type.replace('_', ' ').title()

    def get_annotation_scope_title(self):
        """Get human-readable title for the annotation scope."""
        annotation_scope = getattr(self.context, 'annotation_scope', None)
        if not annotation_scope:
            return "Whole Item"
        
        # Convert snake_case to Title Case
        return annotation_scope.replace('_', ' ').title()
    
    def get_suggested_related_notes(self, max_results=5):
        """Get suggested related Research Notes.
        
        Args:
            max_results (int): Maximum number of suggestions to return
            
        Returns:
            list: List of related note suggestions with relevance scores and reasons
        """
        return self.context.suggest_related_notes(max_results=max_results)
