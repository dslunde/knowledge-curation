import React, { useState, useEffect, useCallback } from 'react';
import { 
  Segment, 
  Header, 
  Icon, 
  Message, 
  Form, 
  Button, 
  Table, 
  Label, 
  Modal, 
  Dropdown, 
  Card, 
  Statistic,
  Grid,
  Progress
} from 'semantic-ui-react';
import { injectIntl, defineMessages } from 'react-intl';
import { toast } from 'react-toastify';

const messages = defineMessages({
  title: {
    id: 'sharing-permissions.title',
    defaultMessage: 'Sharing & Permissions Manager',
  },
  sovereignty: {
    id: 'sharing-permissions.sovereignty',
    defaultMessage: 'Knowledge sovereignty ensures your intellectual assets remain under your complete control.',
  },
  createAgreement: {
    id: 'sharing-permissions.create-agreement',
    defaultMessage: 'Create Sharing Agreement',
  },
  sovereigntyLevel: {
    id: 'sharing-permissions.sovereignty-level',
    defaultMessage: 'Sovereignty Level',
  },
  shareScope: {
    id: 'sharing-permissions.share-scope',
    defaultMessage: 'Share Scope',
  },
  permissions: {
    id: 'sharing-permissions.permissions',
    defaultMessage: 'Permissions',
  },
  grantee: {
    id: 'sharing-permissions.grantee',
    defaultMessage: 'Share With User',
  },
  activeAgreements: {
    id: 'sharing-permissions.active-agreements',
    defaultMessage: 'Active Sharing Agreements',
  },
  academicCompliance: {
    id: 'sharing-permissions.academic-compliance',
    defaultMessage: 'Academic Compliance',
  },
});

const sovereigntyLevelOptions = [
  { key: 'full_control', value: 'full_control', text: 'Full Control', description: 'Complete user control' },
  { key: 'federated', value: 'federated', text: 'Federated', description: 'Trusted institutional sharing' },
  { key: 'academic_open', value: 'academic_open', text: 'Academic Open', description: 'Open academic community' },
  { key: 'public_domain', value: 'public_domain', text: 'Public Domain', description: 'Public with attribution' },
];

const shareScopeOptions = [
  { key: 'individual', value: 'individual', text: 'Individual', description: 'Specific person' },
  { key: 'research_group', value: 'research_group', text: 'Research Group', description: 'Research collaborators' },
  { key: 'institution', value: 'institution', text: 'Institution', description: 'Academic institution' },
  { key: 'academic_public', value: 'academic_public', text: 'Academic Public', description: 'Academic community' },
  { key: 'controlled_public', value: 'controlled_public', text: 'Controlled Public', description: 'Public with controls' },
];

const permissionOptions = [
  { key: 'view', value: 'view', text: 'View', description: 'Read-only access' },
  { key: 'comment', value: 'comment', text: 'Comment', description: 'Add annotations' },
  { key: 'cite', value: 'cite', text: 'Cite', description: 'Citation rights' },
  { key: 'reference', value: 'reference', text: 'Reference', description: 'Academic reference' },
  { key: 'collaborate', value: 'collaborate', text: 'Collaborate', description: 'Co-author access' },
  { key: 'curate', value: 'curate', text: 'Curate', description: 'Manage collection' },
  { key: 'export', value: 'export', text: 'Export', description: 'Export for personal use' },
];

const SharingPermissionsManager = ({ data, onChange, containerUID, academicMode, intl }) => {
  const [agreements, setAgreements] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sovereigntyReport, setSovereigntyReport] = useState(null);
  
  // Form state for creating new agreements
  const [newAgreement, setNewAgreement] = useState({
    grantee_id: '',
    sovereignty_level: 'academic_open',
    share_scope: 'individual',
    permissions: ['view', 'cite'],
    citation_required: true,
    academic_use_only: true,
    expiry_days: 365,
  });

  // Load existing agreements
  useEffect(() => {
    if (containerUID) {
      loadSharingAgreements();
      loadSovereigntyReport();
    }
  }, [containerUID]);

  const loadSharingAgreements = useCallback(async () => {
    try {
      setLoading(true);
      // API call to load sharing agreements
      const response = await fetch(`/@knowledge-containers/${containerUID}/sharing-agreements`);
      if (response.ok) {
        const data = await response.json();
        setAgreements(data.agreements || []);
      }
    } catch (error) {
      console.error('Error loading sharing agreements:', error);
      toast.error('Failed to load sharing agreements');
    } finally {
      setLoading(false);
    }
  }, [containerUID]);

  const loadSovereigntyReport = useCallback(async () => {
    try {
      const response = await fetch(`/@knowledge-containers/${containerUID}/sovereignty-report`);
      if (response.ok) {
        const report = await response.json();
        setSovereigntyReport(report);
      }
    } catch (error) {
      console.error('Error loading sovereignty report:', error);
    }
  }, [containerUID]);

  const handleCreateAgreement = async () => {
    try {
      setLoading(true);
      
      const agreementData = {
        ...newAgreement,
        container_uid: containerUID
      };

      const response = await fetch(`/@knowledge-containers/${containerUID}/sharing-agreements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agreementData),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('Sharing agreement created successfully');
        setShowCreateModal(false);
        setNewAgreement({
          grantee_id: '',
          sovereignty_level: 'academic_open',
          share_scope: 'individual',
          permissions: ['view', 'cite'],
          citation_required: true,
          academic_use_only: true,
          expiry_days: 365,
        });
        loadSharingAgreements();
        loadSovereigntyReport();
      } else {
        const error = await response.json();
        toast.error(`Failed to create agreement: ${error.message}`);
      }
    } catch (error) {
      console.error('Error creating agreement:', error);
      toast.error('Failed to create sharing agreement');
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeAgreement = async (agreementId) => {
    try {
      const response = await fetch(`/@knowledge-containers/${containerUID}/sharing-agreements/${agreementId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast.success('Sharing agreement revoked');
        loadSharingAgreements();
        loadSovereigntyReport();
      } else {
        toast.error('Failed to revoke agreement');
      }
    } catch (error) {
      console.error('Error revoking agreement:', error);
      toast.error('Failed to revoke agreement');
    }
  };

  const getSovereigntyLevelColor = (level) => {
    switch (level) {
      case 'full_control': return 'red';
      case 'federated': return 'orange';
      case 'academic_open': return 'blue';
      case 'public_domain': return 'green';
      default: return 'grey';
    }
  };

  return (
    <Segment loading={loading}>
      <Header as="h3" dividing>
        <Icon name="shield" />
        {intl.formatMessage(messages.title)}
      </Header>
      
      <Message info>
        <Message.Header>Knowledge Sovereignty Protection</Message.Header>
        <p>{intl.formatMessage(messages.sovereignty)}</p>
      </Message>

      {/* Sovereignty Report Summary */}
      {sovereigntyReport && (
        <Card.Group>
          <Card>
            <Card.Content>
              <Card.Header>Academic Compliance</Card.Header>
              <Statistic size="small">
                <Statistic.Value>
                  {sovereigntyReport.compliance_status?.academic_standards ? '✓' : '✗'}
                </Statistic.Value>
                <Statistic.Label>Standards Met</Statistic.Label>
              </Statistic>
            </Card.Content>
          </Card>
          
          <Card>
            <Card.Content>
              <Card.Header>Active Agreements</Card.Header>
              <Statistic size="small">
                <Statistic.Value>{agreements.length}</Statistic.Value>
                <Statistic.Label>Sharing Partners</Statistic.Label>
              </Statistic>
            </Card.Content>
          </Card>
          
          <Card>
            <Card.Content>
              <Card.Header>Sovereignty Score</Card.Header>
              <Progress 
                percent={85} 
                color="blue" 
                size="small"
                label="Knowledge Control Level"
              />
            </Card.Content>
          </Card>
        </Card.Group>
      )}

      <Grid stackable>
        <Grid.Row>
          <Grid.Column>
            <Button 
              primary 
              icon="plus" 
              content={intl.formatMessage(messages.createAgreement)}
              onClick={() => setShowCreateModal(true)}
            />
          </Grid.Column>
        </Grid.Row>
      </Grid>

      {/* Active Agreements Table */}
      <Header as="h4">{intl.formatMessage(messages.activeAgreements)}</Header>
      <Table celled striped>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Grantee</Table.HeaderCell>
            <Table.HeaderCell>Sovereignty Level</Table.HeaderCell>
            <Table.HeaderCell>Permissions</Table.HeaderCell>
            <Table.HeaderCell>Created</Table.HeaderCell>
            <Table.HeaderCell>Status</Table.HeaderCell>
            <Table.HeaderCell>Actions</Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {agreements.map((agreement) => (
            <Table.Row key={agreement.agreement_id}>
              <Table.Cell>{agreement.grantee_id}</Table.Cell>
              <Table.Cell>
                <Label color={getSovereigntyLevelColor(agreement.sovereignty_level)}>
                  {agreement.sovereignty_level}
                </Label>
              </Table.Cell>
              <Table.Cell>
                {agreement.permissions.map(perm => (
                  <Label key={perm} size="mini">{perm}</Label>
                ))}
              </Table.Cell>
              <Table.Cell>
                {new Date(agreement.created_date).toLocaleDateString()}
              </Table.Cell>
              <Table.Cell>
                <Label color={agreement.expiry_date && new Date(agreement.expiry_date) < new Date() ? 'red' : 'green'}>
                  {agreement.expiry_date && new Date(agreement.expiry_date) < new Date() ? 'Expired' : 'Active'}
                </Label>
              </Table.Cell>
              <Table.Cell>
                <Button 
                  size="mini" 
                  negative 
                  icon="remove" 
                  onClick={() => handleRevokeAgreement(agreement.agreement_id)}
                />
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>

      {/* Create Agreement Modal */}
      <Modal open={showCreateModal} onClose={() => setShowCreateModal(false)}>
        <Modal.Header>{intl.formatMessage(messages.createAgreement)}</Modal.Header>
        <Modal.Content>
          <Form>
            <Form.Input
              label={intl.formatMessage(messages.grantee)}
              placeholder="Enter username or email"
              value={newAgreement.grantee_id}
              onChange={(e, { value }) => setNewAgreement({ ...newAgreement, grantee_id: value })}
            />
            
            <Form.Dropdown
              label={intl.formatMessage(messages.sovereigntyLevel)}
              placeholder="Select sovereignty level"
              fluid
              selection
              options={sovereigntyLevelOptions}
              value={newAgreement.sovereignty_level}
              onChange={(e, { value }) => setNewAgreement({ ...newAgreement, sovereignty_level: value })}
            />
            
            <Form.Dropdown
              label={intl.formatMessage(messages.shareScope)}
              placeholder="Select sharing scope"
              fluid
              selection
              options={shareScopeOptions}
              value={newAgreement.share_scope}
              onChange={(e, { value }) => setNewAgreement({ ...newAgreement, share_scope: value })}
            />
            
            <Form.Dropdown
              label={intl.formatMessage(messages.permissions)}
              placeholder="Select permissions"
              fluid
              multiple
              selection
              options={permissionOptions}
              value={newAgreement.permissions}
              onChange={(e, { value }) => setNewAgreement({ ...newAgreement, permissions: value })}
            />
            
            <Form.Group>
              <Form.Checkbox
                label="Require citation"
                checked={newAgreement.citation_required}
                onChange={(e, { checked }) => setNewAgreement({ ...newAgreement, citation_required: checked })}
              />
              <Form.Checkbox
                label="Academic use only"
                checked={newAgreement.academic_use_only}
                onChange={(e, { checked }) => setNewAgreement({ ...newAgreement, academic_use_only: checked })}
              />
            </Form.Group>
            
            <Form.Input
              type="number"
              label="Expiry (days)"
              value={newAgreement.expiry_days}
              onChange={(e, { value }) => setNewAgreement({ ...newAgreement, expiry_days: parseInt(value) })}
            />
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setShowCreateModal(false)}>Cancel</Button>
          <Button primary onClick={handleCreateAgreement} loading={loading}>
            Create Agreement
          </Button>
        </Modal.Actions>
      </Modal>
    </Segment>
  );
};

export default injectIntl(SharingPermissionsManager); 