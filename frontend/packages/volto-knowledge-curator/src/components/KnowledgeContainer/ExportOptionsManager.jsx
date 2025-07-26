import React from 'react';
import { Segment, Header, Icon, Message } from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';

const messages = defineMessages({
  title: {
    id: 'export-options.title',
    defaultMessage: 'Export Options Manager',
  },
  placeholder: {
    id: 'export-options.placeholder',
    defaultMessage: 'Advanced export configuration will be available in future updates.',
  },
  academic: {
    id: 'export-options.academic',
    defaultMessage: 'Academic formats include LaTeX, APA citations, and bibliography management.',
  },
});

const ExportOptionsManager = ({ data, onChange, academicFormats, citationSupport, intl }) => {
  return (
    <Segment>
      <Header as="h3" dividing>
        <Icon name="download" />
        {intl.formatMessage(messages.title)}
      </Header>
      
      <Message info>
        <Icon name="info circle" />
        <Message.Content>
          {intl.formatMessage(messages.placeholder)}
        </Message.Content>
      </Message>

      {academicFormats && (
        <Message>
          <Icon name="university" />
          <Message.Content>
            <Message.Header>Academic Export Formats</Message.Header>
            {intl.formatMessage(messages.academic)}
          </Message.Content>
        </Message>
      )}

      {citationSupport && (
        <Message positive>
          <Icon name="quote right" />
          Citation Support: APA, MLA, Chicago, IEEE, Harvard formats available
        </Message>
      )}
    </Segment>
  );
};

export default injectIntl(ExportOptionsManager); 