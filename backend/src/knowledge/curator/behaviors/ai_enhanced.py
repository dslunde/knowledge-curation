"""AI-enhanced behavior for content types."""

from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel import directives
from zope import schema
from zope.component import adapter
from zope.interface import Interface, implementer, provider

from knowledge.curator import _


@provider(IFormFieldProvider)
class IAIEnhancedBehavior(model.Schema):
    """Behavior for AI-enhanced features."""
    
    directives.fieldset(
        'ai_features',
        label=_(u'AI Features'),
        fields=['ai_summary', 'ai_tags', 'sentiment_score', 'readability_score'],
    )
    
    ai_summary = schema.Text(
        title=_(u'AI Summary'),
        description=_(u'AI-generated summary of the content'),
        required=False,
        readonly=True,
    )
    
    ai_tags = schema.List(
        title=_(u'AI Suggested Tags'),
        description=_(u'Tags suggested by AI analysis'),
        value_type=schema.TextLine(),
        required=False,
        readonly=True,
        default=[],
    )
    
    sentiment_score = schema.Float(
        title=_(u'Sentiment Score'),
        description=_(u'AI-calculated sentiment score (-1 to 1)'),
        required=False,
        readonly=True,
        min=-1.0,
        max=1.0,
    )
    
    readability_score = schema.Float(
        title=_(u'Readability Score'),
        description=_(u'AI-calculated readability score (0-100)'),
        required=False,
        readonly=True,
        min=0.0,
        max=100.0,
    )


@implementer(IAIEnhancedBehavior)
@adapter(Interface)
class AIEnhancedBehavior(object):
    """Adapter for AI-enhanced behavior."""
    
    def __init__(self, context):
        self.context = context
    
    @property
    def ai_summary(self):
        return getattr(self.context, 'ai_summary', None)
    
    @ai_summary.setter
    def ai_summary(self, value):
        self.context.ai_summary = value
    
    @property
    def ai_tags(self):
        return getattr(self.context, 'ai_tags', [])
    
    @ai_tags.setter
    def ai_tags(self, value):
        self.context.ai_tags = value
    
    @property
    def sentiment_score(self):
        return getattr(self.context, 'sentiment_score', None)
    
    @sentiment_score.setter
    def sentiment_score(self, value):
        self.context.sentiment_score = value
    
    @property
    def readability_score(self):
        return getattr(self.context, 'readability_score', None)
    
    @readability_score.setter
    def readability_score(self, value):
        self.context.readability_score = value