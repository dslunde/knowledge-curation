import React, { useState, useCallback } from 'react';
import { 
  Segment, 
  Header, 
  Icon, 
  Button,
  List,
  Modal,
  Grid,
  Label,
  Dropdown,
  Message
} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import ProjectLogEntryEditor from '../StructuredObjects/ProjectLogEntryEditor';

const entryTypeColors = {
  progress: 'blue',
  milestone: 'green',
  issue: 'red',
  decision: 'purple',
  meeting: 'teal',
  research: 'orange',
  review: 'yellow',
};

const EntriesManager = ({ 
  value = [], 
  onChange,
  title = 'Project Log Entries',
  description = 'Track all project activities and progress',
}) => {
  const [editingEntry, setEditingEntry] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [sortOrder, setSortOrder] = useState('newest');

  const handleAddEntry = useCallback(() => {
    const newEntry = {
      id: `entry-${Date.now()}`,
      timestamp: new Date().toISOString(),
      author: '',
      entry_type: 'progress',
      description: '',
      related_items: [],
    };
    setEditingEntry(newEntry);
  }, []);

  const handleSaveEntry = useCallback((entry) => {
    const index = value.findIndex(e => e.id === entry.id);
    if (index >= 0) {
      const newEntries = [...value];
      newEntries[index] = entry;
      onChange(newEntries);
    } else {
      onChange([...value, entry]);
    }
    setEditingEntry(null);
  }, [value, onChange]);

  const handleRemoveEntry = useCallback((id) => {
    onChange(value.filter(e => e.id !== id));
  }, [value, onChange]);

  const getFilteredAndSortedEntries = () => {
    let entries = [...value];
    
    // Filter
    if (filterType !== 'all') {
      entries = entries.filter(e => e.entry_type === filterType);
    }
    
    // Sort
    entries.sort((a, b) => {
      const dateA = new Date(a.timestamp);
      const dateB = new Date(b.timestamp);
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });
    
    return entries;
  };

  const entryTypeOptions = [
    { key: 'all', text: 'All Types', value: 'all' },
    { key: 'progress', text: 'Progress Updates', value: 'progress' },
    { key: 'milestone', text: 'Milestones', value: 'milestone' },
    { key: 'issue', text: 'Issues', value: 'issue' },
    { key: 'decision', text: 'Decisions', value: 'decision' },
    { key: 'meeting', text: 'Meetings', value: 'meeting' },
    { key: 'research', text: 'Research', value: 'research' },
    { key: 'review', text: 'Reviews', value: 'review' },
  ];

  const sortOptions = [
    { key: 'newest', text: 'Newest First', value: 'newest' },
    { key: 'oldest', text: 'Oldest First', value: 'oldest' },
  ];

  const entries = getFilteredAndSortedEntries();

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <Segment>
      <Header as="h3">
        <Icon name="list alternate" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      <Grid>
        <Grid.Row>
          <Grid.Column width={12}>
            <Dropdown
              placeholder="Filter by type"
              selection
              options={entryTypeOptions}
              value={filterType}
              onChange={(e, { value }) => setFilterType(value)}
              style={{ marginRight: '1em' }}
            />
            <Dropdown
              placeholder="Sort order"
              selection
              options={sortOptions}
              value={sortOrder}
              onChange={(e, { value }) => setSortOrder(value)}
            />
          </Grid.Column>
          <Grid.Column width={4} textAlign="right">
            <Button primary onClick={handleAddEntry}>
              <Icon name="plus" />
              Add Entry
            </Button>
          </Grid.Column>
        </Grid.Row>
      </Grid>

      {entries.length === 0 ? (
        <Segment placeholder textAlign="center" style={{ marginTop: '1em' }}>
          <Header icon>
            <Icon name="clipboard outline" />
            {filterType === 'all' ? 'No entries yet' : `No ${filterType} entries`}
          </Header>
          <Button primary onClick={handleAddEntry}>
            Add Your First Entry
          </Button>
        </Segment>
      ) : (
        <List divided relaxed style={{ marginTop: '1em' }}>
          {entries.map((entry) => (
            <List.Item key={entry.id}>
              <List.Content floated="right">
                <Button.Group size="tiny">
                  <Button 
                    icon="edit" 
                    onClick={() => setEditingEntry(entry)}
                  />
                  <Button 
                    icon="trash" 
                    onClick={() => {
                      if (window.confirm('Delete this entry?')) {
                        handleRemoveEntry(entry.id);
                      }
                    }}
                  />
                </Button.Group>
              </List.Content>
              <List.Icon 
                name={
                  entry.entry_type === 'progress' ? 'forward' :
                  entry.entry_type === 'milestone' ? 'flag' :
                  entry.entry_type === 'issue' ? 'warning circle' :
                  entry.entry_type === 'decision' ? 'balance scale' :
                  entry.entry_type === 'meeting' ? 'users' :
                  entry.entry_type === 'research' ? 'book' :
                  entry.entry_type === 'review' ? 'eye' :
                  'file'
                }
                size="large" 
                verticalAlign="middle"
                color={entryTypeColors[entry.entry_type] || 'grey'}
              />
              <List.Content>
                <List.Header>
                  {entry.author} - {formatDate(entry.timestamp)}
                </List.Header>
                <List.Description>
                  {entry.description}
                  <div style={{ marginTop: '0.5em' }}>
                    <Label 
                      size="tiny" 
                      color={entryTypeColors[entry.entry_type] || 'grey'}
                    >
                      {entry.entry_type}
                    </Label>
                    <Label size="tiny">
                      <Icon name="clock" />
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </Label>
                    {entry.related_items && entry.related_items.length > 0 && (
                      <Label size="tiny">
                        <Icon name="linkify" />
                        {entry.related_items.length} linked items
                      </Label>
                    )}
                  </div>
                </List.Description>
              </List.Content>
            </List.Item>
          ))}
        </List>
      )}

      <Modal
        open={!!editingEntry}
        onClose={() => setEditingEntry(null)}
        size="large"
      >
        <Modal.Header>
          {editingEntry?.id?.startsWith('entry-') ? 'Add' : 'Edit'} Log Entry
        </Modal.Header>
        <Modal.Content>
          {editingEntry && (
            <ProjectLogEntryEditor
              value={editingEntry}
              onChange={setEditingEntry}
              required={true}
            />
          )}
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setEditingEntry(null)}>Cancel</Button>
          <Button 
            primary 
            onClick={() => handleSaveEntry(editingEntry)}
            disabled={!editingEntry?.description || !editingEntry?.author}
          >
            Save
          </Button>
        </Modal.Actions>
      </Modal>

      {entries.length > 0 && (
        <Message info icon style={{ marginTop: '2em' }}>
          <Icon name="info circle" />
          <Message.Content>
            <Message.Header>Entry Statistics</Message.Header>
            <p>
              Total entries: {entries.length} | 
              {Object.entries(entryTypeColors).map(([type, color]) => {
                const count = value.filter(e => e.entry_type === type).length;
                if (count === 0) return null;
                return (
                  <span key={type}>
                    {' '}
                    <Label size="tiny" color={color}>
                      {type}: {count}
                    </Label>
                  </span>
                );
              })}
            </p>
          </Message.Content>
        </Message>
      )}
    </Segment>
  );
};

EntriesManager.propTypes = {
  value: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    timestamp: PropTypes.string,
    author: PropTypes.string,
    entry_type: PropTypes.string,
    description: PropTypes.string,
    related_items: PropTypes.arrayOf(PropTypes.string),
  })),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
};

export default EntriesManager;