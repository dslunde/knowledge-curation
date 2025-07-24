"""Vocabularies for knowledge.curator."""

from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class PriorityVocabulary:
    """Vocabulary for priority levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value='low', title='Low'),
            SimpleTerm(value='medium', title='Medium'),
            SimpleTerm(value='high', title='High'),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ProjectStatusVocabulary:
    """Vocabulary for project status."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="planning", title="Planning"),
            SimpleTerm(value="active", title="Active"),
            SimpleTerm(value="paused", title="Paused"),
            SimpleTerm(value="completed", title="Completed"),
            SimpleTerm(value="archived", title="Archived"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ReadStatusVocabulary:
    """Vocabulary for read status."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="unread", title="Unread"),
            SimpleTerm(value="reading", title="Reading"),
            SimpleTerm(value="read", title="Read"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ImportanceVocabulary:
    """Vocabulary for importance levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="low", title="Low"),
            SimpleTerm(value="medium", title="Medium"),
            SimpleTerm(value="high", title="High"),
            SimpleTerm(value="critical", title="Critical"),
        ]
        return SimpleVocabulary(terms)


PriorityVocabularyFactory = PriorityVocabulary()
ProjectStatusVocabularyFactory = ProjectStatusVocabulary()
ReadStatusVocabularyFactory = ReadStatusVocabulary()
ImportanceVocabularyFactory = ImportanceVocabulary()
