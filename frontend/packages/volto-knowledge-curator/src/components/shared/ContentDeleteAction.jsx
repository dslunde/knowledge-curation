import React, { useState } from 'react';
import { 
  Button, 
  Icon,
  Dropdown,
  Confirm
} from 'semantic-ui-react';
import { defineMessages, injectIntl } from 'react-intl';
import { connect } from 'react-redux';
import { compose } from 'redux';
import { deleteContent } from '@plone/volto/actions';
import { toast } from 'react-toastify';
import { withRouter } from 'react-router-dom';
import DeleteConfirmationModal from './DeleteConfirmationModal';

const messages = defineMessages({
  delete: {
    id: 'content-delete.delete',
    defaultMessage: 'Delete',
  },
  deleteContent: {
    id: 'content-delete.delete-content',
    defaultMessage: 'Delete Content',
  },
  deleteSuccess: {
    id: 'content-delete.success',
    defaultMessage: 'Content deleted successfully',
  },
  deleteError: {
    id: 'content-delete.error',
    defaultMessage: 'Error deleting content',
  },
  confirmDeleteTitle: {
    id: 'content-delete.confirm-title',
    defaultMessage: 'Delete Content',
  },
});

const ContentDeleteAction = ({
  intl,
  content,
  deleteContent,
  deleteRequest,
  history,
  size = 'medium',
  buttonType = 'button', // 'button', 'dropdown-item', 'icon-only'
  color = 'red',
  redirectAfterDelete = true,
  onDeleteSuccess,
  onDeleteError,
  className = '',
}) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!content?.['@id']) {
      toast.error(intl.formatMessage(messages.deleteError));
      return;
    }

    setDeleting(true);
    
    try {
      await deleteContent(content['@id']);
      
      toast.success(intl.formatMessage(messages.deleteSuccess));
      
      if (onDeleteSuccess) {
        onDeleteSuccess(content);
      }
      
      if (redirectAfterDelete) {
        // Navigate to parent or home
        const pathParts = content['@id'].split('/');
        const parentPath = pathParts.slice(0, -1).join('/') || '/';
        history.push(parentPath);
      }
      
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(intl.formatMessage(messages.deleteError));
      
      if (onDeleteError) {
        onDeleteError(error);
      }
    } finally {
      setDeleting(false);
      setShowConfirm(false);
    }
  };

  const renderButton = () => {
    switch (buttonType) {
      case 'dropdown-item':
        return (
          <Dropdown.Item
            onClick={() => setShowConfirm(true)}
            icon="trash"
            text={intl.formatMessage(messages.delete)}
            className={className}
          />
        );
      
      case 'icon-only':
        return (
          <Button
            icon="trash"
            color={color}
            size={size}
            onClick={() => setShowConfirm(true)}
            loading={deleting}
            disabled={deleting}
            className={className}
            title={intl.formatMessage(messages.deleteContent)}
          />
        );
      
      default:
        return (
          <Button
            color={color}
            size={size}
            onClick={() => setShowConfirm(true)}
            loading={deleting}
            disabled={deleting}
            className={className}
          >
            <Icon name="trash" />
            {intl.formatMessage(messages.delete)}
          </Button>
        );
    }
  };

  return (
    <>
      {renderButton()}
      
      <DeleteConfirmationModal
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleDelete}
        title={intl.formatMessage(messages.confirmDeleteTitle)}
        itemTitle={content?.title}
        itemType="content"
        severity="high"
        loading={deleting}
      />
    </>
  );
};

export default compose(
  injectIntl,
  withRouter,
  connect(
    (state) => ({
      deleteRequest: state.content.delete,
    }),
    { deleteContent }
  )
)(ContentDeleteAction); 