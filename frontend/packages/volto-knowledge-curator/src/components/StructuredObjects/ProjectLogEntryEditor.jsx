import React, { useCallback } from 'react';
import { Form, Segment, Label, Icon, Dropdown } from 'semantic-ui-react';
import PropTypes from 'prop-types';
import BaseStructuredEditor from '../shared/BaseStructuredEditor';

const entryTypeOptions = [
  { key: 'progress', text: 'Progress Update', value: 'progress', icon: 'forward' },
  { key: 'milestone', text: 'Milestone', value: 'milestone', icon: 'flag' },
  { key: 'issue', text: 'Issue', value: 'issue', icon: 'warning circle' },
  { key: 'decision', text: 'Decision', value: 'decision', icon: 'balance scale' },
  { key: 'meeting', text: 'Meeting', value: 'meeting', icon: 'users' },
  { key: 'research', text: 'Research', value: 'research', icon: 'book' },
  { key: 'review', text: 'Review', value: 'review', icon: 'eye' },
];

const ProjectLogEntryEditor = ({ value = {}, onChange, errors, title, description, required }) => {
  const handleFieldChange = useCallback((field, fieldValue) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  }, [value, onChange]);

  const handleRelatedItemsChange = useCallback((items) => {
    handleFieldChange('related_items', items.split(',').map(item => item.trim()).filter(Boolean));
  }, [handleFieldChange]);

  const validateEntry = useCallback((entry) => {
    const errors = [];
    if (!entry.description || entry.description.trim() === '') {
      errors.push('Entry description is required');
    }
    if (!entry.author || entry.author.trim() === '') {
      errors.push('Author is required');
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
      onValidate={validateEntry}
    >
      {({ value: entryValue, onChange: handleChange }) => (
        <Segment>
          <Form.Group widths="equal">
            <Form.Field required>
              <label>Author</label>
              <Form.Input
                placeholder="Enter author name..."
                value={entryValue.author || ''}
                onChange={(e, { value }) => handleFieldChange('author', value)}
                icon="user"
                iconPosition="left"
              />
            </Form.Field>

            <Form.Field>
              <label>Entry Type</label>
              <Dropdown
                placeholder="Select entry type"
                fluid
                selection
                options={entryTypeOptions}
                value={entryValue.entry_type || ''}
                onChange={(e, { value }) => handleFieldChange('entry_type', value)}
              />
            </Form.Field>
          </Form.Group>

          <Form.Field>
            <label>Timestamp</label>
            <input
              type="datetime-local"
              value={currentTimestamp.slice(0, 16)}
              onChange={(e) => handleFieldChange('timestamp', new Date(e.target.value).toISOString())}
            />
          </Form.Field>

          <Form.Field required>
            <label>Description</label>
            <Form.TextArea
              placeholder="Describe the log entry..."
              value={entryValue.description || ''}
              onChange={(e, { value }) => handleFieldChange('description', value)}
              rows={4}
            />
          </Form.Field>

          <Form.Field>
            <label>Related Items</label>
            <Form.Input
              placeholder="Enter related item IDs separated by commas..."
              value={(entryValue.related_items || []).join(', ')}
              onChange={(e, { value }) => handleRelatedItemsChange(value)}
              icon="linkify"
              iconPosition="left"
            />
            <Label pointing>
              <Icon name="info circle" />
              Enter UIDs or titles of related content items
            </Label>
          </Form.Field>

          {entryValue.entry_type && (
            <Label color="blue" size="small">
              <Icon name={entryTypeOptions.find(opt => opt.value === entryValue.entry_type)?.icon || 'file'} />
              {entryTypeOptions.find(opt => opt.value === entryValue.entry_type)?.text || entryValue.entry_type}
            </Label>
          )}
        </Segment>
      )}
    </BaseStructuredEditor>
  );
};

ProjectLogEntryEditor.propTypes = {
  value: PropTypes.shape({
    id: PropTypes.string,
    timestamp: PropTypes.string,
    author: PropTypes.string,
    entry_type: PropTypes.string,
    description: PropTypes.string,
    related_items: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string,
  description: PropTypes.string,
  required: PropTypes.bool,
};

export default ProjectLogEntryEditor;