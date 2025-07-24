import {
  ResearchNoteView,
  ResearchNoteEdit,
  LearningGoalView,
  LearningGoalEdit,
  ProjectLogView,
  ProjectLogEdit,
  BookmarkPlusView,
  BookmarkPlusEdit,
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
    },
    layoutViews: {
      ...config.views.layoutViews,
      ResearchNote: ResearchNoteView,
      LearningGoal: LearningGoalView,
      ProjectLog: ProjectLogView,
      BookmarkPlus: BookmarkPlusView,
    },
  };

  // Register edit forms
  config.widgets = {
    ...config.widgets,
    views: {
      ...config.widgets.views,
      ResearchNote: ResearchNoteEdit,
      LearningGoal: LearningGoalEdit,
      ProjectLog: ProjectLogEdit,
      BookmarkPlus: BookmarkPlusEdit,
    },
  };

  return config;
};

export default applyConfig;
