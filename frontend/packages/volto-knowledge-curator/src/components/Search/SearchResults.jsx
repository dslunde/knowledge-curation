import React, { useState } from 'react';
import { 
  Segment, 
  Header, 
  Card, 
  Label, 
  Button, 
  Icon, 
  Grid,
  Progress,
  Message,
  Dimmer,
  Loader,
  Statistic,
  Divider,
  Popup,
  List
} from 'semantic-ui-react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

const SearchResults = ({ 
  results = [], 
  loading = false, 
  error = null,
  searchMode = 'semantic',
  stats = null,
  onSimilarSearch,
  onBookmark,
  onShare
}) => {
  const [sortBy, setSortBy] = useState('relevance');
  const [viewMode, setViewMode] = useState('cards'); // cards, list, detailed

  // Get content type icon
  const getContentTypeIcon = (contentType) => {
    const iconMap = {
      'KnowledgeItem': 'lightbulb',
      'ResearchNote': 'lab',
      'BookmarkPlus': 'bookmark',
      'LearningGoal': 'target',
      'ProjectLog': 'clipboard list',
      'KnowledgeContainer': 'archive'
    };
    return iconMap[contentType] || 'file';
  };

  // Get content type color
  const getContentTypeColor = (contentType) => {
    const colorMap = {
      'KnowledgeItem': 'blue',
      'ResearchNote': 'green',
      'BookmarkPlus': 'orange',
      'LearningGoal': 'purple',
      'ProjectLog': 'brown',
      'KnowledgeContainer': 'grey'
    };
    return colorMap[contentType] || 'grey';
  };

  // Format similarity score
  const formatScore = (score) => {
    if (typeof score !== 'number') return null;
    return (score * 100).toFixed(1);
  };

  // Get score color
  const getScoreColor = (score) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'yellow';
    if (score >= 0.4) return 'orange';
    return 'red';
  };

  // Sort results
  const sortedResults = [...results].sort((a, b) => {
    switch (sortBy) {
      case 'relevance':
        return (b.score || 0) - (a.score || 0);
      case 'date':
        return new Date(b.modified || b.created) - new Date(a.modified || a.created);
      case 'title':
        return (a.title || '').localeCompare(b.title || '');
      case 'type':
        return (a.content_type || a['@type'] || '').localeCompare(b.content_type || b['@type'] || '');
      default:
        return 0;
    }
  });

  // Render loading state
  if (loading) {
    return (
      <Segment>
        <Dimmer active>
          <Loader size="large">Searching knowledge base...</Loader>
        </Dimmer>
        <div style={{ height: '200px' }} />
      </Segment>
    );
  }

  // Render error state
  if (error) {
    return (
      <Message negative>
        <Message.Header>Search Error</Message.Header>
        <p>{error}</p>
        <Button 
          icon="refresh" 
          content="Try Again" 
          onClick={() => window.location.reload()}
        />
      </Message>
    );
  }

  // Render empty state
  if (!results.length && stats) {
    return (
      <Message info>
        <Message.Header>No Results Found</Message.Header>
        <p>
          No content matches your search criteria. Try:
        </p>
        <List bulleted>
          <List.Item>Using different keywords</List.Item>
          <List.Item>Reducing the similarity threshold</List.Item>
          <List.Item>Expanding content type filters</List.Item>
          <List.Item>Trying semantic search for concept-based queries</List.Item>
        </List>
      </Message>
    );
  }

  // Render result card
  const renderResultCard = (result, index) => {
    const contentType = result.content_type || result['@type'];
    const score = result.score;
    const hasScore = typeof score === 'number';
    
    return (
      <Card key={result.uid || result['@id'] || index} fluid className="search-result-card">
        <Card.Content>
          <Card.Header>
            <Grid>
              <Grid.Column width={12}>
                <Icon 
                  name={getContentTypeIcon(contentType)} 
                  color={getContentTypeColor(contentType)}
                />
                <Link to={result.url || result['@id']} className="result-title">
                  {result.title}
                </Link>
              </Grid.Column>
              <Grid.Column width={4} textAlign="right">
                {hasScore && (
                  <Popup
                    content={`Similarity score: ${formatScore(score)}%`}
                    trigger={
                      <Progress 
                        percent={formatScore(score)}
                        color={getScoreColor(score)}
                        size="tiny"
                        className="score-progress"
                      />
                    }
                  />
                )}
              </Grid.Column>
            </Grid>
          </Card.Header>
          
          <Card.Meta>
            <Label 
              size="mini" 
              color={getContentTypeColor(contentType)}
            >
              {contentType}
            </Label>
            {result.workflow_state && (
              <Label size="mini" basic>
                {result.workflow_state}
              </Label>
            )}
            {result.modified && (
              <span className="date">
                <Icon name="clock" />
                {formatDistanceToNow(new Date(result.modified), { addSuffix: true })}
              </span>
            )}
          </Card.Meta>

          {result.description && (
            <Card.Description>
              {result.description.length > 200 
                ? `${result.description.substring(0, 200)}...`
                : result.description
              }
            </Card.Description>
          )}

          {/* Tags */}
          {result.tags && result.tags.length > 0 && (
            <div className="result-tags">
              {result.tags.slice(0, 5).map((tag, tagIndex) => (
                <Label key={tagIndex} size="tiny" basic>
                  {tag}
                </Label>
              ))}
              {result.tags.length > 5 && (
                <Label size="tiny" basic>
                  +{result.tags.length - 5} more
                </Label>
              )}
            </div>
          )}

          {/* Additional metadata for specific content types */}
          {contentType === 'KnowledgeItem' && result.difficulty_level && (
            <div className="result-metadata">
              <Label size="mini" color="blue">
                <Icon name="graduation cap" />
                {result.difficulty_level}
              </Label>
            </div>
          )}

          {contentType === 'ResearchNote' && result.research_method && (
            <div className="result-metadata">
              <Label size="mini" color="green">
                <Icon name="lab" />
                {result.research_method}
              </Label>
            </div>
          )}
        </Card.Content>

        <Card.Content extra>
          <Button.Group size="mini" basic>
            <Button 
              icon="eye" 
              content="View"
              as={Link}
              to={result.url || result['@id']}
            />
            <Button 
              icon="clone" 
              content="Find Similar"
              onClick={() => onSimilarSearch && onSimilarSearch(result.uid || result['@id'])}
            />
            <Button 
              icon="bookmark" 
              content="Bookmark"
              onClick={() => onBookmark && onBookmark(result)}
            />
            <Button 
              icon="share" 
              content="Share"
              onClick={() => onShare && onShare(result)}
            />
          </Button.Group>
        </Card.Content>
      </Card>
    );
  };

  // Render result list item
  const renderResultListItem = (result, index) => {
    const contentType = result.content_type || result['@type'];
    const score = result.score;
    const hasScore = typeof score === 'number';
    
    return (
      <List.Item key={result.uid || result['@id'] || index} className="search-result-list-item">
        <List.Content>
          <List.Header>
            <Grid>
              <Grid.Column width={10}>
                <Icon 
                  name={getContentTypeIcon(contentType)} 
                  color={getContentTypeColor(contentType)}
                />
                <Link to={result.url || result['@id']}>
                  {result.title}
                </Link>
              </Grid.Column>
              <Grid.Column width={3}>
                <Label size="mini" color={getContentTypeColor(contentType)}>
                  {contentType}
                </Label>
              </Grid.Column>
              <Grid.Column width={3} textAlign="right">
                {hasScore && (
                  <Label size="mini" color={getScoreColor(score)}>
                    {formatScore(score)}%
                  </Label>
                )}
              </Grid.Column>
            </Grid>
          </List.Header>
          <List.Description>
            {result.description && result.description.substring(0, 150)}
            {result.description && result.description.length > 150 && '...'}
          </List.Description>
        </List.Content>
      </List.Item>
    );
  };

  return (
    <div className="search-results">
      {/* Results Header */}
      {stats && (
        <Segment>
          <Grid>
            <Grid.Column width={8}>
              <Statistic.Group size="mini">
                <Statistic>
                  <Statistic.Value>{stats.total}</Statistic.Value>
                  <Statistic.Label>Results</Statistic.Label>
                </Statistic>
                {stats.queryTime && (
                  <Statistic>
                    <Statistic.Value>{stats.queryTime}ms</Statistic.Value>
                    <Statistic.Label>Query Time</Statistic.Label>
                  </Statistic>
                )}
              </Statistic.Group>
              <div className="search-mode-indicator">
                <Label color="blue">
                  <Icon name={searchMode === 'semantic' ? 'brain' : 'search'} />
                  {searchMode} search
                </Label>
              </div>
            </Grid.Column>
            
            <Grid.Column width={8} textAlign="right">
              <Button.Group size="mini">
                <Button 
                  icon="sort" 
                  content="Sort"
                  onClick={() => {
                    const options = ['relevance', 'date', 'title', 'type'];
                    const currentIndex = options.indexOf(sortBy);
                    const nextIndex = (currentIndex + 1) % options.length;
                    setSortBy(options[nextIndex]);
                  }}
                />
                <Button.Or />
                <Button 
                  icon={viewMode === 'cards' ? 'list' : 'grid layout'}
                  onClick={() => setViewMode(viewMode === 'cards' ? 'list' : 'cards')}
                />
              </Button.Group>
            </Grid.Column>
          </Grid>
        </Segment>
      )}

      {/* Results Display */}
      <Segment>
        {viewMode === 'cards' ? (
          <Card.Group>
            {sortedResults.map(renderResultCard)}
          </Card.Group>
        ) : (
          <List divided relaxed>
            {sortedResults.map(renderResultListItem)}
          </List>
        )}
      </Segment>

      {/* Load More Button */}
      {results.length >= 20 && (
        <Segment textAlign="center">
          <Button 
            content="Load More Results" 
            icon="arrow down"
            size="large"
            basic
          />
        </Segment>
      )}
    </div>
  );
};

export default SearchResults; 