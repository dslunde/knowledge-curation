import React, { useState, useEffect } from 'react';
import { Container, Header, Segment, Message, Grid, Statistic } from 'semantic-ui-react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';
import { searchContent } from '@plone/volto/actions';
import KnowledgeItemCarousel from './KnowledgeItemCarousel';
import KnowledgeContainerCarousel from './KnowledgeContainerCarousel';
import HeroSection from './HeroSection';
import './HomePage.css';

const HomePage = () => {
  const intl = useIntl();
  const dispatch = useDispatch();
  
  const [knowledgeItems, setKnowledgeItems] = useState([]);
  const [knowledgeContainers, setKnowledgeContainers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get search results from Redux store
  const searchResults = useSelector((state) => state.search?.subrequests || {});

  useEffect(() => {
    const fetchContent = async () => {
      try {
        setLoading(true);
        
        // Fetch Knowledge Items
        dispatch(searchContent(
          '/',
          { 
            portal_type: 'KnowledgeItem',
            sort_on: 'created',
            sort_order: 'descending',
            metadata_fields: ['description', 'knowledge_type', 'difficulty_level'],
            b_size: 20
          },
          'knowledgeItems'
        ));

        // Fetch Knowledge Containers  
        dispatch(searchContent(
          '/',
          {
            portal_type: 'KnowledgeContainer',
            sort_on: 'created', 
            sort_order: 'descending',
            metadata_fields: ['description', 'collection_type'],
            b_size: 10
          },
          'knowledgeContainers'
        ));

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [dispatch]);

  // Update local state when Redux state changes
  useEffect(() => {
    if (searchResults.knowledgeItems?.items) {
      setKnowledgeItems(searchResults.knowledgeItems.items);
    }
    if (searchResults.knowledgeContainers?.items) {
      setKnowledgeContainers(searchResults.knowledgeContainers.items);
    }
  }, [searchResults]);

  const stats = {
    totalKnowledgeItems: knowledgeItems.length,
    totalContainers: knowledgeContainers.length,
    // Calculate additional stats
    difficultyCounts: knowledgeItems.reduce((acc, item) => {
      const difficulty = item.difficulty_level || 'unknown';
      acc[difficulty] = (acc[difficulty] || 0) + 1;
      return acc;
    }, {}),
    typeCounts: knowledgeItems.reduce((acc, item) => {
      const type = item.knowledge_type || 'unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {})
  };

  if (error) {
    return (
      <Container>
        <Message negative>
          <Message.Header>Content Loading Error</Message.Header>
          <p>Unable to retrieve knowledge base content: {error}</p>
        </Message>
      </Container>
    );
  }

  return (
    <div className="knowledge-curator-homepage">
      {/* Academic Header Section */}
      <HeroSection stats={stats} loading={loading} />

      <Container>
        {/* Knowledge Collections Section */}
        <section className="knowledge-section">
          <Header as="h2" className="section-header">
            Knowledge Collections
            <Header.Subheader>
              Curated repositories of structured intellectual content organized for systematic study and research
            </Header.Subheader>
          </Header>
          
          <KnowledgeContainerCarousel 
            containers={knowledgeContainers}
            loading={loading}
          />
        </section>

        {/* Knowledge Items Section */}
        <section className="knowledge-section">
          <Header as="h2" className="section-header">
            Knowledge Items
            <Header.Subheader>
              Atomic units of validated knowledge serving as foundational elements for intellectual synthesis
            </Header.Subheader>
          </Header>
          
          <KnowledgeItemCarousel 
            items={knowledgeItems}
            loading={loading}
          />
        </section>

        {/* Knowledge Base Analytics */}
        {!loading && (
          <section className="analytics-section">
            <Grid columns={2} stackable>
              <Grid.Column>
                <Segment className="analytics-panel">
                  <Header as="h3" className="analytics-header">Knowledge Base Metrics</Header>
                  <Statistic.Group size="small" className="knowledge-statistics">
                    <Statistic>
                      <Statistic.Value>{stats.totalKnowledgeItems}</Statistic.Value>
                      <Statistic.Label>Total Knowledge Items</Statistic.Label>
                    </Statistic>
                    <Statistic>
                      <Statistic.Value>{stats.totalContainers}</Statistic.Value>
                      <Statistic.Label>Active Collections</Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                </Segment>
              </Grid.Column>
              
              <Grid.Column>
                <Segment className="analytics-panel">
                  <Header as="h3" className="analytics-header">Difficulty Distribution</Header>
                  <Statistic.Group size="small" className="difficulty-statistics">
                    <Statistic>
                      <Statistic.Value>{stats.difficultyCounts.beginner || 0}</Statistic.Value>
                      <Statistic.Label>Foundational</Statistic.Label>
                    </Statistic>
                    <Statistic>
                      <Statistic.Value>{stats.difficultyCounts.intermediate || 0}</Statistic.Value>
                      <Statistic.Label>Intermediate</Statistic.Label>
                    </Statistic>
                    <Statistic>
                      <Statistic.Value>{stats.difficultyCounts.advanced || 0}</Statistic.Value>
                      <Statistic.Label>Advanced</Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                </Segment>
              </Grid.Column>
            </Grid>
          </section>
        )}
      </Container>
    </div>
  );
};

export default HomePage; 