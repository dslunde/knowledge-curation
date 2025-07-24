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
    },
    layoutViews: {
      ...config.views.layoutViews,
      ResearchNote: ResearchNoteView,
      LearningGoal: LearningGoalView,
      ProjectLog: ProjectLogView,
      BookmarkPlus: BookmarkPlusView,
      KnowledgeItem: KnowledgeItemView,
    },
  };

  return config;
};

export default applyConfig;
