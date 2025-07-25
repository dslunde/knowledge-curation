import React, { useState, useCallback } from 'react';
import { 
  Segment, 
  Header, 
  Icon, 
  Button,
  Progress,
  Grid,
  Label,
  Message,
  List,
  Modal,
  Statistic
} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import LearningMilestoneEditor from '../StructuredObjects/LearningMilestoneEditor';

const MilestoneTracker = ({ 
  value = [], 
  onChange,
  title = 'Learning Milestones',
  description = 'Track your progress through learning milestones',
}) => {
  const [editingMilestone, setEditingMilestone] = useState(null);
  const [showTimeline, setShowTimeline] = useState(true);

  const handleAddMilestone = useCallback(() => {
    const newMilestone = {
      id: `milestone-${Date.now()}`,
      title: '',
      description: '',
      target_date: '',
      status: 'not_started',
      progress_percentage: 0,
      completion_criteria: '',
    };
    setEditingMilestone(newMilestone);
  }, []);

  const handleSaveMilestone = useCallback((milestone) => {
    if (milestone.id && milestone.id.startsWith('milestone-')) {
      // New milestone
      onChange([...value, milestone]);
    } else {
      // Existing milestone
      const index = value.findIndex(m => m.id === milestone.id);
      if (index >= 0) {
        const newMilestones = [...value];
        newMilestones[index] = milestone;
        onChange(newMilestones);
      }
    }
    setEditingMilestone(null);
  }, [value, onChange]);

  const handleRemoveMilestone = useCallback((id) => {
    onChange(value.filter(m => m.id !== id));
  }, [value, onChange]);

  const calculateOverallProgress = () => {
    if (value.length === 0) return 0;
    const totalProgress = value.reduce((sum, m) => sum + (m.progress_percentage || 0), 0);
    return Math.round(totalProgress / value.length);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'green';
      case 'in_progress': return 'yellow';
      case 'blocked': return 'red';
      case 'deferred': return 'orange';
      default: return 'grey';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return 'check circle';
      case 'in_progress': return 'circle notched';
      case 'blocked': return 'ban';
      case 'deferred': return 'pause';
      default: return 'circle outline';
    }
  };

  const sortedMilestones = [...value].sort((a, b) => {
    if (!a.target_date && !b.target_date) return 0;
    if (!a.target_date) return 1;
    if (!b.target_date) return -1;
    return new Date(a.target_date) - new Date(b.target_date);
  });

  const statistics = {
    total: value.length,
    completed: value.filter(m => m.status === 'completed').length,
    inProgress: value.filter(m => m.status === 'in_progress').length,
    blocked: value.filter(m => m.status === 'blocked').length,
  };

  const TimelineView = () => (
    <div style={{ position: 'relative', paddingLeft: '2em' }}>
      <div 
        style={{
          position: 'absolute',
          left: '0.5em',
          top: '0',
          bottom: '0',
          width: '2px',
          backgroundColor: '#e0e0e0',
        }}
      />
      {sortedMilestones.map((milestone, index) => (
        <div key={milestone.id} style={{ position: 'relative', marginBottom: '2em' }}>
          <div 
            style={{
              position: 'absolute',
              left: '-1.5em',
              top: '0.5em',
              width: '1em',
              height: '1em',
              borderRadius: '50%',
              backgroundColor: getStatusColor(milestone.status),
              border: '2px solid white',
              boxShadow: '0 0 0 2px ' + getStatusColor(milestone.status),
            }}
          />
          <Segment>
            <Grid>
              <Grid.Row>
                <Grid.Column width={13}>
                  <Header as="h4">
                    <Icon name={getStatusIcon(milestone.status)} color={getStatusColor(milestone.status)} />
                    <Header.Content>
                      {milestone.title || 'Untitled Milestone'}
                      {milestone.target_date && (
                        <Header.Subheader>
                          Target: {new Date(milestone.target_date).toLocaleDateString()}
                        </Header.Subheader>
                      )}
                    </Header.Content>
                  </Header>
                  {milestone.description && (
                    <p style={{ marginTop: '0.5em' }}>{milestone.description}</p>
                  )}
                  <Progress 
                    percent={milestone.progress_percentage || 0} 
                    size="tiny" 
                    color={getStatusColor(milestone.status)}
                  />
                </Grid.Column>
                <Grid.Column width={3} textAlign="right">
                  <Button.Group size="tiny">
                    <Button 
                      icon="edit" 
                      onClick={() => setEditingMilestone(milestone)}
                    />
                    <Button 
                      icon="trash" 
                      onClick={() => {
                        if (window.confirm('Delete this milestone?')) {
                          handleRemoveMilestone(milestone.id);
                        }
                      }}
                    />
                  </Button.Group>
                </Grid.Column>
              </Grid.Row>
            </Grid>
          </Segment>
        </div>
      ))}
    </div>
  );

  const ListView = () => (
    <List divided relaxed>
      {sortedMilestones.map((milestone) => (
        <List.Item key={milestone.id}>
          <List.Content floated="right">
            <Button.Group size="tiny">
              <Button 
                icon="edit" 
                onClick={() => setEditingMilestone(milestone)}
              />
              <Button 
                icon="trash" 
                onClick={() => {
                  if (window.confirm('Delete this milestone?')) {
                    handleRemoveMilestone(milestone.id);
                  }
                }}
              />
            </Button.Group>
          </List.Content>
          <List.Icon 
            name={getStatusIcon(milestone.status)} 
            size="large" 
            verticalAlign="middle"
            color={getStatusColor(milestone.status)}
          />
          <List.Content>
            <List.Header>{milestone.title || 'Untitled Milestone'}</List.Header>
            <List.Description>
              {milestone.description}
              <div style={{ marginTop: '0.5em' }}>
                <Label size="tiny" color={getStatusColor(milestone.status)}>
                  {milestone.status.replace('_', ' ')}
                </Label>
                <Label size="tiny">
                  {milestone.progress_percentage || 0}% complete
                </Label>
                {milestone.target_date && (
                  <Label size="tiny">
                    <Icon name="calendar" />
                    {new Date(milestone.target_date).toLocaleDateString()}
                  </Label>
                )}
              </div>
            </List.Description>
          </List.Content>
        </List.Item>
      ))}
    </List>
  );

  return (
    <Segment>
      <Header as="h3">
        <Icon name="flag checkered" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      <Statistic.Group size="mini" widths="four">
        <Statistic>
          <Statistic.Value>{statistics.total}</Statistic.Value>
          <Statistic.Label>Total</Statistic.Label>
        </Statistic>
        <Statistic color="green">
          <Statistic.Value>{statistics.completed}</Statistic.Value>
          <Statistic.Label>Completed</Statistic.Label>
        </Statistic>
        <Statistic color="yellow">
          <Statistic.Value>{statistics.inProgress}</Statistic.Value>
          <Statistic.Label>In Progress</Statistic.Label>
        </Statistic>
        <Statistic color="red">
          <Statistic.Value>{statistics.blocked}</Statistic.Value>
          <Statistic.Label>Blocked</Statistic.Label>
        </Statistic>
      </Statistic.Group>

      <Segment>
        <Grid>
          <Grid.Row>
            <Grid.Column width={12}>
              <Header as="h4">Overall Progress</Header>
            </Grid.Column>
            <Grid.Column width={4} textAlign="right">
              <Button.Group size="tiny">
                <Button 
                  active={showTimeline}
                  onClick={() => setShowTimeline(true)}
                >
                  Timeline
                </Button>
                <Button 
                  active={!showTimeline}
                  onClick={() => setShowTimeline(false)}
                >
                  List
                </Button>
              </Button.Group>
            </Grid.Column>
          </Grid.Row>
        </Grid>
        <Progress 
          percent={calculateOverallProgress()} 
          indicating 
          label={`${calculateOverallProgress()}% Complete`}
        />
      </Segment>

      {value.length === 0 ? (
        <Segment placeholder textAlign="center">
          <Header icon>
            <Icon name="flag outline" />
            No milestones defined yet
          </Header>
          <Button primary onClick={handleAddMilestone}>
            Add Your First Milestone
          </Button>
        </Segment>
      ) : (
        <>
          {showTimeline ? <TimelineView /> : <ListView />}
          <Button 
            primary 
            onClick={handleAddMilestone}
            style={{ marginTop: '1em' }}
          >
            <Icon name="plus" />
            Add Milestone
          </Button>
        </>
      )}

      <Modal
        open={!!editingMilestone}
        onClose={() => setEditingMilestone(null)}
        size="large"
      >
        <Modal.Header>
          {editingMilestone?.id?.startsWith('milestone-') ? 'Add' : 'Edit'} Milestone
        </Modal.Header>
        <Modal.Content>
          {editingMilestone && (
            <LearningMilestoneEditor
              value={editingMilestone}
              onChange={setEditingMilestone}
              required={true}
            />
          )}
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setEditingMilestone(null)}>Cancel</Button>
          <Button 
            primary 
            onClick={() => handleSaveMilestone(editingMilestone)}
            disabled={!editingMilestone?.title}
          >
            Save
          </Button>
        </Modal.Actions>
      </Modal>
    </Segment>
  );
};

MilestoneTracker.propTypes = {
  value: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    title: PropTypes.string,
    description: PropTypes.string,
    target_date: PropTypes.string,
    status: PropTypes.string,
    progress_percentage: PropTypes.number,
    completion_criteria: PropTypes.string,
  })),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
};

export default MilestoneTracker;