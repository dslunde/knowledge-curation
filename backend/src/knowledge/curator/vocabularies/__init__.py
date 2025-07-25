"""Vocabularies for knowledge.curator."""

from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from knowledge.curator.graph.relationships import RelationshipType


@implementer(IVocabularyFactory)
class PriorityVocabulary:
    """Vocabulary for priority levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="low", title="Low"),
            SimpleTerm(value="medium", title="Medium"),
            SimpleTerm(value="high", title="High"),
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


# Learning-specific vocabularies
@implementer(IVocabularyFactory)
class DifficultyLevelsVocabulary:
    """Vocabulary for difficulty levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="beginner", title="Beginner"),
            SimpleTerm(value="intermediate", title="Intermediate"),
            SimpleTerm(value="advanced", title="Advanced"),
            SimpleTerm(value="expert", title="Expert"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class CognitiveLoadVocabulary:
    """Vocabulary for cognitive load levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="low", title="Low cognitive load"),
            SimpleTerm(value="moderate", title="Moderate cognitive load"),
            SimpleTerm(value="high", title="High cognitive load"),
            SimpleTerm(value="intensive", title="Intensive cognitive load"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class LearningStylesVocabulary:
    """Vocabulary for learning styles."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="visual", title="Visual learner"),
            SimpleTerm(value="auditory", title="Auditory learner"),
            SimpleTerm(value="kinesthetic", title="Kinesthetic learner"),
            SimpleTerm(value="reading_writing", title="Reading/Writing learner"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class KnowledgeTypesVocabulary:
    """Vocabulary for knowledge types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="factual", title="Factual knowledge"),
            SimpleTerm(value="conceptual", title="Conceptual knowledge"),
            SimpleTerm(value="procedural", title="Procedural knowledge"),
            SimpleTerm(value="metacognitive", title="Metacognitive knowledge"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class BloomLevelsVocabulary:
    """Vocabulary for Bloom's taxonomy levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="remember", title="Remember"),
            SimpleTerm(value="understand", title="Understand"),
            SimpleTerm(value="apply", title="Apply"),
            SimpleTerm(value="analyze", title="Analyze"),
            SimpleTerm(value="evaluate", title="Evaluate"),
            SimpleTerm(value="create", title="Create"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class KnowledgeStatusVocabulary:
    """Vocabulary for knowledge status."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="draft", title="Draft"),
            SimpleTerm(value="reviewed", title="Reviewed"),
            SimpleTerm(value="verified", title="Verified"),
            SimpleTerm(value="archived", title="Archived"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class AssessmentTypesVocabulary:
    """Vocabulary for assessment types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="formative", title="Formative"),
            SimpleTerm(value="summative", title="Summative"),
            SimpleTerm(value="diagnostic", title="Diagnostic"),
            SimpleTerm(value="benchmark", title="Benchmark"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class LearningModalitiesVocabulary:
    """Vocabulary for learning modalities."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="synchronous", title="Synchronous"),
            SimpleTerm(value="asynchronous", title="Asynchronous"),
            SimpleTerm(value="blended", title="Blended"),
            SimpleTerm(value="self_paced", title="Self-paced"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class MasteryLevelsVocabulary:
    """Vocabulary for mastery levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="novice", title="Novice"),
            SimpleTerm(value="developing", title="Developing"),
            SimpleTerm(value="proficient", title="Proficient"),
            SimpleTerm(value="exemplary", title="Exemplary"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class MilestoneStatusVocabulary:
    """Vocabulary for milestone status."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="not_started", title="Not Started"),
            SimpleTerm(value="in_progress", title="In Progress"),
            SimpleTerm(value="completed", title="Completed"),
            SimpleTerm(value="blocked", title="Blocked"),
            SimpleTerm(value="deferred", title="Deferred"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class CompetencyLevelsVocabulary:
    """Vocabulary for competency levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="beginner", title="Beginner"),
            SimpleTerm(value="competent", title="Competent"),
            SimpleTerm(value="proficient", title="Proficient"),
            SimpleTerm(value="expert", title="Expert"),
            SimpleTerm(value="master", title="Master"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class EntryTypesVocabulary:
    """Vocabulary for project log entry types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="progress", title="Progress Update"),
            SimpleTerm(value="decision", title="Decision"),
            SimpleTerm(value="issue", title="Issue"),
            SimpleTerm(value="milestone", title="Milestone"),
            SimpleTerm(value="note", title="Note"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class DeliverableStatusVocabulary:
    """Vocabulary for deliverable status."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="not_started", title="Not Started"),
            SimpleTerm(value="in_progress", title="In Progress"),
            SimpleTerm(value="completed", title="Completed"),
            SimpleTerm(value="approved", title="Approved"),
            SimpleTerm(value="rejected", title="Rejected"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class StakeholderLevelsVocabulary:
    """Vocabulary for stakeholder interest/influence levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="low", title="Low"),
            SimpleTerm(value="medium", title="Medium"),
            SimpleTerm(value="high", title="High"),
            SimpleTerm(value="critical", title="Critical"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ResourceTypesVocabulary:
    """Vocabulary for resource types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="human", title="Human Resource"),
            SimpleTerm(value="financial", title="Financial Resource"),
            SimpleTerm(value="material", title="Material Resource"),
            SimpleTerm(value="technical", title="Technical Resource"),
            SimpleTerm(value="time", title="Time Resource"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class AvailabilityStatusVocabulary:
    """Vocabulary for resource availability."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="available", title="Available"),
            SimpleTerm(value="limited", title="Limited"),
            SimpleTerm(value="unavailable", title="Unavailable"),
            SimpleTerm(value="pending", title="Pending"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ImpactLevelsVocabulary:
    """Vocabulary for impact levels."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="low", title="Low Impact"),
            SimpleTerm(value="medium", title="Medium Impact"),
            SimpleTerm(value="high", title="High Impact"),
            SimpleTerm(value="critical", title="Critical Impact"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ActionStatusVocabulary:
    """Vocabulary for action status."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="pending", title="Pending"),
            SimpleTerm(value="in_progress", title="In Progress"),
            SimpleTerm(value="completed", title="Completed"),
            SimpleTerm(value="cancelled", title="Cancelled"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class AnnotationTypesVocabulary:
    """Vocabulary for annotation types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="comment", title="Comment"),
            SimpleTerm(value="question", title="Question"),
            SimpleTerm(value="highlight", title="Highlight"),
            SimpleTerm(value="correction", title="Correction"),
            SimpleTerm(value="reference", title="Reference"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ObjectiveCategoryVocabulary:
    """Vocabulary for learning objective categories."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="knowledge", title="Knowledge"),
            SimpleTerm(value="skill", title="Skill"),
            SimpleTerm(value="attitude", title="Attitude"),
            SimpleTerm(value="behavior", title="Behavior"),
        ]
        return SimpleVocabulary(terms)


# Instantiate factory singletons
DifficultyLevelsVocabularyFactory = DifficultyLevelsVocabulary()
CognitiveLoadVocabularyFactory = CognitiveLoadVocabulary()
LearningStylesVocabularyFactory = LearningStylesVocabulary()
KnowledgeTypesVocabularyFactory = KnowledgeTypesVocabulary()
BloomLevelsVocabularyFactory = BloomLevelsVocabulary()
KnowledgeStatusVocabularyFactory = KnowledgeStatusVocabulary()
AssessmentTypesVocabularyFactory = AssessmentTypesVocabulary()
LearningModalitiesVocabularyFactory = LearningModalitiesVocabulary()
MasteryLevelsVocabularyFactory = MasteryLevelsVocabulary()
MilestoneStatusVocabularyFactory = MilestoneStatusVocabulary()
CompetencyLevelsVocabularyFactory = CompetencyLevelsVocabulary()
EntryTypesVocabularyFactory = EntryTypesVocabulary()
DeliverableStatusVocabularyFactory = DeliverableStatusVocabulary()
StakeholderLevelsVocabularyFactory = StakeholderLevelsVocabulary()
ResourceTypesVocabularyFactory = ResourceTypesVocabulary()
AvailabilityStatusVocabularyFactory = AvailabilityStatusVocabulary()
ImpactLevelsVocabularyFactory = ImpactLevelsVocabulary()
ActionStatusVocabularyFactory = ActionStatusVocabulary()
AnnotationTypesVocabularyFactory = AnnotationTypesVocabulary()
ObjectiveCategoryVocabularyFactory = ObjectiveCategoryVocabulary()


@implementer(IVocabularyFactory)
class CitationFormatsVocabulary:
    """Vocabulary for citation formats."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="APA", title="APA"),
            SimpleTerm(value="MLA", title="MLA"),
            SimpleTerm(value="Chicago", title="Chicago"),
            SimpleTerm(value="Harvard", title="Harvard"),
            SimpleTerm(value="IEEE", title="IEEE"),
            SimpleTerm(value="Vancouver", title="Vancouver"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class LearningStrategiesVocabulary:
    """Vocabulary for learning strategies for navigating knowledge graphs."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="linear", title="Linear"),
            SimpleTerm(value="adaptive", title="Adaptive"),
            SimpleTerm(value="exploratory", title="Exploratory"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class RelationshipTypesVocabulary:
    """Vocabulary for knowledge graph relationship types."""

    def __call__(self, context):
        terms = []
        for rel_type in RelationshipType:
            # Create user-friendly titles from enum values
            title = rel_type.value.replace('_', ' ').title()
            terms.append(SimpleTerm(value=rel_type.value, title=title))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class SessionTypesVocabulary:
    """Vocabulary for learning session types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="self_study", title="Self Study"),
            SimpleTerm(value="guided_learning", title="Guided Learning"),
            SimpleTerm(value="review_session", title="Review Session"),
            SimpleTerm(value="practice_session", title="Practice Session"),
            SimpleTerm(value="assessment", title="Assessment"),
            SimpleTerm(value="collaborative", title="Collaborative Learning"),
        ]
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class MilestoneTypesVocabulary:
    """Vocabulary for knowledge item milestone types."""

    def __call__(self, context):
        terms = [
            SimpleTerm(value="first_encounter", title="First Encounter"),
            SimpleTerm(value="basic_understanding", title="Basic Understanding"),
            SimpleTerm(value="practical_application", title="Practical Application"),
            SimpleTerm(value="mastery_achieved", title="Mastery Achieved"),
            SimpleTerm(value="teaching_ready", title="Teaching Ready"),
            SimpleTerm(value="advanced_synthesis", title="Advanced Synthesis"),
        ]
        return SimpleVocabulary(terms)


RelationshipTypesVocabularyFactory = RelationshipTypesVocabulary()
CitationFormatsVocabularyFactory = CitationFormatsVocabulary()
LearningStrategiesVocabularyFactory = LearningStrategiesVocabulary()
SessionTypesVocabularyFactory = SessionTypesVocabulary()
MilestoneTypesVocabularyFactory = MilestoneTypesVocabulary()
