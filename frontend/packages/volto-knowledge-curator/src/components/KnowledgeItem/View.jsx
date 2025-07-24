import React from 'react';
import { Container, Segment, Header, Label, Icon, Button } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const KnowledgeItemView = ({ content }) => {
  const {
    title,
    description,
    text,
    tags = [],
    source_url,
    embedding_vector = [],
    ai_summary,
    relevance_score,
    attachment,
    created,
    modified,
  } = content;

  return (
    <Container>
      <Header as="h1">{title}</Header>
      
      {description && (
        <Segment>
          <Header as="h3">Summary</Header>
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
          <Header as="h4">
            <Icon name="linkify" />
            Source
          </Header>
          <p>
            <a href={source_url} target="_blank" rel="noopener noreferrer">
              {source_url}
            </a>
          </p>
        </Segment>
      )}

      {attachment && (
        <Segment>
          <Header as="h4">
            <Icon name="file" />
            Attachment
          </Header>
          <p>
            <a href={attachment.download} download>
              <Icon name="download" />
              {attachment.filename}
            </a>
            {attachment.size && <span> ({(attachment.size / 1024).toFixed(1)} KB)</span>}
          </p>
        </Segment>
      )}

      {ai_summary && (
        <Segment color="blue">
          <Header as="h4">
            <Icon name="brain" />
            AI Summary
          </Header>
          <p>{ai_summary}</p>
        </Segment>
      )}

      {relevance_score !== undefined && relevance_score > 0 && (
        <Segment color="purple">
          <Header as="h4">
            <Icon name="star" />
            Relevance Score
          </Header>
          <div>
            <Label color="purple" size="medium">
              {(relevance_score * 100).toFixed(1)}%
            </Label>
          </div>
        </Segment>
      )}

      {tags && tags.length > 0 && (
        <Segment>
          <Header as="h4">
            <Icon name="tags" />
            Tags
          </Header>
          <div>
            {tags.map((tag, index) => (
              <Label key={index} color="teal" size="small" style={{ marginRight: '5px' }}>
                {tag}
              </Label>
            ))}
          </div>
        </Segment>
      )}

      {embedding_vector && embedding_vector.length > 0 && (
        <Segment color="grey">
          <Header as="h4">
            <Icon name="code" />
            AI Features
          </Header>
          <p>
            <Icon name="vector square" />
            Embedding Vector: {embedding_vector.length} dimensions
          </p>
        </Segment>
      )}

      <Segment basic clearing>
        <div style={{ marginTop: '20px', fontSize: '0.9em', color: '#999' }}>
          <Icon name="clock" />
          Created: <FormattedDate value={created} />
          {modified && modified !== created && (
            <>
              {' • '}
              <Icon name="edit" />
              Modified: <FormattedDate value={modified} />
            </>
          )}
        </div>
      </Segment>
    </Container>
  );
};

export default KnowledgeItemView; 