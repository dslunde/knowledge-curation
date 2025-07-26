import {
  ResearchNoteView,
  ResearchNoteEdit,
  LearningGoalView,
  LearningGoalEdit,
  ProjectLogView,
  ProjectLogEdit,
  BookmarkPlusView,
  BookmarkPlusEdit,
  KnowledgeItemView,
  KnowledgeItemEdit,
  HomePage,
} from './components';

const applyConfig = (config) => {
  config.settings.isMultilingual = false;
  config.settings.supportedLanguages = ['en'];
  config.settings.defaultLanguage = 'en';

  // Register Knowledge Curator content type views
  config.views = {
    ...config.views,
    contentTypesViews: {
      ...config.views.contentTypesViews,
      ResearchNote: ResearchNoteView,
      LearningGoal: LearningGoalView,
      ProjectLog: ProjectLogView,
      BookmarkPlus: BookmarkPlusView,
      KnowledgeItem: KnowledgeItemView,
      // Override the Plone Site homepage
      'Plone Site': HomePage,
    },
    layoutViews: {
      ...config.views.layoutViews,
      ResearchNote: ResearchNoteView,
      LearningGoal: LearningGoalView,
      ProjectLog: ProjectLogView,
      BookmarkPlus: BookmarkPlusView,
      KnowledgeItem: KnowledgeItemView,
      // Override the Plone Site homepage in layout views too
      'Plone Site': HomePage,
    },
  };

  // Register edit components for content types
  config.views.contentTypesEdit = {
    ...config.views.contentTypesEdit,
    ResearchNote: ResearchNoteEdit,
    LearningGoal: LearningGoalEdit,
    ProjectLog: ProjectLogEdit,
    BookmarkPlus: BookmarkPlusEdit,
    KnowledgeItem: KnowledgeItemEdit,
  };

  return config;
};

export default applyConfig;
