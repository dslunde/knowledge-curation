import React from 'react';
import { Container, Segment, Header, Label, List, Icon } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const ResearchNoteView = ({ content }) => {
  const {
    title,
    description,
    text,
    tags = [],
    source_url,
    key_insights = [],
    ai_summary,
    ai_tags = [],
    sentiment_score,
    created,
    modified,
  } = content;

  return (
    <Container>
      <Header as="h1">{title}</Header>
      
      {description && (
        <Segment>
          <Header as="h3">Description</Header>
          <p>{description}</p>
        </Segment>
      )}

      {text && (
        <Segment>
          <Header as="h3">Content</Header>
          <div dangerouslySetInnerHTML={{ __html: text.data }} />
        </Segment>
      )}

      {source_url && (
        <Segment>
          <Header as="h3">Source</Header>
          <a href={source_url} target="_blank" rel="noopener noreferrer">
            <Icon name="external" />
            {source_url}
          </a>
        </Segment>
      )}

      {key_insights && key_insights.length > 0 && (
        <Segment>
          <Header as="h3">Key Insights</Header>
          <List bulleted>
            {key_insights.map((insight, index) => (
              <List.Item key={index}>{insight}</List.Item>
            ))}
          </List>
        </Segment>
      )}

      {ai_summary && (
        <Segment color="blue">
          <Header as="h3">
            <Icon name="brain" />
            AI Summary
          </Header>
          <p>{ai_summary}</p>
        </Segment>
      )}

      <Segment>
        <Header as="h3">Tags</Header>
        <div>
          {tags.map((tag, index) => (
            <Label key={`tag-${index}`} color="teal">
              {tag}
            </Label>
          ))}
          {ai_tags.map((tag, index) => (
            <Label key={`ai-tag-${index}`} color="purple">
              <Icon name="brain" />
              {tag}
            </Label>
          ))}
        </div>
      </Segment>

      {sentiment_score && (
        <Segment>
          <Header as="h4">
            <Icon name="chart line" />
            Sentiment Score: {sentiment_score.toFixed(2)}
          </Header>
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

export default ResearchNoteView; 