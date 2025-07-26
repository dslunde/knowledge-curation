import React from 'react';
import { Segment, Header, Icon, Message } from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';

const messages = defineMessages({
  title: {
    id: 'sharing-permissions.title',
    defaultMessage: 'Sharing & Permissions Manager',
  },
  placeholder: {
    id: 'sharing-permissions.placeholder',
    defaultMessage: 'Advanced sharing and permission management will be available in future updates.',
  },
  sovereignty: {
    id: 'sharing-permissions.sovereignty',
    defaultMessage: 'Knowledge sovereignty ensures your intellectual assets remain under your complete control.',
  },
});

const SharingPermissionsManager = ({ data, onChange, academicStandards, knowledgeSovereignty, intl }) => {
  return (
    <Segment>
      <Header as="h3" dividing>
        <Icon name="share alternate" />
        {intl.formatMessage(messages.title)}
      </Header>
      
      <Message info>
        <Icon name="info circle" />
        <Message.Content>
          {intl.formatMessage(messages.placeholder)}
        </Message.Content>
      </Message>

      {knowledgeSovereignty && (
        <Message positive>
          <Icon name="shield alternate" />
          <Message.Content>
            <Message.Header>Knowledge Sovereignty</Message.Header>
            {intl.formatMessage(messages.sovereignty)}
          </Message.Content>
        </Message>
      )}

      {academicStandards && (
        <Message>
          <Icon name="university" />
          Academic Standards: Privacy-first sharing with proper attribution
        </Message>
      )}
    </Segment>
  );
};

export default injectIntl(SharingPermissionsManager); 