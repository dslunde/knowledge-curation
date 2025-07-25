import React, { useState } from 'react';
import {
  Container,
  Header,
  Icon,
  Tab,
  Segment
} from 'semantic-ui-react';
import LearningProgressDashboard from './LearningProgressDashboard';
import CompetencyMatrix from './CompetencyMatrix';
import KnowledgeGapAnalysis from './KnowledgeGapAnalysis';
import LearningVelocityChart from './LearningVelocityChart';
import EnhancedKnowledgeGraph from './EnhancedKnowledgeGraph';

// Sample data for demonstration
const sampleLearningGoals = [
  {
    id: 'goal-1',
    title: 'Master React Development',
    category: 'Technical',
    priority: 'high',
    milestones: [
      { id: 'm1', title: 'Learn React Hooks', status: 'completed', completion_date: '2024-01-15T10:00:00Z' },
      { id: 'm2', title: 'Build Component Library', status: 'completed', completion_date: '2024-01-20T10:00:00Z' },
      { id: 'm3', title: 'Master State Management', status: 'in_progress' },
      { id: 'm4', title: 'Learn React Testing', status: 'pending' }
    ]
  },
  {
    id: 'goal-2',
    title: 'Data Science Fundamentals',
    category: 'Technical',
    priority: 'medium',
    milestones: [
      { id: 'm5', title: 'Statistics Basics', status: 'completed', completion_date: '2024-01-10T10:00:00Z' },
      { id: 'm6', title: 'Python for Data Science', status: 'completed', completion_date: '2024-01-18T10:00:00Z' },
      { id: 'm7', title: 'Machine Learning Intro', status: 'pending' }
    ]
  }
];

const sampleCompetencies = [
  { id: 'c1', name: 'JavaScript', description: 'Core JS and ES6+', level: 'advanced', category: 'Programming' },
  { id: 'c2', name: 'React', description: 'React framework', level: 'intermediate', category: 'Frameworks' },
  { id: 'c3', name: 'Python', description: 'Python programming', level: 'intermediate', category: 'Programming' },
  { id: 'c4', name: 'Data Analysis', description: 'Statistical analysis', level: 'beginner', category: 'Data Science' },
  { id: 'c5', name: 'SQL', description: 'Database queries', level: 'advanced', category: 'Databases' },
  { id: 'c6', name: 'Docker', description: 'Containerization', level: 'novice', category: 'DevOps' }
];

const sampleKnowledgeGaps = [
  {
    id: 'gap-1',
    gap_description: 'Need to understand advanced React patterns like render props and compound components',
    importance: 'high',
    suggested_topics: ['React Patterns', 'Advanced React', 'Component Design'],
    confidence: 0.85,
    category: 'React'
  },
  {
    id: 'gap-2',
    gap_description: 'Lacking knowledge in machine learning algorithms and their practical applications',
    importance: 'critical',
    suggested_topics: ['ML Algorithms', 'Scikit-learn', 'TensorFlow Basics'],
    confidence: 0.92,
    category: 'Data Science'
  },
  {
    id: 'gap-3',
    gap_description: 'Need to improve understanding of microservices architecture',
    importance: 'medium',
    suggested_topics: ['Microservices', 'API Design', 'Service Mesh'],
    confidence: 0.78,
    category: 'Architecture'
  }
];

const sampleNodes = [
  { id: 'node-1', title: 'React Hooks', type: 'knowledge_item', centrality_score: 0.8 },
  { id: 'node-2', title: 'State Management', type: 'knowledge_item', centrality_score: 0.7 },
  { id: 'node-3', title: 'Component Patterns', type: 'research_note', centrality_score: 0.6 },
  { id: 'node-4', title: 'Master React', type: 'learning_goal', centrality_score: 0.9 },
  { id: 'node-5', title: 'Python Data Science', type: 'knowledge_item', centrality_score: 0.5 },
  { id: 'node-6', title: 'Machine Learning', type: 'research_note', centrality_score: 0.7 }
];

const sampleRelationships = [
  {
    id: 'rel-1',
    source_uid: 'node-1',
    target_uid: 'node-2',
    relationship_type: 'related',
    strength: 0.8,
    confidence: 0.9
  },
  {
    id: 'rel-2',
    source_uid: 'node-1',
    target_uid: 'node-4',
    relationship_type: 'supports',
    strength: 0.9,
    confidence: 0.95
  },
  {
    id: 'rel-3',
    source_uid: 'node-3',
    target_uid: 'node-4',
    relationship_type: 'derived',
    strength: 0.7,
    confidence: 0.85
  },
  {
    id: 'rel-4',
    source_uid: 'node-5',
    target_uid: 'node-6',
    relationship_type: 'prerequisite',
    strength: 0.9,
    confidence: 0.9
  }
];

const sampleMilestones = [
  ...sampleLearningGoals.flatMap(goal => 
    goal.milestones.map(m => ({ ...m, category: goal.category }))
  )
];

const AnalyticsDashboard = () => {
  const panes = [
    {
      menuItem: { key: 'progress', icon: 'chart line', content: 'Learning Progress' },
      render: () => (
        <Tab.Pane>
          <LearningProgressDashboard 
            learningGoals={sampleLearningGoals}
            dateRange={30}
          />
        </Tab.Pane>
      )
    },
    {
      menuItem: { key: 'competency', icon: 'th', content: 'Competency Matrix' },
      render: () => (
        <Tab.Pane>
          <CompetencyMatrix 
            competencies={sampleCompetencies}
            timeRange="current"
          />
        </Tab.Pane>
      )
    },
    {
      menuItem: { key: 'gaps', icon: 'search', content: 'Knowledge Gaps' },
      render: () => (
        <Tab.Pane>
          <KnowledgeGapAnalysis 
            knowledgeGaps={sampleKnowledgeGaps}
            learningResources={[
              { id: 'res-1', title: 'React Advanced Patterns Course', type: 'Course' },
              { id: 'res-2', title: 'ML Fundamentals Book', type: 'Book' },
              { id: 'res-3', title: 'Microservices Tutorial', type: 'Tutorial' }
            ]}
            onGapUpdate={(id, updates) => console.log('Update gap:', id, updates)}
            onResourceLink={(gapId, resourceIds) => console.log('Link resources:', gapId, resourceIds)}
          />
        </Tab.Pane>
      )
    },
    {
      menuItem: { key: 'velocity', icon: 'tachometer alternate', content: 'Learning Velocity' },
      render: () => (
        <Tab.Pane>
          <LearningVelocityChart 
            milestones={sampleMilestones}
            timeFrame="month"
          />
        </Tab.Pane>
      )
    },
    {
      menuItem: { key: 'graph', icon: 'sitemap', content: 'Knowledge Graph' },
      render: () => (
        <Tab.Pane>
          <EnhancedKnowledgeGraph 
            nodes={sampleNodes}
            relationships={sampleRelationships}
            onNodeClick={(node) => console.log('Node clicked:', node)}
            onRelationshipEdit={(rel) => console.log('Edit relationship:', rel)}
            onRelationshipAdd={(rel) => console.log('Add relationship:', rel)}
            onRelationshipDelete={(id) => console.log('Delete relationship:', id)}
            enableEditing={true}
            height="600px"
          />
        </Tab.Pane>
      )
    }
  ];

  return (
    <Container>
      <Segment basic>
        <Header as="h1">
          <Icon name="dashboard" />
          <Header.Content>
            Learning Analytics Dashboard
            <Header.Subheader>
              Comprehensive analytics and visualizations for your learning journey
            </Header.Subheader>
          </Header.Content>
        </Header>
      </Segment>

      <Tab panes={panes} />
    </Container>
  );
};

export default AnalyticsDashboard;