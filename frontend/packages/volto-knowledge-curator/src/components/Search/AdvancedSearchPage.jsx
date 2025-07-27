import React, { useState, useEffect, useCallback } from 'react';
import { 
  Container, 
  Header, 
  Segment, 
  Grid, 
  Tab, 
  Message,
  Dimmer,
  Loader,
  Button,
  Icon,
  Label,
  Statistic
} from 'semantic-ui-react';
import { useIntl } from 'react-intl';
import { Helmet } from '@plone/volto/helpers';
import SearchInput from './SearchInput';
import SearchFilters from './SearchFilters';
import SearchResults from './SearchResults';
import SimilarContentFinder from './SimilarContentFinder';
import SearchSuggestions from './SearchSuggestions';
import SearchHistory from './SearchHistory';
import SearchAnalytics from './SearchAnalytics';
import './AdvancedSearch.css';

const AdvancedSearchPage = () => {
  const intl = useIntl();
  
  // Search state
  const [searchMode, setSearchMode] = useState('semantic'); // semantic, keyword, similar
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    contentTypes: [],
    dateRange: null,
    similarityThreshold: 0.5,
    tags: [],
    difficulty: [],
    workflowState: []
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchStats, setSearchStats] = useState(null);
  const [searchHistory, setSearchHistory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  // Advanced features state
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [saveSearchModal, setSaveSearchModal] = useState(false);
  const [searchAnalytics, setSearchAnalytics] = useState(null);

  // Perform search
  const performSearch = useCallback(async (searchQuery = query, searchFilters = filters) => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const searchParams = {
        q: searchQuery,
        limit: 20,
        threshold: searchFilters.similarityThreshold,
        types: searchFilters.contentTypes.join(','),
        ...searchFilters
      };

      // Choose API endpoint based on search mode
      const endpoint = searchMode === 'semantic' ? '/@vector-search' : '/@search';
      
      const response = await fetch(`${endpoint}?${new URLSearchParams(searchParams)}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Handle different response formats
      const searchResults = searchMode === 'semantic' ? data : data.items || [];
      
      setResults(searchResults);
      setSearchStats({
        total: searchResults.length,
        queryTime: data.query_time || 0,
        searchMode,
        query: searchQuery
      });

      // Add to search history
      const historyEntry = {
        query: searchQuery,
        mode: searchMode,
        results: searchResults.length,
        timestamp: new Date().toISOString(),
        filters: { ...searchFilters }
      };
      setSearchHistory(prev => [historyEntry, ...prev.slice(0, 9)]); // Keep last 10

    } catch (err) {
      setError(err.message);
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  }, [query, filters, searchMode]);

  // Get search suggestions
  const getSuggestions = useCallback(async (inputValue) => {
    if (inputValue.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/@vector-search?q=${encodeURIComponent(inputValue)}&limit=5&suggest=true`, {
        headers: { 'Accept': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.warn('Suggestions failed:', err);
    }
  }, []);

  // Load search analytics
  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const response = await fetch('/@search-analytics', {
          headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
          const data = await response.json();
          setSearchAnalytics(data);
        }
      } catch (err) {
        console.warn('Analytics loading failed:', err);
      }
    };

    loadAnalytics();
  }, []);

  // Search tabs configuration
  const searchTabs = [
    {
      menuItem: { key: 'semantic', icon: 'brain', content: 'Semantic Search' },
      render: () => (
        <Tab.Pane key="semantic">
          <Header as="h3" color="blue">
            <Icon name="brain" />
            Semantic Search
            <Header.Subheader>
              Find content by meaning and context, not just keywords
            </Header.Subheader>
          </Header>
          
          <SearchInput
            value={query}
            onChange={setQuery}
            onSearch={performSearch}
            suggestions={suggestions}
            onInputChange={getSuggestions}
            placeholder="Describe what you're looking for in natural language..."
            loading={loading}
            advanced={true}
          />
        </Tab.Pane>
      )
    },
    {
      menuItem: { key: 'keyword', icon: 'search', content: 'Keyword Search' },
      render: () => (
        <Tab.Pane key="keyword">
          <Header as="h3" color="green">
            <Icon name="search" />
            Keyword Search
            <Header.Subheader>
              Traditional search using exact terms and phrases
            </Header.Subheader>
          </Header>
          
          <SearchInput
            value={query}
            onChange={setQuery}
            onSearch={performSearch}
            placeholder="Enter specific keywords or phrases..."
            loading={loading}
          />
        </Tab.Pane>
      )
    },
    {
      menuItem: { key: 'similar', icon: 'clone', content: 'Find Similar' },
      render: () => (
        <Tab.Pane key="similar">
          <Header as="h3" color="purple">
            <Icon name="clone" />
            Find Similar Content
            <Header.Subheader>
              Discover content similar to items you specify
            </Header.Subheader>
          </Header>
          
          <SimilarContentFinder
            onResults={setResults}
            onLoading={setLoading}
            onError={setError}
          />
        </Tab.Pane>
      )
    }
  ];

  const handleTabChange = (e, { activeIndex }) => {
    const modes = ['semantic', 'keyword', 'similar'];
    setSearchMode(modes[activeIndex]);
    setResults([]);
    setError(null);
  };

  return (
    <div className="advanced-search-page">
      <Helmet>
        <title>Advanced Search - Knowledge Curator</title>
        <meta name="description" content="Advanced semantic search for knowledge discovery" />
      </Helmet>

      <Container>
        <Header as="h1" className="search-page-header">
          <Icon name="search" color="blue" />
          Advanced Knowledge Search
          <Header.Subheader>
            Discover knowledge using AI-powered semantic search and intelligent filtering
          </Header.Subheader>
        </Header>

        <Grid>
          <Grid.Column width={12}>
            {/* Main Search Interface */}
            <Segment className="search-interface">
              <Tab 
                panes={searchTabs} 
                onTabChange={handleTabChange}
                className="search-tabs"
              />
              
              {/* Advanced Filters */}
              <SearchFilters
                filters={filters}
                onChange={setFilters}
                show={showAdvancedFilters}
                onToggle={setShowAdvancedFilters}
              />

              {/* Search Actions */}
              <div className="search-actions">
                <Button.Group>
                  <Button 
                    icon="filter" 
                    content="Advanced Filters"
                    toggle
                    active={showAdvancedFilters}
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  />
                  <Button 
                    icon="save" 
                    content="Save Search"
                    onClick={() => setSaveSearchModal(true)}
                    disabled={!query}
                  />
                  <Button 
                    icon="download" 
                    content="Export Results"
                    disabled={results.length === 0}
                  />
                </Button.Group>
              </div>
            </Segment>

            {/* Search Results */}
            <SearchResults
              results={results}
              loading={loading}
              error={error}
              searchMode={searchMode}
              stats={searchStats}
              onSimilarSearch={(uid) => {
                setSearchMode('similar');
                // Trigger similar search
              }}
            />
          </Grid.Column>

          <Grid.Column width={4}>
            {/* Search Suggestions */}
            <SearchSuggestions 
              analytics={searchAnalytics}
              onSuggestionClick={(suggestion) => {
                setQuery(suggestion);
                performSearch(suggestion);
              }}
            />

            {/* Search History */}
            <SearchHistory
              history={searchHistory}
              onHistoryClick={(historyItem) => {
                setQuery(historyItem.query);
                setSearchMode(historyItem.mode);
                setFilters(historyItem.filters);
                performSearch(historyItem.query, historyItem.filters);
              }}
            />

            {/* Search Analytics */}
            <SearchAnalytics 
              analytics={searchAnalytics}
              currentStats={searchStats}
            />
          </Grid.Column>
        </Grid>
      </Container>
    </div>
  );
};

export default AdvancedSearchPage; 