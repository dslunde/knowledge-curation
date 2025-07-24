import React from 'react';
import { Segment, Header, Progress, Icon, Label } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const SpacedRepetitionWidget = ({ value, field, title }) => {
  if (!value || !value.sr_enabled) return null;

  const getUrgencyColor = (nextReview) => {
    if (!nextReview) return 'blue';
    const now = new Date();
    const reviewDate = new Date(nextReview);
    const daysUntil = Math.ceil((reviewDate - now) / (1000 * 60 * 60 * 24));
    
    if (daysUntil < 0) return 'red'; // overdue
    if (daysUntil === 0) return 'orange'; // due today
    if (daysUntil <= 3) return 'yellow'; // due soon
    return 'green'; // not due yet
  };

  return (
    <Segment color="purple">
      <Header as="h4">
        <Icon name="refresh" />
        {title || 'Spaced Repetition'}
      </Header>
      
      {value.retention_score && (
        <div style={{ marginBottom: '10px' }}>
          <strong>Retention Score:</strong>
          <Progress 
            percent={value.retention_score * 100} 
            size="small" 
            color={value.retention_score > 0.7 ? 'green' : 'yellow'}
          />
        </div>
      )}
      
      <div style={{ marginBottom: '10px' }}>
        <Label size="small">
          <Icon name="repeat" />
          {value.repetitions || 0} reviews
        </Label>
        
        <Label size="small" color={getUrgencyColor(value.next_review)}>
          <Icon name="calendar" />
          Next: {value.next_review ? (
            <FormattedDate value={value.next_review} />
          ) : 'Not scheduled'}
        </Label>
      </div>
      
      {value.average_quality && (
        <div>
          <small>
            <strong>Average Quality:</strong> {value.average_quality.toFixed(1)}/5.0
          </small>
        </div>
      )}
    </Segment>
  );
};

export default SpacedRepetitionWidget; 