import React, { useState, useEffect } from 'react';
import { 
  Segment, 
  Header, 
  Form, 
  Dropdown, 
  Checkbox,
  Grid,
  Icon,
  Label,
  Button,
  Accordion,
  Message,
  Divider
} from 'semantic-ui-react';
import { format, subDays, subWeeks, subMonths } from 'date-fns';

const SearchFilters = ({ 
  filters = {}, 
  onChange, 
  show = false, 
  onToggle,
  onReset
}) => {
  const [activeFilters, setActiveFilters] = useState(0);
  const [presetDateRanges] = useState([
    { key: 'today', text: 'Today', value: { days: 0 } },
    { key: 'week', text: 'This Week', value: { days: 7 } },
    { key: 'month', text: 'This Month', value: { days: 30 } },
    { key: 'quarter', text: 'This Quarter', value: { days: 90 } },
    { key: 'year', text: 'This Year', value: { days: 365 } },
    { key: 'custom', text: 'Custom Range', value: null }
  ]);

  // Content type options
  const contentTypeOptions = [
    { key: 'KnowledgeItem', text: 'Knowledge Items', value: 'KnowledgeItem', icon: 'lightbulb' },
    { key: 'ResearchNote', text: 'Research Notes', value: 'ResearchNote', icon: 'lab' },
    { key: 'BookmarkPlus', text: 'Bookmarks+', value: 'BookmarkPlus', icon: 'bookmark' },
    { key: 'LearningGoal', text: 'Learning Goals', value: 'LearningGoal', icon: 'target' },
    { key: 'ProjectLog', text: 'Project Logs', value: 'ProjectLog', icon: 'clipboard list' },
    { key: 'KnowledgeContainer', text: 'Knowledge Containers', value: 'KnowledgeContainer', icon: 'archive' }
  ];

  // Difficulty level options
  const difficultyOptions = [
    { key: 'beginner', text: 'Beginner', value: 'beginner', icon: 'circle outline' },
    { key: 'intermediate', text: 'Intermediate', value: 'intermediate', icon: 'circle half outline' },
    { key: 'advanced', text: 'Advanced', value: 'advanced', icon: 'circle' },
    { key: 'expert', text: 'Expert', value: 'expert', icon: 'star' }
  ];

  // Workflow state options
  const workflowStateOptions = [
    { key: 'capture', text: 'Capture', value: 'capture', color: 'yellow' },
    { key: 'private', text: 'Private', value: 'private', color: 'grey' },
    { key: 'process', text: 'Process', value: 'process', color: 'blue' },
    { key: 'reviewed', text: 'Reviewed', value: 'reviewed', color: 'green' },
    { key: 'published', text: 'Published', value: 'published', color: 'teal' }
  ];

  // Update filters
  const updateFilter = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    onChange(newFilters);
  };

  // Handle content type selection
  const handleContentTypeChange = (e, { value }) => {
    updateFilter('contentTypes', value);
  };

  // Handle difficulty selection
  const handleDifficultyChange = (e, { value }) => {
    updateFilter('difficulty', value);
  };

  // Handle workflow state selection
  const handleWorkflowStateChange = (e, { value }) => {
    updateFilter('workflowState', value);
  };

  // Handle similarity threshold change
  const handleThresholdChange = (value) => {
    updateFilter('similarityThreshold', value);
  };

  // Handle date range preset selection
  const handleDateRangePreset = (preset) => {
    if (preset.value) {
      const startDate = subDays(new Date(), preset.value.days);
      updateFilter('dateRange', {
        start: startDate.toISOString(),
        end: new Date().toISOString(),
        preset: preset.key
      });
    } else {
      // Custom range - clear preset
      updateFilter('dateRange', { 
        ...filters.dateRange,
        preset: 'custom' 
      });
    }
  };

  // Handle custom date inputs
  const handleCustomDateChange = (field, value) => {
    updateFilter('dateRange', {
      ...filters.dateRange,
      [field]: value,
      preset: 'custom'
    });
  };

  // Clear all filters
  const clearFilters = () => {
    const defaultFilters = {
      contentTypes: [],
      dateRange: null,
      similarityThreshold: 0.5,
      tags: [],
      difficulty: [],
      workflowState: []
    };
    onChange(defaultFilters);
  };

  // Count active filters
  useEffect(() => {
    let count = 0;
    if (filters.contentTypes?.length > 0) count++;
    if (filters.dateRange) count++;
    if (filters.similarityThreshold !== 0.5) count++;
    if (filters.difficulty?.length > 0) count++;
    if (filters.workflowState?.length > 0) count++;
    if (filters.tags?.length > 0) count++;
    setActiveFilters(count);
  }, [filters]);

  if (!show) {
    return (
      <div className="search-filters-collapsed">
        {activeFilters > 0 && (
          <Message info size="mini">
            <Icon name="filter" />
            {activeFilters} active filter{activeFilters !== 1 ? 's' : ''}
            <Button 
              size="mini" 
              basic 
              floated="right"
              onClick={clearFilters}
              content="Clear All"
            />
          </Message>
        )}
      </div>
    );
  }

  return (
    <Segment className="search-filters-expanded">
      <Header as="h4">
        <Icon name="filter" />
        Advanced Filters
        <Header.Subheader>
          Refine your search with specific criteria
        </Header.Subheader>
      </Header>

      <Form>
        <Grid stackable>
          {/* Content Types */}
          <Grid.Column width={8}>
            <Form.Field>
              <label>Content Types</label>
              <Dropdown
                placeholder="Select content types"
                fluid
                multiple
                selection
                options={contentTypeOptions}
                value={filters.contentTypes || []}
                onChange={handleContentTypeChange}
                renderLabel={(option) => ({
                  color: 'blue',
                  content: option.text,
                  icon: option.icon
                })}
              />
            </Form.Field>
          </Grid.Column>

          {/* Similarity Threshold */}
          <Grid.Column width={8}>
            <Form.Field>
              <label>
                Similarity Threshold: {((filters.similarityThreshold || 0.5) * 100).toFixed(0)}%
              </label>
              <div className="threshold-slider">
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={filters.similarityThreshold || 0.5}
                  onChange={(e) => handleThresholdChange(parseFloat(e.target.value))}
                  className="ui slider"
                  style={{ width: '100%', marginBottom: '0.5rem' }}
                />
                <div className="threshold-labels">
                  <span>Less Similar</span>
                  <span>More Similar</span>
                </div>
              </div>
              <small>
                Lower values return more results, higher values return more precise matches
              </small>
            </Form.Field>
          </Grid.Column>

          {/* Date Range */}
          <Grid.Column width={8}>
            <Form.Field>
              <label>Date Range</label>
              <div className="date-range-presets">
                {presetDateRanges.map((preset) => (
                  <Button
                    key={preset.key}
                    size="mini"
                    basic={filters.dateRange?.preset !== preset.key}
                    primary={filters.dateRange?.preset === preset.key}
                    onClick={() => handleDateRangePreset(preset)}
                    content={preset.text}
                  />
                ))}
              </div>
              
              {filters.dateRange?.preset === 'custom' && (
                <Grid columns={2} className="custom-date-inputs">
                  <Grid.Column>
                    <Form.Input
                      type="date"
                      label="Start Date"
                      value={filters.dateRange?.start ? 
                        format(new Date(filters.dateRange.start), 'yyyy-MM-dd') : ''
                      }
                      onChange={(e, { value }) => 
                        handleCustomDateChange('start', new Date(value).toISOString())
                      }
                    />
                  </Grid.Column>
                  <Grid.Column>
                    <Form.Input
                      type="date"
                      label="End Date"
                      value={filters.dateRange?.end ? 
                        format(new Date(filters.dateRange.end), 'yyyy-MM-dd') : ''
                      }
                      onChange={(e, { value }) => 
                        handleCustomDateChange('end', new Date(value).toISOString())
                      }
                    />
                  </Grid.Column>
                </Grid>
              )}
            </Form.Field>
          </Grid.Column>

          {/* Difficulty Level */}
          <Grid.Column width={8}>
            <Form.Field>
              <label>Difficulty Level</label>
              <Dropdown
                placeholder="Select difficulty levels"
                fluid
                multiple
                selection
                options={difficultyOptions}
                value={filters.difficulty || []}
                onChange={handleDifficultyChange}
                renderLabel={(option) => ({
                  content: option.text,
                  icon: option.icon
                })}
              />
            </Form.Field>
          </Grid.Column>

          {/* Workflow State */}
          <Grid.Column width={8}>
            <Form.Field>
              <label>Workflow State</label>
              <Dropdown
                placeholder="Select workflow states"
                fluid
                multiple
                selection
                options={workflowStateOptions}
                value={filters.workflowState || []}
                onChange={handleWorkflowStateChange}
                renderLabel={(option) => ({
                  color: option.color,
                  content: option.text
                })}
              />
            </Form.Field>
          </Grid.Column>

          {/* Additional Options */}
          <Grid.Column width={16}>
            <Divider />
            <Header as="h5">Additional Options</Header>
            <Form.Group>
              <Form.Field>
                <Checkbox 
                  label="Include archived content"
                  checked={filters.includeArchived || false}
                  onChange={(e, { checked }) => updateFilter('includeArchived', checked)}
                />
              </Form.Field>
              <Form.Field>
                <Checkbox 
                  label="Only show content with embeddings"
                  checked={filters.hasEmbeddings || false}
                  onChange={(e, { checked }) => updateFilter('hasEmbeddings', checked)}
                />
              </Form.Field>
              <Form.Field>
                <Checkbox 
                  label="Exclude duplicates"
                  checked={filters.excludeDuplicates || false}
                  onChange={(e, { checked }) => updateFilter('excludeDuplicates', checked)}
                />
              </Form.Field>
            </Form.Group>
          </Grid.Column>
        </Grid>

        {/* Filter Actions */}
        <Divider />
        <Button.Group>
          <Button 
            icon="eraser" 
            content="Clear All"
            onClick={clearFilters}
            disabled={activeFilters === 0}
          />
          <Button 
            icon="save" 
            content="Save Filter Preset"
            disabled={activeFilters === 0}
          />
          <Button 
            icon="upload" 
            content="Load Preset"
          />
        </Button.Group>

        {/* Active Filters Summary */}
        {activeFilters > 0 && (
          <Message info className="active-filters-summary">
            <Message.Header>Active Filters ({activeFilters})</Message.Header>
            <div className="filter-tags">
              {filters.contentTypes?.map((type) => (
                <Label key={type} size="mini" color="blue">
                  {type}
                  <Icon 
                    name="delete" 
                    onClick={() => {
                      const newTypes = filters.contentTypes.filter(t => t !== type);
                      updateFilter('contentTypes', newTypes);
                    }}
                  />
                </Label>
              ))}
              
              {filters.dateRange && (
                <Label size="mini" color="green">
                  Date: {filters.dateRange.preset || 'Custom'}
                  <Icon 
                    name="delete" 
                    onClick={() => updateFilter('dateRange', null)}
                  />
                </Label>
              )}

              {filters.similarityThreshold !== 0.5 && (
                <Label size="mini" color="orange">
                  Similarity: {(filters.similarityThreshold * 100).toFixed(0)}%
                  <Icon 
                    name="delete" 
                    onClick={() => updateFilter('similarityThreshold', 0.5)}
                  />
                </Label>
              )}

              {filters.difficulty?.map((level) => (
                <Label key={level} size="mini" color="purple">
                  {level}
                  <Icon 
                    name="delete" 
                    onClick={() => {
                      const newLevels = filters.difficulty.filter(l => l !== level);
                      updateFilter('difficulty', newLevels);
                    }}
                  />
                </Label>
              ))}

              {filters.workflowState?.map((state) => (
                <Label key={state} size="mini" color="teal">
                  {state}
                  <Icon 
                    name="delete" 
                    onClick={() => {
                      const newStates = filters.workflowState.filter(s => s !== state);
                      updateFilter('workflowState', newStates);
                    }}
                  />
                </Label>
              ))}
            </div>
          </Message>
        )}
      </Form>
    </Segment>
  );
};

export default SearchFilters; 