import React from 'react';
import { Segment, Header, List, Icon, Progress } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const MilestonesWidget = ({ value, field, title }) => {
  if (!value || !Array.isArray(value) || value.length === 0) return null;

  const completedCount = value.filter(m => m.completed).length;
  const progressPercent = (completedCount / value.length) * 100;

  return (
    <Segment color="green">
      <Header as="h4">
        <Icon name="flag" />
        {title || 'Milestones'}
      </Header>
      
      <Progress percent={progressPercent} size="small" indicating>
        {completedCount}/{value.length} completed
      </Progress>
      
      <List divided>
        {value.map((milestone, index) => (
          <List.Item key={index}>
            <Icon 
              name={milestone.completed ? 'check circle' : 'circle outline'} 
              color={milestone.completed ? 'green' : 'grey'}
            />
            <List.Content>
              <List.Header style={{ 
                textDecoration: milestone.completed ? 'line-through' : 'none' 
              }}>
                {milestone.title || `Milestone ${index + 1}`}
              </List.Header>
              {milestone.description && (
                <List.Description>{milestone.description}</List.Description>
              )}
              {milestone.target_date && (
                <List.Description>
                  <small>
                    <Icon name="calendar" />
                    Due: <FormattedDate value={milestone.target_date} />
                  </small>
                </List.Description>
              )}
            </List.Content>
          </List.Item>
        ))}
      </List>
    </Segment>
  );
};

export default MilestonesWidget; 