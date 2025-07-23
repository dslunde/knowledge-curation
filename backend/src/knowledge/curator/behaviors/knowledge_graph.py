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
        fields=['related_concepts', 'concept_weight', 'graph_metadata'],
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
    """Adapter for knowledge graph behavior."""
    
    def __init__(self, context):
        self.context = context
    
    @property
    def related_concepts(self):
        return getattr(self.context, 'related_concepts', [])
    
    @related_concepts.setter
    def related_concepts(self, value):
        self.context.related_concepts = value
    
    @property
    def concept_weight(self):
        return getattr(self.context, 'concept_weight', 1.0)
    
    @concept_weight.setter
    def concept_weight(self, value):
        self.context.concept_weight = value
    
    @property
    def graph_metadata(self):
        return getattr(self.context, 'graph_metadata', {})
    
    @graph_metadata.setter
    def graph_metadata(self, value):
        self.context.graph_metadata = value