"""Views for Research Note content type."""

from Products.Five.browser import BrowserView
from plone import api


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
                    pass
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
