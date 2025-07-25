import React, { useState, useMemo } from 'react';
import {
  Segment,
  Header,
  Icon,
  Grid,
  Card,
  Label,
  Progress,
  Button,
  List,
  Message,
  Dropdown,
  Table,
  Modal,
  Form,
  Statistic
} from 'semantic-ui-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, TreeMap } from 'recharts';
import PropTypes from 'prop-types';

const importanceLevels = {
  low: { color: 'green', priority: 1 },
  medium: { color: 'yellow', priority: 2 },
  high: { color: 'orange', priority: 3 },
  critical: { color: 'red', priority: 4 }
};

const KnowledgeGapAnalysis = ({ 
  knowledgeGaps = [], 
  learningResources = [],
  onGapUpdate,
  onResourceLink 
}) => {
  const [selectedImportance, setSelectedImportance] = useState('all');
  const [viewMode, setViewMode] = useState('cards'); // cards, treemap, priority
  const [linkingGap, setLinkingGap] = useState(null);
  const [selectedResources, setSelectedResources] = useState([]);

  // Filter gaps by importance
  const filteredGaps = useMemo(() => {
    if (selectedImportance === 'all') return knowledgeGaps;
    return knowledgeGaps.filter(gap => gap.importance === selectedImportance);
  }, [knowledgeGaps, selectedImportance]);

  // Sort gaps by priority
  const sortedGaps = useMemo(() => {
    return [...filteredGaps].sort((a, b) => {
      const priorityA = importanceLevels[a.importance]?.priority || 0;
      const priorityB = importanceLevels[b.importance]?.priority || 0;
      return priorityB - priorityA;
    });
  }, [filteredGaps]);

  // Prepare data for treemap
  const treemapData = useMemo(() => {
    const grouped = {};
    
    filteredGaps.forEach(gap => {
      const category = gap.category || 'General';
      if (!grouped[category]) {
        grouped[category] = {
          name: category,
          children: []
        };
      }
      
      grouped[category].children.push({
        name: gap.gap_description.substring(0, 50) + '...',
        size: importanceLevels[gap.importance]?.priority || 1,
        fullDescription: gap.gap_description,
        importance: gap.importance,
        confidence: gap.confidence,
        suggestedTopics: gap.suggested_topics || []
      });
    });

    return {
      name: 'Knowledge Gaps',
      children: Object.values(grouped)
    };
  }, [filteredGaps]);

  // Calculate statistics
  const statistics = useMemo(() => {
    const stats = {
      total: knowledgeGaps.length,
      byImportance: {},
      avgConfidence: 0,
      topTopics: {}
    };

    Object.keys(importanceLevels).forEach(level => {
      stats.byImportance[level] = knowledgeGaps.filter(gap => gap.importance === level).length;
    });

    stats.avgConfidence = knowledgeGaps.length > 0
      ? knowledgeGaps.reduce((sum, gap) => sum + (gap.confidence || 0), 0) / knowledgeGaps.length
      : 0;

    // Count suggested topics
    knowledgeGaps.forEach(gap => {
      (gap.suggested_topics || []).forEach(topic => {
        stats.topTopics[topic] = (stats.topTopics[topic] || 0) + 1;
      });
    });

    return stats;
  }, [knowledgeGaps]);

  const handleResourceLink = () => {
    if (linkingGap && selectedResources.length > 0 && onResourceLink) {
      onResourceLink(linkingGap.id, selectedResources);
      setLinkingGap(null);
      setSelectedResources([]);
    }
  };

  const renderGapCard = (gap) => {
    const importanceInfo = importanceLevels[gap.importance] || importanceLevels.medium;
    
    return (
      <Card key={gap.id} color={importanceInfo.color}>
        <Card.Content>
          <Label color={importanceInfo.color} ribbon>
            {gap.importance}
          </Label>
          <Card.Header style={{ marginTop: '0.5em' }}>
            Knowledge Gap
          </Card.Header>
          <Card.Description>
            {gap.gap_description}
          </Card.Description>
        </Card.Content>
        <Card.Content extra>
          <div style={{ marginBottom: '0.5em' }}>
            <Icon name="chart line" />
            Confidence: {(gap.confidence * 100).toFixed(0)}%
            <Progress 
              percent={gap.confidence * 100} 
              size="tiny" 
              color="blue"
              style={{ marginTop: '0.25em' }}
            />
          </div>
          {gap.suggested_topics && gap.suggested_topics.length > 0 && (
            <div>
              <Icon name="tags" />
              Suggested Topics:
              <div style={{ marginTop: '0.25em' }}>
                {gap.suggested_topics.map((topic, idx) => (
                  <Label key={idx} size="tiny" style={{ margin: '0.1em' }}>
                    {topic}
                  </Label>
                ))}
              </div>
            </div>
          )}
        </Card.Content>
        <Card.Content extra>
          <Button.Group size="tiny" fluid>
            <Button 
              icon="linkify" 
              content="Link Resources"
              onClick={() => setLinkingGap(gap)}
            />
            {onGapUpdate && (
              <Button 
                icon="check" 
                content="Mark Addressed"
                onClick={() => onGapUpdate(gap.id, { status: 'addressed' })}
              />
            )}
          </Button.Group>
        </Card.Content>
      </Card>
    );
  };

  const renderTreeMap = () => (
    <Segment>
      <Header as="h4">Knowledge Gap Hierarchy</Header>
      <div style={{ height: '500px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <TreeMap
            data={[treemapData]}
            dataKey="size"
            ratio={4/3}
            stroke="#fff"
            fill="#8884d8"
            content={({ root, depth, x, y, width, height, index, colors, name }) => {
              const gap = root.children?.find(item => item.name === name);
              const color = gap ? importanceLevels[gap.importance]?.color : '#8884d8';
              
              return (
                <g>
                  <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    style={{
                      fill: depth === 1 ? '#fafafa' : color,
                      stroke: '#fff',
                      strokeWidth: 2 / (depth + 1e-10),
                      strokeOpacity: 1 / (depth + 1e-10),
                    }}
                  />
                  {depth === 1 && (
                    <text
                      x={x + width / 2}
                      y={y + height / 2}
                      textAnchor="middle"
                      fill="#000"
                      fontSize={14}
                    >
                      {name}
                    </text>
                  )}
                  {depth === 2 && width > 50 && height > 30 && (
                    <text
                      x={x + 4}
                      y={y + 18}
                      fill="#fff"
                      fontSize={12}
                      fillOpacity={0.9}
                    >
                      {name.substring(0, Math.floor(width / 8))}
                    </text>
                  )}
                </g>
              );
            }}
          />
        </ResponsiveContainer>
      </div>
    </Segment>
  );

  const renderPriorityMatrix = () => (
    <Segment>
      <Header as="h4">Gap Priority Matrix</Header>
      <Table celled>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Priority</Table.HeaderCell>
            <Table.HeaderCell>Gap Description</Table.HeaderCell>
            <Table.HeaderCell>Confidence</Table.HeaderCell>
            <Table.HeaderCell>Suggested Topics</Table.HeaderCell>
            <Table.HeaderCell>Actions</Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {sortedGaps.map(gap => {
            const importanceInfo = importanceLevels[gap.importance] || importanceLevels.medium;
            
            return (
              <Table.Row key={gap.id}>
                <Table.Cell>
                  <Label color={importanceInfo.color}>
                    {gap.importance}
                  </Label>
                </Table.Cell>
                <Table.Cell>{gap.gap_description}</Table.Cell>
                <Table.Cell>
                  <Progress 
                    percent={gap.confidence * 100} 
                    size="tiny" 
                    color="blue"
                  />
                </Table.Cell>
                <Table.Cell>
                  {(gap.suggested_topics || []).map((topic, idx) => (
                    <Label key={idx} size="tiny" style={{ margin: '0.1em' }}>
                      {topic}
                    </Label>
                  ))}
                </Table.Cell>
                <Table.Cell>
                  <Button.Group size="tiny">
                    <Button 
                      icon="linkify" 
                      onClick={() => setLinkingGap(gap)}
                    />
                    {onGapUpdate && (
                      <Button 
                        icon="check" 
                        color="green"
                        onClick={() => onGapUpdate(gap.id, { status: 'addressed' })}
                      />
                    )}
                  </Button.Group>
                </Table.Cell>
              </Table.Row>
            );
          })}
        </Table.Body>
      </Table>
    </Segment>
  );

  const topTopics = Object.entries(statistics.topTopics)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  return (
    <Segment>
      <Header as="h2">
        <Icon name="search" />
        <Header.Content>
          Knowledge Gap Analysis
          <Header.Subheader>Identify and prioritize learning gaps</Header.Subheader>
        </Header.Content>
      </Header>

      {/* Statistics Overview */}
      <Card.Group itemsPerRow={5}>
        <Card>
          <Card.Content textAlign="center">
            <Statistic size="tiny">
              <Statistic.Value>{statistics.total}</Statistic.Value>
              <Statistic.Label>Total Gaps</Statistic.Label>
            </Statistic>
          </Card.Content>
        </Card>
        {Object.entries(importanceLevels).map(([level, info]) => (
          <Card key={level} color={info.color}>
            <Card.Content textAlign="center">
              <Statistic size="tiny">
                <Statistic.Value>{statistics.byImportance[level] || 0}</Statistic.Value>
                <Statistic.Label>{level}</Statistic.Label>
              </Statistic>
            </Card.Content>
          </Card>
        ))}
      </Card.Group>

      {/* Filters and View Controls */}
      <Grid style={{ marginTop: '1em' }}>
        <Grid.Row>
          <Grid.Column width={8}>
            <Dropdown
              placeholder="Filter by Importance"
              fluid
              selection
              options={[
                { key: 'all', text: 'All Importance Levels', value: 'all' },
                ...Object.keys(importanceLevels).map(level => ({
                  key: level,
                  text: level.charAt(0).toUpperCase() + level.slice(1),
                  value: level
                }))
              ]}
              value={selectedImportance}
              onChange={(e, { value }) => setSelectedImportance(value)}
            />
          </Grid.Column>
          <Grid.Column width={8}>
            <Button.Group fluid>
              <Button 
                active={viewMode === 'cards'}
                onClick={() => setViewMode('cards')}
                icon="th"
                content="Cards"
              />
              <Button 
                active={viewMode === 'treemap'}
                onClick={() => setViewMode('treemap')}
                icon="tree"
                content="Tree Map"
              />
              <Button 
                active={viewMode === 'priority'}
                onClick={() => setViewMode('priority')}
                icon="ordered list"
                content="Priority"
              />
            </Button.Group>
          </Grid.Column>
        </Grid.Row>
      </Grid>

      {/* Top Suggested Topics */}
      {topTopics.length > 0 && (
        <Message info>
          <Message.Header>Most Frequently Suggested Topics</Message.Header>
          <Message.Content>
            {topTopics.map(([topic, count]) => (
              <Label key={topic} style={{ margin: '0.2em' }}>
                {topic}
                <Label.Detail>{count}</Label.Detail>
              </Label>
            ))}
          </Message.Content>
        </Message>
      )}

      {/* Main Content */}
      {filteredGaps.length === 0 ? (
        <Segment placeholder textAlign="center">
          <Header icon>
            <Icon name="search" />
            No knowledge gaps found
          </Header>
          <p>Great! No gaps identified with the current filters.</p>
        </Segment>
      ) : (
        <>
          {viewMode === 'cards' && (
            <Card.Group itemsPerRow={3} style={{ marginTop: '1em' }}>
              {sortedGaps.map(gap => renderGapCard(gap))}
            </Card.Group>
          )}
          {viewMode === 'treemap' && renderTreeMap()}
          {viewMode === 'priority' && renderPriorityMatrix()}
        </>
      )}

      {/* Resource Linking Modal */}
      <Modal
        open={!!linkingGap}
        onClose={() => {
          setLinkingGap(null);
          setSelectedResources([]);
        }}
        size="small"
      >
        <Modal.Header>Link Learning Resources</Modal.Header>
        <Modal.Content>
          {linkingGap && (
            <>
              <Header as="h4">Gap: {linkingGap.gap_description}</Header>
              <Form>
                <Form.Field>
                  <label>Select Resources</label>
                  <Dropdown
                    placeholder="Choose learning resources"
                    fluid
                    multiple
                    selection
                    options={learningResources.map(resource => ({
                      key: resource.id,
                      text: resource.title,
                      value: resource.id,
                      description: resource.type
                    }))}
                    value={selectedResources}
                    onChange={(e, { value }) => setSelectedResources(value)}
                  />
                </Form.Field>
              </Form>
              {linkingGap.suggested_topics && linkingGap.suggested_topics.length > 0 && (
                <Message>
                  <Message.Header>Suggested Topics</Message.Header>
                  <Message.Content>
                    {linkingGap.suggested_topics.map((topic, idx) => (
                      <Label key={idx} size="small" style={{ margin: '0.1em' }}>
                        {topic}
                      </Label>
                    ))}
                  </Message.Content>
                </Message>
              )}
            </>
          )}
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => {
            setLinkingGap(null);
            setSelectedResources([]);
          }}>
            Cancel
          </Button>
          <Button 
            primary 
            onClick={handleResourceLink}
            disabled={selectedResources.length === 0}
          >
            Link Resources
          </Button>
        </Modal.Actions>
      </Modal>
    </Segment>
  );
};

KnowledgeGapAnalysis.propTypes = {
  knowledgeGaps: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    gap_description: PropTypes.string.isRequired,
    importance: PropTypes.oneOf(['low', 'medium', 'high', 'critical']).isRequired,
    suggested_topics: PropTypes.arrayOf(PropTypes.string),
    confidence: PropTypes.number,
    category: PropTypes.string
  })),
  learningResources: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    type: PropTypes.string
  })),
  onGapUpdate: PropTypes.func,
  onResourceLink: PropTypes.func
};

export default KnowledgeGapAnalysis;