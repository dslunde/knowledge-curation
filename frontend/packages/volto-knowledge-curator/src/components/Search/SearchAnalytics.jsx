import React from 'react';
import { 
  Segment, 
  Header, 
  Statistic, 
  Icon, 
  Progress,
  List,
  Label
} from 'semantic-ui-react';

const SearchAnalytics = ({ analytics, currentStats }) => {
  // Mock analytics data - in real app this would come from backend
  const defaultAnalytics = {
    totalSearches: 1247,
    averageResultsPerSearch: 8.3,
    mostPopularTerms: [
      { term: "machine learning", count: 156 },
      { term: "data visualization", count: 134 },
      { term: "research methods", count: 89 },
      { term: "python programming", count: 76 },
      { term: "statistical analysis", count: 67 }
    ],
    searchModeDistribution: {
      semantic: 65,
      keyword: 25,
      similar: 10
    },
    averageQueryTime: 245
  };

  const data = analytics || defaultAnalytics;

  return (
    <Segment>
      <Header as="h4">
        <Icon name="chart line" />
        Search Analytics
      </Header>
      
      {/* Current Search Stats */}
      {currentStats && (
        <>
          <Header as="h5" color="blue">Current Search</Header>
          <Statistic.Group size="mini">
            <Statistic>
              <Statistic.Value>{currentStats.total}</Statistic.Value>
              <Statistic.Label>Results</Statistic.Label>
            </Statistic>
            {currentStats.queryTime && (
              <Statistic>
                <Statistic.Value>{currentStats.queryTime}ms</Statistic.Value>
                <Statistic.Label>Query Time</Statistic.Label>
              </Statistic>
            )}
          </Statistic.Group>
        </>
      )}

      {/* Overall Analytics */}
      <Header as="h5" color="grey">Overall Statistics</Header>
      <Statistic.Group size="mini">
        <Statistic>
          <Statistic.Value>{data.totalSearches}</Statistic.Value>
          <Statistic.Label>Total Searches</Statistic.Label>
        </Statistic>
        <Statistic>
          <Statistic.Value>{data.averageResultsPerSearch}</Statistic.Value>
          <Statistic.Label>Avg Results</Statistic.Label>
        </Statistic>
      </Statistic.Group>

      {/* Search Mode Distribution */}
      <div style={{ marginTop: '1rem' }}>
        <Header as="h6">Search Mode Usage</Header>
        <div className="search-mode-stats">
          <div className="mode-stat">
            <Label color="blue" size="mini">Semantic</Label>
            <Progress 
              percent={data.searchModeDistribution.semantic} 
              color="blue" 
              size="tiny"
            />
          </div>
          <div className="mode-stat">
            <Label color="green" size="mini">Keyword</Label>
            <Progress 
              percent={data.searchModeDistribution.keyword} 
              color="green" 
              size="tiny"
            />
          </div>
          <div className="mode-stat">
            <Label color="purple" size="mini">Similar</Label>
            <Progress 
              percent={data.searchModeDistribution.similar} 
              color="purple" 
              size="tiny"
            />
          </div>
        </div>
      </div>

      {/* Popular Terms */}
      <div style={{ marginTop: '1rem' }}>
        <Header as="h6">Popular Search Terms</Header>
        <List size="small">
          {data.mostPopularTerms.slice(0, 5).map((term, index) => (
            <List.Item key={index}>
              <List.Content>
                <List.Header>{term.term}</List.Header>
                <List.Description>
                  <Label size="mini" basic>{term.count} searches</Label>
                </List.Description>
              </List.Content>
            </List.Item>
          ))}
        </List>
      </div>

      {/* Performance */}
      <div style={{ marginTop: '1rem' }}>
        <Header as="h6">Performance</Header>
        <Statistic size="mini">
          <Statistic.Value>{data.averageQueryTime}ms</Statistic.Value>
          <Statistic.Label>Avg Query Time</Statistic.Label>
        </Statistic>
      </div>
    </Segment>
  );
};

export default SearchAnalytics; 