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
  Message
} from 'semantic-ui-react';

const AdvancedSearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

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
          type: 'Research Note'
        }
      ]);
      setLoading(false);
    }, 1000);
  };

  return (
    <Container style={{ padding: '2rem 0' }}>
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
            />
            <Form.Button 
              width={4}
              primary 
              onClick={handleSearch}
              loading={loading}
              disabled={!query.trim()}
            >
              <Icon name="search" />
              Search
            </Form.Button>
          </Form.Group>
        </Form>
      </Segment>

      <Grid columns={2} stackable>
        <Grid.Column width={4}>
          <Segment>
            <Header as="h4">Search Filters</Header>
            <Form>
              <Form.Select
                label="Content Type"
                placeholder="All Types"
                options={[
                  { key: 'all', value: 'all', text: 'All Types' },
                  { key: 'note', value: 'note', text: 'Research Notes' },
                  { key: 'goal', value: 'goal', text: 'Learning Goals' },
                  { key: 'bookmark', value: 'bookmark', text: 'Bookmarks' }
                ]}
              />
              
              <Form.Field>
                <label>Similarity Threshold</label>
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.1" 
                  defaultValue="0.5"
                  style={{ width: '100%' }}
                />
              </Form.Field>
              
              <Form.Checkbox label="Include archived items" />
              <Form.Checkbox label="Search in content body" />
            </Form>
          </Segment>
        </Grid.Column>
        
        <Grid.Column width={12}>
          <Segment>
            <Header as="h4">Search Results</Header>
            
            {loading ? (
              <Message icon>
                <Icon name="circle notched" loading />
                <Message.Content>
                  <Message.Header>Searching...</Message.Header>
                  Analyzing your knowledge base with AI-powered similarity matching
                </Message.Content>
              </Message>
            ) : results.length > 0 ? (
              <div>
                {results.map(result => (
                  <Segment key={result.id}>
                    <Header as="h5">{result.title}</Header>
                    <p>{result.description}</p>
                    <Button size="small" primary>View Details</Button>
                  </Segment>
                ))}
              </div>
            ) : query ? (
              <Message info>
                <Message.Header>No Results Found</Message.Header>
                <p>Try adjusting your search query or filters.</p>
              </Message>
            ) : (
              <Message>
                <Message.Header>Welcome to Advanced Search</Message.Header>
                <p>Enter a search query above to find relevant knowledge items using AI-powered similarity matching.</p>
                
                <Divider />
                
                <Header as="h5">Search Tips:</Header>
                <ul>
                  <li>Use descriptive phrases for better results</li>
                  <li>Try different keyword combinations</li>
                  <li>Adjust the similarity threshold for broader or narrower results</li>
                  <li>Use content type filters to narrow your search</li>
                </ul>
              </Message>
            )}
          </Segment>
        </Grid.Column>
      </Grid>
      
      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <Button as="a" href="/" basic>
          <Icon name="arrow left" />
          Back to Homepage
        </Button>
      </div>
    </Container>
  );
};

export default AdvancedSearchPage; 