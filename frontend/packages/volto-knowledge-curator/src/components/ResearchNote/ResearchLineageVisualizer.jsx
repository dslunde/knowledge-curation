import React, { useState, useCallback, useEffect } from 'react';
import { 
  Segment, 
  Header, 
  Icon, 
  Button,
  Grid,
  Label,
  Message,
  List,
  Dropdown,
  Modal,
  Form
} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const ResearchLineageVisualizer = ({ 
  value = {}, 
  onChange,
  title = 'Research Lineage',
  description = 'Track relationships with other research',
  onSearchContent,
}) => {
  const [searchModal, setSearchModal] = useState(false);
  const [searchType, setSearchType] = useState('builds_upon');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedItems, setSelectedItems] = useState(new Set());

  const { builds_upon = [], contradicts = [], replication_studies = [] } = value;

  const handleAddRelationship = useCallback((type, items) => {
    const currentItems = value[type] || [];
    const newItems = [...new Set([...currentItems, ...items])];
    onChange({
      ...value,
      [type]: newItems,
    });
  }, [value, onChange]);

  const handleRemoveRelationship = useCallback((type, itemToRemove) => {
    const currentItems = value[type] || [];
    onChange({
      ...value,
      [type]: currentItems.filter(item => item !== itemToRemove),
    });
  }, [value, onChange]);

  const handleSearch = useCallback(async () => {
    if (onSearchContent && searchQuery) {
      try {
        const results = await onSearchContent(searchQuery);
        setSearchResults(results);
      } catch (error) {
        console.error('Search failed:', error);
        setSearchResults([]);
      }
    }
  }, [onSearchContent, searchQuery]);

  const handleAddSelected = useCallback(() => {
    const itemsToAdd = Array.from(selectedItems);
    handleAddRelationship(searchType, itemsToAdd);
    setSearchModal(false);
    setSelectedItems(new Set());
    setSearchQuery('');
    setSearchResults([]);
  }, [selectedItems, searchType, handleAddRelationship]);

  const RelationshipSection = ({ type, items, icon, color, label }) => (
    <Segment>
      <Header as="h4">
        <Icon name={icon} color={color} />
        <Header.Content>{label}</Header.Content>
      </Header>
      
      {items.length > 0 ? (
        <List divided relaxed>
          {items.map((item, index) => (
            <List.Item key={index}>
              <List.Content floated="right">
                <Icon 
                  name="trash" 
                  color="red" 
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleRemoveRelationship(type, item)}
                />
              </List.Content>
              <List.Icon name="file alternate" size="large" verticalAlign="middle" />
              <List.Content>
                <List.Header>{item}</List.Header>
                <List.Description>
                  <Label size="tiny" color={color}>
                    {label}
                  </Label>
                </List.Description>
              </List.Content>
            </List.Item>
          ))}
        </List>
      ) : (
        <Message>
          <p>No {label.toLowerCase()} relationships defined</p>
        </Message>
      )}
      
      <Button 
        size="small" 
        onClick={() => {
          setSearchType(type);
          setSearchModal(true);
        }}
        style={{ marginTop: '1em' }}
      >
        <Icon name="plus" />
        Add {label}
      </Button>
    </Segment>
  );

  const relationshipOptions = [
    { key: 'builds_upon', text: 'Builds Upon', value: 'builds_upon' },
    { key: 'contradicts', text: 'Contradicts', value: 'contradicts' },
    { key: 'replication_studies', text: 'Replication Studies', value: 'replication_studies' },
  ];

  return (
    <Segment>
      <Header as="h3">
        <Icon name="sitemap" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      <Grid columns={1} stackable>
        <Grid.Column>
          <RelationshipSection
            type="builds_upon"
            items={builds_upon}
            icon="arrow up"
            color="green"
            label="Builds Upon"
          />
        </Grid.Column>
        
        <Grid.Column>
          <RelationshipSection
            type="contradicts"
            items={contradicts}
            icon="x"
            color="red"
            label="Contradicts"
          />
        </Grid.Column>
        
        <Grid.Column>
          <RelationshipSection
            type="replication_studies"
            items={replication_studies}
            icon="copy"
            color="blue"
            label="Replication Studies"
          />
        </Grid.Column>
      </Grid>

      <Modal
        open={searchModal}
        onClose={() => setSearchModal(false)}
        size="large"
      >
        <Modal.Header>
          Add Research Relationship
        </Modal.Header>
        <Modal.Content>
          <Form>
            <Form.Field>
              <label>Relationship Type</label>
              <Dropdown
                placeholder="Select relationship type"
                fluid
                selection
                options={relationshipOptions}
                value={searchType}
                onChange={(e, { value }) => setSearchType(value)}
              />
            </Form.Field>
            
            {onSearchContent ? (
              <>
                <Form.Field>
                  <label>Search for Content</label>
                  <Form.Input
                    placeholder="Search by title or keyword..."
                    value={searchQuery}
                    onChange={(e, { value }) => setSearchQuery(value)}
                    action={{
                      icon: 'search',
                      onClick: handleSearch,
                    }}
                  />
                </Form.Field>

                {searchResults.length > 0 && (
                  <Segment>
                    <Header as="h5">Search Results</Header>
                    <List divided selection>
                      {searchResults.map((result) => (
                        <List.Item 
                          key={result.uid}
                          onClick={() => {
                            const newSelected = new Set(selectedItems);
                            if (newSelected.has(result.uid)) {
                              newSelected.delete(result.uid);
                            } else {
                              newSelected.add(result.uid);
                            }
                            setSelectedItems(newSelected);
                          }}
                          active={selectedItems.has(result.uid)}
                        >
                          <List.Icon name={selectedItems.has(result.uid) ? 'check square' : 'square outline'} />
                          <List.Content>
                            <List.Header>{result.title}</List.Header>
                            <List.Description>{result.description}</List.Description>
                          </List.Content>
                        </List.Item>
                      ))}
                    </List>
                  </Segment>
                )}
              </>
            ) : (
              <Form.Field>
                <label>Content UIDs</label>
                <Form.TextArea
                  placeholder="Enter content UIDs, one per line..."
                  rows={4}
                  value={searchQuery}
                  onChange={(e, { value }) => setSearchQuery(value)}
                />
              </Form.Field>
            )}
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setSearchModal(false)}>Cancel</Button>
          <Button 
            primary 
            onClick={() => {
              if (onSearchContent) {
                handleAddSelected();
              } else {
                // Manual entry mode
                const items = searchQuery.split('\n').map(s => s.trim()).filter(Boolean);
                handleAddRelationship(searchType, items);
                setSearchModal(false);
                setSearchQuery('');
              }
            }}
            disabled={onSearchContent ? selectedItems.size === 0 : !searchQuery}
          >
            Add Selected
          </Button>
        </Modal.Actions>
      </Modal>

      <Message info icon style={{ marginTop: '2em' }}>
        <Icon name="info circle" />
        <Message.Content>
          <Message.Header>Understanding Research Relationships</Message.Header>
          <List>
            <List.Item>
              <strong>Builds Upon:</strong> Research that this work extends or is based on
            </List.Item>
            <List.Item>
              <strong>Contradicts:</strong> Research that this work challenges or disputes
            </List.Item>
            <List.Item>
              <strong>Replication Studies:</strong> Studies that attempt to replicate this research
            </List.Item>
          </List>
        </Message.Content>
      </Message>
    </Segment>
  );
};

ResearchLineageVisualizer.propTypes = {
  value: PropTypes.shape({
    builds_upon: PropTypes.arrayOf(PropTypes.string),
    contradicts: PropTypes.arrayOf(PropTypes.string),
    replication_studies: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
  onSearchContent: PropTypes.func,
};

export default ResearchLineageVisualizer;