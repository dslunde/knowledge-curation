import React, { useCallback } from 'react';
import { Form, Segment, Label, Icon, Dropdown, Message } from 'semantic-ui-react';
import PropTypes from 'prop-types';
import BaseStructuredEditor from '../shared/BaseStructuredEditor';

const annotationTypeOptions = [
  { key: 'note', text: 'Note', value: 'note', icon: 'sticky note' },
  { key: 'question', text: 'Question', value: 'question', icon: 'question circle' },
  { key: 'highlight', text: 'Highlight', value: 'highlight', icon: 'highlighter' },
  { key: 'correction', text: 'Correction', value: 'correction', icon: 'edit' },
  { key: 'reference', text: 'Reference', value: 'reference', icon: 'linkify' },
  { key: 'idea', text: 'Idea', value: 'idea', icon: 'lightbulb' },
  { key: 'todo', text: 'To-Do', value: 'todo', icon: 'tasks' },
];

const AnnotationEditor = ({ value = {}, onChange, errors, title, description, required }) => {
  const handleFieldChange = useCallback((field, fieldValue) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  }, [value, onChange]);

  const validateAnnotation = useCallback((annotation) => {
    const errors = [];
    if (!annotation.text || annotation.text.trim() === '') {
      errors.push('Annotation text is required');
    }
    if (!annotation.author || annotation.author.trim() === '') {
      errors.push('Author is required');
    }
    return errors;
  }, []);

  const currentTimestamp = value.timestamp || new Date().toISOString();
  const selectedType = annotationTypeOptions.find(opt => opt.value === value.annotation_type);

  return (
    <BaseStructuredEditor
      value={value}
      onChange={onChange}
      errors={errors}
      title={title}
      description={description}
      required={required}
      onValidate={validateAnnotation}
    >
      {({ value: annotationValue, onChange: handleChange }) => (
        <Segment>
          <Form.Group widths="equal">
            <Form.Field required>
              <label>Author</label>
              <Form.Input
                placeholder="Enter your name..."
                value={annotationValue.author || ''}
                onChange={(e, { value }) => handleFieldChange('author', value)}
                icon="user"
                iconPosition="left"
              />
            </Form.Field>

            <Form.Field>
              <label>Annotation Type</label>
              <Dropdown
                placeholder="Select type"
                fluid
                selection
                options={annotationTypeOptions}
                value={annotationValue.annotation_type || 'note'}
                onChange={(e, { value }) => handleFieldChange('annotation_type', value)}
              />
            </Form.Field>
          </Form.Group>

          <Form.Field>
            <label>Target Element</label>
            <Form.Input
              placeholder="What element does this annotation refer to? (optional)"
              value={annotationValue.target_element || ''}
              onChange={(e, { value }) => handleFieldChange('target_element', value)}
              icon="target"
              iconPosition="left"
            />
          </Form.Field>

          <Form.Field required>
            <label>Annotation Text</label>
            <Form.TextArea
              placeholder={`Enter your ${selectedType ? selectedType.text.toLowerCase() : 'annotation'}...`}
              value={annotationValue.text || ''}
              onChange={(e, { value }) => handleFieldChange('text', value)}
              rows={3}
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

          {selectedType && (
            <Message info size="tiny">
              <Icon name={selectedType.icon} />
              <Message.Content>
                {selectedType.value === 'note' && 'Add a general note or observation'}
                {selectedType.value === 'question' && 'Ask a question for clarification'}
                {selectedType.value === 'highlight' && 'Highlight important information'}
                {selectedType.value === 'correction' && 'Suggest a correction or improvement'}
                {selectedType.value === 'reference' && 'Add a reference or link to related content'}
                {selectedType.value === 'idea' && 'Capture an idea or insight'}
                {selectedType.value === 'todo' && 'Create a to-do item or action point'}
              </Message.Content>
            </Message>
          )}
        </Segment>
      )}
    </BaseStructuredEditor>
  );
};

AnnotationEditor.propTypes = {
  value: PropTypes.shape({
    text: PropTypes.string,
    author: PropTypes.string,
    timestamp: PropTypes.string,
    target_element: PropTypes.string,
    annotation_type: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string,
  description: PropTypes.string,
  required: PropTypes.bool,
};

export default AnnotationEditor;