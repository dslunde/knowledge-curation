import React from 'react';
import { Segment, Header, Label, Icon } from 'semantic-ui-react';

const AIFeaturesWidget = ({ value, field, title }) => {
  if (!value) return null;

  return (
    <Segment color="blue">
      <Header as="h4">
        <Icon name="brain" />
        {title || 'AI Features'}
      </Header>
      
      {value.ai_summary && (
        <div style={{ marginBottom: '10px' }}>
          <strong>AI Summary:</strong>
          <p>{value.ai_summary}</p>
        </div>
      )}
      
      {value.ai_tags && value.ai_tags.length > 0 && (
        <div style={{ marginBottom: '10px' }}>
          <strong>AI Suggested Tags:</strong>
          <div>
            {value.ai_tags.map((tag, index) => (
              <Label key={index} color="purple" size="small">
                {tag}
              </Label>
            ))}
          </div>
        </div>
      )}
      
      {value.sentiment_score && (
        <div style={{ marginBottom: '10px' }}>
          <strong>Sentiment Score:</strong> {value.sentiment_score.toFixed(2)}
        </div>
      )}
      
      {value.readability_score && (
        <div>
          <strong>Readability Score:</strong> {value.readability_score.toFixed(1)}
        </div>
      )}
    </Segment>
  );
};

export default AIFeaturesWidget; 