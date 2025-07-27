import React, { useState } from 'react';
import { 
  Segment, 
  Header, 
  Button, 
  Icon, 
  Input,
  Grid,
  Message
} from 'semantic-ui-react';
import { Link } from 'react-router-dom';

const SearchWidget = ({ 
  compact = false, 
  showExamples = true 
}) => {
  const [query, setQuery] = useState('');

  const handleSearch = () => {
    if (query.trim()) {
      // Navigate to advanced search with query
      window.location.href = `/advanced-search?q=${encodeURIComponent(query)}`;
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <Segment className="search-widget" style={{ margin: '2rem 0' }}>
      <Header as="h3" icon textAlign="center">
        <Icon name="search" />
        Advanced Knowledge Search
        <Header.Subheader>
          Search across all your knowledge items with AI-powered similarity
        </Header.Subheader>
      </Header>
      
      <Grid centered>
        <Grid.Column width={12}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <Input
              fluid
              placeholder="Search your knowledge base..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              action={
                <Button 
                  primary 
                  onClick={handleSearch}
                  disabled={!query.trim()}
                >
                  <Icon name="search" />
                  Search
                </Button>
              }
            />
          </div>
          
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <Button as={Link} to="/advanced-search" size="small">
              <Icon name="options" />
              Advanced Search Options
            </Button>
          </div>
          
          {showExamples && (
            <Message info style={{ marginTop: '1rem' }}>
              <Message.Header>Search Examples:</Message.Header>
              <p>
                • "machine learning algorithms"<br/>
                • "project management techniques"<br/>
                • "research methodology"
              </p>
            </Message>
          )}
        </Grid.Column>
      </Grid>
    </Segment>
  );
};

export default SearchWidget; 