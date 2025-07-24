import React from 'react';
import { Container, Segment, Header, Label, Icon, Button } from 'semantic-ui-react';
import { FormattedDate } from 'react-intl';

const BookmarkPlusView = ({ content }) => {
  const {
    title,
    url,
    tags = [],
    notes,
    read_status,
    importance,
    created,
    modified,
  } = content;

  const getImportanceColor = (importance) => {
    switch (importance) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'grey';
    }
  };

  const getReadStatusIcon = (status) => {
    switch (status) {
      case 'read': return 'check circle';
      case 'reading': return 'eye';
      case 'unread': return 'circle outline';
      default: return 'circle outline';
    }
  };

  return (
    <Container>
      <Header as="h1">
        {title}
        <Label color={getImportanceColor(importance)} size="small">
          {importance}
        </Label>
        <Label size="small">
          <Icon name={getReadStatusIcon(read_status)} />
          {read_status}
        </Label>
      </Header>
      
      <Segment>
        <Header as="h3">URL</Header>
        <Button 
          as="a" 
          href={url} 
          target="_blank" 
          rel="noopener noreferrer"
          primary
        >
          <Icon name="external" />
          Visit Link
        </Button>
        <p><small>{url}</small></p>
      </Segment>

      {notes && (
        <Segment>
          <Header as="h3">Notes</Header>
          <p>{notes}</p>
        </Segment>
      )}

      {tags && tags.length > 0 && (
        <Segment>
          <Header as="h3">Tags</Header>
          <div>
            {tags.map((tag, index) => (
              <Label key={index} color="teal">
                {tag}
              </Label>
            ))}
          </div>
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

export default BookmarkPlusView; 