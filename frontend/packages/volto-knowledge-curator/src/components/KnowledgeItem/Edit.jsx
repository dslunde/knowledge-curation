import React from 'react';
import { Form } from '@plone/volto/components';
import { Container, Header } from 'semantic-ui-react';

const KnowledgeItemEdit = (props) => {
  // In Volto, when adding content, the location pathname includes /add
  // and there's no content id yet
  const isAddMode = !props.content?.['@id'];
  
  return (
    <Container>
      <Header as="h1" style={{ marginBottom: '2rem' }}>
        {isAddMode ? 'Add New Knowledge Item' : 'Edit Knowledge Item'}
      </Header>
      <Form {...props} />
    </Container>
  );
};

export default KnowledgeItemEdit; 