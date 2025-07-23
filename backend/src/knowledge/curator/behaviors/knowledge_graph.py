"""Knowledge graph behavior for content types."""

from plone.supermodel import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import Interface, implementer, provider

from knowledge.curator import _


@provider(IFormFieldProvider)
class IKnowledgeGraphBehavior(model.Schema):
    """Behavior for knowledge graph relationships."""
    
    directives.fieldset(
        'knowledge_graph',
        label=_(u'Knowledge Graph'),
        fields=['connections', 'embedding_vector', 'related_concepts', 'concept_weight', 'graph_metadata'],
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

    related_concepts = schema.List(
        title=_(u'Related Concepts'),
        description=_(u'Concepts related to this content'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )
    
    concept_weight = schema.Float(
        title=_(u'Concept Weight'),
        description=_(u'Weight of this content in the knowledge graph'),
        required=False,
        default=1.0,
        min=0.0,
        max=10.0,
    )
    
    graph_metadata = schema.Dict(
        title=_(u'Graph Metadata'),
        description=_(u'Additional metadata for knowledge graph'),
        key_type=schema.TextLine(),
        value_type=schema.Field(),
        required=False,
        default={},
    )


@implementer(IKnowledgeGraphBehavior)
@adapter(Interface)
class KnowledgeGraphBehavior(object):
    """Knowledge graph behavior adapter."""
    
    def __init__(self, context):
        self.context = context
    
    @property
    def connections(self):
        """Get connections."""
        return getattr(self.context, 'connections', [])
    
    @connections.setter
    def connections(self, value):
        """Set connections."""
        self.context.connections = value
    
    @property
    def embedding_vector(self):
        """Get embedding vector."""
        return getattr(self.context, 'embedding_vector', [])
    
    @embedding_vector.setter 
    def embedding_vector(self, value):
        """Set embedding vector."""
        self.context.embedding_vector = value
    
    @property
    def related_concepts(self):
        """Get related concepts."""
        return getattr(self.context, 'related_concepts', [])
    
    @related_concepts.setter
    def related_concepts(self, value):
        """Set related concepts."""
        self.context.related_concepts = value