import React, { useCallback } from 'react';
import { Container, Segment, Tab } from 'semantic-ui-react';
import { Form } from '@plone/volto/components';
import { injectIntl } from 'react-intl';
import StructuredInsightEditor from './StructuredInsightEditor';
import CitationManager from './CitationManager';
import ResearchLineageVisualizer from './ResearchLineageVisualizer';

const ResearchNoteEdit = (props) => {
  const { data, onChangeField, intl } = props;

  const handleInsightsChange = useCallback((insights) => {
    onChangeField('key_insights', insights);
  }, [onChangeField]);

  const handleCitationChange = useCallback((citationData) => {
    // Update multiple fields from citation data
    Object.entries(citationData).forEach(([field, value]) => {
      if (field !== 'title') { // Don't override the main title
        onChangeField(field, value);
      }
    });
  }, [onChangeField]);

  const handleLineageChange = useCallback((lineageData) => {
    Object.entries(lineageData).forEach(([field, value]) => {
      onChangeField(field, value);
    });
  }, [onChangeField]);

  // Create a custom schema that includes our structured editors
  const customSchema = {
    ...props.schema,
    properties: {
      ...props.schema.properties,
      // Hide the raw fields that are managed by custom components
      key_insights: { ...props.schema.properties.key_insights, widget: 'hidden' },
      authors: { ...props.schema.properties.authors, widget: 'hidden' },
      builds_upon: { ...props.schema.properties.builds_upon, widget: 'hidden' },
      contradicts: { ...props.schema.properties.contradicts, widget: 'hidden' },
      replication_studies: { ...props.schema.properties.replication_studies, widget: 'hidden' },
    },
  };

  const panes = [
    {
      menuItem: 'Basic Information',
      render: () => (
        <Tab.Pane>
          <Form {...props} schema={customSchema} />
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Key Insights',
      render: () => (
        <Tab.Pane>
          <StructuredInsightEditor
            value={data.key_insights || []}
            onChange={handleInsightsChange}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Citation Information',
      render: () => (
        <Tab.Pane>
          <CitationManager
            value={{
              authors: data.authors || [],
              publication_date: data.publication_date,
              source_url: data.source_url,
              doi: data.doi,
              isbn: data.isbn,
              journal_name: data.journal_name,
              volume_issue: data.volume_issue,
              page_numbers: data.page_numbers,
              publisher: data.publisher,
              title: data.title,
            }}
            onChange={handleCitationChange}
          />
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Research Lineage',
      render: () => (
        <Tab.Pane>
          <ResearchLineageVisualizer
            value={{
              builds_upon: data.builds_upon || [],
              contradicts: data.contradicts || [],
              replication_studies: data.replication_studies || [],
            }}
            onChange={handleLineageChange}
          />
        </Tab.Pane>
      ),
    },
  ];

  return (
    <Container>
      <Segment>
        <Tab panes={panes} />
      </Segment>
    </Container>
  );
};

export default injectIntl(ResearchNoteEdit); 