import React, { useState, useMemo } from 'react';
import {
  Segment,
  Header,
  Icon,
  Grid,
  Progress,
  Statistic,
  Label,
  Dropdown,
  Table,
  Button,
  Card
} from 'semantic-ui-react';
import { format, parseISO, isWithinInterval, subDays } from 'date-fns';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import PropTypes from 'prop-types';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const LearningProgressDashboard = ({ learningGoals = [], dateRange = 30 }) => {
  const [selectedGoal, setSelectedGoal] = useState('all');
  const [dateFilter, setDateFilter] = useState(dateRange);
  const [viewMode, setViewMode] = useState('overview'); // overview, timeline, detailed

  // Calculate overall progress metrics
  const progressMetrics = useMemo(() => {
    const now = new Date();
    const startDate = subDays(now, dateFilter);
    
    // Filter goals based on selected goal
    const filteredGoals = selectedGoal === 'all' 
      ? learningGoals 
      : learningGoals.filter(goal => goal.id === selectedGoal);

    // Calculate milestone statistics
    const milestoneStats = filteredGoals.reduce((acc, goal) => {
      const milestones = goal.milestones || [];
      
      milestones.forEach(milestone => {
        acc.total++;
        
        if (milestone.status === 'completed') {
          acc.completed++;
          
          // Check if completed within date range
          if (milestone.completion_date && 
              isWithinInterval(parseISO(milestone.completion_date), { start: startDate, end: now })) {
            acc.recentlyCompleted++;
          }
        } else if (milestone.status === 'in_progress') {
          acc.inProgress++;
        } else {
          acc.pending++;
        }
      });
      
      return acc;
    }, { total: 0, completed: 0, inProgress: 0, pending: 0, recentlyCompleted: 0 });

    // Calculate completion percentage
    const completionPercentage = milestoneStats.total > 0 
      ? Math.round((milestoneStats.completed / milestoneStats.total) * 100)
      : 0;

    // Calculate progress by goal
    const progressByGoal = learningGoals.map(goal => {
      const milestones = goal.milestones || [];
      const completed = milestones.filter(m => m.status === 'completed').length;
      const total = milestones.length;
      
      return {
        id: goal.id,
        title: goal.title,
        progress: total > 0 ? Math.round((completed / total) * 100) : 0,
        completed,
        total,
        category: goal.category || 'Uncategorized',
        priority: goal.priority || 'medium'
      };
    });

    // Generate timeline data
    const timelineData = generateTimelineData(filteredGoals, dateFilter);

    return {
      milestoneStats,
      completionPercentage,
      progressByGoal,
      timelineData
    };
  }, [learningGoals, selectedGoal, dateFilter]);

  // Generate timeline visualization data
  const generateTimelineData = (goals, days) => {
    const data = [];
    const now = new Date();
    
    for (let i = days; i >= 0; i--) {
      const date = subDays(now, i);
      const dateStr = format(date, 'yyyy-MM-dd');
      
      const dayData = {
        date: format(date, 'MMM dd'),
        completed: 0,
        total: 0
      };
      
      goals.forEach(goal => {
        const milestones = goal.milestones || [];
        milestones.forEach(milestone => {
          if (milestone.completion_date && 
              format(parseISO(milestone.completion_date), 'yyyy-MM-dd') === dateStr) {
            dayData.completed++;
          }
          
          // Count milestones that existed on this date
          if (!milestone.created_date || parseISO(milestone.created_date) <= date) {
            dayData.total++;
          }
        });
      });
      
      data.push(dayData);
    }
    
    return data;
  };

  const goalOptions = [
    { key: 'all', text: 'All Learning Goals', value: 'all' },
    ...learningGoals.map(goal => ({
      key: goal.id,
      text: goal.title,
      value: goal.id
    }))
  ];

  const dateRangeOptions = [
    { key: '7', text: 'Last 7 days', value: 7 },
    { key: '30', text: 'Last 30 days', value: 30 },
    { key: '90', text: 'Last 90 days', value: 90 },
    { key: '365', text: 'Last year', value: 365 }
  ];

  const renderOverview = () => (
    <>
      <Grid columns={4} divided>
        <Grid.Row>
          <Grid.Column>
            <Statistic color="blue">
              <Statistic.Value>{progressMetrics.milestoneStats.total}</Statistic.Value>
              <Statistic.Label>Total Milestones</Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic color="green">
              <Statistic.Value>{progressMetrics.milestoneStats.completed}</Statistic.Value>
              <Statistic.Label>Completed</Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic color="yellow">
              <Statistic.Value>{progressMetrics.milestoneStats.inProgress}</Statistic.Value>
              <Statistic.Label>In Progress</Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic color="grey">
              <Statistic.Value>{progressMetrics.milestoneStats.pending}</Statistic.Value>
              <Statistic.Label>Pending</Statistic.Label>
            </Statistic>
          </Grid.Column>
        </Grid.Row>
      </Grid>

      <Segment>
        <Header as="h4">Overall Progress</Header>
        <Progress
          percent={progressMetrics.completionPercentage}
          progress
          color="green"
          size="large"
        />
      </Segment>

      <Grid columns={2}>
        <Grid.Column>
          <Segment>
            <Header as="h4">Progress by Learning Goal</Header>
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={progressMetrics.progressByGoal}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="title" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="progress" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Segment>
        </Grid.Column>
        <Grid.Column>
          <Segment>
            <Header as="h4">Milestone Distribution</Header>
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Completed', value: progressMetrics.milestoneStats.completed },
                      { name: 'In Progress', value: progressMetrics.milestoneStats.inProgress },
                      { name: 'Pending', value: progressMetrics.milestoneStats.pending }
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {[
                      { name: 'Completed', value: progressMetrics.milestoneStats.completed },
                      { name: 'In Progress', value: progressMetrics.milestoneStats.inProgress },
                      { name: 'Pending', value: progressMetrics.milestoneStats.pending }
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Segment>
        </Grid.Column>
      </Grid>
    </>
  );

  const renderTimeline = () => (
    <Segment>
      <Header as="h4">Milestone Completion Timeline</Header>
      <div style={{ height: '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={progressMetrics.timelineData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="completed" 
              stroke="#00C49F" 
              name="Completed Milestones"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Segment>
  );

  const renderDetailed = () => (
    <Table celled striped>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell>Learning Goal</Table.HeaderCell>
          <Table.HeaderCell>Category</Table.HeaderCell>
          <Table.HeaderCell>Priority</Table.HeaderCell>
          <Table.HeaderCell>Progress</Table.HeaderCell>
          <Table.HeaderCell>Milestones</Table.HeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {progressMetrics.progressByGoal.map(goal => (
          <Table.Row key={goal.id}>
            <Table.Cell>{goal.title}</Table.Cell>
            <Table.Cell>
              <Label color="teal">{goal.category}</Label>
            </Table.Cell>
            <Table.Cell>
              <Label 
                color={
                  goal.priority === 'high' ? 'red' : 
                  goal.priority === 'medium' ? 'yellow' : 
                  'green'
                }
              >
                {goal.priority}
              </Label>
            </Table.Cell>
            <Table.Cell>
              <Progress 
                percent={goal.progress} 
                size="small" 
                color={goal.progress === 100 ? 'green' : 'blue'}
              />
            </Table.Cell>
            <Table.Cell>
              {goal.completed} / {goal.total}
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );

  return (
    <Segment>
      <Header as="h2">
        <Icon name="chart line" />
        <Header.Content>
          Learning Progress Dashboard
          <Header.Subheader>Track your learning milestones and progress</Header.Subheader>
        </Header.Content>
      </Header>

      <Grid>
        <Grid.Row>
          <Grid.Column width={6}>
            <Dropdown
              placeholder="Select Learning Goal"
              fluid
              selection
              options={goalOptions}
              value={selectedGoal}
              onChange={(e, { value }) => setSelectedGoal(value)}
            />
          </Grid.Column>
          <Grid.Column width={6}>
            <Dropdown
              placeholder="Select Date Range"
              fluid
              selection
              options={dateRangeOptions}
              value={dateFilter}
              onChange={(e, { value }) => setDateFilter(value)}
            />
          </Grid.Column>
          <Grid.Column width={4}>
            <Button.Group fluid>
              <Button 
                active={viewMode === 'overview'}
                onClick={() => setViewMode('overview')}
              >
                Overview
              </Button>
              <Button 
                active={viewMode === 'timeline'}
                onClick={() => setViewMode('timeline')}
              >
                Timeline
              </Button>
              <Button 
                active={viewMode === 'detailed'}
                onClick={() => setViewMode('detailed')}
              >
                Detailed
              </Button>
            </Button.Group>
          </Grid.Column>
        </Grid.Row>
      </Grid>

      {progressMetrics.milestoneStats.recentlyCompleted > 0 && (
        <Card fluid color="green">
          <Card.Content>
            <Icon name="trophy" />
            <strong>{progressMetrics.milestoneStats.recentlyCompleted} milestones</strong> completed in the last {dateFilter} days!
          </Card.Content>
        </Card>
      )}

      {viewMode === 'overview' && renderOverview()}
      {viewMode === 'timeline' && renderTimeline()}
      {viewMode === 'detailed' && renderDetailed()}

      <Button 
        icon="download" 
        content="Export Data" 
        floated="right"
        style={{ marginTop: '1em' }}
        onClick={() => {
          // Export functionality would go here
          const data = {
            metrics: progressMetrics,
            dateRange: dateFilter,
            exportDate: new Date().toISOString()
          };
          console.log('Export data:', data);
        }}
      />
    </Segment>
  );
};

LearningProgressDashboard.propTypes = {
  learningGoals: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    category: PropTypes.string,
    priority: PropTypes.string,
    milestones: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string,
      title: PropTypes.string,
      status: PropTypes.oneOf(['pending', 'in_progress', 'completed']),
      completion_date: PropTypes.string,
      created_date: PropTypes.string
    }))
  })),
  dateRange: PropTypes.number
};

export default LearningProgressDashboard;