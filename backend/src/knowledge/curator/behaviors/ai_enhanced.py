"""AI-enhanced behavior for content types."""

from knowledge.curator import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import directives
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


@provider(IFormFieldProvider)
class IAIEnhancedBehavior(model.Schema):
    """Behavior for AI-enhanced features."""

    directives.fieldset(
<<<<<<< HEAD
        "ai_features",
        label=_("AI Features"),
        fields=["ai_summary", "ai_tags", "sentiment_score", "readability_score"],
    )

    ai_summary = schema.Text(
        title=_("AI Summary"),
        description=_("AI-generated summary of the content"),
=======
        'ai_features',
        label=_('AI Features'),
        fields=['ai_summary', 'ai_tags', 'sentiment_score', 'readability_score'],
    )

    ai_summary = schema.Text(
        title=_('AI Summary'),
        description=_('AI-generated summary of the content'),
>>>>>>> fixing_linting_and_tests
        required=False,
        readonly=True,
    )

    ai_tags = schema.List(
<<<<<<< HEAD
        title=_("AI Suggested Tags"),
        description=_("Tags suggested by AI analysis"),
=======
        title=_('AI Suggested Tags'),
        description=_('Tags suggested by AI analysis'),
>>>>>>> fixing_linting_and_tests
        value_type=schema.TextLine(),
        required=False,
        readonly=True,
        default=[],
    )

    sentiment_score = schema.Float(
<<<<<<< HEAD
        title=_("Sentiment Score"),
        description=_("AI-calculated sentiment score (-1 to 1)"),
=======
        title=_('Sentiment Score'),
        description=_('AI-calculated sentiment score (-1 to 1)'),
>>>>>>> fixing_linting_and_tests
        required=False,
        readonly=True,
        min=-1.0,
        max=1.0,
    )

    readability_score = schema.Float(
<<<<<<< HEAD
        title=_("Readability Score"),
        description=_("AI-calculated readability score (0-100)"),
=======
        title=_('Readability Score'),
        description=_('AI-calculated readability score (0-100)'),
>>>>>>> fixing_linting_and_tests
        required=False,
        readonly=True,
        min=0.0,
        max=100.0,
    )


@implementer(IAIEnhancedBehavior)
@adapter(Interface)
class AIEnhancedBehavior:
    """Adapter for AI-enhanced behavior."""

    def __init__(self, context):
        self.context = context

    @property
    def ai_summary(self):
<<<<<<< HEAD
        return getattr(self.context, "ai_summary", None)
=======
        return getattr(self.context, 'ai_summary', None)
>>>>>>> fixing_linting_and_tests

    @ai_summary.setter
    def ai_summary(self, value):
        self.context.ai_summary = value

    @property
    def ai_tags(self):
<<<<<<< HEAD
        return getattr(self.context, "ai_tags", [])
=======
        return getattr(self.context, 'ai_tags', [])
>>>>>>> fixing_linting_and_tests

    @ai_tags.setter
    def ai_tags(self, value):
        self.context.ai_tags = value

    @property
    def sentiment_score(self):
<<<<<<< HEAD
        return getattr(self.context, "sentiment_score", None)
=======
        return getattr(self.context, 'sentiment_score', None)
>>>>>>> fixing_linting_and_tests

    @sentiment_score.setter
    def sentiment_score(self, value):
        self.context.sentiment_score = value

    @property
    def readability_score(self):
<<<<<<< HEAD
        return getattr(self.context, "readability_score", None)
=======
        return getattr(self.context, 'readability_score', None)
>>>>>>> fixing_linting_and_tests

    @readability_score.setter
    def readability_score(self, value):
        self.context.readability_score = value
