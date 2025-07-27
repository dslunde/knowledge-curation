import React from 'react';
import { Container, Header, Button } from 'semantic-ui-react';

const KnowledgeItemView = ({ content }) => {
  // Safety check
  if (!content) {
    return (
      <Container>
        <Header as="h1">Content not found</Header>
      </Container>
    );
  }
  
  const title = content.title || 'Untitled';

  const handleEdit = () => {
    if (content['@id']) {
      window.location.href = `${content['@id']}/edit`;
    }
  };

  const handleDelete = () => {
    console.log('Content object:', content);
    console.log('Content @id:', content['@id']);
    
    if (window.confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
      if (content['@id']) {
        // Construct the proper API URL
        let apiUrl = content['@id'];
        
        // If the URL doesn't contain ++api++, we need to add it
        if (!apiUrl.includes('++api++')) {
          // Get the base URL and add ++api++
          const url = new URL(window.location.href);
          const basePath = url.pathname;
          const segments = basePath.split('/').filter(Boolean);
          const itemSlug = segments[segments.length - 1];
          apiUrl = `${url.origin}/++api++/${itemSlug}`;
        }
        
        console.log('Attempting to delete with URL:', apiUrl);
        
        fetch(apiUrl, {
          method: 'DELETE',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        })
        .then(response => {
          console.log('Delete response:', response);
          if (response.ok) {
            // Navigate to home page instead of trying to calculate parent
            window.location.href = '/';
          } else {
            console.error('Delete failed with status:', response.status);
            alert(`Failed to delete content. Status: ${response.status}`);
          }
        })
        .catch(error => {
          console.error('Delete error:', error);
          alert('Failed to delete content. Please try again.');
        });
      }
    }
  };

  return (
    <Container>
      <Header as="h1">{title}</Header>
      
      {/* Summary Section */}
      {content.description && (
        <div style={{ margin: '20px 0', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          <Header as="h3">Summary</Header>
          <p>{content.description}</p>
        </div>
      )}

      {/* Content Section */}
      {content.text && content.text.data && (
        <div style={{ margin: '20px 0', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          <Header as="h3">Content</Header>
          <div dangerouslySetInnerHTML={{ __html: content.text.data }} />
        </div>
      )}

      {/* Tags Section */}
      {content.tags && content.tags.length > 0 && (
        <div style={{ margin: '20px 0', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
          <Header as="h4">Tags</Header>
          <div>
            {content.tags.map((tag, index) => (
              <span
                key={index}
                style={{
                  display: 'inline-block',
                  backgroundColor: '#00b5ad',
                  color: 'white',
                  padding: '4px 8px',
                  margin: '2px',
                  borderRadius: '3px',
                  fontSize: '12px'
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions Section */}
      <div style={{ margin: '20px 0', padding: '20px', border: '1px solid #ddd' }}>
        <Header as="h4">Actions</Header>
        <Button
          content="Edit"
          primary
          onClick={handleEdit}
          style={{ marginRight: '10px' }}
        />
        <Button
          content="Delete"
          color="red"
          onClick={handleDelete}
        />
      </div>
    </Container>
  );
};

export default KnowledgeItemView; 