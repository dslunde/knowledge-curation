"""BookmarkPlus content type."""

from datetime import datetime
from plone.dexterity.content import Item
from zope.interface import implementer

from knowledge.curator.interfaces import IBookmarkPlus


@implementer(IBookmarkPlus)
class BookmarkPlus(Item):
    """BookmarkPlus content type implementation."""

    def get_embedding(self):
        """Get the embedding vector for this bookmark."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector

    def mark_as_read(self):
        """Mark the bookmark as read."""
        self.read_status = 'read'
        # Store read date as annotation
        from zope.annotation.interfaces import IAnnotations
        annotations = IAnnotations(self)
        annotations['bookmark_read_date'] = datetime.now().isoformat()

    def mark_as_reading(self):
        """Mark the bookmark as currently reading."""
        self.read_status = 'reading'
        # Store started reading date
        from zope.annotation.interfaces import IAnnotations
        annotations = IAnnotations(self)
        annotations['bookmark_reading_started'] = datetime.now().isoformat()

    def get_read_date(self):
        """Get the date when bookmark was marked as read."""
        from zope.annotation.interfaces import IAnnotations
        annotations = IAnnotations(self)
        return annotations.get('bookmark_read_date', None)

    def get_reading_started_date(self):
        """Get the date when started reading."""
        from zope.annotation.interfaces import IAnnotations
        annotations = IAnnotations(self)
        return annotations.get('bookmark_reading_started', None)

    def add_tag(self, tag):
        """Add a tag to the bookmark."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        """Remove a tag from the bookmark."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def update_importance(self, new_importance):
        """Update bookmark importance with validation."""
        valid_levels = ['low', 'medium', 'high', 'critical']
        if new_importance in valid_levels:
            self.importance = new_importance
            return True
        return False

    def is_high_priority(self):
        """Check if bookmark is high priority (unread and high/critical importance)."""
        return (self.read_status == 'unread' and
                self.importance in ['high', 'critical'])

    def get_summary_text(self):
        """Get text for generating embeddings/summaries."""
        # Combine title, description, and notes for embedding generation
        parts = [self.title]
        if self.description:
            parts.append(self.description)
        if self.notes and self.notes.raw:
            parts.append(self.notes.raw)
        return ' '.join(parts)
