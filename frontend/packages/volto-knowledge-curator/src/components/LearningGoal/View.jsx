import React from 'react';
import { Container, Segment, Header, Label, Progress, List, Icon } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const LearningGoalView = ({ content }) => {
  const {
    title,
    description,
    target_date,
    priority,
    progress = 0,
    milestones = [],
    related_notes = [],
    reflection,
    created,
    modified,
  } = content;

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'grey';
    }
  };

  return (
    <Container>
      <Header as="h1">
        {title}
        <Label color={getPriorityColor(priority)} size="small">
          {priority} priority
        </Label>
      </Header>
      
      {description && (
        <Segment>
          <Header as="h3">Description</Header>
          <p>{description}</p>
        </Segment>
      )}

      <Segment>
        <Header as="h3">Progress</Header>
        <Progress percent={progress} indicating>
          {progress}% Complete
        </Progress>
      </Segment>

      {target_date && (
        <Segment>
          <Header as="h3">Target Date</Header>
          <Icon name="calendar" />
          <FormattedDate value={target_date} />
        </Segment>
      )}

      {milestones && milestones.length > 0 && (
        <Segment>
          <Header as="h3">Milestones</Header>
          <List>
            {milestones.map((milestone, index) => (
              <List.Item key={index}>
                <Icon name="flag" />
                <List.Content>
                  <List.Header>{milestone.title || milestone}</List.Header>
                  {milestone.description && (
                    <List.Description>{milestone.description}</List.Description>
                  )}
                </List.Content>
              </List.Item>
            ))}
          </List>
        </Segment>
      )}

      {reflection && (
        <Segment>
          <Header as="h3">Reflection</Header>
          <p>{reflection}</p>
        </Segment>
      )}

      <Segment>
        <small>
          Created: <FormattedDate value={created} /> | 
          Modified: <FormattedDate value={modified} />
        </small>
      </Segment>
    </Container>
  );
};

export default LearningGoalView; 