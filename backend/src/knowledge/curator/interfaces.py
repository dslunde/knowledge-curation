"""Interfaces for knowledge.curator."""

<<<<<<< HEAD
=======
from plone.autoform.interfaces import IFormFieldProvider
from plone.app.textfield import RichText
from plone.supermodel import model
from zope import schema
from zope.interface import Interface, provider

>>>>>>> fixing_linting_and_tests
from knowledge.curator import _
from plone.app.textfield import RichText
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import Interface
from zope.interface import provider


class IKnowledgeCuratorLayer(Interface):
    """Browser layer for knowledge.curator"""


@provider(IFormFieldProvider)
class IResearchNote(model.Schema):
    """Schema for Research Note content type."""

    title = schema.TextLine(
<<<<<<< HEAD
        title=_("Title"),
=======
        title=_('Title'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    description = schema.Text(
<<<<<<< HEAD
        title=_("Description"),
        description=_("Brief description of the research note"),
=======
        title=_('Description'),
        description=_('Brief description of the research note'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    content = RichText(
<<<<<<< HEAD
        title=_("Content"),
        description=_("Main content of the research note"),
=======
        title=_('Content'),
        description=_('Main content of the research note'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    tags = schema.List(
<<<<<<< HEAD
        title=_("Tags"),
        description=_("Tags for categorization"),
=======
        title=_('Tags'),
        description=_('Tags for categorization'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    source_url = schema.URI(
<<<<<<< HEAD
        title=_("Source URL"),
        description=_("Original source of the research"),
=======
        title=_('Source URL'),
        description=_('Original source of the research'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    key_insights = schema.List(
<<<<<<< HEAD
        title=_("Key Insights"),
        description=_("List of key insights from this research"),
=======
        title=_('Key Insights'),
        description=_('List of key insights from this research'),
>>>>>>> fixing_linting_and_tests
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
<<<<<<< HEAD
        title=_("Title"),
=======
        title=_('Title'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    description = schema.Text(
<<<<<<< HEAD
        title=_("Description"),
        description=_("Detailed description of the learning goal"),
=======
        title=_('Description'),
        description=_('Detailed description of the learning goal'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    target_date = schema.Date(
<<<<<<< HEAD
        title=_("Target Date"),
        description=_("Target completion date"),
=======
        title=_('Target Date'),
        description=_('Target completion date'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    priority = schema.Choice(
<<<<<<< HEAD
        title=_("Priority"),
        description=_("Priority level of this goal"),
        vocabulary="knowledge.curator.priority_vocabulary",
=======
        title=_('Priority'),
        description=_('Priority level of this goal'),
        vocabulary='knowledge.curator.priority_vocabulary',
>>>>>>> fixing_linting_and_tests
        required=False,
        default="medium",
    )

    progress = schema.Int(
<<<<<<< HEAD
        title=_("Progress"),
        description=_("Progress percentage (0-100)"),
=======
        title=_('Progress'),
        description=_('Progress percentage (0-100)'),
>>>>>>> fixing_linting_and_tests
        required=False,
        default=0,
        min=0,
        max=100,
    )

    milestones = schema.List(
<<<<<<< HEAD
        title=_("Milestones"),
        description=_("List of milestones to achieve this goal"),
=======
        title=_('Milestones'),
        description=_('List of milestones to achieve this goal'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    related_notes = schema.List(
<<<<<<< HEAD
        title=_("Related Notes"),
        description=_("Research notes related to this goal"),
=======
        title=_('Related Notes'),
        description=_('Research notes related to this goal'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    reflection = schema.Text(
<<<<<<< HEAD
        title=_("Reflection"),
        description=_("Personal reflection on the learning process"),
=======
        title=_('Reflection'),
        description=_('Personal reflection on the learning process'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )


@provider(IFormFieldProvider)
class IProjectLog(model.Schema):
    """Schema for Project Log content type."""

    title = schema.TextLine(
<<<<<<< HEAD
        title=_("Title"),
=======
        title=_('Title'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    description = schema.Text(
<<<<<<< HEAD
        title=_("Description"),
        description=_("Project description"),
=======
        title=_('Description'),
        description=_('Project description'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    start_date = schema.Date(
<<<<<<< HEAD
        title=_("Start Date"),
        description=_("Project start date"),
=======
        title=_('Start Date'),
        description=_('Project start date'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    status = schema.Choice(
<<<<<<< HEAD
        title=_("Status"),
        description=_("Current status of the project"),
        vocabulary="knowledge.curator.project_status_vocabulary",
=======
        title=_('Status'),
        description=_('Current status of the project'),
        vocabulary='knowledge.curator.project_status_vocabulary',
>>>>>>> fixing_linting_and_tests
        required=False,
        default="planning",
    )

    entries = schema.List(
<<<<<<< HEAD
        title=_("Log Entries"),
        description=_("Project log entries"),
=======
        title=_('Log Entries'),
        description=_('Project log entries'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    deliverables = schema.List(
<<<<<<< HEAD
        title=_("Deliverables"),
        description=_("Project deliverables"),
=======
        title=_('Deliverables'),
        description=_('Project deliverables'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.Text(),
        required=False,
        default=[],
    )

    learnings = schema.Text(
<<<<<<< HEAD
        title=_("Learnings"),
        description=_("What was learned from this project"),
=======
        title=_('Learnings'),
        description=_('What was learned from this project'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )


@provider(IFormFieldProvider)
class IBookmarkPlus(model.Schema):
    """Schema for BookmarkPlus content type."""

    title = schema.TextLine(
<<<<<<< HEAD
        title=_("Title"),
=======
        title=_('Title'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    url = schema.URI(
<<<<<<< HEAD
        title=_("URL"),
        description=_("The bookmarked URL"),
=======
        title=_('URL'),
        description=_('The bookmarked URL'),
>>>>>>> fixing_linting_and_tests
        required=True,
    )

    tags = schema.List(
<<<<<<< HEAD
        title=_("Tags"),
        description=_("Tags for categorization"),
=======
        title=_('Tags'),
        description=_('Tags for categorization'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    notes = schema.Text(
<<<<<<< HEAD
        title=_("Notes"),
        description=_("Personal notes about this bookmark"),
=======
        title=_('Notes'),
        description=_('Personal notes about this bookmark'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    read_status = schema.Choice(
<<<<<<< HEAD
        title=_("Read Status"),
        description=_("Whether you have read this content"),
        vocabulary="knowledge.curator.read_status_vocabulary",
=======
        title=_('Read Status'),
        description=_('Whether you have read this content'),
        vocabulary='knowledge.curator.read_status_vocabulary',
>>>>>>> fixing_linting_and_tests
        required=False,
        default="unread",
    )

    importance = schema.Choice(
<<<<<<< HEAD
        title=_("Importance"),
        description=_("How important is this bookmark"),
        vocabulary="knowledge.curator.importance_vocabulary",
=======
        title=_('Importance'),
        description=_('How important is this bookmark'),
        vocabulary='knowledge.curator.importance_vocabulary',
>>>>>>> fixing_linting_and_tests
        required=False,
        default="medium",
    )

    # NOTE: ai_summary, embedding_vector are provided by behaviors
    # to avoid duplication conflicts


# Additional interfaces for the system


class IKnowledgeGraph(Interface):
    """Interface for knowledge graph functionality."""

    def add_connection(source_uid, target_uid, relationship_type="related"):
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
