"""Knowledge Item content type."""

from knowledge.curator.interfaces import IKnowledgeItem
from plone.dexterity.content import Container
from zope.interface import implementer


@implementer(IKnowledgeItem)
class KnowledgeItem(Container):
    """Knowledge Item content type implementation."""

    def get_embedding(self):
        """Get the embedding vector for this item."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector
