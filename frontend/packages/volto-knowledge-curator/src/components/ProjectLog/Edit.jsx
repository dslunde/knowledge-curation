import React, { useCallback } from 'react';
import { Container, Segment, Tab } from 'semantic-ui-react';
import { Form } from '@plone/volto/components';
import { injectIntl } from 'react-intl';
import EntriesManager from './EntriesManager';

const ProjectLogEdit = (props) => {
  const { data, onChangeField, intl } = props;

  const handleEntriesChange = useCallback((entries) => {
    onChangeField('entries', entries);
  }, [onChangeField]);

  // Create a custom schema that includes our structured editors
  const customSchema = {
    ...props.schema,
    properties: {
      ...props.schema.properties,
      // Hide the raw fields that are managed by custom components
      entries: { ...props.schema.properties.entries, widget: 'hidden' },
      deliverables: { ...props.schema.properties.deliverables, widget: 'hidden' },
      stakeholders: { ...props.schema.properties.stakeholders, widget: 'hidden' },
      resources_used: { ...props.schema.properties.resources_used, widget: 'hidden' },
      success_metrics: { ...props.schema.properties.success_metrics, widget: 'hidden' },
      lessons_learned: { ...props.schema.properties.lessons_learned, widget: 'hidden' },
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
      menuItem: 'Log Entries',
      render: () => (
        <Tab.Pane>
          <EntriesManager
            value={data.entries || []}
            onChange={handleEntriesChange}
          />
        </Tab.Pane>
      ),
    },
    // Additional tabs for deliverables, stakeholders, etc. can be added here
    // following the same pattern as ResearchNote and LearningGoal
  ];

  return (
    <Container>
      <Segment>
        <Tab panes={panes} />
      </Segment>
    </Container>
  );
};

export default injectIntl(ProjectLogEdit); 