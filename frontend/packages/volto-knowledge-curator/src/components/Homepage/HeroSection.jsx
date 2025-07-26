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
        <Grid stackable verticalAlign="middle">
          <Grid.Row>
            <Grid.Column width={10}>
              <div className="hero-content">
                <Header as="h1" className="hero-title">
                  Knowledge Curator
                  <Header.Subheader className="hero-subtitle">
                    Personal Knowledge Management for Academic Excellence
                  </Header.Subheader>
                </Header>
                
                <div className="hero-description">
                  <p className="primary-description">
                    A sophisticated platform for researchers, academics, and knowledge professionals 
                    who demand enterprise-grade reliability for their most valuable intellectual assets.
                  </p>
                  <p className="secondary-description">
                    Built upon Plone's proven foundation of security leadership and architectural 
                    excellence, Knowledge Curator champions knowledge sovereignty—your intellectual 
                    work belongs to you, not to surveillance-based platforms.
                  </p>
                </div>
                
                <div className="hero-actions">
                  <Button 
                    primary 
                    size="large"
                    as={Link}
                    to="/++add++KnowledgeItem"
                    className="primary-action"
                  >
                    Create Knowledge Item
                  </Button>
                  
                  <Button 
                    secondary
                    size="large"
                    as={Link}
                    to="/++add++LearningGoal"
                    className="secondary-action"
                  >
                    Define Learning Goal
                  </Button>
                </div>
              </div>
            </Grid.Column>
            
            <Grid.Column width={6}>
              <div className="hero-analytics">
                <Header as="h3" className="analytics-title">
                  Knowledge Base Overview
                </Header>
                
                {loading ? (
                  <div className="analytics-loading">
                    <Placeholder>
                      <Placeholder.Line length="short" />
                      <Placeholder.Line length="medium" />
                      <Placeholder.Line length="short" />
                      <Placeholder.Line length="medium" />
                    </Placeholder>
                  </div>
                ) : (
                  <div className="analytics-content">
                    <Statistic.Group size="small" className="hero-statistics">
                      <Statistic className="primary-stat">
                        <Statistic.Value>{totalKnowledgeItems}</Statistic.Value>
                        <Statistic.Label>Knowledge Items</Statistic.Label>
                      </Statistic>
                      
                      <Statistic className="primary-stat">
                        <Statistic.Value>{totalContainers}</Statistic.Value>
                        <Statistic.Label>Collections</Statistic.Label>
                      </Statistic>
                    </Statistic.Group>
                    
                    {/* Knowledge Maturity Distribution */}
                    <div className="maturity-distribution">
                      <Header as="h4" className="distribution-title">Knowledge Maturity</Header>
                      <div className="maturity-metrics">
                        <div className="maturity-item">
                          <span className="maturity-label">Foundational</span>
                          <span className="maturity-value">{difficultyCounts.beginner || 0}</span>
                        </div>
                        <div className="maturity-item">
                          <span className="maturity-label">Intermediate</span>
                          <span className="maturity-value">{difficultyCounts.intermediate || 0}</span>
                        </div>
                        <div className="maturity-item">
                          <span className="maturity-label">Advanced</span>
                          <span className="maturity-value">{difficultyCounts.advanced || 0}</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Knowledge Types Distribution */}
                    {!loading && Object.keys(typeCounts).length > 0 && (
                      <div className="type-distribution">
                        <Header as="h4" className="distribution-title">Knowledge Types</Header>
                        <div className="type-indicators">
                          {Object.entries(typeCounts).map(([type, count]) => (
                            <div key={type} className="type-indicator">
                              <Icon name={getTypeIcon(type)} className="type-icon" />
                              <span className="type-name">{formatTypeName(type)}</span>
                              <span className="type-count">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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
    default: return 'circle outline';
  }
};

const formatTypeName = (type) => {
  if (!type) return 'Unclassified';
  return type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
};

export default HeroSection; 