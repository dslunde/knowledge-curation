import React, { useState, useMemo } from 'react';
import {
  Segment,
  Header,
  Icon,
  Grid,
  Button,
  Dropdown,
  Card,
  Label,
  Table,
  Statistic,
  List
} from 'semantic-ui-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip, Legend, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import * as d3 from 'd3';
import PropTypes from 'prop-types';

const competencyLevels = {
  novice: 1,
  beginner: 2,
  intermediate: 3,
  advanced: 4,
  expert: 5
};

const levelColors = {
  novice: '#dc3545',
  beginner: '#fd7e14',
  intermediate: '#ffc107',
  advanced: '#28a745',
  expert: '#007bff'
};

const CompetencyMatrix = ({ competencies = [], timeRange = 'current' }) => {
  const [viewMode, setViewMode] = useState('radar'); // radar, heatmap, progression
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [comparisonMode, setComparisonMode] = useState(false);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(competencies.map(c => c.category || 'Uncategorized'));
    return ['all', ...Array.from(cats)];
  }, [competencies]);

  // Filter competencies by category
  const filteredCompetencies = useMemo(() => {
    if (selectedCategory === 'all') return competencies;
    return competencies.filter(c => (c.category || 'Uncategorized') === selectedCategory);
  }, [competencies, selectedCategory]);

  // Prepare data for radar chart
  const radarData = useMemo(() => {
    const groupedByCategory = {};
    
    filteredCompetencies.forEach(comp => {
      const category = comp.category || 'Uncategorized';
      if (!groupedByCategory[category]) {
        groupedByCategory[category] = {
          category,
          totalScore: 0,
          count: 0,
          competencies: []
        };
      }
      
      const score = competencyLevels[comp.level] || 1;
      groupedByCategory[category].totalScore += score;
      groupedByCategory[category].count += 1;
      groupedByCategory[category].competencies.push({
        name: comp.name,
        score: score,
        level: comp.level
      });
    });

    // Calculate average score per category
    return Object.values(groupedByCategory).map(cat => ({
      category: cat.category,
      score: cat.count > 0 ? cat.totalScore / cat.count : 0,
      fullScore: 5,
      count: cat.count,
      competencies: cat.competencies
    }));
  }, [filteredCompetencies]);

  // Prepare data for heatmap
  const heatmapData = useMemo(() => {
    const matrix = [];
    const competencyNames = filteredCompetencies.map(c => c.name);
    const categoryNames = [...new Set(filteredCompetencies.map(c => c.category || 'Uncategorized'))];
    
    categoryNames.forEach((category, i) => {
      competencyNames.forEach((competency, j) => {
        const comp = filteredCompetencies.find(c => c.name === competency && (c.category || 'Uncategorized') === category);
        if (comp) {
          matrix.push({
            category: i,
            competency: j,
            value: competencyLevels[comp.level] || 0,
            level: comp.level,
            categoryName: category,
            competencyName: competency
          });
        }
      });
    });
    
    return { matrix, competencyNames, categoryNames };
  }, [filteredCompetencies]);

  // Generate progression data (mock historical data for demonstration)
  const progressionData = useMemo(() => {
    // In a real implementation, this would come from historical data
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const data = [];
    
    const uniqueCategories = [...new Set(filteredCompetencies.map(c => c.category || 'Uncategorized'))];
    
    months.forEach((month, index) => {
      const monthData = { month };
      uniqueCategories.forEach(category => {
        // Simulate progression with some randomness
        const categoryComps = filteredCompetencies.filter(c => (c.category || 'Uncategorized') === category);
        const currentAvg = categoryComps.reduce((sum, c) => sum + (competencyLevels[c.level] || 1), 0) / categoryComps.length;
        // Add some variance for historical data
        monthData[category] = Math.max(1, Math.min(5, currentAvg - (5 - index) * 0.3 + Math.random() * 0.5));
      });
      data.push(monthData);
    });
    
    return { data, categories: uniqueCategories };
  }, [filteredCompetencies]);

  const renderRadarChart = () => (
    <Segment>
      <Header as="h4">Competency Radar Chart</Header>
      <div style={{ height: '500px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e0e0e0" />
            <PolarAngleAxis dataKey="category" />
            <PolarRadiusAxis angle={90} domain={[0, 5]} />
            <Radar 
              name="Current Level" 
              dataKey="score" 
              stroke="#8884d8" 
              fill="#8884d8" 
              fillOpacity={0.6}
            />
            {comparisonMode && (
              <Radar 
                name="Target Level" 
                dataKey="fullScore" 
                stroke="#82ca9d" 
                fill="#82ca9d" 
                fillOpacity={0.3}
              />
            )}
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <Card>
                      <Card.Content>
                        <Card.Header>{data.category}</Card.Header>
                        <Card.Meta>Average Score: {data.score.toFixed(2)}/5</Card.Meta>
                        <Card.Description>
                          <strong>Competencies ({data.count}):</strong>
                          <List>
                            {data.competencies.map((comp, idx) => (
                              <div key={idx}>
                                {comp.name}: <Label size="tiny" color={levelColors[comp.level]}>{comp.level}</Label>
                              </div>
                            ))}
                          </List>
                        </Card.Description>
                      </Card.Content>
                    </Card>
                  );
                }
                return null;
              }}
            />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </Segment>
  );

  const renderHeatmap = () => {
    // This would use D3 for a proper heatmap, but for simplicity, we'll use a table
    const { competencyNames, categoryNames } = heatmapData;
    
    return (
      <Segment>
        <Header as="h4">Competency Heatmap</Header>
        <div style={{ overflowX: 'auto' }}>
          <Table celled structured>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell rowSpan="2">Category</Table.HeaderCell>
                <Table.HeaderCell colSpan={competencyNames.length} textAlign="center">
                  Competencies
                </Table.HeaderCell>
              </Table.Row>
              <Table.Row>
                {competencyNames.map((name, idx) => (
                  <Table.HeaderCell key={idx} style={{ writingMode: 'vertical-lr', textOrientation: 'mixed' }}>
                    {name}
                  </Table.HeaderCell>
                ))}
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {categoryNames.map((category, catIdx) => (
                <Table.Row key={catIdx}>
                  <Table.Cell>{category}</Table.Cell>
                  {competencyNames.map((competency, compIdx) => {
                    const comp = filteredCompetencies.find(
                      c => c.name === competency && (c.category || 'Uncategorized') === category
                    );
                    const level = comp ? comp.level : null;
                    const score = comp ? competencyLevels[level] : 0;
                    
                    return (
                      <Table.Cell 
                        key={compIdx} 
                        style={{
                          backgroundColor: level ? levelColors[level] : '#f8f9fa',
                          opacity: score / 5,
                          textAlign: 'center'
                        }}
                      >
                        {score > 0 && (
                          <strong style={{ color: score > 3 ? 'white' : 'black' }}>
                            {score}
                          </strong>
                        )}
                      </Table.Cell>
                    );
                  })}
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </div>
        
        <Grid columns={5} style={{ marginTop: '1em' }}>
          {Object.entries(levelColors).map(([level, color]) => (
            <Grid.Column key={level}>
              <Label 
                style={{ backgroundColor: color, color: 'white', width: '100%', textAlign: 'center' }}
              >
                {level} ({competencyLevels[level]})
              </Label>
            </Grid.Column>
          ))}
        </Grid>
      </Segment>
    );
  };

  const renderProgression = () => {
    const { data, categories: progressionCategories } = progressionData;
    const colors = d3.schemeCategory10;
    
    return (
      <Segment>
        <Header as="h4">Competency Progression Over Time</Header>
        <div style={{ height: '400px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis domain={[0, 5]} />
              <Tooltip />
              <Legend />
              {progressionCategories.map((category, index) => (
                <Line
                  key={category}
                  type="monotone"
                  dataKey={category}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Segment>
    );
  };

  const exportData = () => {
    const exportObject = {
      competencies: filteredCompetencies,
      summary: {
        total: filteredCompetencies.length,
        byLevel: Object.entries(competencyLevels).reduce((acc, [level]) => {
          acc[level] = filteredCompetencies.filter(c => c.level === level).length;
          return acc;
        }, {}),
        byCategory: categories.filter(c => c !== 'all').reduce((acc, category) => {
          acc[category] = filteredCompetencies.filter(c => (c.category || 'Uncategorized') === category).length;
          return acc;
        }, {})
      },
      exportDate: new Date().toISOString()
    };
    
    console.log('Export data:', exportObject);
    // In a real implementation, this would download as JSON or CSV
  };

  return (
    <Segment>
      <Header as="h2">
        <Icon name="th" />
        <Header.Content>
          Competency Matrix
          <Header.Subheader>Visualize and track your skill levels across categories</Header.Subheader>
        </Header.Content>
      </Header>

      <Grid>
        <Grid.Row>
          <Grid.Column width={6}>
            <Dropdown
              placeholder="Filter by Category"
              fluid
              selection
              options={categories.map(cat => ({
                key: cat,
                text: cat === 'all' ? 'All Categories' : cat,
                value: cat
              }))}
              value={selectedCategory}
              onChange={(e, { value }) => setSelectedCategory(value)}
            />
          </Grid.Column>
          <Grid.Column width={6}>
            <Button.Group fluid>
              <Button 
                active={viewMode === 'radar'}
                onClick={() => setViewMode('radar')}
                icon="chart area"
                content="Radar"
              />
              <Button 
                active={viewMode === 'heatmap'}
                onClick={() => setViewMode('heatmap')}
                icon="th"
                content="Heatmap"
              />
              <Button 
                active={viewMode === 'progression'}
                onClick={() => setViewMode('progression')}
                icon="line graph"
                content="Progression"
              />
            </Button.Group>
          </Grid.Column>
          <Grid.Column width={4}>
            <Button.Group fluid>
              <Button 
                toggle
                active={comparisonMode}
                onClick={() => setComparisonMode(!comparisonMode)}
                icon="exchange"
                content="Compare"
              />
              <Button 
                icon="download"
                content="Export"
                onClick={exportData}
              />
            </Button.Group>
          </Grid.Column>
        </Grid.Row>
      </Grid>

      <Card.Group itemsPerRow={4} style={{ marginTop: '1em', marginBottom: '1em' }}>
        {Object.entries(competencyLevels).map(([level, score]) => {
          const count = filteredCompetencies.filter(c => c.level === level).length;
          return (
            <Card key={level} color={levelColors[level]}>
              <Card.Content textAlign="center">
                <Card.Header>{level}</Card.Header>
                <Card.Meta>Level {score}</Card.Meta>
                <Card.Description>
                  <Statistic size="mini">
                    <Statistic.Value>{count}</Statistic.Value>
                    <Statistic.Label>Competencies</Statistic.Label>
                  </Statistic>
                </Card.Description>
              </Card.Content>
            </Card>
          );
        })}
      </Card.Group>

      {viewMode === 'radar' && renderRadarChart()}
      {viewMode === 'heatmap' && renderHeatmap()}
      {viewMode === 'progression' && renderProgression()}
    </Segment>
  );
};

CompetencyMatrix.propTypes = {
  competencies: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string.isRequired,
    description: PropTypes.string,
    level: PropTypes.oneOf(['novice', 'beginner', 'intermediate', 'advanced', 'expert']).isRequired,
    category: PropTypes.string
  })),
  timeRange: PropTypes.string
};

export default CompetencyMatrix;