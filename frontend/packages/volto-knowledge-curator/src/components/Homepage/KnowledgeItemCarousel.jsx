import React from 'react';
import { Card, Button, Icon, Label, Loader, Dimmer } from 'semantic-ui-react';
import { Link } from 'react-router-dom';
import { useHistory } from 'react-router-dom';
import { BodyClass } from '@plone/volto/helpers';
import './KnowledgeItemCarousel.css';

const KnowledgeItemCarousel = ({ items = [], loading = false }) => {
  const history = useHistory();

  const handleAddNew = () => {
    // Navigate to the Knowledge Item creation form using Volto pattern
    history.push('/add?type=KnowledgeItem');
  };

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

  const truncateText = (text, maxLength = 120) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (loading) {
    return (
      <div className="knowledge-item-carousel loading">
        <Dimmer active inverted>
          <Loader size="large">Loading Knowledge Items...</Loader>
        </Dimmer>
      </div>
    );
  }

  return (
    <div className="knowledge-item-carousel">
      <div className="carousel-container">
        <div className="carousel-track">
          {/* Existing Knowledge Items */}
          {items.map((item, index) => (
            <Card 
              key={item['@id'] || index} 
              className="knowledge-item-card"
              as={Link}
              to={item['@id']}
            >
              <Card.Content>
                <Card.Header className="item-title">
                  <Icon 
                    name={getKnowledgeTypeIcon(item.knowledge_type)} 
                    color="blue"
                  />
                  {item.title}
                </Card.Header>
                
                <Card.Meta>
                  <div className="item-meta">
                    <Label 
                      size="mini" 
                      color={getDifficultyColor(item.difficulty_level)}
                    >
                      {item.difficulty_level || 'Unknown'}
                    </Label>
                    <Label size="mini" basic>
                      {item.knowledge_type || 'General'}
                    </Label>
                  </div>
                </Card.Meta>
                
                <Card.Description>
                  {truncateText(item.description)}
                </Card.Description>
              </Card.Content>
              
              <Card.Content extra>
                <div className="item-actions">
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
          <Card className="add-new-card" onClick={handleAddNew}>
            <Card.Content className="add-new-content">
              <div className="add-new-icon">
                <Icon name="plus circle" size="huge" color="blue" />
              </div>
              <Card.Header className="add-new-title">
                Create Knowledge Item
              </Card.Header>
              <Card.Description>
                Add a new atomic unit of knowledge to your collection
              </Card.Description>
            </Card.Content>
          </Card>
        </div>
      </div>
      
      {/* Scroll indicators */}
      {items.length > 3 && (
        <div className="carousel-controls">
          <Button 
            circular 
            icon="chevron left" 
            className="carousel-prev"
            onClick={() => {
              const track = document.querySelector('.carousel-track');
              track.scrollBy({ left: -300, behavior: 'smooth' });
            }}
          />
          <Button 
            circular 
            icon="chevron right" 
            className="carousel-next"
            onClick={() => {
              const track = document.querySelector('.carousel-track');
              track.scrollBy({ left: 300, behavior: 'smooth' });
            }}
          />
        </div>
      )}
    </div>
  );
};

export default KnowledgeItemCarousel; 