import React, { useState, useEffect } from 'react';
import { Card, Button, Icon, Label, Loader, Container, Header } from 'semantic-ui-react';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';
import { searchContent } from '@plone/volto/actions';

const KnowledgeItemsBlock = ({ data, ...props }) => {
  const intl = useIntl();
  const dispatch = useDispatch();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  // Get search results from Redux store
  const searchResults = useSelector((state) => state.search?.subrequests?.knowledgeItems);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        dispatch(searchContent(
          '/',
          { 
            portal_type: 'KnowledgeItem',
            sort_on: 'created',
            sort_order: 'descending',
            b_size: 20
          },
          'knowledgeItems'
        ));
      } catch (err) {
        console.error('Error fetching Knowledge Items:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, [dispatch]);

  useEffect(() => {
    if (searchResults?.items) {
      setItems(searchResults.items);
      setLoading(false);
    }
  }, [searchResults]);

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner': return 'green';
      case 'intermediate': return 'yellow';
      case 'advanced': return 'red';
      default: return 'grey';
    }
  };

  const getKnowledgeTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'factual': return 'info circle';
      case 'conceptual': return 'lightbulb outline';
      case 'procedural': return 'cogs';
      case 'metacognitive': return 'brain';
      default: return 'question circle';
    }
  };

  if (loading) {
    return (
      <Container style={{ padding: '2rem', textAlign: 'center' }}>
        <Loader active inline="centered" size="large">
          Loading Knowledge Items...
        </Loader>
      </Container>
    );
  }

  return (
    <Container style={{ padding: '2rem' }}>
      <Header as="h2" style={{ marginBottom: '2rem' }}>
        <Icon name="puzzle piece" color="blue" />
        Knowledge Items
        <Header.Subheader>
          {items.length} learning items available
        </Header.Subheader>
      </Header>

      {items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <Icon name="puzzle piece" size="huge" color="grey" />
          <Header as="h3" color="grey">
            No Knowledge Items Found
          </Header>
          <p>Start building your knowledge base by creating your first Knowledge Item.</p>
          <Button primary as={Link} to="/++add++KnowledgeItem">
            <Icon name="plus" />
            Create Knowledge Item
          </Button>
        </div>
      ) : (
        <Card.Group itemsPerRow={3} stackable>
          {items.map((item, index) => (
            <Card key={item['@id'] || index} style={{ height: '300px' }}>
              <Card.Content>
                <Card.Header style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Icon 
                    name={getKnowledgeTypeIcon(item.knowledge_type)} 
                    color="blue"
                  />
                  {item.title}
                </Card.Header>
                
                <Card.Meta style={{ margin: '0.5rem 0' }}>
                  <Label 
                    size="mini" 
                    color={getDifficultyColor(item.difficulty_level)}
                  >
                    {item.difficulty_level || 'Unknown'}
                  </Label>
                  <Label size="mini" basic>
                    {item.knowledge_type || 'General'}
                  </Label>
                </Card.Meta>
                
                <Card.Description>
                  {item.description && item.description.length > 100 
                    ? item.description.substring(0, 100) + '...'
                    : item.description || 'No description available'}
                </Card.Description>
              </Card.Content>
              
              <Card.Content extra>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'space-between' }}>
                  <Button
                    basic
                    color="blue" 
                    size="small"
                    as={Link}
                    to={item['@id']}
                  >
                    <Icon name="book" />
                    Study
                  </Button>
                  <Button
                    basic
                    color="grey"
                    size="small"
                    as={Link}
                    to={`${item['@id']}/edit`}
                  >
                    <Icon name="edit" />
                    Edit
                  </Button>
                </div>
              </Card.Content>
            </Card>
          ))}
          
          {/* Add New Card */}
          <Card style={{ height: '300px', border: '2px dashed #0084ff', background: 'rgba(0, 132, 255, 0.05)' }}>
            <Card.Content style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', height: '100%' }}>
              <Icon name="plus circle" size="huge" color="blue" style={{ marginBottom: '1rem' }} />
              <Card.Header style={{ color: '#0084ff', marginBottom: '1rem' }}>
                Create Knowledge Item
              </Card.Header>
              <Card.Description style={{ marginBottom: '1rem' }}>
                Add a new atomic unit of knowledge to your collection
              </Card.Description>
              <Button 
                primary 
                as={Link} 
                to="/++add++KnowledgeItem"
                style={{ marginTop: 'auto' }}
              >
                <Icon name="plus" />
                Create
              </Button>
            </Card.Content>
          </Card>
        </Card.Group>
      )}
    </Container>
  );
};

export default KnowledgeItemsBlock; 