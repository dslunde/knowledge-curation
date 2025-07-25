import React, { useState, useCallback } from 'react';
import { 
  Segment, 
  Header, 
  Icon, 
  Button,
  Grid,
  Label,
  Progress,
  List,
  Modal,
  Form,
  Dropdown,
  Card,
  Statistic,
  Tab
} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const competencyLevels = [
  { key: 'novice', text: 'Novice', value: 'novice', color: 'grey' },
  { key: 'beginner', text: 'Beginner', value: 'beginner', color: 'orange' },
  { key: 'intermediate', text: 'Intermediate', value: 'intermediate', color: 'yellow' },
  { key: 'advanced', text: 'Advanced', value: 'advanced', color: 'green' },
  { key: 'expert', text: 'Expert', value: 'expert', color: 'blue' },
];

const CompetencyDashboard = ({ 
  value = [], 
  onChange,
  title = 'Competency Dashboard',
  description = 'Track and visualize your competency progression',
}) => {
  const [editingCompetency, setEditingCompetency] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('cards'); // cards, list, chart

  const handleAddCompetency = useCallback(() => {
    const newCompetency = {
      id: `competency-${Date.now()}`,
      name: '',
      description: '',
      level: 'novice',
      category: '',
    };
    setEditingCompetency(newCompetency);
  }, []);

  const handleSaveCompetency = useCallback((competency) => {
    const index = value.findIndex(c => c.id === competency.id);
    if (index >= 0) {
      const newCompetencies = [...value];
      newCompetencies[index] = competency;
      onChange(newCompetencies);
    } else {
      onChange([...value, competency]);
    }
    setEditingCompetency(null);
  }, [value, onChange]);

  const handleRemoveCompetency = useCallback((id) => {
    onChange(value.filter(c => c.id !== id));
  }, [value, onChange]);

  const handleFieldChange = useCallback((field, fieldValue) => {
    setEditingCompetency({
      ...editingCompetency,
      [field]: fieldValue,
    });
  }, [editingCompetency]);

  const getCategories = () => {
    const categories = new Set(value.map(c => c.category).filter(Boolean));
    return ['all', ...Array.from(categories)];
  };

  const getFilteredCompetencies = () => {
    if (selectedCategory === 'all') return value;
    return value.filter(c => c.category === selectedCategory);
  };

  const getLevelProgress = (level) => {
    const levelIndex = competencyLevels.findIndex(l => l.value === level);
    return ((levelIndex + 1) / competencyLevels.length) * 100;
  };

  const getStatistics = () => {
    const stats = {
      total: value.length,
      byLevel: {},
      byCategory: {},
    };

    competencyLevels.forEach(level => {
      stats.byLevel[level.value] = value.filter(c => c.level === level.value).length;
    });

    const categories = new Set(value.map(c => c.category).filter(Boolean));
    categories.forEach(category => {
      stats.byCategory[category] = value.filter(c => c.category === category).length;
    });

    return stats;
  };

  const stats = getStatistics();
  const filteredCompetencies = getFilteredCompetencies();

  const CompetencyCard = ({ competency }) => {
    const levelInfo = competencyLevels.find(l => l.value === competency.level);
    
    return (
      <Card>
        <Card.Content>
          <Card.Header>
            {competency.name}
            <Button.Group size="mini" floated="right">
              <Button 
                icon="edit" 
                onClick={() => setEditingCompetency(competency)}
              />
              <Button 
                icon="trash" 
                onClick={() => {
                  if (window.confirm('Delete this competency?')) {
                    handleRemoveCompetency(competency.id);
                  }
                }}
              />
            </Button.Group>
          </Card.Header>
          <Card.Meta>
            {competency.category && (
              <Label size="tiny" color="teal">
                {competency.category}
              </Label>
            )}
          </Card.Meta>
          <Card.Description>{competency.description}</Card.Description>
        </Card.Content>
        <Card.Content extra>
          <Label color={levelInfo?.color} ribbon>
            {levelInfo?.text}
          </Label>
          <Progress 
            percent={getLevelProgress(competency.level)} 
            size="tiny" 
            color={levelInfo?.color}
            style={{ marginTop: '0.5em' }}
          />
        </Card.Content>
      </Card>
    );
  };

  const CompetencyList = () => (
    <List divided relaxed>
      {filteredCompetencies.map((competency) => {
        const levelInfo = competencyLevels.find(l => l.value === competency.level);
        
        return (
          <List.Item key={competency.id}>
            <List.Content floated="right">
              <Button.Group size="tiny">
                <Button 
                  icon="edit" 
                  onClick={() => setEditingCompetency(competency)}
                />
                <Button 
                  icon="trash" 
                  onClick={() => {
                    if (window.confirm('Delete this competency?')) {
                      handleRemoveCompetency(competency.id);
                    }
                  }}
                />
              </Button.Group>
            </List.Content>
            <List.Icon name="certificate" size="large" verticalAlign="middle" />
            <List.Content>
              <List.Header>{competency.name}</List.Header>
              <List.Description>
                {competency.description}
                <div style={{ marginTop: '0.5em' }}>
                  <Label size="tiny" color={levelInfo?.color}>
                    {levelInfo?.text}
                  </Label>
                  {competency.category && (
                    <Label size="tiny" color="teal">
                      {competency.category}
                    </Label>
                  )}
                  <Progress 
                    percent={getLevelProgress(competency.level)} 
                    size="tiny" 
                    color={levelInfo?.color}
                    style={{ marginTop: '0.5em', maxWidth: '200px' }}
                  />
                </div>
              </List.Description>
            </List.Content>
          </List.Item>
        );
      })}
    </List>
  );

  const CompetencyChart = () => (
    <Grid>
      <Grid.Row>
        <Grid.Column width={8}>
          <Segment>
            <Header as="h4">Competencies by Level</Header>
            <List>
              {competencyLevels.map(level => (
                <List.Item key={level.value}>
                  <List.Content floated="right">
                    <Label circular color={level.color}>
                      {stats.byLevel[level.value] || 0}
                    </Label>
                  </List.Content>
                  <List.Content>
                    <Label color={level.color} horizontal>
                      {level.text}
                    </Label>
                    <Progress 
                      percent={(stats.byLevel[level.value] || 0) / stats.total * 100} 
                      size="tiny" 
                      color={level.color}
                      style={{ margin: '0.5em 0' }}
                    />
                  </List.Content>
                </List.Item>
              ))}
            </List>
          </Segment>
        </Grid.Column>
        <Grid.Column width={8}>
          <Segment>
            <Header as="h4">Competencies by Category</Header>
            <List>
              {Object.entries(stats.byCategory).map(([category, count]) => (
                <List.Item key={category}>
                  <List.Content floated="right">
                    <Label circular>
                      {count}
                    </Label>
                  </List.Content>
                  <List.Content>
                    <Label horizontal>
                      {category}
                    </Label>
                    <Progress 
                      percent={count / stats.total * 100} 
                      size="tiny" 
                      style={{ margin: '0.5em 0' }}
                    />
                  </List.Content>
                </List.Item>
              ))}
            </List>
          </Segment>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );

  const panes = [
    {
      menuItem: { key: 'overview', icon: 'dashboard', content: 'Overview' },
      render: () => (
        <Tab.Pane>
          <Statistic.Group size="small" widths="five">
            <Statistic>
              <Statistic.Value>{stats.total}</Statistic.Value>
              <Statistic.Label>Total</Statistic.Label>
            </Statistic>
            {competencyLevels.map(level => (
              <Statistic key={level.value} color={level.color}>
                <Statistic.Value>{stats.byLevel[level.value] || 0}</Statistic.Value>
                <Statistic.Label>{level.text}</Statistic.Label>
              </Statistic>
            ))}
          </Statistic.Group>
          <CompetencyChart />
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: 'competencies', icon: 'certificate', content: 'Competencies' },
      render: () => (
        <Tab.Pane>
          <Grid>
            <Grid.Row>
              <Grid.Column width={12}>
                <Dropdown
                  placeholder="Filter by category"
                  selection
                  options={getCategories().map(cat => ({
                    key: cat,
                    text: cat === 'all' ? 'All Categories' : cat,
                    value: cat,
                  }))}
                  value={selectedCategory}
                  onChange={(e, { value }) => setSelectedCategory(value)}
                />
              </Grid.Column>
              <Grid.Column width={4} textAlign="right">
                <Button.Group size="small">
                  <Button 
                    icon="th" 
                    active={viewMode === 'cards'}
                    onClick={() => setViewMode('cards')}
                  />
                  <Button 
                    icon="list" 
                    active={viewMode === 'list'}
                    onClick={() => setViewMode('list')}
                  />
                </Button.Group>
              </Grid.Column>
            </Grid.Row>
          </Grid>

          {filteredCompetencies.length === 0 ? (
            <Segment placeholder textAlign="center">
              <Header icon>
                <Icon name="certificate" />
                No competencies found
              </Header>
              <Button primary onClick={handleAddCompetency}>
                Add Competency
              </Button>
            </Segment>
          ) : (
            <>
              {viewMode === 'cards' ? (
                <Card.Group itemsPerRow={3} style={{ marginTop: '1em' }}>
                  {filteredCompetencies.map(competency => (
                    <CompetencyCard key={competency.id} competency={competency} />
                  ))}
                </Card.Group>
              ) : (
                <CompetencyList />
              )}
            </>
          )}
        </Tab.Pane>
      ),
    },
  ];

  return (
    <Segment>
      <Header as="h3">
        <Icon name="chart line" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      <Button 
        primary 
        floated="right"
        onClick={handleAddCompetency}
        style={{ marginBottom: '1em' }}
      >
        <Icon name="plus" />
        Add Competency
      </Button>

      <Tab panes={panes} />

      <Modal
        open={!!editingCompetency}
        onClose={() => setEditingCompetency(null)}
        size="small"
      >
        <Modal.Header>
          {editingCompetency?.id?.startsWith('competency-') ? 'Add' : 'Edit'} Competency
        </Modal.Header>
        <Modal.Content>
          {editingCompetency && (
            <Form>
              <Form.Field required>
                <label>Competency Name</label>
                <Form.Input
                  placeholder="e.g., Python Programming, Data Analysis..."
                  value={editingCompetency.name || ''}
                  onChange={(e, { value }) => handleFieldChange('name', value)}
                />
              </Form.Field>
              <Form.Field>
                <label>Description</label>
                <Form.TextArea
                  placeholder="Describe this competency..."
                  value={editingCompetency.description || ''}
                  onChange={(e, { value }) => handleFieldChange('description', value)}
                  rows={3}
                />
              </Form.Field>
              <Form.Group widths="equal">
                <Form.Field>
                  <label>Category</label>
                  <Form.Input
                    placeholder="e.g., Technical, Soft Skills..."
                    value={editingCompetency.category || ''}
                    onChange={(e, { value }) => handleFieldChange('category', value)}
                  />
                </Form.Field>
                <Form.Field>
                  <label>Current Level</label>
                  <Dropdown
                    placeholder="Select level"
                    fluid
                    selection
                    options={competencyLevels}
                    value={editingCompetency.level || 'novice'}
                    onChange={(e, { value }) => handleFieldChange('level', value)}
                  />
                </Form.Field>
              </Form.Group>
            </Form>
          )}
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setEditingCompetency(null)}>Cancel</Button>
          <Button 
            primary 
            onClick={() => handleSaveCompetency(editingCompetency)}
            disabled={!editingCompetency?.name}
          >
            Save
          </Button>
        </Modal.Actions>
      </Modal>
    </Segment>
  );
};

CompetencyDashboard.propTypes = {
  value: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    description: PropTypes.string,
    level: PropTypes.string,
    category: PropTypes.string,
  })),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
};

export default CompetencyDashboard;