import React, { useCallback } from 'react';
import { Form, Segment, Progress, Dropdown } from 'semantic-ui-react';
import PropTypes from 'prop-types';
import BaseStructuredEditor from '../shared/BaseStructuredEditor';

const statusOptions = [
  { key: 'not_started', text: 'Not Started', value: 'not_started' },
  { key: 'in_progress', text: 'In Progress', value: 'in_progress' },
  { key: 'completed', text: 'Completed', value: 'completed' },
  { key: 'blocked', text: 'Blocked', value: 'blocked' },
  { key: 'deferred', text: 'Deferred', value: 'deferred' },
];

const LearningMilestoneEditor = ({ value = {}, onChange, errors, title, description, required }) => {
  const handleFieldChange = useCallback((field, fieldValue) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  }, [value, onChange]);

  const validateMilestone = useCallback((milestone) => {
    const errors = [];
    if (!milestone.title || milestone.title.trim() === '') {
      errors.push('Milestone title is required');
    }
    if (milestone.progress_percentage !== undefined && 
        (milestone.progress_percentage < 0 || milestone.progress_percentage > 100)) {
      errors.push('Progress must be between 0 and 100');
    }
    return errors;
  }, []);

  const progressPercentage = value.progress_percentage || 0;
  const isCompleted = value.status === 'completed';

  return (
    <BaseStructuredEditor
      value={value}
      onChange={onChange}
      errors={errors}
      title={title}
      description={description}
      required={required}
      onValidate={validateMilestone}
    >
      {({ value: milestoneValue, onChange: handleChange }) => (
        <Segment>
          <Form.Field required>
            <label>Milestone Title</label>
            <Form.Input
              placeholder="Enter milestone title..."
              value={milestoneValue.title || ''}
              onChange={(e, { value }) => handleFieldChange('title', value)}
            />
          </Form.Field>

          <Form.Field>
            <label>Description</label>
            <Form.TextArea
              placeholder="Describe the milestone..."
              value={milestoneValue.description || ''}
              onChange={(e, { value }) => handleFieldChange('description', value)}
              rows={2}
            />
          </Form.Field>

          <Form.Group widths="equal">
            <Form.Field>
              <label>Target Date</label>
              <input
                type="date"
                value={milestoneValue.target_date || ''}
                onChange={(e) => handleFieldChange('target_date', e.target.value)}
              />
            </Form.Field>

            <Form.Field>
              <label>Status</label>
              <Dropdown
                placeholder="Select status"
                fluid
                selection
                options={statusOptions}
                value={milestoneValue.status || 'not_started'}
                onChange={(e, { value }) => {
                  handleFieldChange('status', value);
                  // Auto-set progress to 100% if completed
                  if (value === 'completed') {
                    handleFieldChange('progress_percentage', 100);
                  }
                }}
              />
            </Form.Field>
          </Form.Group>

          <Form.Field>
            <label>Progress: {progressPercentage}%</label>
            <Progress
              percent={progressPercentage}
              indicating
              success={isCompleted}
              warning={progressPercentage >= 50 && progressPercentage < 100}
              error={value.status === 'blocked'}
            />
            <input
              type="range"
              min="0"
              max="100"
              value={progressPercentage}
              onChange={(e) => handleFieldChange('progress_percentage', parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
          </Form.Field>

          <Form.Field>
            <label>Completion Criteria</label>
            <Form.TextArea
              placeholder="Define what constitutes completion of this milestone..."
              value={milestoneValue.completion_criteria || ''}
              onChange={(e, { value }) => handleFieldChange('completion_criteria', value)}
              rows={2}
            />
          </Form.Field>
        </Segment>
      )}
    </BaseStructuredEditor>
  );
};

LearningMilestoneEditor.propTypes = {
  value: PropTypes.shape({
    id: PropTypes.string,
    title: PropTypes.string,
    description: PropTypes.string,
    target_date: PropTypes.string,
    status: PropTypes.string,
    progress_percentage: PropTypes.number,
    completion_criteria: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string,
  description: PropTypes.string,
  required: PropTypes.bool,
};

export default LearningMilestoneEditor;