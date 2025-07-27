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
export { default as KnowledgeContainerView } from './KnowledgeContainer/View';
export { default as KnowledgeContainerEdit } from './KnowledgeContainer/Edit';

// Views
export { default as KnowledgeItemsView } from './Views/KnowledgeItemsView';

// Homepage Components
export { default as HomePage } from './Homepage/HomePage';
export { default as KnowledgeItemCarousel } from './Homepage/KnowledgeItemCarousel';
export { default as KnowledgeContainerCarousel } from './Homepage/KnowledgeContainerCarousel';
export { default as HeroSection } from './Homepage/HeroSection';

// Advanced Search Components
export { 
  AdvancedSearchPage,
  SearchInput,
  SearchResults,
  SearchFilters,
  SearchWidget,
  SimilarContentFinder,
  SearchSuggestions,
  SearchHistory,
  SearchAnalytics
} from './Search';

// Blocks
export { default as KnowledgeItemsBlock } from './Blocks/KnowledgeItemsBlock';

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

// KnowledgeContainer Components
export { default as ContentCollectionManager } from './KnowledgeContainer/ContentCollectionManager';
export { default as OrganizationStructureEditor } from './KnowledgeContainer/OrganizationStructureEditor';
export { default as SharingPermissionsManager } from './KnowledgeContainer/SharingPermissionsManager';
export { default as ExportOptionsManager } from './KnowledgeContainer/ExportOptionsManager';
export { default as ContainerAnalytics } from './KnowledgeContainer/ContainerAnalytics';

// Structured Object Editors
export { default as KeyInsightEditor } from './StructuredObjects/KeyInsightEditor';
export { default as LearningMilestoneEditor } from './StructuredObjects/LearningMilestoneEditor';
export { default as ProjectLogEntryEditor } from './StructuredObjects/ProjectLogEntryEditor';
export { default as AnnotationEditor } from './StructuredObjects/AnnotationEditor';

// Shared Components
export { default as BaseStructuredEditor } from './shared/BaseStructuredEditor';
export { default as ContentDeleteAction } from './shared/ContentDeleteAction';
export { default as DeleteConfirmationModal } from './shared/DeleteConfirmationModal';

// Analytics Components
export { 
  LearningProgressDashboard,
  CompetencyMatrix,
  KnowledgeGapAnalysis,
  LearningVelocityChart,
  EnhancedKnowledgeGraph
} from './Analytics'; 