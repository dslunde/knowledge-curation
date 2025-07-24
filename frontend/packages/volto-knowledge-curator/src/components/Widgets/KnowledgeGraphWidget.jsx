import React from 'react';
import { Segment, Header, List, Icon } from 'semantic-ui-react';

const KnowledgeGraphWidget = ({ value, field, title }) => {
  if (!value || !value.connections || value.connections.length === 0) {
    return null;
  }

  return (
    <Segment color="teal">
      <Header as="h4">
        <Icon name="sitemap" />
        {title || 'Knowledge Graph Connections'}
      </Header>
      
      <List>
        {value.connections.map((connection, index) => (
          <List.Item key={index}>
            <Icon name="link" />
            <List.Content>
              <List.Header>{connection.title || connection}</List.Header>
              {connection.description && (
                <List.Description>{connection.description}</List.Description>
              )}
            </List.Content>
          </List.Item>
        ))}
      </List>
      
      {value.concept_weight && (
        <div style={{ marginTop: '10px' }}>
          <small>
            <strong>Concept Weight:</strong> {value.concept_weight}
          </small>
        </div>
      )}
    </Segment>
  );
};

export default KnowledgeGraphWidget; 