import React from 'react';
import { 
  Modal, 
  Button, 
  Header, 
  Icon, 
  Message,
  Segment,
  Label
} from 'semantic-ui-react';
import { defineMessages, injectIntl } from 'react-intl';

const messages = defineMessages({
  deleteConfirmTitle: {
    id: 'delete-confirmation.title',
    defaultMessage: 'Confirm Deletion',
  },
  deleteConfirmMessage: {
    id: 'delete-confirmation.message',
    defaultMessage: 'Are you sure you want to delete this item?',
  },
  deleteConfirmWarning: {
    id: 'delete-confirmation.warning',
    defaultMessage: 'This action cannot be undone.',
  },
  deleteButton: {
    id: 'delete-confirmation.delete',
    defaultMessage: 'Delete',
  },
  cancelButton: {
    id: 'delete-confirmation.cancel',
    defaultMessage: 'Cancel',
  },
  deleteContentWarning: {
    id: 'delete-confirmation.content-warning',
    defaultMessage: 'This will permanently remove the content and all associated data including vectors, relationships, and analytics.',
  },
  deleteRelationshipWarning: {
    id: 'delete-confirmation.relationship-warning',
    defaultMessage: 'This will remove the relationship between the selected items.',
  },
  deleteEntryWarning: {
    id: 'delete-confirmation.entry-warning',
    defaultMessage: 'This will permanently remove this entry from the log.',
  },
});

const DeleteConfirmationModal = ({
  intl,
  open,
  onClose,
  onConfirm,
  title,
  itemTitle,
  itemType = 'item',
  severity = 'medium', // 'low', 'medium', 'high'
  customMessage,
  customWarning,
  loading = false,
}) => {
  const getSeverityConfig = (severity) => {
    switch (severity) {
      case 'high':
        return {
          color: 'red',
          icon: 'warning circle',
          iconColor: 'red',
        };
      case 'medium':
        return {
          color: 'orange',
          icon: 'trash',
          iconColor: 'orange',
        };
      case 'low':
        return {
          color: 'grey',
          icon: 'trash outline',
          iconColor: 'grey',
        };
      default:
        return {
          color: 'orange',
          icon: 'trash',
          iconColor: 'orange',
        };
    }
  };

  const config = getSeverityConfig(severity);

  const getDefaultMessage = () => {
    if (customMessage) return customMessage;
    
    if (itemTitle) {
      return `Are you sure you want to delete "${itemTitle}"?`;
    }
    
    return intl.formatMessage(messages.deleteConfirmMessage);
  };

  const getWarningMessage = () => {
    if (customWarning) return customWarning;
    
    switch (itemType) {
      case 'content':
        return intl.formatMessage(messages.deleteContentWarning);
      case 'relationship':
        return intl.formatMessage(messages.deleteRelationshipWarning);
      case 'entry':
        return intl.formatMessage(messages.deleteEntryWarning);
      default:
        return intl.formatMessage(messages.deleteConfirmWarning);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="small"
      dimmer="blurring"
    >
      <Header icon={config.icon} content={title || intl.formatMessage(messages.deleteConfirmTitle)} />
      
      <Modal.Content>
        <Segment basic>
          <Message icon size="large">
            <Icon name={config.icon} color={config.iconColor} />
            <Message.Content>
              <Message.Header>{getDefaultMessage()}</Message.Header>
              <p>{getWarningMessage()}</p>
            </Message.Content>
          </Message>
          
          {itemTitle && (
            <Segment color={config.color}>
              <Label color={config.color} ribbon="right">
                {itemType.charAt(0).toUpperCase() + itemType.slice(1)}
              </Label>
              <p><strong>Item:</strong> {itemTitle}</p>
            </Segment>
          )}
        </Segment>
      </Modal.Content>

      <Modal.Actions>
        <Button 
          onClick={onClose}
          disabled={loading}
        >
          <Icon name="remove" />
          {intl.formatMessage(messages.cancelButton)}
        </Button>
        <Button 
          color={config.color}
          onClick={onConfirm}
          loading={loading}
          disabled={loading}
        >
          <Icon name="checkmark" />
          {intl.formatMessage(messages.deleteButton)}
        </Button>
      </Modal.Actions>
    </Modal>
  );
};

export default injectIntl(DeleteConfirmationModal); 