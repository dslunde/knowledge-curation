import React, { useState, useEffect } from 'react';
import { Container, Header, Segment, Message } from 'semantic-ui-react';
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
          <Message.Header>Error Loading Content</Message.Header>
          <p>{error}</p>
        </Message>
      </Container>
    );
  }

  return (
    <div className="knowledge-curator-homepage">
      {/* Hero Section */}
      <HeroSection stats={stats} loading={loading} />

      <Container>
        {/* Knowledge Containers Section */}
        <Segment basic>
          <Header as="h2" className="section-header">
            🗂️ Knowledge Containers
            <Header.Subheader>
              Organized collections of knowledge for structured learning
            </Header.Subheader>
          </Header>
          
          <KnowledgeContainerCarousel 
            containers={knowledgeContainers}
            loading={loading}
          />
        </Segment>

        {/* Knowledge Items Section */}
        <Segment basic>
          <Header as="h2" className="section-header">
            🧩 Knowledge Items
            <Header.Subheader>
              Atomic units of knowledge - building blocks for learning
            </Header.Subheader>
          </Header>
          
          <KnowledgeItemCarousel 
            items={knowledgeItems}
            loading={loading}
          />
        </Segment>

        {/* Quick Stats Section */}
        {!loading && (
          <Segment basic className="stats-section">
            <Header as="h3">📊 Quick Overview</Header>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">{stats.totalKnowledgeItems}</div>
                <div className="stat-label">Knowledge Items</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.totalContainers}</div>
                <div className="stat-label">Collections</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.difficultyCounts.beginner || 0}</div>
                <div className="stat-label">Beginner Items</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.difficultyCounts.advanced || 0}</div>
                <div className="stat-label">Advanced Items</div>
              </div>
            </div>
          </Segment>
        )}
      </Container>
    </div>
  );
};

export default HomePage; 