"""Knowledge Item content type."""

from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.namedfile.field import NamedBlobFile
from plone.schema import Email
from plone.supermodel import model
from zope import schema
from zope.interface import implementer

from knowledge.curator import _


class IKnowledgeItem(model.Schema):
    """Schema for Knowledge Item content type."""

    title = schema.TextLine(
        title=_(u'Title'),
        required=True,
    )

    description = schema.Text(
        title=_(u'Summary'),
        description=_(u'A short summary of the knowledge item'),
        required=False,
    )

    text = RichText(
        title=_(u'Body Text'),
        description=_(u'Main content of the knowledge item'),
        required=False,
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
        description=_(u'Original source of the information'),
        required=False,
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

    relevance_score = schema.Float(
        title=_(u'Relevance Score'),
        description=_(u'AI-calculated relevance score'),
        required=False,
        readonly=True,
        default=0.0,
    )

    attachment = NamedBlobFile(
        title=_(u'Attachment'),
        description=_(u'Upload a file attachment'),
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