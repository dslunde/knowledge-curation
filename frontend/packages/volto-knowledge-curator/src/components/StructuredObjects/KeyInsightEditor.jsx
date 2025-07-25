import React, { useCallback } from 'react';
import { Form, Segment, Button, Icon, Dropdown } from 'semantic-ui-react';
import PropTypes from 'prop-types';
import BaseStructuredEditor from '../shared/BaseStructuredEditor';

const importanceOptions = [
  { key: 'low', text: 'Low', value: 'low' },
  { key: 'medium', text: 'Medium', value: 'medium' },
  { key: 'high', text: 'High', value: 'high' },
  { key: 'critical', text: 'Critical', value: 'critical' },
];

const KeyInsightEditor = ({ value = {}, onChange, errors, title, description, required }) => {
  const handleFieldChange = useCallback((field, fieldValue) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  }, [value, onChange]);

  const validateInsight = useCallback((insight) => {
    const errors = [];
    if (!insight.text || insight.text.trim() === '') {
      errors.push('Insight text is required');
    }
    if (insight.text && insight.text.length < 10) {
      errors.push('Insight text should be at least 10 characters');
    }
    return errors;
  }, []);

  const currentTimestamp = value.timestamp || new Date().toISOString();

  return (
    <BaseStructuredEditor
      value={value}
      onChange={onChange}
      errors={errors}
      title={title}
      description={description}
      required={required}
      onValidate={validateInsight}
    >
      {({ value: insightValue, onChange: handleChange }) => (
        <Segment>
          <Form.Field required>
            <label>Insight Text</label>
            <Form.TextArea
              placeholder="Enter the key insight..."
              value={insightValue.text || ''}
              onChange={(e, { value }) => handleFieldChange('text', value)}
              rows={3}
            />
          </Form.Field>

          <Form.Group widths="equal">
            <Form.Field>
              <label>Importance</label>
              <Dropdown
                placeholder="Select importance"
                fluid
                selection
                options={importanceOptions}
                value={insightValue.importance || 'medium'}
                onChange={(e, { value }) => handleFieldChange('importance', value)}
              />
            </Form.Field>

            <Form.Field>
              <label>Timestamp</label>
              <input
                type="datetime-local"
                value={currentTimestamp.slice(0, 16)}
                onChange={(e) => handleFieldChange('timestamp', new Date(e.target.value).toISOString())}
              />
            </Form.Field>
          </Form.Group>

          <Form.Field>
            <label>Supporting Evidence</label>
            <Form.TextArea
              placeholder="Provide evidence or references supporting this insight..."
              value={insightValue.evidence || ''}
              onChange={(e, { value }) => handleFieldChange('evidence', value)}
              rows={2}
            />
          </Form.Field>
        </Segment>
      )}
    </BaseStructuredEditor>
  );
};

KeyInsightEditor.propTypes = {
  value: PropTypes.shape({
    text: PropTypes.string,
    importance: PropTypes.string,
    evidence: PropTypes.string,
    timestamp: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string,
  description: PropTypes.string,
  required: PropTypes.bool,
};

export default KeyInsightEditor;