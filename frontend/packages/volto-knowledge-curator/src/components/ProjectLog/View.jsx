import React from 'react';
import { Container, Segment, Header, Label, List, Icon } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const ProjectLogView = ({ content }) => {
  const {
    title,
    description,
    start_date,
    status,
    entries = [],
    deliverables = [],
    learnings,
    created,
    modified,
  } = content;

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'green';
      case 'active': return 'blue';
      case 'paused': return 'yellow';
      case 'archived': return 'grey';
      case 'planning': return 'orange';
      default: return 'grey';
    }
  };

  return (
    <Container>
      <Header as="h1">
        {title}
        <Label color={getStatusColor(status)} size="small">
          {status}
        </Label>
      </Header>
      
      {description && (
        <Segment>
          <Header as="h3">Description</Header>
          <p>{description}</p>
        </Segment>
      )}

      {start_date && (
        <Segment>
          <Header as="h3">Start Date</Header>
          <Icon name="calendar" />
          <FormattedDate value={start_date} />
        </Segment>
      )}

      {deliverables && deliverables.length > 0 && (
        <Segment>
          <Header as="h3">Deliverables</Header>
          <List bulleted>
            {deliverables.map((deliverable, index) => (
              <List.Item key={index}>{deliverable}</List.Item>
            ))}
          </List>
        </Segment>
      )}

      {entries && entries.length > 0 && (
        <Segment>
          <Header as="h3">Log Entries</Header>
          <List divided>
            {entries.map((entry, index) => (
              <List.Item key={index}>
                <List.Content>
                  <List.Header>{entry.title || `Entry ${index + 1}`}</List.Header>
                  <List.Description>
                    {entry.content || entry}
                    {entry.timestamp && (
                      <small style={{ display: 'block', marginTop: '5px' }}>
                        <FormattedDate value={entry.timestamp} />
                      </small>
                    )}
                  </List.Description>
                </List.Content>
              </List.Item>
            ))}
          </List>
        </Segment>
      )}

      {learnings && (
        <Segment>
          <Header as="h3">Learnings</Header>
          <p>{learnings}</p>
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

export default ProjectLogView; 