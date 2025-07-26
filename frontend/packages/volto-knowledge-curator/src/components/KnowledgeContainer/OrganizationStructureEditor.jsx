import React from 'react';
import { Segment, Header, Icon, Message } from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';

const messages = defineMessages({
  title: {
    id: 'organization-structure.title',
    defaultMessage: 'Organization Structure Editor',
  },
  placeholder: {
    id: 'organization-structure.placeholder',
    defaultMessage: 'Advanced organization structure management will be available in future updates.',
  },
});

const OrganizationStructureEditor = ({ data, onChange, academicMode, intl }) => {
  return (
    <Segment>
      <Header as="h3" dividing>
        <Icon name="sitemap" />
        {intl.formatMessage(messages.title)}
      </Header>
      
      <Message info>
        <Icon name="info circle" />
        <Message.Content>
          {intl.formatMessage(messages.placeholder)}
        </Message.Content>
      </Message>

      {academicMode && (
        <Message>
          <Icon name="university" />
          Academic Mode: Structure optimization for scholarly presentations
        </Message>
      )}
    </Segment>
  );
};

export default injectIntl(OrganizationStructureEditor); 