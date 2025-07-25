"""Vocabulary for knowledge item connection types."""

from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from knowledge.curator import _


@implementer(IVocabularyFactory)
class ConnectionTypesVocabularyFactory:
    """Vocabulary factory for knowledge item connection types."""
    
    def __call__(self, context):
        """Create vocabulary of connection types.
        
        These are the specific learning-focused connection types
        for the knowledge graph.
        """
        items = [
            ('prerequisite', _('Prerequisite'), 
             _('Knowledge that must be mastered before this item')),
            ('builds_on', _('Builds On'), 
             _('Extends or develops concepts from the source')),
            ('reinforces', _('Reinforces'), 
             _('Strengthens understanding through practice or repetition')),
            ('applies', _('Applies'), 
             _('Practical application of theoretical knowledge')),
        ]
        
        terms = []
        for value, title, description in items:
            term = SimpleTerm(
                value=value,
                token=value,
                title=title
            )
            # Store description as an attribute for UI use
            term.description = description
            terms.append(term)
        
        return SimpleVocabulary(terms)


ConnectionTypesVocabularyFactory = ConnectionTypesVocabularyFactory()