import React from 'react';
import { Segment, Header, Icon, Message } from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';

const messages = defineMessages({
  title: {
    id: 'container-analytics.title',
    defaultMessage: 'Container Analytics & Insights',
  },
  placeholder: {
    id: 'container-analytics.placeholder',
    defaultMessage: 'Advanced analytics and learning insights will be available in future updates.',
  },
  academic: {
    id: 'container-analytics.academic',
    defaultMessage: 'Academic metrics focus on knowledge depth, research quality, and learning effectiveness.',
  },
});

const ContainerAnalytics = ({ data, containerUID, academicMetrics, intl }) => {
  return (
    <Segment>
      <Header as="h3" dividing>
        <Icon name="chart bar" />
        {intl.formatMessage(messages.title)}
      </Header>
      
      <Message info>
        <Icon name="info circle" />
        <Message.Content>
          {intl.formatMessage(messages.placeholder)}
        </Message.Content>
      </Message>

      {academicMetrics && (
        <Message>
          <Icon name="university" />
          <Message.Content>
            <Message.Header>Academic Analytics</Message.Header>
            {intl.formatMessage(messages.academic)}
          </Message.Content>
        </Message>
      )}

      {containerUID && (
        <Message positive>
          <Icon name="chart line" />
          Collection UID: <code>{containerUID}</code> - Ready for advanced analytics
        </Message>
      )}
    </Segment>
  );
};

export default injectIntl(ContainerAnalytics); 