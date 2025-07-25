import React, { useState, useMemo } from 'react';
import {
  Segment,
  Header,
  Icon,
  Grid,
  Dropdown,
  Card,
  Statistic,
  Button,
  Message,
  Label,
  Table,
  Progress
} from 'semantic-ui-react';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ComposedChart,
  Bar,
  ReferenceLine
} from 'recharts';
import { format, parseISO, differenceInDays, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay } from 'date-fns';
import PropTypes from 'prop-types';

const LearningVelocityChart = ({ 
  learningData = [], 
  milestones = [],
  timeFrame = 'month' // week, month, quarter, year
}) => {
  const [selectedMetric, setSelectedMetric] = useState('milestones'); // milestones, competencies, knowledge
  const [viewMode, setViewMode] = useState('velocity'); // velocity, cumulative, projection
  const [showTrend, setShowTrend] = useState(true);

  // Calculate velocity metrics
  const velocityData = useMemo(() => {
    const now = new Date();
    let days, groupBy;
    
    switch (timeFrame) {
      case 'week':
        days = 7;
        groupBy = 'day';
        break;
      case 'month':
        days = 30;
        groupBy = 'week';
        break;
      case 'quarter':
        days = 90;
        groupBy = 'week';
        break;
      case 'year':
        days = 365;
        groupBy = 'month';
        break;
      default:
        days = 30;
        groupBy = 'week';
    }

    const startDate = addDays(now, -days);
    const dateRange = eachDayOfInterval({ start: startDate, end: now });

    // Group milestones by completion date
    const milestonesByDate = {};
    milestones.forEach(milestone => {
      if (milestone.completion_date && milestone.status === 'completed') {
        const date = format(parseISO(milestone.completion_date), 'yyyy-MM-dd');
        if (!milestonesByDate[date]) {
          milestonesByDate[date] = 0;
        }
        milestonesByDate[date]++;
      }
    });

    // Calculate daily/weekly/monthly velocities
    const velocityPoints = [];
    let cumulativeTotal = 0;
    
    dateRange.forEach(date => {
      const dateStr = format(date, 'yyyy-MM-dd');
      const completed = milestonesByDate[dateStr] || 0;
      cumulativeTotal += completed;
      
      velocityPoints.push({
        date: dateStr,
        displayDate: format(date, 'MMM dd'),
        completed,
        cumulative: cumulativeTotal,
        weekday: format(date, 'EEEE')
      });
    });

    // Calculate moving average (7-day)
    const movingAverage = velocityPoints.map((point, index) => {
      const start = Math.max(0, index - 6);
      const relevantPoints = velocityPoints.slice(start, index + 1);
      const avg = relevantPoints.reduce((sum, p) => sum + p.completed, 0) / relevantPoints.length;
      return {
        ...point,
        movingAverage: avg
      };
    });

    // Calculate statistics
    const totalCompleted = cumulativeTotal;
    const avgPerDay = totalCompleted / days;
    const avgPerWeek = avgPerDay * 7;
    const avgPerMonth = avgPerDay * 30;

    // Find peak performance
    const maxDay = Math.max(...velocityPoints.map(p => p.completed));
    const peakDays = velocityPoints.filter(p => p.completed === maxDay);

    // Calculate trend (simple linear regression)
    const n = movingAverage.length;
    const sumX = movingAverage.reduce((sum, _, i) => sum + i, 0);
    const sumY = movingAverage.reduce((sum, p) => sum + p.completed, 0);
    const sumXY = movingAverage.reduce((sum, p, i) => sum + i * p.completed, 0);
    const sumX2 = movingAverage.reduce((sum, _, i) => sum + i * i, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const trend = slope > 0.01 ? 'increasing' : slope < -0.01 ? 'decreasing' : 'stable';

    // Generate projection
    const projectionDays = 30;
    const projectedData = [];
    for (let i = 1; i <= projectionDays; i++) {
      const projectedDate = addDays(now, i);
      const projectedValue = avgPerDay + (slope * (n + i));
      projectedData.push({
        date: format(projectedDate, 'yyyy-MM-dd'),
        displayDate: format(projectedDate, 'MMM dd'),
        projected: Math.max(0, projectedValue),
        cumulativeProjected: cumulativeTotal + (avgPerDay * i)
      });
    }

    return {
      velocityPoints: movingAverage,
      statistics: {
        totalCompleted,
        avgPerDay: avgPerDay.toFixed(2),
        avgPerWeek: avgPerWeek.toFixed(1),
        avgPerMonth: avgPerMonth.toFixed(0),
        maxDay,
        peakDays,
        trend,
        trendSlope: slope
      },
      projectedData
    };
  }, [milestones, timeFrame]);

  // Calculate completion rates by category
  const categoryRates = useMemo(() => {
    const categories = {};
    
    milestones.forEach(milestone => {
      const category = milestone.category || 'Uncategorized';
      if (!categories[category]) {
        categories[category] = {
          total: 0,
          completed: 0,
          inProgress: 0,
          pending: 0
        };
      }
      
      categories[category].total++;
      if (milestone.status === 'completed') {
        categories[category].completed++;
      } else if (milestone.status === 'in_progress') {
        categories[category].inProgress++;
      } else {
        categories[category].pending++;
      }
    });

    return Object.entries(categories).map(([category, stats]) => ({
      category,
      ...stats,
      completionRate: stats.total > 0 ? (stats.completed / stats.total * 100).toFixed(1) : 0
    }));
  }, [milestones]);

  const renderVelocityChart = () => {
    const data = viewMode === 'projection' 
      ? [...velocityData.velocityPoints, ...velocityData.projectedData]
      : velocityData.velocityPoints;

    return (
      <div style={{ height: '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
          {viewMode === 'cumulative' ? (
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="displayDate" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="cumulative" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.6}
                name="Cumulative Milestones"
              />
              {viewMode === 'projection' && (
                <Area 
                  type="monotone" 
                  dataKey="cumulativeProjected" 
                  stroke="#82ca9d" 
                  fill="#82ca9d" 
                  fillOpacity={0.3}
                  strokeDasharray="5 5"
                  name="Projected"
                />
              )}
            </AreaChart>
          ) : (
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="displayDate" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar 
                dataKey="completed" 
                fill="#8884d8" 
                name="Completed per Day"
                opacity={0.6}
              />
              {showTrend && (
                <Line 
                  type="monotone" 
                  dataKey="movingAverage" 
                  stroke="#ff7300" 
                  name="7-day Average"
                  strokeWidth={2}
                  dot={false}
                />
              )}
              {viewMode === 'projection' && (
                <Line 
                  type="monotone" 
                  dataKey="projected" 
                  stroke="#82ca9d" 
                  name="Projected"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                />
              )}
              <ReferenceLine 
                y={velocityData.statistics.avgPerDay} 
                stroke="red" 
                strokeDasharray="3 3"
                label="Average"
              />
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>
    );
  };

  const getTrendIcon = () => {
    const { trend } = velocityData.statistics;
    if (trend === 'increasing') return <Icon name="arrow up" color="green" />;
    if (trend === 'decreasing') return <Icon name="arrow down" color="red" />;
    return <Icon name="minus" color="yellow" />;
  };

  const renderStatistics = () => (
    <Card.Group itemsPerRow={4}>
      <Card>
        <Card.Content textAlign="center">
          <Statistic size="tiny">
            <Statistic.Value>{velocityData.statistics.totalCompleted}</Statistic.Value>
            <Statistic.Label>Total Completed</Statistic.Label>
          </Statistic>
        </Card.Content>
      </Card>
      <Card>
        <Card.Content textAlign="center">
          <Statistic size="tiny">
            <Statistic.Value>{velocityData.statistics.avgPerDay}</Statistic.Value>
            <Statistic.Label>Per Day</Statistic.Label>
          </Statistic>
        </Card.Content>
      </Card>
      <Card>
        <Card.Content textAlign="center">
          <Statistic size="tiny">
            <Statistic.Value>{velocityData.statistics.avgPerWeek}</Statistic.Value>
            <Statistic.Label>Per Week</Statistic.Label>
          </Statistic>
        </Card.Content>
      </Card>
      <Card>
        <Card.Content textAlign="center">
          <Statistic size="tiny">
            <Statistic.Value>
              {getTrendIcon()}
              {velocityData.statistics.trend}
            </Statistic.Value>
            <Statistic.Label>Trend</Statistic.Label>
          </Statistic>
        </Card.Content>
      </Card>
    </Card.Group>
  );

  const renderCategoryRates = () => (
    <Segment>
      <Header as="h4">Completion Rates by Category</Header>
      <Table celled>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Category</Table.HeaderCell>
            <Table.HeaderCell>Total</Table.HeaderCell>
            <Table.HeaderCell>Completed</Table.HeaderCell>
            <Table.HeaderCell>In Progress</Table.HeaderCell>
            <Table.HeaderCell>Completion Rate</Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {categoryRates.map(category => (
            <Table.Row key={category.category}>
              <Table.Cell>
                <Label color="blue" horizontal>
                  {category.category}
                </Label>
              </Table.Cell>
              <Table.Cell>{category.total}</Table.Cell>
              <Table.Cell>
                <Label color="green" size="tiny">
                  {category.completed}
                </Label>
              </Table.Cell>
              <Table.Cell>
                <Label color="yellow" size="tiny">
                  {category.inProgress}
                </Label>
              </Table.Cell>
              <Table.Cell>
                <Progress 
                  percent={parseFloat(category.completionRate)} 
                  size="tiny" 
                  color={parseFloat(category.completionRate) > 75 ? 'green' : 'blue'}
                />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
    </Segment>
  );

  return (
    <Segment>
      <Header as="h2">
        <Icon name="tachometer alternate" />
        <Header.Content>
          Learning Velocity
          <Header.Subheader>Track your learning speed and progress trends</Header.Subheader>
        </Header.Content>
      </Header>

      <Grid>
        <Grid.Row>
          <Grid.Column width={6}>
            <Dropdown
              placeholder="Select Time Frame"
              fluid
              selection
              options={[
                { key: 'week', text: 'Last Week', value: 'week' },
                { key: 'month', text: 'Last Month', value: 'month' },
                { key: 'quarter', text: 'Last Quarter', value: 'quarter' },
                { key: 'year', text: 'Last Year', value: 'year' }
              ]}
              value={timeFrame}
              onChange={(e, { value }) => setTimeFrame(value)}
            />
          </Grid.Column>
          <Grid.Column width={6}>
            <Button.Group fluid>
              <Button 
                active={viewMode === 'velocity'}
                onClick={() => setViewMode('velocity')}
                content="Velocity"
              />
              <Button 
                active={viewMode === 'cumulative'}
                onClick={() => setViewMode('cumulative')}
                content="Cumulative"
              />
              <Button 
                active={viewMode === 'projection'}
                onClick={() => setViewMode('projection')}
                content="Projection"
              />
            </Button.Group>
          </Grid.Column>
          <Grid.Column width={4}>
            <Button 
              toggle
              active={showTrend}
              onClick={() => setShowTrend(!showTrend)}
              icon="chart line"
              content="Show Trend"
              fluid
            />
          </Grid.Column>
        </Grid.Row>
      </Grid>

      {renderStatistics()}

      {velocityData.statistics.maxDay > 0 && (
        <Message positive>
          <Message.Header>Peak Performance</Message.Header>
          <p>
            Your best day was {velocityData.statistics.peakDays[0]?.displayDate} with {velocityData.statistics.maxDay} milestones completed!
          </p>
        </Message>
      )}

      <Segment>
        <Header as="h4">
          {viewMode === 'velocity' && 'Daily Completion Velocity'}
          {viewMode === 'cumulative' && 'Cumulative Progress'}
          {viewMode === 'projection' && '30-Day Projection'}
        </Header>
        {renderVelocityChart()}
      </Segment>

      {renderCategoryRates()}

      <Button 
        icon="download" 
        content="Export Velocity Data" 
        floated="right"
        onClick={() => {
          const exportData = {
            statistics: velocityData.statistics,
            velocityPoints: velocityData.velocityPoints,
            categoryRates,
            exportDate: new Date().toISOString()
          };
          console.log('Export velocity data:', exportData);
        }}
      />
    </Segment>
  );
};

LearningVelocityChart.propTypes = {
  learningData: PropTypes.array,
  milestones: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    title: PropTypes.string,
    status: PropTypes.oneOf(['pending', 'in_progress', 'completed']),
    completion_date: PropTypes.string,
    category: PropTypes.string
  })),
  timeFrame: PropTypes.oneOf(['week', 'month', 'quarter', 'year'])
};

export default LearningVelocityChart;