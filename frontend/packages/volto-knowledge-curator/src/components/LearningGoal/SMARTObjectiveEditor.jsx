import React, { useState, useCallback } from 'react';
import { 
  Segment, 
  Header, 
  Icon, 
  Button,
  Form,
  Grid,
  Label,
  Message,
  List,
  Modal,
  Checkbox,
  Step
} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const SMARTObjectiveEditor = ({ 
  value = [], 
  onChange,
  title = 'SMART Learning Objectives',
  description = 'Define Specific, Measurable, Achievable, Relevant, and Time-bound objectives',
}) => {
  const [editingObjective, setEditingObjective] = useState(null);
  const [activeStep, setActiveStep] = useState('specific');

  const handleAddObjective = useCallback(() => {
    const newObjective = {
      id: `objective-${Date.now()}`,
      objective_text: '',
      measurable: false,
      achievable: false,
      relevant: false,
      time_bound: false,
      success_metrics: [],
    };
    setEditingObjective(newObjective);
    setActiveStep('specific');
  }, []);

  const handleSaveObjective = useCallback((objective) => {
    const index = value.findIndex(o => o.id === objective.id);
    if (index >= 0) {
      const newObjectives = [...value];
      newObjectives[index] = objective;
      onChange(newObjectives);
    } else {
      onChange([...value, objective]);
    }
    setEditingObjective(null);
  }, [value, onChange]);

  const handleRemoveObjective = useCallback((id) => {
    onChange(value.filter(o => o.id !== id));
  }, [value, onChange]);

  const handleObjectiveFieldChange = useCallback((field, fieldValue) => {
    setEditingObjective({
      ...editingObjective,
      [field]: fieldValue,
    });
  }, [editingObjective]);

  const handleAddMetric = useCallback(() => {
    const metrics = editingObjective.success_metrics || [];
    handleObjectiveFieldChange('success_metrics', [...metrics, '']);
  }, [editingObjective, handleObjectiveFieldChange]);

  const handleUpdateMetric = useCallback((index, value) => {
    const metrics = [...(editingObjective.success_metrics || [])];
    metrics[index] = value;
    handleObjectiveFieldChange('success_metrics', metrics);
  }, [editingObjective, handleObjectiveFieldChange]);

  const handleRemoveMetric = useCallback((index) => {
    const metrics = editingObjective.success_metrics || [];
    handleObjectiveFieldChange('success_metrics', metrics.filter((_, i) => i !== index));
  }, [editingObjective, handleObjectiveFieldChange]);

  const getSMARTScore = (objective) => {
    let score = 0;
    if (objective.objective_text) score += 20;
    if (objective.measurable) score += 20;
    if (objective.achievable) score += 20;
    if (objective.relevant) score += 20;
    if (objective.time_bound) score += 20;
    return score;
  };

  const getSMARTColor = (score) => {
    if (score >= 80) return 'green';
    if (score >= 60) return 'yellow';
    if (score >= 40) return 'orange';
    return 'red';
  };

  const steps = [
    {
      key: 'specific',
      icon: 'target',
      title: 'Specific',
      description: 'What exactly do you want to accomplish?',
    },
    {
      key: 'measurable',
      icon: 'chart line',
      title: 'Measurable',
      description: 'How will you measure progress and success?',
    },
    {
      key: 'achievable',
      icon: 'check',
      title: 'Achievable',
      description: 'Is this objective realistic and attainable?',
    },
    {
      key: 'relevant',
      icon: 'bullseye',
      title: 'Relevant',
      description: 'Does this align with your broader goals?',
    },
    {
      key: 'time_bound',
      icon: 'clock',
      title: 'Time-bound',
      description: 'When will you accomplish this?',
    },
  ];

  const renderStepContent = () => {
    if (!editingObjective) return null;

    switch (activeStep) {
      case 'specific':
        return (
          <div>
            <Form.Field required>
              <label>Objective Statement</label>
              <Form.TextArea
                placeholder="Write a clear, specific objective statement..."
                value={editingObjective.objective_text || ''}
                onChange={(e, { value }) => handleObjectiveFieldChange('objective_text', value)}
                rows={4}
              />
            </Form.Field>
            <Message info>
              <Message.Header>Tips for Specific Objectives</Message.Header>
              <List bulleted>
                <List.Item>Use action verbs (learn, create, implement, etc.)</List.Item>
                <List.Item>Be clear about what you want to achieve</List.Item>
                <List.Item>Avoid vague terms like "understand better" or "improve"</List.Item>
              </List>
            </Message>
          </div>
        );

      case 'measurable':
        return (
          <div>
            <Form.Field>
              <Checkbox
                label="This objective has measurable outcomes"
                checked={editingObjective.measurable || false}
                onChange={(e, { checked }) => handleObjectiveFieldChange('measurable', checked)}
              />
            </Form.Field>
            <Header as="h5">Success Metrics</Header>
            {(editingObjective.success_metrics || []).map((metric, index) => (
              <Form.Field key={index}>
                <Form.Input
                  placeholder="Define a success metric..."
                  value={metric}
                  onChange={(e, { value }) => handleUpdateMetric(index, value)}
                  action={{
                    icon: 'trash',
                    color: 'red',
                    onClick: () => handleRemoveMetric(index),
                  }}
                />
              </Form.Field>
            ))}
            <Button size="small" onClick={handleAddMetric}>
              <Icon name="plus" />
              Add Metric
            </Button>
            <Message info>
              <p>Define concrete ways to measure your progress and completion</p>
            </Message>
          </div>
        );

      case 'achievable':
        return (
          <div>
            <Form.Field>
              <Checkbox
                label="I have assessed and believe this objective is achievable"
                checked={editingObjective.achievable || false}
                onChange={(e, { checked }) => handleObjectiveFieldChange('achievable', checked)}
              />
            </Form.Field>
            <Message info>
              <Message.Header>Consider These Factors</Message.Header>
              <List bulleted>
                <List.Item>Current skill level and knowledge</List.Item>
                <List.Item>Available time and resources</List.Item>
                <List.Item>Potential obstacles or challenges</List.Item>
                <List.Item>Support systems and help available</List.Item>
              </List>
            </Message>
          </div>
        );

      case 'relevant':
        return (
          <div>
            <Form.Field>
              <Checkbox
                label="This objective aligns with my broader goals and priorities"
                checked={editingObjective.relevant || false}
                onChange={(e, { checked }) => handleObjectiveFieldChange('relevant', checked)}
              />
            </Form.Field>
            <Message info>
              <Message.Header>Relevance Check</Message.Header>
              <List bulleted>
                <List.Item>Does this support your career goals?</List.Item>
                <List.Item>Is this the right time for this objective?</List.Item>
                <List.Item>Will achieving this have meaningful impact?</List.Item>
              </List>
            </Message>
          </div>
        );

      case 'time_bound':
        return (
          <div>
            <Form.Field>
              <Checkbox
                label="This objective has a clear timeline"
                checked={editingObjective.time_bound || false}
                onChange={(e, { checked }) => handleObjectiveFieldChange('time_bound', checked)}
              />
            </Form.Field>
            <Message info>
              <Message.Header>Setting Timelines</Message.Header>
              <p>Consider adding specific dates or timeframes to your objective statement</p>
            </Message>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Segment>
      <Header as="h3">
        <Icon name="tasks" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      {value.length === 0 ? (
        <Segment placeholder textAlign="center">
          <Header icon>
            <Icon name="clipboard outline" />
            No objectives defined yet
          </Header>
          <Button primary onClick={handleAddObjective}>
            Create Your First SMART Objective
          </Button>
        </Segment>
      ) : (
        <>
          <List divided relaxed>
            {value.map((objective) => {
              const score = getSMARTScore(objective);
              const color = getSMARTColor(score);
              
              return (
                <List.Item key={objective.id}>
                  <List.Content floated="right">
                    <Button.Group size="tiny">
                      <Button 
                        icon="edit" 
                        onClick={() => {
                          setEditingObjective(objective);
                          setActiveStep('specific');
                        }}
                      />
                      <Button 
                        icon="trash" 
                        onClick={() => {
                          if (window.confirm('Delete this objective?')) {
                            handleRemoveObjective(objective.id);
                          }
                        }}
                      />
                    </Button.Group>
                  </List.Content>
                  <List.Icon name="clipboard check" size="large" verticalAlign="middle" />
                  <List.Content>
                    <List.Header>{objective.objective_text || 'Untitled Objective'}</List.Header>
                    <List.Description>
                      <Label.Group size="tiny" style={{ marginTop: '0.5em' }}>
                        <Label color={color}>
                          SMART Score: {score}%
                        </Label>
                        {objective.measurable && <Label color="green">Measurable</Label>}
                        {objective.achievable && <Label color="green">Achievable</Label>}
                        {objective.relevant && <Label color="green">Relevant</Label>}
                        {objective.time_bound && <Label color="green">Time-bound</Label>}
                      </Label.Group>
                      {objective.success_metrics && objective.success_metrics.length > 0 && (
                        <div style={{ marginTop: '0.5em' }}>
                          <strong>Metrics:</strong> {objective.success_metrics.join(', ')}
                        </div>
                      )}
                    </List.Description>
                  </List.Content>
                </List.Item>
              );
            })}
          </List>
          <Button 
            primary 
            onClick={handleAddObjective}
            style={{ marginTop: '1em' }}
          >
            <Icon name="plus" />
            Add SMART Objective
          </Button>
        </>
      )}

      <Modal
        open={!!editingObjective}
        onClose={() => setEditingObjective(null)}
        size="large"
      >
        <Modal.Header>
          Create SMART Objective
        </Modal.Header>
        <Modal.Content>
          {editingObjective && (
            <>
              <Step.Group fluid>
                {steps.map((step) => (
                  <Step
                    key={step.key}
                    active={activeStep === step.key}
                    completed={
                      step.key === 'specific' ? !!editingObjective.objective_text :
                      editingObjective[step.key]
                    }
                    onClick={() => setActiveStep(step.key)}
                  >
                    <Icon name={step.icon} />
                    <Step.Content>
                      <Step.Title>{step.title}</Step.Title>
                    </Step.Content>
                  </Step>
                ))}
              </Step.Group>

              <Segment>
                <Header as="h4">
                  {steps.find(s => s.key === activeStep)?.title}
                  <Header.Subheader>
                    {steps.find(s => s.key === activeStep)?.description}
                  </Header.Subheader>
                </Header>
                {renderStepContent()}
              </Segment>

              <Grid>
                <Grid.Row>
                  <Grid.Column width={8}>
                    {activeStep !== 'specific' && (
                      <Button 
                        onClick={() => {
                          const currentIndex = steps.findIndex(s => s.key === activeStep);
                          if (currentIndex > 0) {
                            setActiveStep(steps[currentIndex - 1].key);
                          }
                        }}
                      >
                        <Icon name="arrow left" />
                        Previous
                      </Button>
                    )}
                  </Grid.Column>
                  <Grid.Column width={8} textAlign="right">
                    {activeStep !== 'time_bound' && (
                      <Button 
                        primary
                        onClick={() => {
                          const currentIndex = steps.findIndex(s => s.key === activeStep);
                          if (currentIndex < steps.length - 1) {
                            setActiveStep(steps[currentIndex + 1].key);
                          }
                        }}
                      >
                        Next
                        <Icon name="arrow right" />
                      </Button>
                    )}
                  </Grid.Column>
                </Grid.Row>
              </Grid>
            </>
          )}
        </Modal.Content>
        <Modal.Actions>
          <Label color={getSMARTColor(getSMARTScore(editingObjective || {}))}>
            SMART Score: {getSMARTScore(editingObjective || {})}%
          </Label>
          <Button onClick={() => setEditingObjective(null)}>Cancel</Button>
          <Button 
            primary 
            onClick={() => handleSaveObjective(editingObjective)}
            disabled={!editingObjective?.objective_text}
          >
            Save Objective
          </Button>
        </Modal.Actions>
      </Modal>
    </Segment>
  );
};

SMARTObjectiveEditor.propTypes = {
  value: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    objective_text: PropTypes.string,
    measurable: PropTypes.bool,
    achievable: PropTypes.bool,
    relevant: PropTypes.bool,
    time_bound: PropTypes.bool,
    success_metrics: PropTypes.arrayOf(PropTypes.string),
  })),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
};

export default SMARTObjectiveEditor;