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
        title=_('Title'),
        required=True,
    )

    description = schema.Text(
        title=_('Summary'),
        description=_('A short summary of the knowledge item'),
        required=False,
    )

    text = RichText(
        title=_('Body Text'),
        description=_('Main content of the knowledge item'),
        required=False,
    )

    tags = schema.List(
        title=_('Tags'),
        description=_('Tags for categorization'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    source_url = schema.URI(
        title=_('Source URL'),
        description=_('Original source of the information'),
        required=False,
    )

    embedding_vector = schema.List(
        title=_('Embedding Vector'),
        description=_('AI-generated embedding vector for similarity search'),
        value_type=schema.Float(),
        required=False,
        readonly=True,
    )

    ai_summary = schema.Text(
        title=_('AI Summary'),
        description=_('AI-generated summary of the content'),
        required=False,
        readonly=True,
    )

    relevance_score = schema.Float(
        title=_('Relevance Score'),
        description=_('AI-calculated relevance score'),
        required=False,
        readonly=True,
        default=0.0,
    )

    attachment = NamedBlobFile(
        title=_('Attachment'),
        description=_('Upload a file attachment'),
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
