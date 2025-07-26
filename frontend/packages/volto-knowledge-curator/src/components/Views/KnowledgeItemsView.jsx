import React, { useState, useEffect } from 'react';
import { Card, Button, Icon, Label, Loader, Container, Header, Message } from 'semantic-ui-react';
import { Link, useHistory } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';
import config from '@plone/volto/registry';

const KnowledgeItemsView = (props) => {
  const intl = useIntl();
  const dispatch = useDispatch();
  const history = useHistory();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleCreateKnowledgeItem = () => {
    history.push('/add?type=KnowledgeItem');
  };

  const handleCreateLearningGoal = () => {
    history.push('/add?type=LearningGoal');
  };

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        
        // Use fetch directly to get Knowledge Items
        const response = await fetch(`${config.settings.apiPath}/@search?portal_type=KnowledgeItem&sort_on=created&sort_order=descending&b_size=20`, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setItems(data.items || []);
        
      } catch (err) {
        console.error('Error fetching Knowledge Items:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, []);

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

  if (error) {
    return (
      <Container style={{ padding: '2rem' }}>
        <Message negative>
          <Message.Header>Error Loading Knowledge Items</Message.Header>
          <p>{error}</p>
        </Message>
      </Container>
    );
  }

  return (
    <Container style={{ padding: '2rem' }}>
      {/* Hero Section */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '3rem 2rem',
        borderRadius: '12px',
        marginBottom: '3rem',
        textAlign: 'center'
      }}>
        <Header as="h1" style={{ color: 'white', fontSize: '2.5rem', marginBottom: '1rem' }}>
          🧠 Knowledge Curator
        </Header>
        <Header.Subheader style={{ color: 'rgba(255,255,255,0.9)', fontSize: '1.2rem' }}>
          React Development Mastery Learning Path
        </Header.Subheader>
        <p style={{ fontSize: '1.1rem', margin: '1.5rem 0', opacity: 0.9 }}>
          Atomic units of knowledge for structured learning and personal knowledge curation
        </p>
        <div style={{ marginTop: '2rem' }}>
          <Button 
            primary 
            size="large"
            onClick={handleCreateKnowledgeItem}
            style={{ marginRight: '1rem' }}
          >
            <Icon name="plus" />
            Create Knowledge Item
          </Button>
          <Button 
            basic
            inverted
            size="large"
            onClick={handleCreateLearningGoal}
          >
            <Icon name="target" />
            Set Learning Goal
          </Button>
        </div>
      </div>

      {/* Knowledge Items Section */}
      <Header as="h2" style={{ marginBottom: '2rem', borderBottom: '3px solid #0084ff', paddingBottom: '1rem' }}>
        <Icon name="puzzle piece" color="blue" />
        Knowledge Items
        <Header.Subheader>
          {items.length} learning items available
        </Header.Subheader>
      </Header>

      {items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', background: '#f8f9fa', borderRadius: '8px' }}>
          <Icon name="puzzle piece" size="huge" color="grey" />
          <Header as="h3" color="grey">
            No Knowledge Items Found
          </Header>
          <p>Start building your knowledge base by creating your first Knowledge Item.</p>
          <Button primary onClick={handleCreateKnowledgeItem}>
            <Icon name="plus" />
            Create Knowledge Item
          </Button>
        </div>
      ) : (
        <Card.Group itemsPerRow={3} stackable>
          {items.map((item, index) => (
            <Card 
              key={item['@id'] || index} 
              style={{ 
                height: '320px',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              <Card.Content>
                <Card.Header style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  fontSize: '1.1rem',
                  height: '3rem',
                  overflow: 'hidden'
                }}>
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
                  {item.description && item.description.length > 120 
                    ? item.description.substring(0, 120) + '...'
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
          <Card style={{ 
            height: '320px', 
            border: '2px dashed #0084ff', 
            background: 'rgba(0, 132, 255, 0.05)',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 132, 255, 0.1)';
            e.currentTarget.style.borderColor = '#0066cc';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(0, 132, 255, 0.05)';
            e.currentTarget.style.borderColor = '#0084ff';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
          >
            <Card.Content style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center', 
              textAlign: 'center', 
              height: '100%',
              padding: '2rem' 
            }}>
              <Icon name="plus circle" size="huge" color="blue" style={{ marginBottom: '1rem' }} />
              <Card.Header style={{ color: '#0084ff', marginBottom: '1rem' }}>
                Create Knowledge Item
              </Card.Header>
              <Card.Description style={{ marginBottom: '1rem' }}>
                Add a new atomic unit of knowledge to your collection
              </Card.Description>
              <Button 
                primary 
                onClick={handleCreateKnowledgeItem}
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

export default KnowledgeItemsView; 