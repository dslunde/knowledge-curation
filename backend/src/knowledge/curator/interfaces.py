"""Interfaces for knowledge.curator."""

from plone.autoform.interfaces import IFormFieldProvider
from plone.app.textfield import RichText
from plone.supermodel import model
from plone import api
from zope import schema
from zope.interface import Interface, provider

from knowledge.curator import _


class IKnowledgeCuratorLayer(Interface):
    """Browser layer for knowledge.curator"""


@provider(IFormFieldProvider)
class IResearchNote(model.Schema):
    """Schema for Research Note content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'Brief description of the research note'),
        required=False,
    )

    content = RichText(
        title=_(u'Content'),
        description=_(u'Main content of the research note'),
        required=True,
    )

    tags = schema.List(
        title=_(u'Tags'),
        description=_(u'Tags for categorization'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    source_url = schema.URI(
        title=_(u'Source URL'),
        description=_(u'Original source of the research'),
        required=False,
    )

    key_insights = schema.List(
        title=_(u'Key Insights'),
        description=_(u'List of key insights from this research'),
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    # NOTE: ai_summary, connections, embedding_vector are provided by behaviors
    # to avoid duplication conflicts


@provider(IFormFieldProvider)
class ILearningGoal(model.Schema):
    """Schema for Learning Goal content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'Detailed description of the learning goal'),
        required=True,
    )

    target_date = schema.Date(
        title=_(u'Target Date'),
        description=_(u'Target completion date'),
        required=False,
    )

    priority = schema.Choice(
        title=_(u'Priority'),
        description=_(u'Priority level of this goal'),
        vocabulary='knowledge.curator.priority_vocabulary',
        required=False,
        default='medium',
    )

    progress = schema.Int(
        title=_(u'Progress'),
        description=_(u'Progress percentage (0-100)'),
        required=False,
        default=0,
        min=0,
        max=100,
    )

    milestones = schema.List(
        title=_(u'Milestones'),
        description=_(u'List of milestones to achieve this goal'),
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    related_notes = schema.List(
        title=_(u'Related Notes'),
        description=_(u'Research notes related to this goal'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    reflection = schema.Text(
        title=_(u'Reflection'),
        description=_(u'Personal reflection on the learning process'),
        required=False,
    )


@provider(IFormFieldProvider)
class IProjectLog(model.Schema):
    """Schema for Project Log content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'Project description'),
        required=True,
    )

    start_date = schema.Date(
        title=_(u'Start Date'),
        description=_(u'Project start date'),
        required=False,
    )

    status = schema.Choice(
        title=_(u'Status'),
        description=_(u'Current status of the project'),
        vocabulary='knowledge.curator.project_status_vocabulary',
        required=False,
        default='planning',
    )

    entries = schema.List(
        title=_(u'Log Entries'),
        description=_(u'Project log entries'),
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    deliverables = schema.List(
        title=_(u'Deliverables'),
        description=_(u'Project deliverables'),
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    learnings = schema.Text(
        title=_(u'Learnings'),
        description=_(u'What was learned from this project'),
        required=False,
    )


@provider(IFormFieldProvider)
class IBookmarkPlus(model.Schema):
    """Schema for BookmarkPlus content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    url = schema.URI(
        title=_(u'URL'),
        description=_(u'The bookmarked URL'),
        required=True,
    )

    tags = schema.List(
        title=_(u'Tags'),
        description=_(u'Tags for categorization'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    notes = schema.Text(
        title=_(u'Notes'),
        description=_(u'Personal notes about this bookmark'),
        required=False,
    )

    read_status = schema.Choice(
        title=_(u'Read Status'),
        description=_(u'Whether you have read this content'),
        vocabulary='knowledge.curator.read_status_vocabulary',
        required=False,
        default='unread',
    )

    importance = schema.Choice(
        title=_(u'Importance'),
        description=_(u'How important is this bookmark'),
        vocabulary='knowledge.curator.importance_vocabulary',
        required=False,
        default='medium',
    )

    # NOTE: ai_summary, embedding_vector are provided by behaviors
    # to avoid duplication conflicts


# Additional interfaces for the system

class IKnowledgeGraph(Interface):
    """Interface for knowledge graph functionality."""

    def add_connection(source_uid, target_uid, relationship_type='related'):
        """Add a connection between two content items."""

    def remove_connection(source_uid, target_uid):
        """Remove a connection between two content items."""

    def get_connections(uid):
        """Get all connections for a content item."""

    def get_related_items(uid, max_items=10):
        """Get related items based on connections and similarity."""


class IVectorSearch(Interface):
    """Interface for vector-based similarity search."""

    def generate_embedding(text):
        """Generate embedding vector for text."""

    def update_embedding(uid, embedding):
        """Update embedding for content item."""

    def find_similar(embedding, max_results=10):
        """Find similar content based on embedding."""


class IAIService(Interface):
    """Interface for AI service utilities."""
    
    def generate_embedding(text):
        """Generate embedding vector for given text."""
    
    def generate_summary(text, max_length=150):
        """Generate AI summary for given text."""
    
    def calculate_similarity(vector1, vector2):
        """Calculate similarity between two embedding vectors."""
    
    def search_similar(query, limit=10):
        """Search for similar content based on query."""


class IAIEnhanced(Interface):
    """Interface for AI enhancement features."""

    def generate_summary(content):
        """Generate AI summary of content."""

    def extract_key_insights(content):
        """Extract key insights from content."""

    def suggest_tags(content):
        """Suggest tags based on content analysis."""

    def analyze_sentiment(content):
        """Analyze sentiment of content."""