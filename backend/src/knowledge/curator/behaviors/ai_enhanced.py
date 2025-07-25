"""AI-enhanced behavior for content types."""

from knowledge.curator import _
from knowledge.curator.behaviors.interfaces import IExtractedConcept, IKnowledgeGap
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import directives
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from datetime import datetime


@provider(IFormFieldProvider)
class IAIEnhancedBehavior(model.Schema):
    """Behavior for AI-enhanced features with confidence tracking."""

    directives.fieldset(
        "ai_features",
        label=_("AI Features"),
        fields=[
            "ai_summary", 
            "ai_summary_confidence",
            "ai_tags", 
            "ai_tags_confidence",
            "extracted_concepts",
            "knowledge_gaps",
            "sentiment_score", 
            "sentiment_confidence",
            "readability_score",
            "ai_model_version",
            "last_ai_analysis",
            "overall_confidence",
            "confidence_breakdown",
        ],
    )

    ai_summary = schema.Text(
        title=_("AI Summary"),
        description=_("AI-generated summary of the content"),
        required=False,
        readonly=True,
    )

    ai_summary_confidence = schema.Float(
        title=_("Summary Confidence"),
        description=_("Confidence score for the AI summary"),
        min=0.0,
        max=1.0,
        required=False,
        readonly=True,
    )

    ai_tags = schema.List(
        title=_("AI Suggested Tags"),
        description=_("Tags suggested by AI analysis"),
        value_type=schema.TextLine(),
        required=False,
        readonly=True,
        default=[],
    )

    ai_tags_confidence = schema.Float(
        title=_("Tags Confidence"),
        description=_("Confidence score for the AI tags"),
        min=0.0,
        max=1.0,
        required=False,
        readonly=True,
    )

    extracted_concepts = schema.List(
        title=_("Extracted Concepts"),
        description=_("Concepts extracted from the content"),
        value_type=schema.Object(schema=IExtractedConcept),
        required=False,
        default=[],
    )

    knowledge_gaps = schema.List(
        title=_("Knowledge Gaps"),
        description=_("Identified gaps in knowledge"),
        value_type=schema.Object(schema=IKnowledgeGap),
        required=False,
        default=[],
    )

    sentiment_score = schema.Float(
        title=_("Sentiment Score"),
        description=_("AI-calculated sentiment score (-1 to 1)"),
        required=False,
        readonly=True,
        min=-1.0,
        max=1.0,
    )

    sentiment_confidence = schema.Float(
        title=_("Sentiment Confidence"),
        description=_("Confidence in sentiment analysis"),
        min=0.0,
        max=1.0,
        required=False,
        readonly=True,
    )

    readability_score = schema.Float(
        title=_("Readability Score"),
        description=_("AI-calculated readability score (0-100)"),
        required=False,
        readonly=True,
        min=0.0,
        max=100.0,
    )

    ai_model_version = schema.TextLine(
        title=_("AI Model Version"),
        description=_("Version of AI model used for analysis"),
        required=False,
        readonly=True,
    )

    last_ai_analysis = schema.Datetime(
        title=_("Last AI Analysis"),
        description=_("When the content was last analyzed by AI"),
        required=False,
        readonly=True,
    )

    overall_confidence = schema.Float(
        title=_("Overall Confidence"),
        description=_("Overall confidence in AI analysis"),
        min=0.0,
        max=1.0,
        required=False,
        readonly=True,
    )

    confidence_breakdown = schema.Dict(
        title=_("Confidence Breakdown"),
        description=_("Confidence scores for each AI feature"),
        key_type=schema.TextLine(),
        value_type=schema.Float(),
        required=False,
        readonly=True,
        default={},
    )


@implementer(IAIEnhancedBehavior)
@adapter(Interface)
class AIEnhancedBehavior:
    """Adapter for AI-enhanced behavior with confidence tracking."""

    def __init__(self, context):
        self.context = context
        self._ensure_persistent_storage()

    def _ensure_persistent_storage(self):
        """Ensure all lists use persistent storage."""
        if not hasattr(self.context, 'extracted_concepts'):
            self.context.extracted_concepts = PersistentList()
        if not hasattr(self.context, 'knowledge_gaps'):
            self.context.knowledge_gaps = PersistentList()
        if not hasattr(self.context, 'confidence_breakdown'):
            self.context.confidence_breakdown = PersistentMapping()

    @property
    def ai_summary(self):
        return getattr(self.context, "ai_summary", None)

    @ai_summary.setter
    def ai_summary(self, value):
        self.context.ai_summary = value

    @property
    def ai_summary_confidence(self):
        return getattr(self.context, "ai_summary_confidence", None)

    @ai_summary_confidence.setter
    def ai_summary_confidence(self, value):
        self.context.ai_summary_confidence = value

    @property
    def ai_tags(self):
        return getattr(self.context, "ai_tags", [])

    @ai_tags.setter
    def ai_tags(self, value):
        self.context.ai_tags = value

    @property
    def ai_tags_confidence(self):
        return getattr(self.context, "ai_tags_confidence", None)

    @ai_tags_confidence.setter
    def ai_tags_confidence(self, value):
        self.context.ai_tags_confidence = value

    @property
    def extracted_concepts(self):
        return getattr(self.context, "extracted_concepts", PersistentList())

    @extracted_concepts.setter
    def extracted_concepts(self, value):
        self.context.extracted_concepts = PersistentList(value) if not isinstance(value, PersistentList) else value

    @property
    def knowledge_gaps(self):
        return getattr(self.context, "knowledge_gaps", PersistentList())

    @knowledge_gaps.setter
    def knowledge_gaps(self, value):
        self.context.knowledge_gaps = PersistentList(value) if not isinstance(value, PersistentList) else value

    @property
    def sentiment_score(self):
        return getattr(self.context, "sentiment_score", None)

    @sentiment_score.setter
    def sentiment_score(self, value):
        self.context.sentiment_score = value

    @property
    def sentiment_confidence(self):
        return getattr(self.context, "sentiment_confidence", None)

    @sentiment_confidence.setter
    def sentiment_confidence(self, value):
        self.context.sentiment_confidence = value

    @property
    def readability_score(self):
        return getattr(self.context, "readability_score", None)

    @readability_score.setter
    def readability_score(self, value):
        self.context.readability_score = value

    @property
    def ai_model_version(self):
        return getattr(self.context, "ai_model_version", None)

    @ai_model_version.setter
    def ai_model_version(self, value):
        self.context.ai_model_version = value

    @property
    def last_ai_analysis(self):
        return getattr(self.context, "last_ai_analysis", None)

    @last_ai_analysis.setter
    def last_ai_analysis(self, value):
        self.context.last_ai_analysis = value

    @property
    def overall_confidence(self):
        return getattr(self.context, "overall_confidence", None)

    @overall_confidence.setter
    def overall_confidence(self, value):
        self.context.overall_confidence = value

    @property
    def confidence_breakdown(self):
        return getattr(self.context, "confidence_breakdown", PersistentMapping())

    @confidence_breakdown.setter
    def confidence_breakdown(self, value):
        self.context.confidence_breakdown = PersistentMapping(value) if not isinstance(value, PersistentMapping) else value

    def update_ai_analysis(self, summary=None, tags=None, sentiment=None, readability=None, 
                          concepts=None, gaps=None, model_version=None):
        """Update AI analysis with confidence scores."""
        self._ensure_persistent_storage()
        
        confidence_scores = PersistentMapping()
        total_confidence = 0.0
        count = 0
        
        if summary is not None:
            self.ai_summary = summary['text']
            self.ai_summary_confidence = summary.get('confidence', 0.8)
            confidence_scores['summary'] = self.ai_summary_confidence
            total_confidence += self.ai_summary_confidence
            count += 1
        
        if tags is not None:
            self.ai_tags = tags['tags']
            self.ai_tags_confidence = tags.get('confidence', 0.7)
            confidence_scores['tags'] = self.ai_tags_confidence
            total_confidence += self.ai_tags_confidence
            count += 1
        
        if sentiment is not None:
            self.sentiment_score = sentiment['score']
            self.sentiment_confidence = sentiment.get('confidence', 0.6)
            confidence_scores['sentiment'] = self.sentiment_confidence
            total_confidence += self.sentiment_confidence
            count += 1
        
        if readability is not None:
            self.readability_score = readability
            confidence_scores['readability'] = 0.9  # Readability is usually reliable
            total_confidence += 0.9
            count += 1
        
        if concepts is not None:
            self.extracted_concepts = PersistentList()
            for concept in concepts:
                concept_obj = PersistentMapping()
                concept_obj['concept'] = concept.get('concept')
                concept_obj['relevance_score'] = concept.get('relevance_score', 0.5)
                concept_obj['frequency'] = concept.get('frequency', 1)
                concept_obj['context'] = concept.get('context', '')
                concept_obj['confidence'] = concept.get('confidence', 0.7)
                self.extracted_concepts.append(concept_obj)
        
        if gaps is not None:
            self.knowledge_gaps = PersistentList()
            for gap in gaps:
                gap_obj = PersistentMapping()
                gap_obj['gap_description'] = gap.get('description')
                gap_obj['importance'] = gap.get('importance', 'medium')
                gap_obj['suggested_topics'] = gap.get('suggested_topics', [])
                gap_obj['confidence'] = gap.get('confidence', 0.6)
                self.knowledge_gaps.append(gap_obj)
        
        if model_version:
            self.ai_model_version = model_version
        
        self.last_ai_analysis = datetime.now()
        self.confidence_breakdown = confidence_scores
        
        if count > 0:
            self.overall_confidence = total_confidence / count
        
        return self.overall_confidence

    def get_high_confidence_concepts(self, threshold=0.7):
        """Get concepts with confidence above threshold."""
        return [c for c in self.extracted_concepts if c.get('confidence', 0) >= threshold]

    def refresh_confidence_scores(self):
        """Recalculate overall confidence from breakdown."""
        if self.confidence_breakdown:
            scores = list(self.confidence_breakdown.values())
            self.overall_confidence = sum(scores) / len(scores) if scores else 0.0
            return self.overall_confidence
        return 0.0
