"""Research Note content type."""

from knowledge.curator.interfaces import IResearchNote, IKeyInsight, IAuthor
from plone.dexterity.content import Container
from zope.interface import implementer
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import uuid
from datetime import datetime


@implementer(IResearchNote)
class ResearchNote(Container):
    """Research Note content type implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize structured lists
        if not hasattr(self, 'key_insights'):
            self.key_insights = PersistentList()
        if not hasattr(self, 'authors'):
            self.authors = PersistentList()
        if not hasattr(self, 'builds_upon'):
            self.builds_upon = PersistentList()
        if not hasattr(self, 'contradicts'):
            self.contradicts = PersistentList()
        if not hasattr(self, 'replication_studies'):
            self.replication_studies = PersistentList()

    def get_embedding(self):
        """Get the embedding vector for this note."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector

    def add_connection(self, uid):
        """Add a connection to another content item."""
        if not hasattr(self, 'connections'):
            self.connections = PersistentList()
        if uid not in self.connections:
            self.connections.append(uid)

    def remove_connection(self, uid):
        """Remove a connection to another content item."""
        if hasattr(self, 'connections') and uid in self.connections:
            self.connections.remove(uid)

    def get_connections(self):
        """Get all connections."""
        return getattr(self, 'connections', PersistentList())

    def add_insight(self, text, importance='medium', evidence=None):
        """Add a structured key insight."""
        if not hasattr(self, 'key_insights'):
            self.key_insights = PersistentList()
        
        insight = PersistentMapping()
        insight['text'] = text
        insight['importance'] = importance
        insight['evidence'] = evidence
        insight['timestamp'] = datetime.now()
        
        self.key_insights.append(insight)
        return insight

    def add_author(self, name, email=None, orcid=None, affiliation=None):
        """Add an author to this research."""
        if not hasattr(self, 'authors'):
            self.authors = PersistentList()
        
        author = PersistentMapping()
        author['name'] = name
        author['email'] = email
        author['orcid'] = orcid
        author['affiliation'] = affiliation
        
        self.authors.append(author)
        return author

    def add_builds_upon(self, uid):
        """Add a research item this builds upon."""
        if not hasattr(self, 'builds_upon'):
            self.builds_upon = PersistentList()
        if uid not in self.builds_upon:
            self.builds_upon.append(uid)

    def add_contradicts(self, uid):
        """Add a research item this contradicts."""
        if not hasattr(self, 'contradicts'):
            self.contradicts = PersistentList()
        if uid not in self.contradicts:
            self.contradicts.append(uid)

    def add_replication_study(self, uid):
        """Add a replication study."""
        if not hasattr(self, 'replication_studies'):
            self.replication_studies = PersistentList()
        if uid not in self.replication_studies:
            self.replication_studies.append(uid)

    def get_related_research(self):
        """Get all related research (builds upon + contradicts)."""
        related = []
        if hasattr(self, 'builds_upon'):
            related.extend(self.builds_upon)
        if hasattr(self, 'contradicts'):
            related.extend(self.contradicts)
        return list(set(related))  # Remove duplicates

    def get_contradicted_research(self):
        """Get research this work contradicts."""
        return getattr(self, 'contradicts', PersistentList())

    def migrate_legacy_insights(self):
        """Migrate legacy text insights to structured format."""
        # Check if we have old-style insights
        if hasattr(self, 'key_insights') and self.key_insights:
            # Check if first item is a string (old format)
            if self.key_insights and isinstance(self.key_insights[0], str):
                old_insights = list(self.key_insights)
                self.key_insights = PersistentList()
                
                for insight_text in old_insights:
                    self.add_insight(
                        text=insight_text,
                        importance='medium',
                        evidence=None
                    )
                return True
        return False
