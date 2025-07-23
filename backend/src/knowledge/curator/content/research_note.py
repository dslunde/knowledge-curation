"""Research Note content type."""

from plone.dexterity.content import Container
from zope.interface import implementer

from knowledge.curator.interfaces import IResearchNote


@implementer(IResearchNote)
class ResearchNote(Container):
    """Research Note content type implementation."""
    
    def get_embedding(self):
        """Get the embedding vector for this note."""
        return self.embedding_vector or []
    
    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector
    
    def add_connection(self, uid):
        """Add a connection to another content item."""
        if not self.connections:
            self.connections = []
        if uid not in self.connections:
            self.connections.append(uid)
    
    def remove_connection(self, uid):
        """Remove a connection to another content item."""
        if self.connections and uid in self.connections:
            self.connections.remove(uid)
    
    def get_connections(self):
        """Get all connections."""
        return self.connections or []
    
    def add_insight(self, insight):
        """Add a key insight."""
        if not self.key_insights:
            self.key_insights = []
        self.key_insights.append(insight)