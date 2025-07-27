import React, { useState, useEffect } from 'react';
import { 
  Form, 
  Button, 
  Segment, 
  Header, 
  Icon, 
  Grid,
  Card,
  Search,
  Label,
  Message,
  Dropdown
} from 'semantic-ui-react';

const SimilarContentFinder = ({ onResults, onLoading, onError }) => {
  const [uid, setUid] = useState('');
  const [selectedContent, setSelectedContent] = useState(null);
  const [searchMode, setSearchMode] = useState('uid'); // uid, browse
  const [browseResults, setBrowseResults] = useState([]);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [similaritySettings, setSimilaritySettings] = useState({
    threshold: 0.6,
    limit: 10,
    sameTypeOnly: false
  });

  // Search for content to browse
  const searchContent = async (query) => {
    if (!query || query.length < 2) {
      setBrowseResults([]);
      return;
    }

    setBrowseLoading(true);
    try {
      const response = await fetch(`/@search?SearchableText=${encodeURIComponent(query)}&metadata_fields=UID,title,description,portal_type`, {
        headers: { 'Accept': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        setBrowseResults(data.items || []);
      }
    } catch (err) {
      console.warn('Browse search failed:', err);
    } finally {
      setBrowseLoading(false);
    }
  };

  // Find similar content
  const findSimilar = async (targetUid = uid) => {
    if (!targetUid) {
      onError && onError('Please provide a content UID or select content to analyze');
      return;
    }

    onLoading && onLoading(true);
    onError && onError(null);

    try {
      const params = new URLSearchParams({
        uid: targetUid,
        limit: similaritySettings.limit,
        threshold: similaritySettings.threshold,
        same_type: similaritySettings.sameTypeOnly ? 'true' : 'false'
      });

      const response = await fetch(`/@vector-search/find_similar?${params}`, {
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Similar search failed: ${response.statusText}`);
      }

      const results = await response.json();
      onResults && onResults(results);

    } catch (err) {
      onError && onError(err.message);
    } finally {
      onLoading && onLoading(false);
    }
  };

  // Handle content selection from browse results
  const handleContentSelect = (content) => {
    setSelectedContent(content);
    setUid(content.UID);
    setBrowseResults([]);
  };

  // Search result renderer for browse mode
  const resultRenderer = ({ title, description, portal_type, UID }) => (
    <div key={UID}>
      <div className="content-browse-item">
        <div className="title">{title}</div>
        <div className="description">{description}</div>
        <Label size="mini" color="blue">{portal_type}</Label>
      </div>
    </div>
  );

  return (
    <div className="similar-content-finder">
      <Segment>
        <Header as="h4">
          <Icon name="clone" />
          Find Similar Content
          <Header.Subheader>
            Discover content semantically similar to any item in your knowledge base
          </Header.Subheader>
        </Header>

        {/* Search Mode Selection */}
        <Grid columns={2}>
          <Grid.Column>
            <Button.Group fluid>
              <Button 
                active={searchMode === 'uid'}
                onClick={() => setSearchMode('uid')}
                icon="code"
                content="By UID"
              />
              <Button 
                active={searchMode === 'browse'}
                onClick={() => setSearchMode('browse')}
                icon="search"
                content="Browse & Select"
              />
            </Button.Group>
          </Grid.Column>
          <Grid.Column>
            <Dropdown
              selection
              fluid
              value={similaritySettings.limit}
              onChange={(e, { value }) => 
                setSimilaritySettings(prev => ({ ...prev, limit: value }))
              }
              options={[
                { key: 5, text: '5 results', value: 5 },
                { key: 10, text: '10 results', value: 10 },
                { key: 15, text: '15 results', value: 15 },
                { key: 20, text: '20 results', value: 20 }
              ]}
            />
          </Grid.Column>
        </Grid>

        {/* UID Input Mode */}
        {searchMode === 'uid' && (
          <Form style={{ marginTop: '1rem' }}>
            <Form.Field>
              <label>Content UID</label>
              <Form.Input
                value={uid}
                onChange={(e, { value }) => setUid(value)}
                placeholder="Enter the UID of content to find similar items for..."
                action={{
                  icon: 'clone',
                  content: 'Find Similar',
                  color: 'blue',
                  onClick: () => findSimilar(),
                  disabled: !uid.trim()
                }}
              />
              <small>
                You can find the UID in the URL or metadata of any content item
              </small>
            </Form.Field>
          </Form>
        )}

        {/* Browse & Select Mode */}
        {searchMode === 'browse' && (
          <div style={{ marginTop: '1rem' }}>
            <Search
              fluid
              loading={browseLoading}
              onSearchChange={(e, { value }) => searchContent(value)}
              results={browseResults}
              resultRenderer={resultRenderer}
              onResultSelect={(e, { result }) => handleContentSelect(result)}
              placeholder="Search for content to analyze..."
              noResultsMessage="No content found"
            />

            {selectedContent && (
              <Card fluid style={{ marginTop: '1rem' }}>
                <Card.Content>
                  <Card.Header>
                    <Icon name="checkmark" color="green" />
                    Selected Content
                  </Card.Header>
                  <Card.Meta>
                    <Label color="blue">{selectedContent.portal_type}</Label>
                    <span>UID: {selectedContent.UID}</span>
                  </Card.Meta>
                  <Card.Description>
                    <strong>{selectedContent.title}</strong>
                    <br />
                    {selectedContent.description}
                  </Card.Description>
                </Card.Content>
                <Card.Content extra>
                  <Button 
                    color="blue"
                    icon="clone"
                    content="Find Similar Content"
                    onClick={() => findSimilar(selectedContent.UID)}
                    fluid
                  />
                </Card.Content>
              </Card>
            )}
          </div>
        )}

        {/* Similarity Settings */}
        <Segment basic>
          <Header as="h5">Similarity Settings</Header>
          <Grid columns={3}>
            <Grid.Column>
              <Form.Field>
                <label>Similarity Threshold: {(similaritySettings.threshold * 100).toFixed(0)}%</label>
                <input 
                  type="range"
                  min="0.3"
                  max="1.0"
                  step="0.1"
                  value={similaritySettings.threshold}
                  onChange={(e) => 
                    setSimilaritySettings(prev => ({ 
                      ...prev, 
                      threshold: parseFloat(e.target.value) 
                    }))
                  }
                />
                <small>Higher = more similar results</small>
              </Form.Field>
            </Grid.Column>
            <Grid.Column>
              <Form.Field>
                <label>Result Limit</label>
                <Dropdown
                  selection
                  value={similaritySettings.limit}
                  onChange={(e, { value }) => 
                    setSimilaritySettings(prev => ({ ...prev, limit: value }))
                  }
                  options={[
                    { key: 5, text: '5 results', value: 5 },
                    { key: 10, text: '10 results', value: 10 },
                    { key: 15, text: '15 results', value: 15 },
                    { key: 20, text: '20 results', value: 20 }
                  ]}
                />
              </Form.Field>
            </Grid.Column>
            <Grid.Column>
              <Form.Field>
                <label style={{ display: 'block', marginBottom: '0.5rem' }}>Content Type</label>
                <Form.Checkbox
                  label="Same type only"
                  checked={similaritySettings.sameTypeOnly}
                  onChange={(e, { checked }) => 
                    setSimilaritySettings(prev => ({ ...prev, sameTypeOnly: checked }))
                  }
                />
                <small>Limit to same content type</small>
              </Form.Field>
            </Grid.Column>
          </Grid>
        </Segment>

        {/* Quick Examples */}
        <Message info>
          <Message.Header>
            <Icon name="lightbulb" />
            How it works
          </Message.Header>
          <Message.List>
            <Message.Item>
              <strong>By UID:</strong> Enter the unique identifier of any content item to find semantically similar content
            </Message.Item>
            <Message.Item>
              <strong>Browse & Select:</strong> Search for content by title and select it to analyze similarity
            </Message.Item>
            <Message.Item>
              <strong>Similarity Threshold:</strong> Higher values return more precise matches, lower values return broader results
            </Message.Item>
          </Message.List>
        </Message>
      </Segment>
    </div>
  );
};

export default SimilarContentFinder; 