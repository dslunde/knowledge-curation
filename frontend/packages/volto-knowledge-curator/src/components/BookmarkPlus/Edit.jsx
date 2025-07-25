import React from 'react';
import { Form } from '@plone/volto/components';
import { Container, Header } from 'semantic-ui-react';

const BookmarkPlusEdit = (props) => {
  // Check if we're in add mode by looking at the content
  const isAddMode = !props.content?.['@id'];
  
  return (
    <Container>
      <Header as="h1" style={{ marginBottom: '2rem' }}>
        {isAddMode ? 'Add New Bookmark Plus' : 'Edit Bookmark Plus'}
      </Header>
      <Form {...props} />
    </Container>
  );
};

export default BookmarkPlusEdit; 