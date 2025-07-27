import React, { useState } from 'react';
import { 
  Container, 
  Header, 
  Segment, 
  Form, 
  Button, 
  Grid, 
  Divider,
  Icon,
  Message,
  Tab,
  Card,
  Label
} from 'semantic-ui-react';
import { Helmet } from '@plone/volto/helpers';
import { useLocation } from 'react-router-dom';

const AdvancedSearchPage = () => {
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialQuery = queryParams.get('q') || '';
  
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [filters, setFilters] = useState({
    contentTypes: [],
    dateRange: { start: '', end: '' },
    similarity: 0.5
  });

  const handleSearch = () => {
    if (!query.trim()) return;
    
    setLoading(true);
    // TODO: Implement actual search API call
    setTimeout(() => {
      setResults([
        {
          id: 1,
          title: 'Sample Knowledge Item',
          description: 'This is a sample search result',
          type: 'Research Note',
          similarity: 0.89,
          created: new Date().toISOString()
        },
        {
          id: 2,
          title: 'Machine Learning Fundamentals',
          description: 'Core concepts and algorithms in machine learning',
          type: 'Knowledge Item',
          similarity: 0.76,
          created: new Date().toISOString()
        }
      ]);
      setLoading(false);
    }, 1000);
  };

  const panes = [
    {
      menuItem: { key: 'semantic', icon: 'brain', content: 'Semantic Search' },
      render: () => (
        <Tab.Pane>
          <Message info>
            <Message.Header>AI-Powered Semantic Search</Message.Header>
            <p>Search using natural language to find conceptually similar content</p>
          </Message>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: 'keyword', icon: 'filter', content: 'Keyword Search' },
      render: () => (
        <Tab.Pane>
          <Message info>
            <Message.Header>Traditional Keyword Search</Message.Header>
            <p>Search for exact matches in titles and content</p>
          </Message>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: 'similar', icon: 'sitemap', content: 'Find Similar' },
      render: () => (
        <Tab.Pane>
          <Message info>
            <Message.Header>Similar Content Discovery</Message.Header>
            <p>Find content similar to a specific knowledge item</p>
          </Message>
        </Tab.Pane>
      ),
    },
  ];

  return (
    <>
      <Helmet title="Advanced Search - Knowledge Curator" />
      <Container className="advanced-search-page" style={{ padding: '2rem 0' }}>
        <Header as="h1" icon textAlign="center">
          <Icon name="search" />
          Advanced Knowledge Search
          <Header.Subheader>
            Search across your knowledge base with powerful filters and AI similarity
          </Header.Subheader>
        </Header>
        
        <Segment>
          <Form>
            <Form.Group>
              <Form.Input
                width={12}
                placeholder="Enter your search query..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                size="large"
              />
              <Form.Button 
                width={4}
                primary 
                onClick={handleSearch}
                loading={loading}
                disabled={!query.trim()}
                size="large"
              >
                <Icon name="search" />
                Search
              </Form.Button>
            </Form.Group>
          </Form>
        </Segment>

        <Tab 
          panes={panes} 
          activeIndex={activeTab}
          onTabChange={(e, { activeIndex }) => setActiveTab(activeIndex)}
        />

        <Divider hidden />

        {/* Filters Section */}
        <Grid>
          <Grid.Column width={4}>
            <Segment>
              <Header as="h4">
                <Icon name="filter" />
                Filters
              </Header>
              <Form>
                <Form.Field>
                  <label>Content Types</label>
                  <Form.Checkbox label="Knowledge Items" />
                  <Form.Checkbox label="Research Notes" />
                  <Form.Checkbox label="Learning Goals" />
                  <Form.Checkbox label="Project Logs" />
                </Form.Field>
                <Divider />
                <Form.Field>
                  <label>Similarity Threshold: {filters.similarity}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={filters.similarity}
                    onChange={(e) => setFilters({...filters, similarity: parseFloat(e.target.value)})}
                  />
                </Form.Field>
              </Form>
            </Segment>
          </Grid.Column>
          
          <Grid.Column width={12}>
            {loading ? (
              <Segment loading style={{ minHeight: 200 }}>
                <p>Loading...</p>
              </Segment>
            ) : results.length > 0 ? (
              <Card.Group>
                {results.map((result) => (
                  <Card key={result.id} fluid>
                    <Card.Content>
                      <Card.Header>{result.title}</Card.Header>
                      <Card.Meta>
                        <Label color="blue" size="small">
                          {result.type}
                        </Label>
                        <Label color="green" size="small">
                          <Icon name="percent" />
                          {(result.similarity * 100).toFixed(0)}% match
                        </Label>
                      </Card.Meta>
                      <Card.Description>{result.description}</Card.Description>
                    </Card.Content>
                    <Card.Content extra>
                      <Button basic primary size="small">
                        <Icon name="eye" />
                        View
                      </Button>
                      <Button basic size="small">
                        <Icon name="sitemap" />
                        Find Similar
                      </Button>
                    </Card.Content>
                  </Card>
                ))}
              </Card.Group>
            ) : query && !loading ? (
              <Message>
                <Message.Header>No results found</Message.Header>
                <p>Try adjusting your search query or filters</p>
              </Message>
            ) : (
              <Segment placeholder>
                <Header icon>
                  <Icon name="search" />
                  Enter a search query to get started
                </Header>
              </Segment>
            )}
          </Grid.Column>
        </Grid>
      </Container>
    </>
  );
};

export default AdvancedSearchPage; 