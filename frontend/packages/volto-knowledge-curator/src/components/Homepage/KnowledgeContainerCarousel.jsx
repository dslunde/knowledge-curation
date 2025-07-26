import React from 'react';
import { Card, Button, Icon, Label, Loader, Dimmer } from 'semantic-ui-react';
import { Link } from 'react-router-dom';
import { useHistory } from 'react-router-dom';
import './KnowledgeContainerCarousel.css';

const KnowledgeContainerCarousel = ({ containers = [], loading = false }) => {
  const history = useHistory();

  const handleAddNew = () => {
    // Navigate to the Knowledge Container creation form using Volto pattern
    history.push('/add?type=KnowledgeContainer');
  };

  const getCollectionTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'course': return 'blue';
      case 'portfolio': return 'purple';
      case 'research_compilation': return 'teal';
      case 'knowledge_base': return 'green';
      default: return 'grey';
    }
  };

  const getCollectionTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'course': return 'graduation cap';
      case 'portfolio': return 'briefcase';
      case 'research_compilation': return 'lab';
      case 'knowledge_base': return 'database';
      default: return 'folder';
    }
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (loading) {
    return (
      <div className="knowledge-container-carousel loading">
        <Dimmer active inverted>
          <Loader size="large">Loading Knowledge Containers...</Loader>
        </Dimmer>
      </div>
    );
  }

  return (
    <div className="knowledge-container-carousel">
      <div className="carousel-container">
        <div className="carousel-track">
          {/* Existing Knowledge Containers */}
          {containers.map((container, index) => (
            <Card 
              key={container['@id'] || index} 
              className="knowledge-container-card"
              as={Link}
              to={container['@id']}
            >
              <Card.Content>
                <Card.Header className="container-title">
                  <Icon 
                    name={getCollectionTypeIcon(container.collection_type)} 
                    color={getCollectionTypeColor(container.collection_type)}
                  />
                  {container.title}
                </Card.Header>
                
                <Card.Meta>
                  <Label 
                    color={getCollectionTypeColor(container.collection_type)}
                    size="small"
                  >
                    {container.collection_type || 'Collection'}
                  </Label>
                </Card.Meta>
                
                <Card.Description>
                  {truncateText(container.description)}
                </Card.Description>
              </Card.Content>
              
              <Card.Content extra>
                <div className="container-stats">
                  <div className="stat-item">
                    <Icon name="puzzle piece" />
                    <span>{container.item_count || 0} Items</span>
                  </div>
                  <div className="stat-item">
                    <Icon name="eye" />
                    <span>{container.publication_status || 'Draft'}</span>
                  </div>
                </div>
                
                <div className="container-actions">
                  <Button
                    basic
                    color="blue" 
                    size="small"
                    as={Link}
                    to={container['@id']}
                  >
                    <Icon name="folder open" />
                    Open
                  </Button>
                  <Button
                    basic
                    color="grey"
                    size="small"
                    as={Link}
                    to={`${container['@id']}/edit`}
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
                <Icon name="plus circle" size="huge" color="teal" />
              </div>
              <Card.Header className="add-new-title">
                Create Container
              </Card.Header>
              <Card.Description>
                Organize your knowledge into structured collections
              </Card.Description>
            </Card.Content>
          </Card>
        </div>
      </div>
      
      {/* Scroll indicators */}
      {containers.length > 2 && (
        <div className="carousel-controls">
          <Button 
            circular 
            icon="chevron left" 
            className="carousel-prev"
            onClick={() => {
              const track = document.querySelector('.knowledge-container-carousel .carousel-track');
              track.scrollBy({ left: -350, behavior: 'smooth' });
            }}
          />
          <Button 
            circular 
            icon="chevron right" 
            className="carousel-next"
            onClick={() => {
              const track = document.querySelector('.knowledge-container-carousel .carousel-track');
              track.scrollBy({ left: 350, behavior: 'smooth' });
            }}
          />
        </div>
      )}
    </div>
  );
};

export default KnowledgeContainerCarousel; 