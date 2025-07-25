"""Interfaces for knowledge.curator."""

from plone import schema
from plone.app.textfield import RichText
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope.interface import Interface
from zope.interface import provider
from zope.interface import invariant
from plone.theme.interfaces import IDefaultPloneLayer
from plone.app.vocabularies.catalog import CatalogSource
from plone.autoform import directives
from z3c.form.browser.radio import RadioFieldWidget
from z3c.relationfield.schema import RelationChoice, RelationList
from plone.app.z3cform.widget import RelatedItemsFieldWidget

from knowledge.curator import _
from knowledge.curator.content.validators import (
    validate_title_length,
    validate_description_length,
    validate_content_length,
    validate_knowledge_type,
    validate_atomic_concepts,
    validate_tags,
    validate_embedding_vector,
    validate_mastery_threshold,
    validate_learning_progress,
    validate_difficulty_level,
    validate_uid_references_list,
    validate_prerequisite_enables_consistency,
    validate_mastery_threshold_progress_consistency,
    validate_knowledge_item_progress_dict,
)
from knowledge.curator.graph.interfaces import IKnowledgeItemConnection


class IKnowledgeCuratorLayer(IDefaultPloneLayer):
    """Marker interface for the knowledge curator theme layer."""


# Base schema for all knowledge objects with learning-specific metadata
@provider(IFormFieldProvider)
class IKnowledgeObjectBase(model.Schema):
    """Base schema for all knowledge objects with learning-specific metadata."""
    
    # Learning metadata fields
    difficulty_level = schema.Choice(
        title=_("Difficulty Level"),
        description=_("The difficulty level of this content"),
        vocabulary="knowledge.curator.difficulty_levels",
        required=False,
        default="intermediate",
    )
    
    cognitive_load = schema.Choice(
        title=_("Cognitive Load"),
        description=_("The cognitive load required to understand this content"),
        vocabulary="knowledge.curator.cognitive_load",
        required=False,
    )
    
    learning_style = schema.List(
        title=_("Learning Styles"),
        description=_("Learning styles this content supports"),
        value_type=schema.Choice(vocabulary="knowledge.curator.learning_styles"),
        required=False,
    )
    
    knowledge_status = schema.Choice(
        title=_("Knowledge Status"),
        description=_("Current status of this knowledge"),
        vocabulary="knowledge.curator.knowledge_status",
        required=True,
        default="draft",
    )
    
    last_reviewed = schema.Datetime(
        title=_("Last Reviewed"),
        description=_("When this content was last reviewed"),
        required=False,
    )
    
    review_frequency = schema.Int(
        title=_("Review Frequency (days)"),
        description=_("How often this content should be reviewed"),
        required=False,
        default=30,
    )
    
    confidence_score = schema.Float(
        title=_("Confidence Score"),
        description=_("Your confidence in understanding this content"),
        min=0.0,
        max=1.0,
        required=False,
    )
    
    # Bibliographic metadata fields
    authors = schema.List(
        title=_("Authors"),
        description=_("Authors of this content"),
        value_type=schema.Object(schema=Interface),  # IAuthor will be defined below
        required=False,
    )
    
    publication_date = schema.Date(
        title=_("Publication Date"),
        description=_("Date of publication"),
        required=False,
    )
    
    source_url = schema.URI(
        title=_("Source URL"),
        description=_("Original source URL"),
        required=False,
    )
    
    doi = schema.TextLine(
        title=_("DOI"),
        description=_("Digital Object Identifier"),
        required=False,
    )
    
    isbn = schema.TextLine(
        title=_("ISBN"),
        description=_("International Standard Book Number"),
        required=False,
    )
    
    journal_name = schema.TextLine(
        title=_("Journal Name"),
        description=_("Name of the journal"),
        required=False,
    )
    
    volume_issue = schema.TextLine(
        title=_("Volume/Issue"),
        description=_("Volume and issue number"),
        required=False,
    )
    
    page_numbers = schema.TextLine(
        title=_("Page Numbers"),
        description=_("Page numbers"),
        required=False,
    )
    
    publisher = schema.TextLine(
        title=_("Publisher"),
        description=_("Publisher name"),
        required=False,
    )
    
    citation_format = schema.Text(
        title=_("Formatted Citation"),
        description=_("Full formatted citation"),
        required=False,
        readonly=True,
    )


# Supporting sub-object interfaces
class IAuthor(Interface):
    """Interface for author information."""
    
    name = schema.TextLine(
        title=_("Name"),
        description=_("Full name of the author"),
        required=True,
    )
    
    email = schema.TextLine(
        title=_("Email"),
        description=_("Email address"),
        required=False,
    )
    
    orcid = schema.TextLine(
        title=_("ORCID"),
        description=_("ORCID identifier"),
        required=False,
    )
    
    affiliation = schema.TextLine(
        title=_("Affiliation"),
        description=_("Institutional affiliation"),
        required=False,
    )


class IKeyInsight(Interface):
    """Interface for key insights."""
    
    text = schema.Text(
        title=_("Insight Text"),
        description=_("The key insight"),
        required=True,
    )
    
    importance = schema.Choice(
        title=_("Importance"),
        description=_("Importance of this insight"),
        vocabulary="knowledge.curator.importance_vocabulary",
        required=False,
        default="medium",
    )
    
    evidence = schema.Text(
        title=_("Evidence"),
        description=_("Supporting evidence for this insight"),
        required=False,
    )
    
    timestamp = schema.Datetime(
        title=_("Timestamp"),
        description=_("When this insight was added"),
        required=True,
    )


class ILearningMilestone(Interface):
    """Interface for a learning milestone."""
    
    id = schema.TextLine(
        title=_("Milestone ID"),
        description=_("Unique identifier for the milestone"),
        required=True,
    )
    
    title = schema.TextLine(
        title=_("Title"),
        description=_("Title of the milestone"),
        required=True,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("Detailed description of the milestone"),
        required=False,
    )
    
    target_date = schema.Date(
        title=_("Target Date"),
        description=_("Target completion date for the milestone"),
        required=False,
    )
    
    status = schema.Choice(
        title=_("Status"),
        description=_("Current status of the milestone"),
        vocabulary="knowledge.curator.milestone_status",
        required=False,
        default="not_started",
    )
    
    progress_percentage = schema.Int(
        title=_("Progress Percentage"),
        description=_("Progress percentage (0-100)"),
        required=False,
        default=0,
        min=0,
        max=100,
    )
    
    completion_criteria = schema.Text(
        title=_("Completion Criteria"),
        description=_("Criteria for considering this milestone complete"),
        required=False,
    )


class ILearningObjective(Interface):
    """Interface for learning objectives following SMART criteria."""
    
    objective_text = schema.Text(
        title=_("Objective"),
        description=_("The learning objective"),
        required=True,
    )
    
    measurable = schema.Bool(
        title=_("Measurable"),
        description=_("Is this objective measurable?"),
        required=False,
        default=False,
    )
    
    achievable = schema.Bool(
        title=_("Achievable"),
        description=_("Is this objective achievable?"),
        required=False,
        default=False,
    )
    
    relevant = schema.Bool(
        title=_("Relevant"),
        description=_("Is this objective relevant?"),
        required=False,
        default=False,
    )
    
    time_bound = schema.Bool(
        title=_("Time-bound"),
        description=_("Is this objective time-bound?"),
        required=False,
        default=False,
    )
    
    success_metrics = schema.List(
        title=_("Success Metrics"),
        description=_("How to measure success"),
        value_type=schema.TextLine(),
        required=False,
    )


class IAnnotation(Interface):
    """Interface for annotations on content."""
    
    text = schema.Text(
        title=_("Annotation Text"),
        description=_("The annotation"),
        required=True,
    )
    
    author = schema.TextLine(
        title=_("Author"),
        description=_("Who made this annotation"),
        required=True,
    )
    
    timestamp = schema.Datetime(
        title=_("Timestamp"),
        description=_("When this annotation was made"),
        required=True,
    )
    
    target_element = schema.TextLine(
        title=_("Target Element"),
        description=_("What element this annotation refers to"),
        required=False,
    )
    
    annotation_type = schema.Choice(
        title=_("Annotation Type"),
        description=_("Type of annotation"),
        vocabulary="knowledge.curator.annotation_types",
        required=False,
    )


class IAssessmentCriterion(Interface):
    """Interface for assessment criteria."""
    
    criterion = schema.Text(
        title=_("Criterion"),
        description=_("The assessment criterion"),
        required=True,
    )
    
    weight = schema.Float(
        title=_("Weight"),
        description=_("Weight of this criterion (0-1)"),
        min=0.0,
        max=1.0,
        required=False,
        default=1.0,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("Detailed description of the criterion"),
        required=False,
    )


class ICompetency(Interface):
    """Interface for competencies."""
    
    name = schema.TextLine(
        title=_("Competency Name"),
        description=_("Name of the competency"),
        required=True,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("Description of the competency"),
        required=False,
    )
    
    level = schema.Choice(
        title=_("Level"),
        description=_("Current competency level"),
        vocabulary="knowledge.curator.competency_levels",
        required=False,
    )
    
    category = schema.TextLine(
        title=_("Category"),
        description=_("Category of this competency"),
        required=False,
    )


class IProjectLogEntry(Interface):
    """Interface for a project log entry."""
    
    id = schema.TextLine(
        title=_("Entry ID"),
        description=_("Unique identifier for the entry"),
        required=True,
    )
    
    timestamp = schema.Datetime(
        title=_("Timestamp"),
        description=_("When the entry was created"),
        required=True,
    )
    
    author = schema.TextLine(
        title=_("Author"),
        description=_("Who created this entry"),
        required=True,
    )
    
    entry_type = schema.Choice(
        title=_("Entry Type"),
        description=_("Type of log entry"),
        vocabulary="knowledge.curator.entry_types",
        required=False,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("Entry description"),
        required=True,
    )
    
    related_items = schema.List(
        title=_("Related Items"),
        description=_("Related content items"),
        value_type=schema.TextLine(),
        required=False,
    )


class IProjectDeliverable(Interface):
    """Interface for project deliverables."""
    
    title = schema.TextLine(
        title=_("Title"),
        description=_("Deliverable title"),
        required=True,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("What this deliverable includes"),
        required=False,
    )
    
    due_date = schema.Date(
        title=_("Due Date"),
        description=_("When the deliverable is due"),
        required=False,
    )
    
    status = schema.Choice(
        title=_("Status"),
        description=_("Current status of the deliverable"),
        vocabulary="knowledge.curator.deliverable_status_vocabulary",
        required=False,
    )
    
    assigned_to = schema.TextLine(
        title=_("Assigned To"),
        description=_("Who is responsible for this deliverable"),
        required=False,
    )
    
    completion_percentage = schema.Int(
        title=_("Completion Percentage"),
        description=_("Progress percentage (0-100)"),
        required=False,
        default=0,
        min=0,
        max=100,
    )


class IStakeholder(Interface):
    """Interface for project stakeholders."""
    
    name = schema.TextLine(
        title=_("Name"),
        description=_("Stakeholder name"),
        required=True,
    )
    
    role = schema.TextLine(
        title=_("Role"),
        description=_("Stakeholder role"),
        required=False,
    )
    
    interest_level = schema.Choice(
        title=_("Interest Level"),
        description=_("Level of interest in the project"),
        vocabulary="knowledge.curator.stakeholder_levels",
        required=False,
    )
    
    influence_level = schema.Choice(
        title=_("Influence Level"),
        description=_("Level of influence on the project"),
        vocabulary="knowledge.curator.stakeholder_levels",
        required=False,
    )
    
    contact_info = schema.Text(
        title=_("Contact Information"),
        description=_("How to contact this stakeholder"),
        required=False,
    )


class IProjectResource(Interface):
    """Interface for project resources."""
    
    resource_type = schema.Choice(
        title=_("Resource Type"),
        description=_("Type of resource"),
        vocabulary="knowledge.curator.resource_types",
        required=True,
    )
    
    name = schema.TextLine(
        title=_("Name"),
        description=_("Resource name"),
        required=True,
    )
    
    quantity = schema.Float(
        title=_("Quantity"),
        description=_("Amount of resource needed"),
        required=False,
    )
    
    availability = schema.Choice(
        title=_("Availability"),
        description=_("Resource availability"),
        vocabulary="knowledge.curator.availability_status",
        required=False,
    )
    
    cost = schema.Float(
        title=_("Cost"),
        description=_("Cost of the resource"),
        required=False,
    )


class ISuccessMetric(Interface):
    """Interface for success metrics."""
    
    metric_name = schema.TextLine(
        title=_("Metric Name"),
        description=_("Name of the metric"),
        required=True,
    )
    
    target_value = schema.TextLine(
        title=_("Target Value"),
        description=_("Target value to achieve"),
        required=True,
    )
    
    current_value = schema.TextLine(
        title=_("Current Value"),
        description=_("Current value"),
        required=False,
    )
    
    unit = schema.TextLine(
        title=_("Unit"),
        description=_("Unit of measurement"),
        required=False,
    )
    
    measurement_method = schema.Text(
        title=_("Measurement Method"),
        description=_("How to measure this metric"),
        required=False,
    )


class ILessonLearned(Interface):
    """Interface for lessons learned."""
    
    lesson = schema.Text(
        title=_("Lesson"),
        description=_("The lesson learned"),
        required=True,
    )
    
    context = schema.Text(
        title=_("Context"),
        description=_("Context in which this lesson was learned"),
        required=False,
    )
    
    impact = schema.Choice(
        title=_("Impact"),
        description=_("Impact of this lesson"),
        vocabulary="knowledge.curator.impact_levels",
        required=False,
    )
    
    recommendations = schema.Text(
        title=_("Recommendations"),
        description=_("Recommendations based on this lesson"),
        required=False,
    )


class IFollowUpAction(Interface):
    """Interface for follow-up actions."""
    
    action = schema.Text(
        title=_("Action"),
        description=_("The follow-up action"),
        required=True,
    )
    
    responsible_party = schema.TextLine(
        title=_("Responsible Party"),
        description=_("Who is responsible for this action"),
        required=False,
    )
    
    due_date = schema.Date(
        title=_("Due Date"),
        description=_("When this action is due"),
        required=False,
    )
    
    priority = schema.Choice(
        title=_("Priority"),
        description=_("Priority of this action"),
        vocabulary="knowledge.curator.priority_vocabulary",
        required=False,
    )
    
    status = schema.Choice(
        title=_("Status"),
        description=_("Current status"),
        vocabulary="knowledge.curator.action_status",
        required=False,
    )


class ILearningSession(Interface):
    """Interface for learning session data."""
    
    session_id = schema.TextLine(
        title=_("Session ID"),
        description=_("Unique identifier for the learning session"),
        required=True,
    )
    
    start_time = schema.Datetime(
        title=_("Start Time"),
        description=_("When the learning session started"),
        required=True,
    )
    
    end_time = schema.Datetime(
        title=_("End Time"),
        description=_("When the learning session ended"),
        required=False,
    )
    
    duration_minutes = schema.Int(
        title=_("Duration (minutes)"),
        description=_("Session duration in minutes"),
        required=False,
        min=0,
    )
    
    knowledge_items_studied = schema.List(
        title=_("Knowledge Items Studied"),
        description=_("UIDs of knowledge items studied during this session"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )
    
    progress_updates = schema.Dict(
        title=_("Progress Updates"),
        description=_("Progress updates for each knowledge item (UID -> progress delta)"),
        key_type=schema.TextLine(),
        value_type=schema.Float(min=0.0, max=1.0),
        required=False,
        default={},
    )
    
    notes = schema.Text(
        title=_("Session Notes"),
        description=_("Notes from the learning session"),
        required=False,
    )
    
    effectiveness_rating = schema.Int(
        title=_("Effectiveness Rating"),
        description=_("Self-rated effectiveness of the session (1-5)"),
        required=False,
        min=1,
        max=5,
    )
    
    session_type = schema.Choice(
        title=_("Session Type"),
        description=_("Type of learning session"),
        vocabulary="knowledge.curator.session_types",
        required=False,
        default="self_study",
    )


class IKnowledgeItemMilestone(Interface):
    """Interface for knowledge item milestone achievements."""
    
    milestone_id = schema.TextLine(
        title=_("Milestone ID"),
        description=_("Unique identifier for the milestone"),
        required=True,
    )
    
    knowledge_item_uid = schema.TextLine(
        title=_("Knowledge Item UID"),
        description=_("UID of the related knowledge item"),
        required=True,
    )
    
    milestone_type = schema.Choice(
        title=_("Milestone Type"),
        description=_("Type of milestone achieved"),
        vocabulary="knowledge.curator.milestone_types",
        required=True,
    )
    
    achievement_date = schema.Datetime(
        title=_("Achievement Date"),
        description=_("When the milestone was achieved"),
        required=True,
    )
    
    mastery_level = schema.Float(
        title=_("Mastery Level"),
        description=_("Mastery level when milestone was achieved (0.0-1.0)"),
        required=True,
        min=0.0,
        max=1.0,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("Description of the milestone achievement"),
        required=False,
    )
    
    evidence = schema.Text(
        title=_("Evidence"),
        description=_("Evidence supporting the milestone achievement"),
        required=False,
    )
    
    validation_criteria = schema.Text(
        title=_("Validation Criteria"),
        description=_("Criteria used to validate the milestone achievement"),
        required=False,
    )


@provider(IFormFieldProvider)
class IResearchNote(IKnowledgeObjectBase):
    """Schema for Research Note content type."""

    title = schema.TextLine(
        title=_("Title"),
        required=True,
    )

    description = schema.Text(
        title=_("Description"),
        description=_("Brief description of the research note"),
        required=False,
    )

    content = RichText(
        title=_("Content"),
        description=_("Main content of the research note"),
        required=True,
    )

    tags = schema.List(
        title=_("Tags"),
        description=_("Tags for categorization"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    # Enhanced fields for research
    key_insights = schema.List(
        title=_("Key Insights"),
        description=_("Structured key insights from this research"),
        value_type=schema.Object(schema=IKeyInsight),
        required=False,
        default=[],
    )

    research_method = schema.TextLine(
        title=_("Research Method"),
        description=_("Methodology used for this research"),
        required=False,
    )

    citation_format = schema.Choice(
        title=_("Citation Format"),
        description=_("Citation format to use"),
        vocabulary="knowledge.curator.citation_formats",
        required=False,
        default="APA",
    )

    builds_upon = schema.List(
        title=_("Builds Upon"),
        description=_("UIDs of research this work builds upon"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    contradicts = schema.List(
        title=_("Contradicts"),
        description=_("UIDs of research this work contradicts"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    peer_reviewed = schema.Bool(
        title=_("Peer Reviewed"),
        description=_("Has this research been peer reviewed?"),
        required=False,
        default=False,
    )

    replication_studies = schema.List(
        title=_("Replication Studies"),
        description=_("UIDs of studies that replicate this research"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    # NOTE: ai_summary, connections, embedding_vector are provided by behaviors
    # to avoid duplication conflicts


@provider(IFormFieldProvider)
class ILearningGoal(IKnowledgeObjectBase):
    """Schema for Learning Goal content type."""

    title = schema.TextLine(
        title=_("Title"),
        required=True,
    )

    description = schema.Text(
        title=_("Description"),
        description=_("Detailed description of the learning goal"),
        required=True,
    )

    target_date = schema.Date(
        title=_("Target Date"),
        description=_("Target completion date"),
        required=False,
    )

    priority = schema.Choice(
        title=_("Priority"),
        description=_("Priority level of this goal"),
        vocabulary="knowledge.curator.priority_vocabulary",
        required=False,
        default="medium",
    )

    # Graph-based fields
    starting_knowledge_item = schema.TextLine(
        title=_("Starting Knowledge Item"),
        description=_("UUID of the starting knowledge item for this learning path"),
        required=False,
    )
    
    target_knowledge_items = schema.List(
        title=_("Target Knowledge Items"),
        description=_("List of UUIDs for target knowledge items to master"),
        value_type=schema.TextLine(
            title=_("Knowledge Item UUID"),
        ),
        required=False,
        default=[],
    )
    
    knowledge_item_connections = schema.List(
        title=_("Knowledge Item Connections"),
        description=_("List of connections between knowledge items in this learning path"),
        value_type=schema.Object(
            title=_("Knowledge Item Connection"),
            schema=IKnowledgeItemConnection
        ),
        required=False,
        default=[],
    )
    
    learning_strategy = schema.Choice(
        title=_("Learning Strategy"),
        description=_("Strategy for navigating the knowledge graph"),
        vocabulary="knowledge.curator.learning_strategies",
        required=False,
        default="adaptive",
    )
    
    overall_progress = schema.Float(
        title=_("Overall Progress"),
        description=_("Calculated overall progress across all target items (0.0-1.0)"),
        required=False,
        default=0.0,
        min=0.0,
        max=1.0,
        readonly=True,
    )

    # DEPRECATED: Keeping for backwards compatibility
    progress = schema.Int(
        title=_("Progress (Deprecated)"),
        description=_("Progress percentage (0-100) - DEPRECATED: Use overall_progress instead"),
        required=False,
        default=0,
        min=0,
        max=100,
    )

    # Enhanced fields with structured objects
    milestones = schema.List(
        title=_("Milestones"),
        description=_("Structured milestones to achieve this goal"),
        value_type=schema.Object(schema=ILearningMilestone),
        required=False,
        default=[],
    )

    learning_objectives = schema.List(
        title=_("Learning Objectives"),
        description=_("SMART learning objectives"),
        value_type=schema.Object(schema=ILearningObjective),
        required=False,
        default=[],
    )

    prerequisite_knowledge = schema.List(
        title=_("Prerequisite Knowledge"),
        description=_("Knowledge required before starting this goal"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    assessment_criteria = schema.List(
        title=_("Assessment Criteria"),
        description=_("Criteria for assessing achievement of this goal"),
        value_type=schema.Object(schema=IAssessmentCriterion),
        required=False,
        default=[],
    )

    learning_approach = schema.Text(
        title=_("Learning Approach"),
        description=_("Approach to be taken for learning"),
        required=False,
    )

    estimated_effort = schema.Int(
        title=_("Estimated Effort (hours)"),
        description=_("Estimated hours needed to achieve this goal"),
        required=False,
    )

    competencies = schema.List(
        title=_("Competencies"),
        description=_("Competencies to be developed"),
        value_type=schema.Object(schema=ICompetency),
        required=False,
        default=[],
    )

    related_notes = schema.List(
        title=_("Related Notes"),
        description=_("Research notes related to this goal"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    reflection = schema.Text(
        title=_("Reflection"),
        description=_("Personal reflection on the learning process"),
        required=False,
    )


@provider(IFormFieldProvider)
class IProjectLog(IKnowledgeObjectBase):
    """Schema for Project Log content type."""

    title = schema.TextLine(
        title=_("Title"),
        required=True,
    )

    description = schema.Text(
        title=_("Description"),
        description=_("Project description"),
        required=True,
    )

    start_date = schema.Date(
        title=_("Start Date"),
        description=_("Project start date"),
        required=False,
    )

    status = schema.Choice(
        title=_("Status"),
        description=_("Current status of the project"),
        vocabulary="knowledge.curator.project_status_vocabulary",
        required=False,
        default="planning",
    )

    # Enhanced fields with structured objects
    entries = schema.List(
        title=_("Log Entries"),
        description=_("Structured project log entries"),
        value_type=schema.Object(schema=IProjectLogEntry),
        required=False,
        default=[],
    )

    deliverables = schema.List(
        title=_("Deliverables"),
        description=_("Project deliverables"),
        value_type=schema.Object(schema=IProjectDeliverable),
        required=False,
        default=[],
    )

    project_methodology = schema.TextLine(
        title=_("Project Methodology"),
        description=_("Methodology used for this project"),
        required=False,
    )

    stakeholders = schema.List(
        title=_("Stakeholders"),
        description=_("Project stakeholders"),
        value_type=schema.Object(schema=IStakeholder),
        required=False,
        default=[],
    )

    resources_used = schema.List(
        title=_("Resources Used"),
        description=_("Resources used in this project"),
        value_type=schema.Object(schema=IProjectResource),
        required=False,
        default=[],
    )

    success_metrics = schema.List(
        title=_("Success Metrics"),
        description=_("Metrics for measuring project success"),
        value_type=schema.Object(schema=ISuccessMetric),
        required=False,
        default=[],
    )

    lessons_learned = schema.List(
        title=_("Lessons Learned"),
        description=_("Lessons learned from this project"),
        value_type=schema.Object(schema=ILessonLearned),
        required=False,
        default=[],
    )

    learnings = schema.Text(
        title=_("General Learnings"),
        description=_("General learnings from this project"),
        required=False,
    )

    # Learning Goal Integration Fields
    attached_learning_goal = schema.TextLine(
        title=_("Attached Learning Goal"),
        description=_("UID of the attached Learning Goal"),
        required=True,
    )
    
    knowledge_item_progress = schema.Dict(
        title=_("Knowledge Item Progress"),
        description=_("Progress tracking for Knowledge Items (UID -> mastery level)"),
        key_type=schema.TextLine(
            title=_("Knowledge Item UID"),
            description=_("UID of the Knowledge Item"),
        ),
        value_type=schema.Float(
            title=_("Mastery Level"),
            description=_("Current mastery level (0.0-1.0)"),
            min=0.0,
            max=1.0,
        ),
        required=False,
        default={},
        constraint=validate_knowledge_item_progress_dict,
    )
    
    learning_sessions = schema.List(
        title=_("Learning Sessions"),
        description=_("List of learning sessions for this project"),
        value_type=schema.Object(schema=ILearningSession),
        required=False,
        default=[],
    )
    
    knowledge_item_milestones = schema.List(
        title=_("Knowledge Item Milestones"),
        description=_("List of achieved knowledge item milestones"),
        value_type=schema.Object(schema=IKnowledgeItemMilestone),
        required=False,
        default=[],
    )


@provider(IFormFieldProvider)
class IBookmarkPlus(model.Schema):
    """Schema for BookmarkPlus content type."""

    title = schema.TextLine(
        title=_("Title"),
        required=True,
    )

    url = schema.URI(
        title=_("URL"),
        description=_("The bookmarked URL"),
        required=True,
    )

    tags = schema.List(
        title=_("Tags"),
        description=_("Tags for categorization"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    notes = schema.Text(
        title=_("Notes"),
        description=_("Personal notes about this bookmark"),
        required=False,
    )

    read_status = schema.Choice(
        title=_("Read Status"),
        description=_("Whether you have read this content"),
        vocabulary="knowledge.curator.read_status_vocabulary",
        required=False,
        default="unread",
    )

    importance = schema.Choice(
        title=_("Importance"),
        description=_("How important is this bookmark"),
        vocabulary="knowledge.curator.importance_vocabulary",
        required=False,
        default="medium",
    )

    # NOTE: ai_summary, embedding_vector are provided by behaviors
    # to avoid duplication conflicts


@provider(IFormFieldProvider)
class IKnowledgeItem(model.Schema):
    """Schema for Knowledge Item content type."""

    title = schema.TextLine(
        title=_("Title"),
        description=_("Title of the knowledge item"),
        required=True,
        constraint=validate_title_length,
    )

    description = schema.Text(
        title=_("Description"),
        description=_("A detailed description of the knowledge item"),
        required=True,
        constraint=validate_description_length,
    )

    content = RichText(
        title=_("Content"),
        description=_("Main content of the knowledge item"),
        required=True,
        constraint=validate_content_length,
    )

    knowledge_type = schema.Choice(
        title=_("Knowledge Type"),
        description=_("Type of knowledge according to cognitive taxonomy"),
        vocabulary="knowledge.curator.knowledge_types",
        required=True,
        constraint=validate_knowledge_type,
    )

    atomic_concepts = schema.List(
        title=_("Atomic Concepts"),
        description=_("List of atomic knowledge units contained in this item"),
        value_type=schema.TextLine(
            title=_("Concept"),
            description=_("An atomic concept or knowledge unit"),
        ),
        required=True,
        default=["main_concept"],  # Changed from empty list to have at least one concept
        constraint=validate_atomic_concepts,
    )

    tags = schema.List(
        title=_("Tags"),
        description=_("Tags for categorization"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
        constraint=validate_tags,
    )

    source_url = schema.URI(
        title=_("Source URL"),
        description=_("Original source of the information"),
        required=False,
    )

    embedding_vector = schema.List(
        title=_("Embedding Vector"),
        description=_("AI-generated embedding vector for similarity search"),
        value_type=schema.Float(),
        required=False,
        readonly=True,
        constraint=validate_embedding_vector,
    )

    ai_summary = schema.Text(
        title=_("AI Summary"),
        description=_("AI-generated summary of the content"),
        required=False,
        readonly=True,
    )

    relevance_score = schema.Float(
        title=_("Relevance Score"),
        description=_("AI-calculated relevance score"),
        required=False,
        readonly=True,
        default=0.0,
    )

    attachment = NamedBlobFile(
        title=_("Attachment"),
        description=_("Upload a file attachment"),
        required=False,
    )

    # Learning Integration Fields
    mastery_threshold = schema.Float(
        title=_("Mastery Threshold"),
        description=_("The threshold value (0.0-1.0) that indicates mastery of this knowledge item"),
        required=False,
        default=0.8,
        min=0.0,
        max=1.0,
        constraint=validate_mastery_threshold,
    )

    learning_progress = schema.Float(
        title=_("Learning Progress"),
        description=_("Current learning progress (0.0-1.0) for this knowledge item"),
        required=False,
        default=0.0,
        min=0.0,
        max=1.0,
        readonly=True,
        constraint=validate_learning_progress,
    )

    last_reviewed = schema.Datetime(
        title=_("Last Reviewed"),
        description=_("Timestamp of when this knowledge item was last reviewed"),
        required=False,
    )

    difficulty_level = schema.Choice(
        title=_("Difficulty Level"),
        description=_("The difficulty level of this knowledge item for adaptive learning"),
        vocabulary="knowledge.curator.difficulty_levels",
        required=False,
        default="intermediate",
        constraint=validate_difficulty_level,
    )

    # Relationship fields for knowledge item dependencies
    directives.widget('prerequisite_items', RelatedItemsFieldWidget)
    prerequisite_items = schema.List(
        title=_("Prerequisite Knowledge Items"),
        description=_("Knowledge items that should be understood before this one"),
        value_type=schema.Choice(
            title=_("Knowledge Item"),
            source=CatalogSource(portal_type='KnowledgeItem'),
        ),
        required=False,
        default=[],
        constraint=validate_uid_references_list,
    )

    directives.widget('enables_items', RelatedItemsFieldWidget)
    enables_items = schema.List(
        title=_("Enables Knowledge Items"),
        description=_("Knowledge items that this item enables or unlocks"),
        value_type=schema.Choice(
            title=_("Knowledge Item"),
            source=CatalogSource(portal_type='KnowledgeItem'),
        ),
        required=False,
        default=[],
        constraint=validate_uid_references_list,
    )
    
    # Invariants for cross-field validation
    @invariant
    def validate_prerequisite_enables_consistency(data):
        """Ensure prerequisite and enables lists don't overlap."""
        validate_prerequisite_enables_consistency(data)
    
    @invariant
    def validate_mastery_threshold_progress_consistency(data):
        """Ensure learning progress and mastery threshold are consistent."""
        validate_mastery_threshold_progress_consistency(data)


# Additional interfaces for the system


class IKnowledgeGraph(Interface):
    """Interface for knowledge graph functionality."""

    def add_connection(source_uid, target_uid, relationship_type="related"):
        """Add a connection between two content items."""

    def remove_connection(source_uid, target_uid):
        """Remove a connection between two content items."""

    def get_connections(uid):
        """Get all connections for a content item."""

    def get_related_items(uid, max_items=10):
        """Get related items based on connections and similarity."""

    def get_prerequisite_graph(uid):
        """Get the full prerequisite dependency graph for a knowledge item.
        
        Returns a dict with 'nodes' and 'edges' for visualization.
        """

    def get_learning_path(start_uid, end_uid):
        """Calculate the optimal learning path between two knowledge items.
        
        Returns a list of knowledge item UIDs representing the path.
        """

    def validate_no_circular_dependencies():
        """Validate that there are no circular dependencies in the knowledge graph.
        
        Returns a dict with 'valid' (bool) and 'cycles' (list of cycles found).
        """


class IVectorSearch(Interface):
    """Interface for vector-based similarity search."""

    def generate_embedding(text):
        """Generate embedding vector for text."""

    def update_embedding(uid, embedding):
        """Update embedding for content item."""

    def find_similar(embedding, max_results=10):
        """Find similar content based on embedding."""


class IAIService(Interface):
    """Interface for AI service utilities."""

    def generate_embedding(text):
        """Generate embedding vector for given text."""

    def generate_summary(text, max_length=150):
        """Generate AI summary for given text."""

    def calculate_similarity(vector1, vector2):
        """Calculate similarity between two embedding vectors."""

    def search_similar(query, limit=10):
        """Search for similar content based on query."""


class IAIEnhanced(Interface):
    """Interface for AI enhancement features."""

    def generate_summary(content):
        """Generate AI summary of content."""

    def extract_key_insights(content):
        """Extract key insights from content."""

    def suggest_tags(content):
        """Suggest tags based on content analysis."""

    def analyze_sentiment(content):
        """Analyze sentiment of content."""


# New interfaces for structured objects (Task 1 & 2)

class ILearningMilestone(Interface):
    """Interface for a learning milestone."""
    
    id = schema.TextLine(
        title=_("Milestone ID"),
        description=_("Unique identifier for the milestone"),
        required=True,
    )
    
    title = schema.TextLine(
        title=_("Title"),
        description=_("Title of the milestone"),
        required=True,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("Detailed description of the milestone"),
        required=False,
    )
    
    target_date = schema.Date(
        title=_("Target Date"),
        description=_("Target completion date for the milestone"),
        required=False,
    )
    
    completed = schema.Bool(
        title=_("Completed"),
        description=_("Whether the milestone is completed"),
        required=False,
        default=False,
    )
    
    completed_date = schema.Datetime(
        title=_("Completed Date"),
        description=_("Date when the milestone was completed"),
        required=False,
    )
    
    effort_hours = schema.Float(
        title=_("Effort Hours"),
        description=_("Estimated effort in hours"),
        required=False,
    )
    
    notes = schema.Text(
        title=_("Notes"),
        description=_("Additional notes about the milestone"),
        required=False,
    )


class ILearningObjective(Interface):
    """Interface for a learning objective."""
    
    id = schema.TextLine(
        title=_("Objective ID"),
        description=_("Unique identifier for the objective"),
        required=True,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("What should be learned"),
        required=True,
    )
    
    success_criteria = schema.Text(
        title=_("Success Criteria"),
        description=_("How to measure success"),
        required=False,
    )
    
    category = schema.Choice(
        title=_("Category"),
        description=_("Type of learning objective"),
        vocabulary="knowledge.curator.objective_category_vocabulary",
        required=False,
    )
    
    priority = schema.Int(
        title=_("Priority"),
        description=_("Priority order (1-10)"),
        required=False,
        min=1,
        max=10,
    )


class IProjectLogEntry(Interface):
    """Interface for a project log entry."""
    
    id = schema.TextLine(
        title=_("Entry ID"),
        description=_("Unique identifier for the entry"),
        required=True,
    )
    
    timestamp = schema.Datetime(
        title=_("Timestamp"),
        description=_("When the entry was created"),
        required=True,
    )
    
    title = schema.TextLine(
        title=_("Title"),
        description=_("Entry title"),
        required=True,
    )
    
    content = RichText(
        title=_("Content"),
        description=_("Detailed entry content"),
        required=True,
    )
    
    tags = schema.List(
        title=_("Tags"),
        description=_("Tags for categorization"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )
    
    attachments = schema.List(
        title=_("Attachments"),
        description=_("File attachments"),
        value_type=NamedBlobFile(),
        required=False,
        default=[],
    )
    
    entry_type = schema.Choice(
        title=_("Entry Type"),
        description=_("Type of log entry"),
        vocabulary="knowledge.curator.entry_type_vocabulary",
        required=False,
    )
    
    modified = schema.Datetime(
        title=_("Last Modified"),
        description=_("When the entry was last modified"),
        required=False,
    )
    
    effort_hours = schema.Float(
        title=_("Effort Hours"),
        description=_("Hours spent on this work"),
        required=False,
    )


class IProjectDeliverable(Interface):
    """Interface for a project deliverable."""
    
    id = schema.TextLine(
        title=_("Deliverable ID"),
        description=_("Unique identifier for the deliverable"),
        required=True,
    )
    
    title = schema.TextLine(
        title=_("Title"),
        description=_("Deliverable title"),
        required=True,
    )
    
    description = schema.Text(
        title=_("Description"),
        description=_("What this deliverable includes"),
        required=False,
    )
    
    status = schema.Choice(
        title=_("Status"),
        description=_("Current status of the deliverable"),
        vocabulary="knowledge.curator.deliverable_status_vocabulary",
        required=False,
    )
    
    due_date = schema.Date(
        title=_("Due Date"),
        description=_("When the deliverable is due"),
        required=False,
    )
    
    completed_date = schema.Date(
        title=_("Completed Date"),
        description=_("When the deliverable was completed"),
        required=False,
    )
    
    artifacts = schema.List(
        title=_("Artifacts"),
        description=_("Files or links to deliverable artifacts"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )
    
    acceptance_criteria = schema.Text(
        title=_("Acceptance Criteria"),
        description=_("Criteria for accepting the deliverable"),
        required=False,
    )
