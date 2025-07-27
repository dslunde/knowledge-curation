"""Knowledge Curator Field Deserializer for Display-Only and Readonly Fields."""

from knowledge.curator.behaviors.spaced_repetition import ISpacedRepetition
from knowledge.curator.behaviors.ai_enhanced import IAIEnhanced
from knowledge.curator.behaviors.knowledge_graph import IKnowledgeGraph
from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import IFieldDeserializer
from zope.component import adapter
from zope.interface import implementer, Interface
from zope.schema.interfaces import IField
import logging

logger = logging.getLogger(__name__)


@implementer(IFieldDeserializer)
@adapter(IField, Interface, object)
class KnowledgeCuratorFieldDeserializer:
    """Custom field deserializer for Knowledge Curator behaviors.
    
    This deserializer filters out display-only and readonly fields that should not be
    set during content creation/editing. Handles fields from:
    - Spaced Repetition behavior (display-only computed fields)
    - AI Enhanced behavior (readonly AI-generated fields)  
    - Knowledge Graph behavior (readonly computed fields)
    """

    def __init__(self, field, context, request):
        self.field = field
        self.context = context
        self.request = request

    def __call__(self, value, validate=True, set=True):
        """Deserialize field value, filtering out display-only fields."""
        
        # List of display-only and readonly fields that should be filtered out
        display_only_fields = [
            # Spaced Repetition - display-only fields (computed by SR algorithm)
            'ease_factor',
            'interval', 
            'repetitions',
            'last_review',
            'next_review',
            'total_reviews',
            'average_quality',
            'retention_score',
            
            # AI Enhanced - readonly fields (computed by AI analysis)
            'ai_summary',
            'ai_summary_confidence',
            'ai_tags',
            'ai_tags_confidence',
            'sentiment_score',
            'sentiment_confidence',
            'readability_score',
            'ai_model_version',
            'last_ai_analysis',
            'overall_confidence',
            'confidence_breakdown',
            
            # Knowledge Graph - readonly fields (computed by graph algorithms)
            'embedding_vector',
            'centrality_score',
        ]
        
        # If this is a display-only field, don't set it
        if self.field.__name__ in display_only_fields:
            logger.debug(f"Filtering out display-only field: {self.field.__name__}")
            return
            
        # For all other fields, use standard deserialization
        if hasattr(self.field, 'default'):
            if value is None:
                value = self.field.default
                
        # Handle boolean values properly
        if self.field.__class__.__name__ == 'Bool':
            value = boolean_value(value)
            
        # Validate if requested
        if validate and hasattr(self.field, 'validate'):
            self.field.validate(value)
            
        # Set the value if requested
        if set:
            setattr(self.context, self.field.__name__, value)
            
        return value 