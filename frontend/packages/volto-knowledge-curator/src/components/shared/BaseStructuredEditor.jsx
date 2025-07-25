import React, { useState, useCallback } from 'react';
import { Form, Message, Button, Icon } from 'semantic-ui-react';
import PropTypes from 'prop-types';

/**
 * Base component for structured content editors
 * Provides common functionality for validation, error handling, and accessibility
 */
const BaseStructuredEditor = ({
  value,
  onChange,
  errors,
  fieldSchema,
  title,
  description,
  required,
  children,
  onValidate,
}) => {
  const [localErrors, setLocalErrors] = useState([]);
  const [touched, setTouched] = useState(false);

  const handleChange = useCallback((newValue) => {
    setTouched(true);
    if (onValidate) {
      const validationErrors = onValidate(newValue);
      setLocalErrors(validationErrors);
    }
    onChange(newValue);
  }, [onChange, onValidate]);

  const handleBlur = useCallback(() => {
    setTouched(true);
  }, []);

  const allErrors = [...(errors || []), ...localErrors];
  const showErrors = touched && allErrors.length > 0;

  return (
    <Form.Field required={required} error={showErrors}>
      {title && <label>{title}</label>}
      {description && (
        <Message info size="tiny">
          <p>{description}</p>
        </Message>
      )}
      
      <div onBlur={handleBlur}>
        {typeof children === 'function' 
          ? children({ value, onChange: handleChange, errors: allErrors })
          : children
        }
      </div>

      {showErrors && (
        <Message error size="tiny">
          <Message.Header>Validation Errors</Message.Header>
          <Message.List>
            {allErrors.map((error, index) => (
              <Message.Item key={index}>{error}</Message.Item>
            ))}
          </Message.List>
        </Message>
      )}
    </Form.Field>
  );
};

BaseStructuredEditor.propTypes = {
  value: PropTypes.any,
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  fieldSchema: PropTypes.object,
  title: PropTypes.string,
  description: PropTypes.string,
  required: PropTypes.bool,
  children: PropTypes.oneOfType([PropTypes.node, PropTypes.func]).isRequired,
  onValidate: PropTypes.func,
};

BaseStructuredEditor.defaultProps = {
  errors: [],
  required: false,
};

export default BaseStructuredEditor;