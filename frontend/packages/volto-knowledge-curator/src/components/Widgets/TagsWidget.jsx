import React from 'react';
import { Label } from 'semantic-ui-react';

const TagsWidget = ({ value, field, title }) => {
  if (!value || !Array.isArray(value) || value.length === 0) return null;

  return (
    <div style={{ marginBottom: '10px' }}>
      {title && <strong>{title}: </strong>}
      {value.map((tag, index) => (
        <Label key={index} color="teal" size="small" style={{ marginRight: '5px' }}>
          {tag}
        </Label>
      ))}
    </div>
  );
};

export default TagsWidget; 