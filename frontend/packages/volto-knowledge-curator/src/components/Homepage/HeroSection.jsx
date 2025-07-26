import React from 'react';
import { Container, Header, Button, Statistic, Grid, Icon, Placeholder } from 'semantic-ui-react';
import { Link } from 'react-router-dom';
import './HeroSection.css';

const HeroSection = ({ stats = {}, loading = false }) => {
  const {
    totalKnowledgeItems = 0,
    totalContainers = 0,
    difficultyCounts = {},
    typeCounts = {}
  } = stats;

  return (
    <div className="hero-section">
      <Container>
        <Grid stackable>
          <Grid.Row>
            <Grid.Column width={10}>
              <div className="hero-content">
                <Header as="h1" className="hero-title">
                  🧠 Knowledge Curator
                  <Header.Subheader className="hero-subtitle">
                    React Development Mastery Learning Path
                  </Header.Subheader>
                </Header>
                
                <p className="hero-description">
                  A comprehensive knowledge management system designed for structured learning 
                  and personal knowledge curation. Build your expertise through atomic 
                  knowledge units and organized learning paths.
                </p>
                
                <div className="hero-actions">
                  <Button 
                    primary 
                    size="large"
                    as={Link}
                    to="/++add++KnowledgeItem"
                  >
                    <Icon name="plus" />
                    Create Knowledge Item
                  </Button>
                  
                  <Button 
                    basic
                    size="large"
                    as={Link}
                    to="/++add++LearningGoal"
                  >
                    <Icon name="target" />
                    Set Learning Goal
                  </Button>
                </div>
              </div>
            </Grid.Column>
            
            <Grid.Column width={6}>
              <div className="hero-stats">
                <Header as="h3" className="stats-title">
                  📊 Your Knowledge at a Glance
                </Header>
                
                {loading ? (
                  <div className="stats-loading">
                    <Placeholder>
                      <Placeholder.Line length="short" />
                      <Placeholder.Line length="medium" />
                      <Placeholder.Line length="short" />
                    </Placeholder>
                  </div>
                ) : (
                  <Statistic.Group size="small" className="hero-statistics">
                    <Statistic>
                      <Statistic.Value>
                        <Icon name="puzzle piece" />
                        {totalKnowledgeItems}
                      </Statistic.Value>
                      <Statistic.Label>Knowledge Items</Statistic.Label>
                    </Statistic>
                    
                    <Statistic>
                      <Statistic.Value>
                        <Icon name="folder" />
                        {totalContainers}
                      </Statistic.Value>
                      <Statistic.Label>Collections</Statistic.Label>
                    </Statistic>
                    
                    <Statistic>
                      <Statistic.Value>
                        <Icon name="graduation cap" />
                        {difficultyCounts.beginner || 0}
                      </Statistic.Value>
                      <Statistic.Label>Beginner Items</Statistic.Label>
                    </Statistic>
                    
                    <Statistic>
                      <Statistic.Value>
                        <Icon name="rocket" />
                        {difficultyCounts.advanced || 0}
                      </Statistic.Value>
                      <Statistic.Label>Advanced Items</Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                )}
                
                {/* Knowledge Type Distribution */}
                {!loading && Object.keys(typeCounts).length > 0 && (
                  <div className="type-distribution">
                    <Header as="h4">Knowledge Types</Header>
                    <div className="type-badges">
                      {Object.entries(typeCounts).map(([type, count]) => (
                        <div key={type} className="type-badge">
                          <Icon name={getTypeIcon(type)} />
                          <span className="type-name">{type}</span>
                          <span className="type-count">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Container>
    </div>
  );
};

const getTypeIcon = (type) => {
  switch (type?.toLowerCase()) {
    case 'factual': return 'info circle';
    case 'conceptual': return 'lightbulb outline';
    case 'procedural': return 'cogs';
    case 'metacognitive': return 'brain';
    default: return 'question circle';
  }
};

export default HeroSection; 