// Knowledge Curator Components
export { default as ResearchNoteView } from './ResearchNote/View';
export { default as ResearchNoteEdit } from './ResearchNote/Edit';
export { default as LearningGoalView } from './LearningGoal/View';
export { default as LearningGoalEdit } from './LearningGoal/Edit';
export { default as ProjectLogView } from './ProjectLog/View';
export { default as ProjectLogEdit } from './ProjectLog/Edit';
export { default as BookmarkPlusView } from './BookmarkPlus/View';
export { default as BookmarkPlusEdit } from './BookmarkPlus/Edit';
export { default as KnowledgeItemView } from './KnowledgeItem/View';
export { default as KnowledgeItemEdit } from './KnowledgeItem/Edit';

// Widgets
export { default as AIFeaturesWidget } from './Widgets/AIFeaturesWidget';
export { default as KnowledgeGraphWidget } from './Widgets/KnowledgeGraphWidget';
export { default as SpacedRepetitionWidget } from './Widgets/SpacedRepetitionWidget';
export { default as MilestonesWidget } from './Widgets/MilestonesWidget';
export { default as TagsWidget } from './Widgets/TagsWidget';

// ResearchNote Components
export { default as StructuredInsightEditor } from './ResearchNote/StructuredInsightEditor';
export { default as CitationManager } from './ResearchNote/CitationManager';
export { default as ResearchLineageVisualizer } from './ResearchNote/ResearchLineageVisualizer';

// LearningGoal Components
export { default as MilestoneTracker } from './LearningGoal/MilestoneTracker';
export { default as SMARTObjectiveEditor } from './LearningGoal/SMARTObjectiveEditor';
export { default as CompetencyDashboard } from './LearningGoal/CompetencyDashboard';

// Structured Object Editors
export { default as KeyInsightEditor } from './StructuredObjects/KeyInsightEditor';
export { default as LearningMilestoneEditor } from './StructuredObjects/LearningMilestoneEditor';
export { default as ProjectLogEntryEditor } from './StructuredObjects/ProjectLogEntryEditor';
export { default as AnnotationEditor } from './StructuredObjects/AnnotationEditor';

// Shared Components
export { default as BaseStructuredEditor } from './shared/BaseStructuredEditor';

// Analytics Components
export { 
  LearningProgressDashboard,
  CompetencyMatrix,
  KnowledgeGapAnalysis,
  LearningVelocityChart,
  EnhancedKnowledgeGraph
} from './Analytics'; 