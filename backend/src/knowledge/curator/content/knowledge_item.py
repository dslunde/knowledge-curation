"""Knowledge Item content type."""

from knowledge.curator import _
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class IKnowledgeItem(model.Schema):
    """Schema for Knowledge Item content type."""

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
        title=_("Summary"),
        description=_("A short summary of the knowledge item"),
=======
        title=_('Summary'),
        description=_('A short summary of the knowledge item'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    text = RichText(
<<<<<<< HEAD
        title=_("Body Text"),
        description=_("Main content of the knowledge item"),
=======
        title=_('Body Text'),
        description=_('Main content of the knowledge item'),
>>>>>>> fixing_linting_and_tests
        required=False,
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
        description=_("Original source of the information"),
=======
        title=_('Source URL'),
        description=_('Original source of the information'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )

    embedding_vector = schema.List(
<<<<<<< HEAD
        title=_("Embedding Vector"),
        description=_("AI-generated embedding vector for similarity search"),
=======
        title=_('Embedding Vector'),
        description=_('AI-generated embedding vector for similarity search'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.Float(),
        required=False,
        readonly=True,
    )

    ai_summary = schema.Text(
<<<<<<< HEAD
        title=_("AI Summary"),
        description=_("AI-generated summary of the content"),
=======
        title=_('AI Summary'),
        description=_('AI-generated summary of the content'),
>>>>>>> fixing_linting_and_tests
        required=False,
        readonly=True,
    )

    relevance_score = schema.Float(
<<<<<<< HEAD
        title=_("Relevance Score"),
        description=_("AI-calculated relevance score"),
=======
        title=_('Relevance Score'),
        description=_('AI-calculated relevance score'),
>>>>>>> fixing_linting_and_tests
        required=False,
        readonly=True,
        default=0.0,
    )

    attachment = NamedBlobFile(
<<<<<<< HEAD
        title=_("Attachment"),
        description=_("Upload a file attachment"),
=======
        title=_('Attachment'),
        description=_('Upload a file attachment'),
>>>>>>> fixing_linting_and_tests
        required=False,
    )


@implementer(IKnowledgeItem)
class KnowledgeItem(Container):
    """Knowledge Item content type implementation."""

    def get_embedding(self):
        """Get the embedding vector for this item."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector
