import React, { useCallback, useState, useMemo } from 'react';
import { Container, Segment, Tab, Header, Grid, Card, Icon, Button, Modal, Message } from 'semantic-ui-react';
import { Form } from '@plone/volto/components';
import { injectIntl, defineMessages } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';
import { toast } from 'react-toastify';
import ContentCollectionManager from './ContentCollectionManager';
import OrganizationStructureEditor from './OrganizationStructureEditor';
import SharingPermissionsManager from './SharingPermissionsManager';
import ExportOptionsManager from './ExportOptionsManager';
import ContainerAnalytics from './ContainerAnalytics';

const messages = defineMessages({
  basicInfo: {
    id: 'knowledge-container.tab.basic-info',
    defaultMessage: 'Basic Information',
  },
  contentCollection: {
    id: 'knowledge-container.tab.content-collection',
    defaultMessage: 'Content Collection',
  },
  organization: {
    id: 'knowledge-container.tab.organization',
    defaultMessage: 'Organization & Structure',
  },
  sharing: {
    id: 'knowledge-container.tab.sharing',
    defaultMessage: 'Sharing & Publication',
  },
  export: {
    id: 'knowledge-container.tab.export',
    defaultMessage: 'Export & Publishing',
  },
  analytics: {
    id: 'knowledge-container.tab.analytics',
    defaultMessage: 'Analytics & Insights',
  },
  academicStandards: {
    id: 'knowledge-container.academic-standards',
    defaultMessage: 'Academic Standards Enabled',
  },
  knowledgeSovereignty: {
    id: 'knowledge-container.knowledge-sovereignty',
    defaultMessage: 'Your knowledge remains under your complete control',
  },
  validatingContent: {
    id: 'knowledge-container.validating-content',
    defaultMessage: 'Validating content references...',
  },
  contentValidated: {
    id: 'knowledge-container.content-validated',
    defaultMessage: 'All content references are valid',
  },
  validationErrors: {
    id: 'knowledge-container.validation-errors',
    defaultMessage: 'Some content references are invalid and need attention',
  },
});

const KnowledgeContainerEdit = (props) => {
  const { data, onChangeField, intl, pathname } = props;
  const dispatch = useDispatch();
  
  // Local state for advanced features
  const [validationState, setValidationState] = useState({ loading: false, errors: [], valid: true });
  const [showPreview, setShowPreview] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  // Computed values for academic metadata
  const academicMetadata = useMemo(() => ({
    totalItems: (data.included_learning_goals?.length || 0) +
                (data.included_knowledge_items?.length || 0) +
                (data.included_research_notes?.length || 0) +
                (data.included_project_logs?.length || 0) +
                (data.included_bookmarks?.length || 0),
    collectionType: data.collection_type || 'curated',
    organizationStructure: data.organization_structure || 'hierarchical',
    publicationStatus: data.publication_status || 'draft',
    targetAudience: data.target_audience || 'self',
  }), [data]);

  // Handle content collection changes
  const handleContentCollectionChange = useCallback((contentData) => {
    Object.entries(contentData).forEach(([field, value]) => {
      onChangeField(field, value);
    });
    // Trigger validation after content changes
    setValidationState(prev => ({ ...prev, loading: true }));
    setTimeout(() => validateContentReferences(), 500);
  }, [onChangeField]);

  // Handle organization structure changes
  const handleOrganizationChange = useCallback((organizationData) => {
    Object.entries(organizationData).forEach(([field, value]) => {
      onChangeField(field, value);
    });
  }, [onChangeField]);

  // Handle sharing and permissions
  const handleSharingChange = useCallback((sharingData) => {
    Object.entries(sharingData).forEach(([field, value]) => {
      onChangeField(field, value);
    });
  }, [onChangeField]);

  // Handle export options
  const handleExportOptionsChange = useCallback((exportData) => {
    Object.entries(exportData).forEach(([field, value]) => {
      onChangeField(field, value);
    });
  }, [onChangeField]);

  // Validate content references
  const validateContentReferences = useCallback(async () => {
    try {
      // This would make an API call to validate all UID references
      const response = await fetch(`${pathname}/++api++/@knowledge-containers/${data.UID || 'current'}/validate`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const validationResult = await response.json();
        setValidationState({
          loading: false,
          errors: validationResult.invalid_refs || [],
          valid: validationResult.valid
        });
        
        if (validationResult.valid) {
          toast.success(intl.formatMessage(messages.contentValidated));
        } else {
          toast.warning(intl.formatMessage(messages.validationErrors));
        }
      }
    } catch (error) {
      console.error('Validation error:', error);
      setValidationState({
        loading: false,
        errors: [],
        valid: true
      });
    }
  }, [pathname, data.UID, intl]);

  // Create custom schema for the form
  const customSchema = {
    ...props.schema,
    properties: {
      ...props.schema.properties,
      // Hide complex fields managed by custom components
      included_learning_goals: { ...props.schema.properties.included_learning_goals, widget: 'hidden' },
      included_knowledge_items: { ...props.schema.properties.included_knowledge_items, widget: 'hidden' },
      included_research_notes: { ...props.schema.properties.included_research_notes, widget: 'hidden' },
      included_project_logs: { ...props.schema.properties.included_project_logs, widget: 'hidden' },
      included_bookmarks: { ...props.schema.properties.included_bookmarks, widget: 'hidden' },
      sharing_permissions: { ...props.schema.properties.sharing_permissions, widget: 'hidden' },
      export_formats: { ...props.schema.properties.export_formats, widget: 'hidden' },
      view_analytics: { ...props.schema.properties.view_analytics, widget: 'hidden' },
    },
  };

  // Define tab panes with academic organization
  const panes = [
    {
      menuItem: intl.formatMessage(messages.basicInfo),
      render: () => (
        <Tab.Pane>
          <Container>
            {/* Academic Standards Banner */}
            <Message info icon>
              <Icon name='university' />
              <Message.Content>
                <Message.Header>{intl.formatMessage(messages.academicStandards)}</Message.Header>
                {intl.formatMessage(messages.knowledgeSovereignty)}
              </Message.Content>
            </Message>

            {/* Basic form fields */}
            <Form {...props} schema={customSchema} />

            {/* Collection Overview Card */}
            <Segment>
              <Header as="h3" dividing>
                <Icon name="archive" />
                Collection Overview
              </Header>
              <Grid columns={4} divided>
                <Grid.Column>
                  <Card>
                    <Card.Content>
                      <Card.Header>{academicMetadata.totalItems}</Card.Header>
                      <Card.Meta>Total Items</Card.Meta>
                    </Card.Content>
                  </Card>
                </Grid.Column>
                <Grid.Column>
                  <Card>
                    <Card.Content>
                      <Card.Header>{academicMetadata.collectionType}</Card.Header>
                      <Card.Meta>Collection Type</Card.Meta>
                    </Card.Content>
                  </Card>
                </Grid.Column>
                <Grid.Column>
                  <Card>
                    <Card.Content>
                      <Card.Header>{academicMetadata.organizationStructure}</Card.Header>
                      <Card.Meta>Organization</Card.Meta>
                    </Card.Content>
                  </Card>
                </Grid.Column>
                <Grid.Column>
                  <Card>
                    <Card.Content>
                      <Card.Header>{academicMetadata.publicationStatus}</Card.Header>
                      <Card.Meta>Status</Card.Meta>
                    </Card.Content>
                  </Card>
                </Grid.Column>
              </Grid>
            </Segment>
          </Container>
        </Tab.Pane>
      ),
    },
    {
      menuItem: intl.formatMessage(messages.contentCollection),
      render: () => (
        <Tab.Pane>
          <ContentCollectionManager
            data={data}
            onChange={handleContentCollectionChange}
            validationState={validationState}
            onValidate={validateContentReferences}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: intl.formatMessage(messages.organization),
      render: () => (
        <Tab.Pane>
          <OrganizationStructureEditor
            data={data}
            onChange={handleOrganizationChange}
            academicMode={true}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: intl.formatMessage(messages.sharing),
      render: () => (
        <Tab.Pane>
          <SharingPermissionsManager
            data={data}
            onChange={handleSharingChange}
            academicStandards={true}
            knowledgeSovereignty={true}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: intl.formatMessage(messages.export),
      render: () => (
        <Tab.Pane>
          <ExportOptionsManager
            data={data}
            onChange={handleExportOptionsChange}
            academicFormats={true}
            citationSupport={true}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: intl.formatMessage(messages.analytics),
      render: () => (
        <Tab.Pane>
          <ContainerAnalytics
            data={data}
            containerUID={data.UID}
            academicMetrics={true}
          />
        </Tab.Pane>
      ),
    },
  ];

  return (
    <Container fluid>
      <Segment>
        <Header as="h1" dividing>
          <Icon name="archive" />
          <Header.Content>
            Knowledge Container
            <Header.Subheader>
              Sophisticated Collection Management for Academic Excellence
            </Header.Subheader>
          </Header.Content>
        </Header>

        {/* Validation Status */}
        {validationState.loading && (
          <Message icon>
            <Icon name='circle notched' loading />
            <Message.Content>
              <Message.Header>{intl.formatMessage(messages.validatingContent)}</Message.Header>
            </Message.Content>
          </Message>
        )}

        {!validationState.loading && !validationState.valid && (
          <Message warning>
            <Message.Header>{intl.formatMessage(messages.validationErrors)}</Message.Header>
            <Message.List>
              {validationState.errors.map((error, index) => (
                <Message.Item key={index}>
                  {error.content_type}: {error.uid}
                </Message.Item>
              ))}
            </Message.List>
          </Message>
        )}

        <Tab 
          panes={panes} 
          activeIndex={activeTab}
          onTabChange={(e, { activeIndex }) => setActiveTab(activeIndex)}
        />
      </Segment>

      {/* Preview Modal */}
      <Modal
        open={showPreview}
        onClose={() => setShowPreview(false)}
        size="fullscreen"
      >
        <Modal.Header>
          <Icon name="eye" />
          Collection Preview
        </Modal.Header>
        <Modal.Content>
          {/* Preview would be rendered here */}
          <p>Collection preview functionality</p>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setShowPreview(false)}>
            <Icon name="cancel" /> Close
          </Button>
        </Modal.Actions>
      </Modal>
    </Container>
  );
};

export default injectIntl(KnowledgeContainerEdit); 