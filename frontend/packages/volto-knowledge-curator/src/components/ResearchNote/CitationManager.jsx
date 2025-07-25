import React, { useCallback, useState } from 'react';
import { 
  Form, 
  Segment, 
  Button, 
  Icon, 
  Header, 
  Grid, 
  Label,
  Tab,
  Message,
  List
} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const CitationManager = ({ 
  value = {}, 
  onChange,
  title = 'Citation Information',
  description = 'Manage bibliographic data and author information',
}) => {
  const [activeAuthorIndex, setActiveAuthorIndex] = useState(-1);

  const handleFieldChange = useCallback((field, fieldValue) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  }, [value, onChange]);

  const handleAddAuthor = useCallback(() => {
    const authors = value.authors || [];
    const newAuthor = {
      name: '',
      email: '',
      orcid: '',
      affiliation: '',
    };
    handleFieldChange('authors', [...authors, newAuthor]);
    setActiveAuthorIndex(authors.length);
  }, [value.authors, handleFieldChange]);

  const handleUpdateAuthor = useCallback((index, authorData) => {
    const authors = [...(value.authors || [])];
    authors[index] = authorData;
    handleFieldChange('authors', authors);
  }, [value.authors, handleFieldChange]);

  const handleRemoveAuthor = useCallback((index) => {
    const authors = value.authors || [];
    handleFieldChange('authors', authors.filter((_, i) => i !== index));
    if (activeAuthorIndex === index) {
      setActiveAuthorIndex(-1);
    }
  }, [value.authors, handleFieldChange, activeAuthorIndex]);

  const generateCitation = useCallback(() => {
    const { 
      authors = [], 
      publication_date, 
      title, 
      journal_name,
      volume_issue,
      page_numbers,
      doi,
      publisher
    } = value;

    if (authors.length === 0 || !title) {
      return 'Incomplete citation information';
    }

    // Simple APA-style citation
    let citation = '';
    
    // Authors
    if (authors.length === 1) {
      citation += `${authors[0].name}`;
    } else if (authors.length === 2) {
      citation += `${authors[0].name} & ${authors[1].name}`;
    } else if (authors.length > 2) {
      citation += `${authors[0].name} et al.`;
    }

    // Year
    if (publication_date) {
      const year = new Date(publication_date).getFullYear();
      citation += ` (${year}).`;
    } else {
      citation += ' (n.d.).';
    }

    // Title
    citation += ` ${title}.`;

    // Journal
    if (journal_name) {
      citation += ` ${journal_name}`;
      if (volume_issue) {
        citation += `, ${volume_issue}`;
      }
      if (page_numbers) {
        citation += `, ${page_numbers}`;
      }
      citation += '.';
    } else if (publisher) {
      citation += ` ${publisher}.`;
    }

    // DOI
    if (doi) {
      citation += ` https://doi.org/${doi}`;
    }

    return citation;
  }, [value]);

  const panes = [
    {
      menuItem: 'Authors',
      render: () => (
        <Tab.Pane>
          <Grid>
            <Grid.Row>
              <Grid.Column width={6}>
                <List divided selection>
                  {(value.authors || []).map((author, index) => (
                    <List.Item 
                      key={index}
                      active={activeAuthorIndex === index}
                      onClick={() => setActiveAuthorIndex(index)}
                    >
                      <List.Content floated="right">
                        <Icon 
                          name="trash" 
                          color="red" 
                          style={{ cursor: 'pointer' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveAuthor(index);
                          }}
                        />
                      </List.Content>
                      <List.Icon name="user" size="large" verticalAlign="middle" />
                      <List.Content>
                        <List.Header>{author.name || `Author ${index + 1}`}</List.Header>
                        <List.Description>{author.affiliation || 'No affiliation'}</List.Description>
                      </List.Content>
                    </List.Item>
                  ))}
                  {(value.authors || []).length === 0 && (
                    <List.Item>
                      <List.Content>
                        <List.Description>No authors added</List.Description>
                      </List.Content>
                    </List.Item>
                  )}
                </List>
                <Button primary size="small" onClick={handleAddAuthor} style={{ marginTop: '1em' }}>
                  <Icon name="plus" />
                  Add Author
                </Button>
              </Grid.Column>
              
              <Grid.Column width={10}>
                {activeAuthorIndex >= 0 && value.authors && value.authors[activeAuthorIndex] && (
                  <Segment>
                    <Header as="h4">Edit Author</Header>
                    <Form>
                      <Form.Field required>
                        <label>Name</label>
                        <Form.Input
                          placeholder="Full name"
                          value={value.authors[activeAuthorIndex].name || ''}
                          onChange={(e, { value }) => 
                            handleUpdateAuthor(activeAuthorIndex, {
                              ...value.authors[activeAuthorIndex],
                              name: value
                            })
                          }
                        />
                      </Form.Field>
                      <Form.Field>
                        <label>Email</label>
                        <Form.Input
                          placeholder="email@example.com"
                          type="email"
                          value={value.authors[activeAuthorIndex].email || ''}
                          onChange={(e, { value }) => 
                            handleUpdateAuthor(activeAuthorIndex, {
                              ...value.authors[activeAuthorIndex],
                              email: value
                            })
                          }
                        />
                      </Form.Field>
                      <Form.Field>
                        <label>ORCID</label>
                        <Form.Input
                          placeholder="0000-0000-0000-0000"
                          value={value.authors[activeAuthorIndex].orcid || ''}
                          onChange={(e, { value }) => 
                            handleUpdateAuthor(activeAuthorIndex, {
                              ...value.authors[activeAuthorIndex],
                              orcid: value
                            })
                          }
                        />
                      </Form.Field>
                      <Form.Field>
                        <label>Affiliation</label>
                        <Form.Input
                          placeholder="Institution or organization"
                          value={value.authors[activeAuthorIndex].affiliation || ''}
                          onChange={(e, { value }) => 
                            handleUpdateAuthor(activeAuthorIndex, {
                              ...value.authors[activeAuthorIndex],
                              affiliation: value
                            })
                          }
                        />
                      </Form.Field>
                    </Form>
                  </Segment>
                )}
                {activeAuthorIndex === -1 && (
                  <Message info>
                    <Message.Header>Select an author</Message.Header>
                    <p>Click on an author from the list to edit their details</p>
                  </Message>
                )}
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Publication Details',
      render: () => (
        <Tab.Pane>
          <Form>
            <Form.Group widths="equal">
              <Form.Field>
                <label>Publication Date</label>
                <input
                  type="date"
                  value={value.publication_date || ''}
                  onChange={(e) => handleFieldChange('publication_date', e.target.value)}
                />
              </Form.Field>
              <Form.Field>
                <label>DOI</label>
                <Form.Input
                  placeholder="10.1234/example.doi"
                  value={value.doi || ''}
                  onChange={(e, { value }) => handleFieldChange('doi', value)}
                />
              </Form.Field>
            </Form.Group>

            <Form.Field>
              <label>Journal Name</label>
              <Form.Input
                placeholder="Nature, Science, etc."
                value={value.journal_name || ''}
                onChange={(e, { value }) => handleFieldChange('journal_name', value)}
              />
            </Form.Field>

            <Form.Group widths="equal">
              <Form.Field>
                <label>Volume/Issue</label>
                <Form.Input
                  placeholder="Vol. 123, No. 4"
                  value={value.volume_issue || ''}
                  onChange={(e, { value }) => handleFieldChange('volume_issue', value)}
                />
              </Form.Field>
              <Form.Field>
                <label>Page Numbers</label>
                <Form.Input
                  placeholder="pp. 123-145"
                  value={value.page_numbers || ''}
                  onChange={(e, { value }) => handleFieldChange('page_numbers', value)}
                />
              </Form.Field>
            </Form.Group>

            <Form.Group widths="equal">
              <Form.Field>
                <label>Publisher</label>
                <Form.Input
                  placeholder="Publisher name"
                  value={value.publisher || ''}
                  onChange={(e, { value }) => handleFieldChange('publisher', value)}
                />
              </Form.Field>
              <Form.Field>
                <label>ISBN</label>
                <Form.Input
                  placeholder="978-3-16-148410-0"
                  value={value.isbn || ''}
                  onChange={(e, { value }) => handleFieldChange('isbn', value)}
                />
              </Form.Field>
            </Form.Group>

            <Form.Field>
              <label>Source URL</label>
              <Form.Input
                placeholder="https://example.com/article"
                type="url"
                value={value.source_url || ''}
                onChange={(e, { value }) => handleFieldChange('source_url', value)}
              />
            </Form.Field>
          </Form>
        </Tab.Pane>
      ),
    },
    {
      menuItem: 'Generated Citation',
      render: () => (
        <Tab.Pane>
          <Message info>
            <Message.Header>APA Style Citation</Message.Header>
            <p style={{ fontFamily: 'monospace', lineHeight: '1.6' }}>
              {generateCitation()}
            </p>
          </Message>
          <Button 
            primary 
            onClick={() => {
              navigator.clipboard.writeText(generateCitation());
              alert('Citation copied to clipboard!');
            }}
          >
            <Icon name="copy" />
            Copy Citation
          </Button>
        </Tab.Pane>
      ),
    },
  ];

  return (
    <Segment>
      <Header as="h3">
        <Icon name="quote left" />
        <Header.Content>
          {title}
          <Header.Subheader>{description}</Header.Subheader>
        </Header.Content>
      </Header>

      <Tab panes={panes} />
    </Segment>
  );
};

CitationManager.propTypes = {
  value: PropTypes.shape({
    authors: PropTypes.arrayOf(PropTypes.shape({
      name: PropTypes.string,
      email: PropTypes.string,
      orcid: PropTypes.string,
      affiliation: PropTypes.string,
    })),
    publication_date: PropTypes.string,
    source_url: PropTypes.string,
    doi: PropTypes.string,
    isbn: PropTypes.string,
    journal_name: PropTypes.string,
    volume_issue: PropTypes.string,
    page_numbers: PropTypes.string,
    publisher: PropTypes.string,
    title: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
};

export default CitationManager;