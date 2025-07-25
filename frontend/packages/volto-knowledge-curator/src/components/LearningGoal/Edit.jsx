import React, { useCallback } from 'react';
import { Container, Segment, Tab } from 'semantic-ui-react';
import { Form } from '@plone/volto/components';
import { injectIntl } from 'react-intl';
import MilestoneTracker from './MilestoneTracker';
import SMARTObjectiveEditor from './SMARTObjectiveEditor';
import CompetencyDashboard from './CompetencyDashboard';

const LearningGoalEdit = (props) => {
  const { data, onChangeField, intl } = props;

  const handleMilestonesChange = useCallback((milestones) => {
    onChangeField('milestones', milestones);
    // Auto-calculate overall progress based on milestones
    if (milestones.length > 0) {
      const totalProgress = milestones.reduce((sum, m) => sum + (m.progress_percentage || 0), 0);
      const avgProgress = Math.round(totalProgress / milestones.length);
      onChangeField('progress', avgProgress);
    }
  }, [onChangeField]);

  const handleObjectivesChange = useCallback((objectives) => {
    onChangeField('learning_objectives', objectives);
  }, [onChangeField]);

  const handleCompetenciesChange = useCallback((competencies) => {
    onChangeField('competencies', competencies);
  }, [onChangeField]);

  // Create a custom schema that includes our structured editors
  const customSchema = {
    ...props.schema,
    properties: {
      ...props.schema.properties,
      // Hide the raw fields that are managed by custom components
      milestones: { ...props.schema.properties.milestones, widget: 'hidden' },
      learning_objectives: { ...props.schema.properties.learning_objectives, widget: 'hidden' },
      competencies: { ...props.schema.properties.competencies, widget: 'hidden' },
    },
  };

  const panes = [
    {
      menuItem: 'Basic Information',
      render: () => (
        <Tab.Pane>
          <Form {...props} schema={customSchema} />
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Milestones',
      render: () => (
        <Tab.Pane>
          <MilestoneTracker
            value={data.milestones || []}
            onChange={handleMilestonesChange}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'SMART Objectives',
      render: () => (
        <Tab.Pane>
          <SMARTObjectiveEditor
            value={data.learning_objectives || []}
            onChange={handleObjectivesChange}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Competencies',
      render: () => (
        <Tab.Pane>
          <CompetencyDashboard
            value={data.competencies || []}
            onChange={handleCompetenciesChange}
          />
        </Tab.Pane>
      ),
    },
  ];

  return (
    <Container>
      <Segment>
        <Tab panes={panes} />
      </Segment>
    </Container>
  );
};

export default injectIntl(LearningGoalEdit); 