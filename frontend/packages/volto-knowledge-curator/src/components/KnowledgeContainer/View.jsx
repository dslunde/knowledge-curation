import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Container, 
  Segment, 
  Header, 
  Grid, 
  Card, 
  Icon, 
  Button, 
  Label, 
  Table,
  Message,
  Modal,
  Dropdown,
  Progress,
  Statistic,
  Divider,
  List
} from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';

const messages = defineMessages({
  knowledgeContainer: {
    id: 'knowledge-container.title',
    defaultMessage: 'Knowledge Container',
  },
  academicCollection: {
    id: 'knowledge-container.academic-collection',
    defaultMessage: 'Academic Collection',
  },
  exportCollection: {
    id: 'knowledge-container.export-collection',
    defaultMessage: 'Export Collection',
  },
  citationFormats: {
    id: 'knowledge-container.citation-formats',
    defaultMessage: 'Citation Formats Available',
  },
  knowledgeSovereignty: {
    id: 'knowledge-container.knowledge-sovereignty-note',
    defaultMessage: 'Your intellectual assets remain under your complete control',
  },
  collectionMetrics: {
    id: 'knowledge-container.collection-metrics',
    defaultMessage: 'Collection Metrics',
  },
  academicStandards: {
    id: 'knowledge-container.academic-standards',
    defaultMessage: 'Academic Standards Compliant',
  },
  totalKnowledge: {
    id: 'knowledge-container.total-knowledge-items',
    defaultMessage: 'Knowledge Items',
  },
  researchDepth: {
    id: 'knowledge-container.research-depth',
    defaultMessage: 'Research Depth',
  },
  exportProgress: {
    id: 'knowledge-container.export-progress',
    defaultMessage: 'Preparing export...',
  },
  downloadReady: {
    id: 'knowledge-container.download-ready',
    defaultMessage: 'Export ready for download',
  },
});

const CONTENT_TYPE_CONFIG = {
  knowledge_items: { 
    label: 'Knowledge Items', 
    icon: 'lightbulb', 
    color: 'blue',
    academicWeight: 1.0,
    description: 'Foundational knowledge units'
  },
  learning_goals: { 
    label: 'Learning Goals', 
    icon: 'target', 
    color: 'green',
    academicWeight: 0.8,
    description: 'Learning objectives and pathways'
  },
  research_notes: { 
    label: 'Research Notes', 
    icon: 'file alternate', 
    color: 'orange',
    academicWeight: 1.2,
    description: 'Scholarly annotations and insights'
  },
  project_logs: { 
    label: 'Project Logs', 
    icon: 'tasks', 
    color: 'purple',
    academicWeight: 0.6,
    description: 'Implementation records'
  },
  bookmarks: { 
    label: 'External Resources', 
    icon: 'bookmark', 
    color: 'teal',
    academicWeight: 0.4,
    description: 'Curated external references'
  },
};

const EXPORT_FORMATS = [
  { key: 'pdf', text: 'PDF (Academic)', value: 'pdf', icon: 'file pdf' },
  { key: 'latex', text: 'LaTeX', value: 'latex', icon: 'file code' },
  { key: 'html', text: 'HTML (Web)', value: 'html', icon: 'file code' },
  { key: 'markdown', text: 'Markdown', value: 'markdown', icon: 'file text' },
  { key: 'docx', text: 'Word Document', value: 'docx', icon: 'file word' },
  { key: 'epub', text: 'EPUB (E-book)', value: 'epub', icon: 'book' },
];

const CITATION_FORMATS = [
  { key: 'apa', text: 'APA 7th Edition', value: 'apa' },
  { key: 'mla', text: 'MLA 9th Edition', value: 'mla' },
  { key: 'chicago', text: 'Chicago 17th Edition', value: 'chicago' },
  { key: 'ieee', text: 'IEEE Standard', value: 'ieee' },
  { key: 'harvard', text: 'Harvard Style', value: 'harvard' },
];

const KnowledgeContainerView = ({ content, intl }) => {
  // Component state
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [selectedExportFormat, setSelectedExportFormat] = useState('pdf');
  const [selectedCitationFormat, setSelectedCitationFormat] = useState('apa');
  const [exportProgress, setExportProgress] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [collectionDetails, setCollectionDetails] = useState(null);

  // Calculate academic metrics
  const academicMetrics = useMemo(() => {
    const content_breakdown = {};
    let totalItems = 0;
    let academicWeight = 0;

    Object.keys(CONTENT_TYPE_CONFIG).forEach(type => {
      const fieldName = `included_${type}`;
      const count = content[fieldName]?.length || 0;
      content_breakdown[type] = count;
      totalItems += count;
      academicWeight += count * CONTENT_TYPE_CONFIG[type].academicWeight;
    });

    const researchDepth = content_breakdown.research_notes * 1.5 + 
                         content_breakdown.knowledge_items;
    
    const completeness = totalItems > 0 ? 
      Math.min(100, (academicWeight / totalItems) * 100) : 0;

    return {
      totalItems,
      content_breakdown,
      academicWeight: academicWeight.toFixed(1),
      researchDepth: researchDepth.toFixed(1),
      completeness: Math.round(completeness),
    };
  }, [content]);

  // Fetch detailed collection information
  useEffect(() => {
    const fetchCollectionDetails = async () => {
      if (content?.UID) {
        try {
          const response = await fetch(`/++api++/@knowledge-containers/${content.UID}`, {
            headers: {
              'Accept': 'application/json',
            },
          });
          
          if (response.ok) {
            const details = await response.json();
            setCollectionDetails(details);
          }
        } catch (error) {
          console.error('Error fetching collection details:', error);
        }
      }
    };

    fetchCollectionDetails();
  }, [content?.UID]);

  // Handle export functionality
  const handleExport = useCallback(async () => {
    setExporting(true);
    setExportProgress(0);

    try {
      // Simulate export progress
      const progressInterval = setInterval(() => {
        setExportProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch(`/++api++/@knowledge-containers/${content.UID}/export`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          format: selectedExportFormat,
          citation_format: selectedCitationFormat,
          include_metadata: true,
          academic_style: true,
        }),
      });

      clearInterval(progressInterval);
      setExportProgress(100);

      if (response.ok) {
        // Handle download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${content.title}.${selectedExportFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success(intl.formatMessage(messages.downloadReady));
      } else {
        toast.error('Export failed');
      }
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Export failed');
    }

    setExporting(false);
    setTimeout(() => setExportModalOpen(false), 1000);
  }, [content.UID, content.title, selectedExportFormat, selectedCitationFormat, intl]);

  // Format creation date
  const creationDate = content.created ? 
    new Date(content.created).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }) : 'Unknown';

  return (
    <Container>
      {/* Header Section */}
      <Segment>
        <Header as="h1" dividing>
          <Icon name="archive" color="blue" />
          <Header.Content>
            {content.title}
            <Header.Subheader>
              <Icon name="university" />
              {intl.formatMessage(messages.academicCollection)} • Created {creationDate}
            </Header.Subheader>
          </Header.Content>
        </Header>

        {/* Academic Standards Badge */}
        <Message info icon>
          <Icon name="shield alternate" />
          <Message.Content>
            <Message.Header>{intl.formatMessage(messages.academicStandards)}</Message.Header>
            {intl.formatMessage(messages.knowledgeSovereignty)}
          </Message.Content>
        </Message>

        {/* Description */}
        {content.description && (
          <Segment basic>
            <p style={{ fontSize: '1.1em', lineHeight: '1.6' }}>
              {content.description}
            </p>
          </Segment>
        )}
      </Segment>

      {/* Collection Metrics */}
      <Segment>
        <Header as="h2" dividing>
          <Icon name="chart bar" />
          {intl.formatMessage(messages.collectionMetrics)}
        </Header>

        <Grid columns={4} stackable>
          <Grid.Column>
            <Statistic color="blue">
              <Statistic.Value>{academicMetrics.totalItems}</Statistic.Value>
              <Statistic.Label>Total Items</Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic color="green">
              <Statistic.Value>{academicMetrics.academicWeight}</Statistic.Value>
              <Statistic.Label>Academic Weight</Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic color="orange">
              <Statistic.Value>{academicMetrics.researchDepth}</Statistic.Value>
              <Statistic.Label>Research Depth</Statistic.Label>
            </Statistic>
          </Grid.Column>
          <Grid.Column>
            <Statistic color="purple">
              <Statistic.Value>{academicMetrics.completeness}%</Statistic.Value>
              <Statistic.Label>Completeness</Statistic.Label>
            </Statistic>
          </Grid.Column>
        </Grid>

        {/* Progress Bar for Completeness */}
        <Segment basic>
          <Progress 
            percent={academicMetrics.completeness} 
            color="blue" 
            indicating
            label="Collection Completeness"
          />
        </Segment>
      </Segment>

      {/* Content Overview */}
      <Segment>
        <Header as="h2" dividing>
          <Icon name="list" />
          Collection Contents
        </Header>

        <Grid columns={3} stackable>
          {Object.entries(CONTENT_TYPE_CONFIG).map(([type, config]) => {
            const count = academicMetrics.content_breakdown[type] || 0;
            if (count === 0) return null;

            return (
              <Grid.Column key={type}>
                <Card color={config.color} fluid>
                  <Card.Content>
                    <Card.Header>
                      <Icon name={config.icon} color={config.color} />
                      {config.label}
                    </Card.Header>
                    <Card.Meta>{config.description}</Card.Meta>
                    <Card.Description>
                      <Statistic size="mini">
                        <Statistic.Value>{count}</Statistic.Value>
                        <Statistic.Label>
                          {count === 1 ? 'Item' : 'Items'}
                        </Statistic.Label>
                      </Statistic>
                    </Card.Description>
                  </Card.Content>
                  <Card.Content extra>
                    <Label color={config.color} size="tiny">
                      Academic Weight: {config.academicWeight}
                    </Label>
                  </Card.Content>
                </Card>
              </Grid.Column>
            );
          })}
        </Grid>
      </Segment>

      {/* Collection Metadata */}
      <Segment>
        <Header as="h3" dividing>
          <Icon name="tags" />
          Collection Metadata
        </Header>

        <Grid columns={2}>
          <Grid.Column>
            <List divided relaxed>
              <List.Item>
                <List.Icon name="folder" color="blue" />
                <List.Content>
                  <List.Header>Collection Type</List.Header>
                  <List.Description>{content.collection_type || 'Curated'}</List.Description>
                </List.Content>
              </List.Item>
              <List.Item>
                <List.Icon name="sitemap" color="green" />
                <List.Content>
                  <List.Header>Organization Structure</List.Header>
                  <List.Description>{content.organization_structure || 'Hierarchical'}</List.Description>
                </List.Content>
              </List.Item>
              <List.Item>
                <List.Icon name="eye" color="orange" />
                <List.Content>
                  <List.Header>Target Audience</List.Header>
                  <List.Description>{content.target_audience || 'Self'}</List.Description>
                </List.Content>
              </List.Item>
            </List>
          </Grid.Column>
          <Grid.Column>
            <List divided relaxed>
              <List.Item>
                <List.Icon name="flag" color="purple" />
                <List.Content>
                  <List.Header>Publication Status</List.Header>
                  <List.Description>
                    <Label color={content.publication_status === 'published' ? 'green' : 'orange'}>
                      {content.publication_status || 'Draft'}
                    </Label>
                  </List.Description>
                </List.Content>
              </List.Item>
              <List.Item>
                <List.Icon name="code branch" color="teal" />
                <List.Content>
                  <List.Header>Version</List.Header>
                  <List.Description>{content.container_version || '1.0'}</List.Description>
                </List.Content>
              </List.Item>
              {content.tags && content.tags.length > 0 && (
                <List.Item>
                  <List.Icon name="tags" color="grey" />
                  <List.Content>
                    <List.Header>Tags</List.Header>
                    <List.Description>
                      {content.tags.map(tag => (
                        <Label key={tag} size="tiny" style={{ marginRight: '0.5em' }}>
                          {tag}
                        </Label>
                      ))}
                    </List.Description>
                  </List.Content>
                </List.Item>
              )}
            </List>
          </Grid.Column>
        </Grid>
      </Segment>

      {/* Export Section */}
      <Segment>
        <Header as="h3" dividing>
          <Icon name="download" />
          Export & Sharing
        </Header>

        <Grid columns={2}>
          <Grid.Column>
            <Button 
              primary 
              size="large"
              icon 
              labelPosition="left"
              onClick={() => setExportModalOpen(true)}
            >
              <Icon name="download" />
              {intl.formatMessage(messages.exportCollection)}
            </Button>
          </Grid.Column>
          <Grid.Column>
            <Message info size="tiny">
              <Icon name="info circle" />
              {intl.formatMessage(messages.citationFormats)}
            </Message>
          </Grid.Column>
        </Grid>
      </Segment>

      {/* Export Modal */}
      <Modal
        open={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        size="small"
      >
        <Modal.Header>
          <Icon name="download" />
          Export Academic Collection
        </Modal.Header>
        <Modal.Content>
          <Header as="h4">Export Format</Header>
          <Dropdown
            selection
            fluid
            value={selectedExportFormat}
            onChange={(e, { value }) => setSelectedExportFormat(value)}
            options={EXPORT_FORMATS}
          />

          <Divider />

          <Header as="h4">Citation Format</Header>
          <Dropdown
            selection
            fluid
            value={selectedCitationFormat}
            onChange={(e, { value }) => setSelectedCitationFormat(value)}
            options={CITATION_FORMATS}
          />

          {exporting && (
            <Segment basic>
              <Progress 
                percent={exportProgress} 
                indicating 
                label={intl.formatMessage(messages.exportProgress)}
              />
            </Segment>
          )}

          <Message info icon>
            <Icon name="shield alternate" />
            <Message.Content>
              <Message.Header>Knowledge Sovereignty</Message.Header>
              Your exported collection maintains complete data portability and academic standards compliance.
            </Message.Content>
          </Message>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setExportModalOpen(false)} disabled={exporting}>
            <Icon name="cancel" /> Cancel
          </Button>
          <Button primary onClick={handleExport} loading={exporting}>
            <Icon name="download" /> Export Collection
          </Button>
        </Modal.Actions>
      </Modal>
    </Container>
  );
};

export default injectIntl(KnowledgeContainerView); 