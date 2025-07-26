import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { 
  Container, 
  Segment, 
  Header, 
  Grid, 
  Card, 
  Icon, 
  Button, 
  Modal, 
  Message, 
  Table,
  Dropdown,
  Input,
  Label,
  Dimmer,
  Loader,
  Progress
} from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';
import { toast } from 'react-toastify';

const messages = defineMessages({
  contentCollection: {
    id: 'content-collection.title',
    defaultMessage: 'Content Collection Management',
  },
  addContent: {
    id: 'content-collection.add-content',
    defaultMessage: 'Add Content to Collection',
  },
  searchContent: {
    id: 'content-collection.search-content',
    defaultMessage: 'Search available content...',
  },
  contentAdded: {
    id: 'content-collection.content-added',
    defaultMessage: 'Content added to collection',
  },
  contentRemoved: {
    id: 'content-collection.content-removed',
    defaultMessage: 'Content removed from collection',
  },
  validateReferences: {
    id: 'content-collection.validate-references',
    defaultMessage: 'Validate All References',
  },
  noContentFound: {
    id: 'content-collection.no-content-found',
    defaultMessage: 'No content found matching your criteria',
  },
  academic: {
    id: 'content-collection.academic-note',
    defaultMessage: 'Academic Mode: Content is organized for scholarly rigor',
  },
});

const CONTENT_TYPES = {
  knowledge_items: { 
    label: 'Knowledge Items', 
    icon: 'lightbulb', 
    color: 'blue',
    description: 'Atomic knowledge units - the foundation of your collection'
  },
  learning_goals: { 
    label: 'Learning Goals', 
    icon: 'target', 
    color: 'green',
    description: 'Learning objectives and progress tracking'
  },
  research_notes: { 
    label: 'Research Notes', 
    icon: 'file alternate', 
    color: 'orange',
    description: 'Research insights and scholarly annotations'
  },
  project_logs: { 
    label: 'Project Logs', 
    icon: 'tasks', 
    color: 'purple',
    description: 'Project progress and implementation records'
  },
  bookmarks: { 
    label: 'Bookmark+ Resources', 
    icon: 'bookmark', 
    color: 'teal',
    description: 'External resources and references'
  },
};

const ContentCollectionManager = ({ data, onChange, validationState, onValidate, intl }) => {
  // Component state
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [selectedContentType, setSelectedContentType] = useState('knowledge_items');
  const [searchQuery, setSearchQuery] = useState('');
  const [availableContent, setAvailableContent] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);

  // Get current collection content
  const currentContent = useMemo(() => {
    const content = {};
    Object.keys(CONTENT_TYPES).forEach(type => {
      const fieldName = `included_${type}`;
      content[type] = data[fieldName] || [];
    });
    return content;
  }, [data]);

  // Calculate collection statistics
  const collectionStats = useMemo(() => {
    const stats = {};
    let totalItems = 0;
    
    Object.keys(CONTENT_TYPES).forEach(type => {
      const count = currentContent[type].length;
      stats[type] = count;
      totalItems += count;
    });
    
    return { ...stats, total: totalItems };
  }, [currentContent]);

  // Fetch available content for selection
  const fetchAvailableContent = useCallback(async (contentType, query = '') => {
    setLoading(true);
    try {
      const searchParams = new URLSearchParams({
        portal_type: contentType === 'bookmarks' ? 'BookmarkPlus' : 
                     contentType === 'knowledge_items' ? 'KnowledgeItem' :
                     contentType === 'learning_goals' ? 'LearningGoal' :
                     contentType === 'research_notes' ? 'ResearchNote' :
                     'ProjectLog',
        sort_on: 'created',
        sort_order: 'descending',
        b_size: 50,
      });

      if (query) {
        searchParams.append('SearchableText', query);
      }

      const response = await fetch(`/++api++/@search?${searchParams}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        // Filter out items already in the collection
        const alreadyIncluded = currentContent[contentType] || [];
        const filtered = result.items.filter(item => !alreadyIncluded.includes(item.UID));
        setAvailableContent(filtered);
      } else {
        toast.error('Failed to fetch available content');
        setAvailableContent([]);
      }
    } catch (error) {
      console.error('Error fetching content:', error);
      toast.error('Error fetching content');
      setAvailableContent([]);
    }
    setLoading(false);
  }, [currentContent]);

  // Handle adding content to collection
  const handleAddContent = useCallback(async () => {
    if (selectedItems.length === 0) return;

    const fieldName = `included_${selectedContentType}`;
    const currentItems = data[fieldName] || [];
    const newItems = [...currentItems, ...selectedItems];

    onChange({
      [fieldName]: newItems
    });

    toast.success(intl.formatMessage(messages.contentAdded));
    setSelectedItems([]);
    setAddModalOpen(false);
  }, [selectedItems, selectedContentType, data, onChange, intl]);

  // Handle removing content from collection
  const handleRemoveContent = useCallback((contentType, uid) => {
    const fieldName = `included_${contentType}`;
    const currentItems = data[fieldName] || [];
    const updatedItems = currentItems.filter(item => item !== uid);

    onChange({
      [fieldName]: updatedItems
    });

    toast.success(intl.formatMessage(messages.contentRemoved));
  }, [data, onChange, intl]);

  // Handle content type selection change
  const handleContentTypeChange = useCallback((value) => {
    setSelectedContentType(value);
    setSearchQuery('');
    setSelectedItems([]);
    fetchAvailableContent(value);
  }, [fetchAvailableContent]);

  // Handle search
  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
    if (query.length >= 2 || query.length === 0) {
      fetchAvailableContent(selectedContentType, query);
    }
  }, [selectedContentType, fetchAvailableContent]);

  // Content type options for dropdown
  const contentTypeOptions = Object.entries(CONTENT_TYPES).map(([key, config]) => ({
    key,
    value: key,
    text: config.label,
    icon: config.icon,
    description: config.description,
  }));

  return (
    <Container>
      {/* Academic Standards Notice */}
      <Message info icon>
        <Icon name="university" />
        <Message.Content>
          <Message.Header>Academic Collection Management</Message.Header>
          {intl.formatMessage(messages.academic)}
        </Message.Content>
      </Message>

      {/* Collection Overview */}
      <Segment>
        <Header as="h2" dividing>
          <Icon name="archive" />
          {intl.formatMessage(messages.contentCollection)}
          <Header.Subheader>
            Manage and organize your knowledge collection with academic precision
          </Header.Subheader>
        </Header>

        {/* Statistics Cards */}
        <Grid columns={6} stackable>
          {Object.entries(CONTENT_TYPES).map(([type, config]) => (
            <Grid.Column key={type}>
              <Card color={config.color}>
                <Card.Content textAlign="center">
                  <Icon name={config.icon} size="large" color={config.color} />
                  <Card.Header>{collectionStats[type] || 0}</Card.Header>
                  <Card.Meta>{config.label}</Card.Meta>
                </Card.Content>
              </Card>
            </Grid.Column>
          ))}
          <Grid.Column>
            <Card>
              <Card.Content textAlign="center">
                <Icon name="calculator" size="large" />
                <Card.Header>{collectionStats.total}</Card.Header>
                <Card.Meta>Total Items</Card.Meta>
              </Card.Content>
            </Card>
          </Grid.Column>
        </Grid>

        {/* Action Buttons */}
        <Grid columns={2} style={{ marginTop: '1em' }}>
          <Grid.Column>
            <Button 
              primary 
              icon 
              labelPosition="left"
              onClick={() => setAddModalOpen(true)}
            >
              <Icon name="plus" />
              {intl.formatMessage(messages.addContent)}
            </Button>
          </Grid.Column>
          <Grid.Column textAlign="right">
            <Button 
              icon 
              labelPosition="left"
              onClick={onValidate}
              loading={validationState.loading}
            >
              <Icon name="checkmark" />
              {intl.formatMessage(messages.validateReferences)}
            </Button>
          </Grid.Column>
        </Grid>
      </Segment>

      {/* Current Content Display */}
      {Object.entries(CONTENT_TYPES).map(([type, config]) => {
        const items = currentContent[type] || [];
        if (items.length === 0) return null;

        return (
          <Segment key={type}>
            <Header as="h3" color={config.color}>
              <Icon name={config.icon} />
              {config.label} ({items.length})
            </Header>
            <Table celled striped>
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell>Title</Table.HeaderCell>
                  <Table.HeaderCell>UID</Table.HeaderCell>
                  <Table.HeaderCell width={2}>Actions</Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {items.map((uid, index) => (
                  <Table.Row key={uid}>
                    <Table.Cell>
                      <Label color={config.color}>
                        <Icon name={config.icon} />
                        Item {index + 1}
                      </Label>
                    </Table.Cell>
                    <Table.Cell>
                      <code>{uid}</code>
                    </Table.Cell>
                    <Table.Cell>
                      <Button 
                        size="small" 
                        color="red" 
                        icon="trash"
                        onClick={() => handleRemoveContent(type, uid)}
                      />
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </Segment>
        );
      })}

      {/* Add Content Modal */}
      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        size="large"
      >
        <Modal.Header>
          <Icon name="plus" />
          {intl.formatMessage(messages.addContent)}
        </Modal.Header>
        <Modal.Content>
          <Grid divided>
            <Grid.Row>
              <Grid.Column width={4}>
                <Header as="h4">Content Type</Header>
                <Dropdown
                  selection
                  fluid
                  value={selectedContentType}
                  onChange={(e, { value }) => handleContentTypeChange(value)}
                  options={contentTypeOptions}
                />
              </Grid.Column>
              <Grid.Column width={12}>
                <Header as="h4">Search & Select</Header>
                <Input
                  fluid
                  icon="search"
                  placeholder={intl.formatMessage(messages.searchContent)}
                  value={searchQuery}
                  onChange={(e, { value }) => handleSearch(value)}
                />
              </Grid.Column>
            </Grid.Row>
          </Grid>

          <Dimmer.Dimmable>
            <Dimmer active={loading} inverted>
              <Loader>Loading content...</Loader>
            </Dimmer>

            {availableContent.length > 0 ? (
              <Table selectable celled>
                <Table.Header>
                  <Table.Row>
                    <Table.HeaderCell collapsing>Select</Table.HeaderCell>
                    <Table.HeaderCell>Title</Table.HeaderCell>
                    <Table.HeaderCell>Description</Table.HeaderCell>
                    <Table.HeaderCell>Created</Table.HeaderCell>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {availableContent.map((item) => (
                    <Table.Row 
                      key={item.UID}
                      active={selectedItems.includes(item.UID)}
                      onClick={() => {
                        setSelectedItems(prev => 
                          prev.includes(item.UID) 
                            ? prev.filter(id => id !== item.UID)
                            : [...prev, item.UID]
                        );
                      }}
                    >
                      <Table.Cell>
                        <Icon 
                          name={selectedItems.includes(item.UID) ? 'check circle' : 'circle outline'} 
                          color={selectedItems.includes(item.UID) ? 'green' : 'grey'}
                        />
                      </Table.Cell>
                      <Table.Cell>
                        <strong>{item.title}</strong>
                      </Table.Cell>
                      <Table.Cell>{item.description}</Table.Cell>
                      <Table.Cell>{new Date(item.created).toLocaleDateString()}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            ) : !loading && (
              <Message info>
                <Icon name="info circle" />
                {intl.formatMessage(messages.noContentFound)}
              </Message>
            )}
          </Dimmer.Dimmable>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setAddModalOpen(false)}>
            <Icon name="cancel" /> Cancel
          </Button>
          <Button 
            primary 
            disabled={selectedItems.length === 0}
            onClick={handleAddContent}
          >
            <Icon name="plus" /> Add Selected ({selectedItems.length})
          </Button>
        </Modal.Actions>
      </Modal>
    </Container>
  );
};

export default injectIntl(ContentCollectionManager); 