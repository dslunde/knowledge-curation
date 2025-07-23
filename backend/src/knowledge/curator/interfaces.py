"""Module where all interfaces, events and exceptions live."""

from plone.app.textfield import RichText
from plone.supermodel import model
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from knowledge.curator import _


class IPloneAppKnowledgeLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


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


class IResearchNote(model.Schema):
    """Schema for Research Note content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Summary'),
        description=_(u'A brief summary of the research note'),
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

    connections = schema.List(
        title=_(u'Connections'),
        description=_(u'Related notes and content (UIDs)'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    embedding_vector = schema.List(
        title=_(u'Embedding Vector'),
        description=_(u'AI-generated embedding vector for similarity search'),
        value_type=schema.Float(),
        required=False,
        readonly=True,
    )

    ai_summary = schema.Text(
        title=_(u'AI Summary'),
        description=_(u'AI-generated summary of the content'),
        required=False,
        readonly=True,
    )


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

    milestones = schema.List(
        title=_(u'Milestones'),
        description=_(u'List of milestones to achieve this goal'),
        value_type=schema.Dict(
            value_type=schema.Field(),
            key_type=schema.TextLine()
        ),
        required=False,
        default=[],
    )

    progress = schema.Int(
        title=_(u'Progress'),
        description=_(u'Progress percentage (0-100)'),
        required=False,
        default=0,
        min=0,
        max=100,
    )

    related_notes = schema.List(
        title=_(u'Related Notes'),
        description=_(u'Related research notes (UIDs)'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    priority = schema.Choice(
        title=_(u'Priority'),
        description=_(u'Priority level of this goal'),
        values=['low', 'medium', 'high'],
        required=True,
        default='medium',
    )

    reflection = schema.Text(
        title=_(u'Reflection'),
        description=_(u'Reflection or summary of what was learned'),
        required=False,
    )


class IProjectLog(model.Schema):
    """Schema for Project Log content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'Project overview'),
        required=True,
    )

    start_date = schema.Date(
        title=_(u'Start Date'),
        description=_(u'Project start date'),
        required=True,
    )

    entries = schema.List(
        title=_(u'Log Entries'),
        description=_(u'Chronological project log entries'),
        value_type=schema.Dict(
            value_type=schema.Field(),
            key_type=schema.TextLine()
        ),
        required=False,
        default=[],
    )

    deliverables = schema.List(
        title=_(u'Deliverables'),
        description=_(u'List of project deliverables'),
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    learnings = schema.List(
        title=_(u'Key Learnings'),
        description=_(u'Key learnings from this project'),
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    status = schema.Choice(
        title=_(u'Status'),
        description=_(u'Current project status'),
        values=['planning', 'active', 'paused', 'completed', 'archived'],
        required=True,
        default='planning',
    )


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

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'Description of the bookmarked resource'),
        required=False,
    )

    tags = schema.List(
        title=_(u'Tags'),
        description=_(u'Tags for categorization'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    notes = RichText(
        title=_(u'Notes'),
        description=_(u'Personal notes about this resource'),
        required=False,
    )

    read_status = schema.Choice(
        title=_(u'Read Status'),
        description=_(u'Reading status of the resource'),
        values=['unread', 'reading', 'read'],
        required=True,
        default='unread',
    )

    importance = schema.Choice(
        title=_(u'Importance'),
        description=_(u'Importance level of this resource'),
        values=['low', 'medium', 'high', 'critical'],
        required=True,
        default='medium',
    )

    embedding_vector = schema.List(
        title=_(u'Embedding Vector'),
        description=_(u'AI-generated embedding vector for similarity search'),
        value_type=schema.Float(),
        required=False,
        readonly=True,
    )

    ai_summary = schema.Text(
        title=_(u'AI Summary'),
        description=_(u'AI-generated summary of the content'),
        required=False,
        readonly=True,
    )