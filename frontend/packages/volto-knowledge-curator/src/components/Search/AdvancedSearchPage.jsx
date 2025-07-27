import React, { useState } from 'react';
import { 
  Container, 
  Header, 
  Segment, 
  Form, 
  Button, 
  Grid, 
  Icon,
  Message,
  Tab,
  Label,
  Input,
  Dropdown
} from 'semantic-ui-react';
import { Helmet } from '@plone/volto/helpers';
import { useLocation } from 'react-router-dom';
import './AdvancedSearch.css';

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
    similarity: 0.7
  });
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = () => {
    if (!query.trim()) return;
    
    setLoading(true);
    // TODO: Implement actual search API call
    setTimeout(() => {
      setResults([
        {
          id: 1,
          title: 'Cognitive Load Theory in Educational Design',
          description: 'Analysis of working memory limitations and their implications for instructional design methodologies.',
          type: 'Research Note',
          similarity: 0.89,
          created: new Date().toISOString(),
          tags: ['cognitive-science', 'education', 'methodology']
        },
        {
          id: 2,
          title: 'Machine Learning Fundamentals: A Systematic Review',
          description: 'Comprehensive examination of core algorithms and theoretical foundations in machine learning.',
          type: 'Knowledge Item',
          similarity: 0.76,
          created: new Date().toISOString(),
          tags: ['machine-learning', 'algorithms', 'systematic-review']
        }
      ]);
      setLoading(false);
    }, 1000);
  };

  const contentTypeOptions = [
    { key: 'knowledge', text: 'Knowledge Items', value: 'KnowledgeItem' },
    { key: 'research', text: 'Research Notes', value: 'ResearchNote' },
    { key: 'learning', text: 'Learning Goals', value: 'LearningGoal' },
    { key: 'project', text: 'Project Logs', value: 'ProjectLog' },
    { key: 'bookmark', text: 'Bookmarks', value: 'BookmarkPlus' }
  ];

  const searchModes = [
    {
      menuItem: { key: 'semantic', content: 'Semantic' },
      render: () => (
        <Tab.Pane className="search-mode-pane">
          <div className="search-mode-description">
            AI-powered conceptual search using natural language understanding
          </div>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: 'keyword', content: 'Keyword' },
      render: () => (
        <Tab.Pane className="search-mode-pane">
          <div className="search-mode-description">
            Precise text matching for exact terms and phrases
          </div>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: 'citation', content: 'Citation' },
      render: () => (
        <Tab.Pane className="search-mode-pane">
          <div className="search-mode-description">
            Search by author, publication, or bibliographic metadata
          </div>
        </Tab.Pane>
      ),
    },
  ];

  return (
    <>
      <Helmet title="Advanced Search - Knowledge Curator" />
      <div className="advanced-search-container">
        {/* Integrated Header and Search */}
        <div className="search-header-integrated">
          <div className="header-content">
            <div className="title-with-icon">
              <Icon name="search" size="large" className="header-icon" />
              <div className="title-text">
                <Header as="h2" className="search-title">
                  Advanced Search
                </Header>
                <div className="search-subtitle">
                  Search across your knowledge base with powerful filters and AI similarity
                </div>
              </div>
            </div>
            <Button 
              basic 
              icon="options" 
              content="Filters" 
              onClick={() => setShowFilters(!showFilters)}
              className={`filter-toggle ${showFilters ? 'active' : ''}`}
            />
          </div>
          
          {/* Integrated Search Input */}
          <div className="search-input-integrated">
            <Input
              fluid
              placeholder="Search your knowledge base..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              action={{
                color: 'blue',
                icon: 'search',
                loading: loading,
                disabled: !query.trim(),
                onClick: handleSearch
              }}
              size="large"
              className="main-search-input"
            />
          </div>

          {/* Search Mode Tabs */}
          <div className="search-modes-integrated">
            <Tab 
              menu={{ secondary: true, pointing: true, compact: true }}
              panes={searchModes} 
              activeIndex={activeTab}
              onTabChange={(e, { activeIndex }) => setActiveTab(activeIndex)}
            />
          </div>
        </div>

        {/* Full-Width Content Area */}
        <div className="content-area">
          {/* Filters Panel - Full Width when Open */}
          {showFilters && (
            <div className="filters-panel-fullwidth">
              <Grid columns={4} divided className="filters-grid">
                <Grid.Column>
                  <Form.Field>
                    <label>Content Types</label>
                    <Dropdown
                      placeholder="All types"
                      fluid
                      multiple
                      selection
                      options={contentTypeOptions}
                      value={filters.contentTypes}
                      onChange={(e, { value }) => setFilters({...filters, contentTypes: value})}
                    />
                  </Form.Field>
                </Grid.Column>
                <Grid.Column>
                  <Form.Field>
                    <label>Date Range</label>
                    <Input
                      type="date"
                      placeholder="From"
                      value={filters.dateRange.start}
                      onChange={(e) => setFilters({
                        ...filters, 
                        dateRange: { ...filters.dateRange, start: e.target.value }
                      })}
                    />
                    <Input
                      type="date"
                      placeholder="To"
                      style={{ marginTop: '0.5rem' }}
                      value={filters.dateRange.end}
                      onChange={(e) => setFilters({
                        ...filters, 
                        dateRange: { ...filters.dateRange, end: e.target.value }
                      })}
                    />
                  </Form.Field>
                </Grid.Column>
                <Grid.Column>
                  <Form.Field>
                    <label>Similarity Threshold: {Math.round(filters.similarity * 100)}%</label>
                    <input
                      type="range"
                      min="0.3"
                      max="1"
                      step="0.05"
                      value={filters.similarity}
                      onChange={(e) => setFilters({...filters, similarity: parseFloat(e.target.value)})}
                      style={{ width: '100%' }}
                    />
                  </Form.Field>
                </Grid.Column>
                <Grid.Column>
                  <Form.Field>
                    <label>Advanced Options</label>
                    <Button basic size="small" fluid>Export Results</Button>
                    <Button basic size="small" fluid style={{ marginTop: '0.5rem' }}>Save Search</Button>
                  </Form.Field>
                </Grid.Column>
              </Grid>
            </div>
          )}

          {/* Results Area - Expands Vertically */}
          <div className="results-area">
            {loading ? (
              <Segment loading className="results-loading">
                <div style={{ height: '300px' }} />
              </Segment>
            ) : results.length > 0 ? (
              <div className="results-container">
                <div className="results-meta">
                  <span className="results-count">{results.length} results found</span>
                  <span className="results-time">Search completed in 0.12s</span>
                </div>
                <div className="results-list">
                  {results.map((result) => (
                    <div key={result.id} className="result-item">
                      <div className="result-content">
                        <div className="result-header">
                          <h4 className="result-title">{result.title}</h4>
                          <div className="result-metadata">
                            <Label size="mini" color="blue">{result.type}</Label>
                            <Label size="mini" color="green">
                              {Math.round(result.similarity * 100)}% match
                            </Label>
                          </div>
                        </div>
                        <p className="result-description">{result.description}</p>
                        {result.tags && (
                          <div className="result-tags">
                            {result.tags.map(tag => (
                              <Label key={tag} size="tiny" basic>{tag}</Label>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="result-actions">
                        <Button size="small" basic primary icon="eye" content="View" />
                        <Button size="small" basic icon="sitemap" content="Similar" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : query && !loading ? (
              <Message className="no-results">
                <Message.Header>No results found</Message.Header>
                <p>Consider adjusting your search terms or expanding the date range.</p>
              </Message>
            ) : (
              <div className="search-placeholder-centered">
                <div className="placeholder-content">
                  <Icon name="search" size="big" color="grey" />
                  <h3>Search Your Knowledge Base</h3>
                  <p>Enter terms above to begin searching across your research notes, knowledge items, and bookmarks.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default AdvancedSearchPage; 