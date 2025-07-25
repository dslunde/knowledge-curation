import React, { useCallback, useState } from 'react';
import { Form, Segment, Button, Icon, Header, Label, Grid } from 'semantic-ui-react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import PropTypes from 'prop-types';
import KeyInsightEditor from '../StructuredObjects/KeyInsightEditor';

// Simple polyfill for react-beautiful-dnd
const DnDWrapper = ({ children, ...props }) => {
  try {
    const ReactBeautifulDnd = require('react-beautiful-dnd');
    return <ReactBeautifulDnd.DragDropContext {...props}>{children}</ReactBeautifulDnd.DragDropContext>;
  } catch {
    // Fallback if react-beautiful-dnd is not available
    return <div>{children}</div>;
  }
};

const StructuredInsightEditor = ({ 
  value = [], 
  onChange, 
  title = 'Key Insights',
  description = 'Manage and organize key insights from your research',
  maxInsights = 10,
}) => {
  const [expandedInsights, setExpandedInsights] = useState(new Set());

  const handleAddInsight = useCallback(() => {
    if (value.length >= maxInsights) {
      alert(`Maximum of ${maxInsights} insights allowed`);
      return;
    }
    
    const newInsight = {
      text: '',
      importance: 'medium',
      evidence: '',
      timestamp: new Date().toISOString(),
      id: `insight-${Date.now()}`,
    };
    
    onChange([...value, newInsight]);
    setExpandedInsights(new Set([...expandedInsights, newInsight.id]));
  }, [value, onChange, maxInsights, expandedInsights]);

  const handleRemoveInsight = useCallback((index) => {
    const newInsights = value.filter((_, i) => i !== index);
    onChange(newInsights);
  }, [value, onChange]);

  const handleUpdateInsight = useCallback((index, updatedInsight) => {
    const newInsights = [...value];
    newInsights[index] = updatedInsight;
    onChange(newInsights);
  }, [value, onChange]);

  const handleDragEnd = useCallback((result) => {
    if (!result.destination) return;

    const items = Array.from(value);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    onChange(items);
  }, [value, onChange]);

  const toggleExpanded = useCallback((insightId) => {
    const newExpanded = new Set(expandedInsights);
    if (newExpanded.has(insightId)) {
      newExpanded.delete(insightId);
    } else {
      newExpanded.add(insightId);
    }
    setExpandedInsights(newExpanded);
  }, [expandedInsights]);

  const getImportanceColor = (importance) => {
    switch (importance) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'grey';
      default: return 'grey';
    }
  };

  return (
    <Segment>
      <Header as="h3">
        <Icon name="lightbulb" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      <DnDWrapper onDragEnd={handleDragEnd}>
        <Droppable droppableId="insights">
          {(provided) => (
            <div ref={provided?.innerRef} {...(provided?.droppableProps || {})}>
              {value.map((insight, index) => {
                const isExpanded = expandedInsights.has(insight.id);
                return (
                  <Draggable 
                    key={insight.id || `insight-${index}`} 
                    draggableId={insight.id || `insight-${index}`} 
                    index={index}
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided?.innerRef}
                        {...(provided?.draggableProps || {})}
                        {...(provided?.dragHandleProps || {})}
                        style={{
                          marginBottom: '1em',
                          ...(provided?.draggableProps?.style || {}),
                          backgroundColor: snapshot?.isDragging ? '#f8f9fa' : 'transparent',
                        }}
                      >
                        <Segment>
                          <Grid>
                            <Grid.Row>
                              <Grid.Column width={14}>
                                <div 
                                  style={{ cursor: 'pointer' }}
                                  onClick={() => toggleExpanded(insight.id)}
                                >
                                  <Icon name={isExpanded ? 'chevron down' : 'chevron right'} />
                                  <strong>Insight {index + 1}</strong>
                                  {insight.text && (
                                    <span style={{ marginLeft: '1em', color: '#666' }}>
                                      {insight.text.substring(0, 50)}
                                      {insight.text.length > 50 ? '...' : ''}
                                    </span>
                                  )}
                                  <Label 
                                    size="tiny" 
                                    color={getImportanceColor(insight.importance || 'medium')}
                                    style={{ marginLeft: '0.5em' }}
                                  >
                                    {insight.importance || 'medium'}
                                  </Label>
                                </div>
                              </Grid.Column>
                              <Grid.Column width={2} textAlign="right">
                                <Icon 
                                  name="move" 
                                  color="grey" 
                                  style={{ cursor: 'move', marginRight: '0.5em' }}
                                />
                                <Icon 
                                  name="trash" 
                                  color="red" 
                                  style={{ cursor: 'pointer' }}
                                  onClick={() => {
                                    if (window.confirm('Are you sure you want to delete this insight?')) {
                                      handleRemoveInsight(index);
                                    }
                                  }}
                                />
                              </Grid.Column>
                            </Grid.Row>
                          </Grid>

                          {isExpanded && (
                            <div style={{ marginTop: '1em' }}>
                              <KeyInsightEditor
                                value={insight}
                                onChange={(updatedInsight) => handleUpdateInsight(index, updatedInsight)}
                                required={true}
                              />
                            </div>
                          )}
                        </Segment>
                      </div>
                    )}
                  </Draggable>
                );
              })}
              {provided?.placeholder}
            </div>
          )}
        </Droppable>
      </DnDWrapper>

      <Button 
        primary 
        onClick={handleAddInsight}
        disabled={value.length >= maxInsights}
        style={{ marginTop: '1em' }}
      >
        <Icon name="plus" />
        Add Insight
      </Button>
      
      {value.length >= maxInsights && (
        <Label pointing basic color="orange" style={{ marginLeft: '1em' }}>
          Maximum insights reached ({maxInsights})
        </Label>
      )}

      {value.length === 0 && (
        <Segment placeholder textAlign="center" style={{ marginTop: '1em' }}>
          <Header icon>
            <Icon name="lightbulb outline" />
            No insights added yet
          </Header>
          <Button primary onClick={handleAddInsight}>
            Add Your First Insight
          </Button>
        </Segment>
      )}
    </Segment>
  );
};

StructuredInsightEditor.propTypes = {
  value: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    text: PropTypes.string,
    importance: PropTypes.string,
    evidence: PropTypes.string,
    timestamp: PropTypes.string,
  })),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
  maxInsights: PropTypes.number,
};

export default StructuredInsightEditor;