import React, { useState } from 'react';
import { 
  Segment, 
  Header, 
  Button, 
  Icon, 
  Grid,
  Input,
  Message,
  Label
} from 'semantic-ui-react';
import { Link, useHistory } from 'react-router-dom';

const SearchWidget = ({ 
  compact = false, 
  showExamples = true,
  onSearch
}) => {
  const [query, setQuery] = useState('');
  const history = useHistory();

  const handleQuickSearch = () => {
    if (query.trim()) {
      // Navigate to advanced search with query
      history.push(`/advanced-search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleExampleClick = (example) => {
    history.push(`/advanced-search?q=${encodeURIComponent(example)}`);
  };

  const examples = [
    "machine learning concepts",
    "research methodology", 
    "python programming",
    "data visualization techniques"
  ];

  return (
    <Segment className="search-widget">
      <Header as={compact ? "h4" : "h3"} textAlign="center">
        <Icon name="search" color="blue" />
        {compact ? "Knowledge Search" : "Discover Your Knowledge"}
        <Header.Subheader>
          {compact ? 
            "AI-powered semantic search" : 
            "Find exactly what you're looking for with AI-powered semantic search"
          }
        </Header.Subheader>
      </Header>

      {/* Quick Search Input */}
      <div className="search-widget-input">
        <Input
          fluid
          size={compact ? "small" : "large"}
          value={query}
          onChange={(e, { value }) => setQuery(value)}
          onKeyPress={(e) => e.key === 'Enter' && handleQuickSearch()}
          placeholder="What would you like to learn about?"
          action={
            <Button 
              color="blue"
              icon="search"
              content="Search"
              onClick={handleQuickSearch}
              disabled={!query.trim()}
            />
          }
        />
      </div>

      {/* Search Features */}
      <Grid columns={compact ? 2 : 3} stackable className="search-features">
        <Grid.Column textAlign="center">
          <Icon name="brain" size="large" color="blue" />
          <div className="feature-text">
            <strong>Semantic Search</strong>
            <br />
            <small>Find by meaning, not just keywords</small>
          </div>
        </Grid.Column>
        <Grid.Column textAlign="center">
          <Icon name="clone" size="large" color="purple" />
          <div className="feature-text">
            <strong>Similar Content</strong>
            <br />
            <small>Discover related knowledge</small>
          </div>
        </Grid.Column>
        {!compact && (
          <Grid.Column textAlign="center">
            <Icon name="filter" size="large" color="green" />
            <div className="feature-text">
              <strong>Smart Filters</strong>
              <br />
              <small>Precise content targeting</small>
            </div>
          </Grid.Column>
        )}
      </Grid>

      {/* Search Examples */}
      {showExamples && (
        <div className="search-examples">
          <Header as="h5" textAlign="center">
            <Icon name="lightbulb outline" />
            Try searching for:
          </Header>
          <div className="example-labels">
            {examples.map((example, index) => (
              <Label 
                key={index}
                as="a"
                basic
                size="small"
                onClick={() => handleExampleClick(example)}
                className="search-example-label"
              >
                {example}
              </Label>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Search Link */}
      <div className="advanced-search-link">
        <Button 
          as={Link}
          to="/advanced-search"
          basic
          fluid={compact}
          icon="settings"
          content="Advanced Search Features"
          size={compact ? "small" : "medium"}
        />
      </div>

      {/* Quick Stats */}
      {!compact && (
        <Message info size="mini">
          <Message.Header>
            <Icon name="info circle" />
            Did you know?
          </Message.Header>
          <p>
            Our AI-powered search can understand context and find relevant content 
            even when you don't use exact keywords. Try describing what you want to learn!
          </p>
        </Message>
      )}
    </Segment>
  );
};

export default SearchWidget; 