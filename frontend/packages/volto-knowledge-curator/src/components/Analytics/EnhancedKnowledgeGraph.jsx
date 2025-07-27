import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Segment,
  Header,
  Icon,
  Grid,
  Button,
  Dropdown,
  Card,
  Label,
  Modal,
  Form,
  Input,
  Message,
  Sidebar,
  Menu,
  Checkbox,
  Divider,
  List,
  Popup,
  Statistic
} from 'semantic-ui-react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import PropTypes from 'prop-types';
import DeleteConfirmationModal from '../shared/DeleteConfirmationModal';

const relationshipTypes = {
  related: { color: '#2185d0', dashes: false, label: 'Related' },
  prerequisite: { color: '#db2828', dashes: [5, 5], label: 'Prerequisite' },
  derived: { color: '#21ba45', dashes: [10, 5], label: 'Derived From' },
  contradicts: { color: '#f2711c', dashes: [2, 2], label: 'Contradicts' },
  supports: { color: '#00b5ad', dashes: false, label: 'Supports' },
  references: { color: '#6435c9', dashes: [10, 10], label: 'References' }
};

const nodeTypes = {
  knowledge_item: { color: '#2185d0', shape: 'dot', icon: 'lightbulb' },
  learning_goal: { color: '#21ba45', shape: 'star', icon: 'graduation cap' },
  research_note: { color: '#f2711c', shape: 'diamond', icon: 'flask' },
  project_log: { color: '#6435c9', shape: 'square', icon: 'tasks' },
  bookmark: { color: '#00b5ad', shape: 'triangle', icon: 'bookmark' }
};

const EnhancedKnowledgeGraph = ({ 
  nodes: initialNodes = [], 
  relationships: initialRelationships = [],
  onNodeClick,
  onRelationshipEdit,
  onRelationshipAdd,
  onRelationshipDelete,
  enableEditing = true,
  height = '600px'
}) => {
  const networkRef = useRef(null);
  const [network, setNetwork] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [editingRelationship, setEditingRelationship] = useState(null);
  const [addingRelationship, setAddingRelationship] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    nodeTypes: Object.keys(nodeTypes).reduce((acc, type) => ({ ...acc, [type]: true }), {}),
    relationshipTypes: Object.keys(relationshipTypes).reduce((acc, type) => ({ ...acc, [type]: true }), {}),
    minStrength: 0,
    showLabels: true,
    physics: true
  });
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [layoutMode, setLayoutMode] = useState('hierarchical');
  const [clusterBy, setClusterBy] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState({ open: false, relationshipId: null, relationshipTitle: '' });

  // Prepare network data
  const networkData = useMemo(() => {
    // Filter nodes
    const filteredNodes = initialNodes.filter(node => 
      filterOptions.nodeTypes[node.type || 'knowledge_item']
    );

    // Create node dataset
    const nodes = new DataSet(
      filteredNodes.map(node => {
        const nodeType = nodeTypes[node.type || 'knowledge_item'];
        const centrality = node.centrality_score || 0.5;
        const size = 20 + (centrality * 30); // Size based on centrality

        return {
          id: node.id,
          label: filterOptions.showLabels ? node.title : '',
          title: `<div>
            <strong>${node.title}</strong><br/>
            Type: ${node.type || 'knowledge_item'}<br/>
            Centrality: ${(centrality * 100).toFixed(0)}%<br/>
            ${node.description ? `Description: ${node.description.substring(0, 100)}...` : ''}
          </div>`,
          color: {
            background: nodeType.color,
            border: nodeType.color,
            highlight: {
              background: nodeType.color,
              border: '#000000'
            }
          },
          shape: nodeType.shape,
          size: size,
          font: {
            size: 14,
            color: '#000000'
          },
          ...node
        };
      })
    );

    // Filter relationships
    const filteredRelationships = initialRelationships.filter(rel => {
      const sourceExists = nodes.get(rel.source_uid);
      const targetExists = nodes.get(rel.target_uid);
      const typeAllowed = filterOptions.relationshipTypes[rel.relationship_type || 'related'];
      const strengthAllowed = (rel.strength || 0.5) >= filterOptions.minStrength;
      
      return sourceExists && targetExists && typeAllowed && strengthAllowed;
    });

    // Create edge dataset
    const edges = new DataSet(
      filteredRelationships.map(rel => {
        const relType = relationshipTypes[rel.relationship_type || 'related'];
        const width = 1 + (rel.strength || 0.5) * 4; // Width based on strength

        return {
          id: rel.id || `${rel.source_uid}-${rel.target_uid}`,
          from: rel.source_uid,
          to: rel.target_uid,
          label: filterOptions.showLabels ? relType.label : '',
          title: `<div>
            <strong>${relType.label}</strong><br/>
            Strength: ${((rel.strength || 0.5) * 100).toFixed(0)}%<br/>
            Confidence: ${((rel.confidence || 1) * 100).toFixed(0)}%<br/>
            ${rel.metadata?.reason ? `Reason: ${rel.metadata.reason}` : ''}
          </div>`,
          color: {
            color: relType.color,
            highlight: '#000000'
          },
          dashes: relType.dashes,
          width: width,
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 0.5
            }
          },
          smooth: {
            type: 'curvedCW',
            roundness: 0.2
          },
          ...rel
        };
      })
    );

    return { nodes, edges };
  }, [initialNodes, initialRelationships, filterOptions]);

  // Network options
  const options = useMemo(() => ({
    nodes: {
      borderWidth: 2,
      borderWidthSelected: 3,
      font: {
        size: 14,
        face: 'Arial'
      }
    },
    edges: {
      font: {
        size: 12,
        face: 'Arial',
        align: 'middle'
      },
      smooth: {
        type: 'dynamic'
      }
    },
    physics: {
      enabled: filterOptions.physics,
      solver: 'barnesHut',
      barnesHut: {
        gravitationalConstant: -2000,
        centralGravity: 0.3,
        springLength: 100,
        springConstant: 0.04,
        damping: 0.09
      }
    },
    layout: layoutMode === 'hierarchical' ? {
      hierarchical: {
        enabled: true,
        direction: 'UD',
        sortMethod: 'hubsize',
        levelSeparation: 150,
        nodeSpacing: 100
      }
    } : {},
    interaction: {
      hover: true,
      tooltipDelay: 200,
      navigationButtons: true,
      keyboard: {
        enabled: true
      }
    }
  }), [filterOptions.physics, layoutMode]);

  // Initialize network
  useEffect(() => {
    if (networkRef.current && !network) {
      const newNetwork = new Network(networkRef.current, networkData, options);
      
      // Event handlers
      newNetwork.on('selectNode', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = networkData.nodes.get(nodeId);
          setSelectedNode(node);
          setSelectedEdge(null);
          if (onNodeClick) {
            onNodeClick(node);
          }
        }
      });

      newNetwork.on('selectEdge', (params) => {
        if (params.edges.length > 0) {
          const edgeId = params.edges[0];
          const edge = networkData.edges.get(edgeId);
          setSelectedEdge(edge);
          setSelectedNode(null);
        }
      });

      newNetwork.on('deselectNode', () => {
        setSelectedNode(null);
      });

      newNetwork.on('deselectEdge', () => {
        setSelectedEdge(null);
      });

      setNetwork(newNetwork);
    }
  }, [networkRef.current]);

  // Update network data
  useEffect(() => {
    if (network) {
      network.setData(networkData);
      network.setOptions(options);
    }
  }, [network, networkData, options]);

  // Clustering functions
  const applyCluster = () => {
    if (!network || !clusterBy) return;

    // Clear existing clusters
    network.setData(networkData);

    if (clusterBy === 'type') {
      Object.keys(nodeTypes).forEach(type => {
        const clusterOptions = {
          joinCondition: (nodeOptions) => {
            return nodeOptions.type === type;
          },
          clusterNodeProperties: {
            id: `cluster-${type}`,
            label: `${type} (cluster)`,
            shape: 'database',
            color: nodeTypes[type].color
          }
        };
        network.cluster(clusterOptions);
      });
    } else if (clusterBy === 'centrality') {
      // Cluster by centrality ranges
      const ranges = [
        { min: 0, max: 0.33, label: 'Low Centrality' },
        { min: 0.33, max: 0.66, label: 'Medium Centrality' },
        { min: 0.66, max: 1, label: 'High Centrality' }
      ];

      ranges.forEach((range, index) => {
        const clusterOptions = {
          joinCondition: (nodeOptions) => {
            const centrality = nodeOptions.centrality_score || 0.5;
            return centrality >= range.min && centrality < range.max;
          },
          clusterNodeProperties: {
            id: `cluster-centrality-${index}`,
            label: range.label,
            shape: 'database',
            color: '#' + Math.floor(Math.random()*16777215).toString(16)
          }
        };
        network.cluster(clusterOptions);
      });
    }
  };

  const clearClusters = () => {
    if (network) {
      // Open all clusters
      const clusters = network.getClusteredEdges();
      Object.keys(clusters).forEach(clusterId => {
        network.openCluster(clusterId);
      });
      setClusterBy(null);
    }
  };

  // Layout functions
  const applyLayout = (type) => {
    if (!network) return;

    setLayoutMode(type);
    
    switch (type) {
      case 'hierarchical':
        network.setOptions({
          layout: {
            hierarchical: {
              enabled: true,
              direction: 'UD',
              sortMethod: 'hubsize'
            }
          }
        });
        break;
      case 'circular':
        // Custom circular layout
        const nodeIds = networkData.nodes.getIds();
        const positions = {};
        const radius = 300;
        nodeIds.forEach((id, index) => {
          const angle = (2 * Math.PI * index) / nodeIds.length;
          positions[id] = {
            x: radius * Math.cos(angle),
            y: radius * Math.sin(angle)
          };
        });
        network.setOptions({ layout: { hierarchical: { enabled: false } } });
        nodeIds.forEach(id => {
          network.moveNode(id, positions[id].x, positions[id].y);
        });
        break;
      case 'force':
        network.setOptions({
          layout: { hierarchical: { enabled: false } },
          physics: { enabled: true }
        });
        network.stabilize();
        break;
    }
  };

  // Delete confirmation handler
  const handleConfirmDelete = () => {
    if (deleteConfirm.relationshipId && onRelationshipDelete) {
      onRelationshipDelete(deleteConfirm.relationshipId);
      setDeleteConfirm({ open: false, relationshipId: null, relationshipTitle: '' });
    }
  };

  // Export functions
  const exportGraph = () => {
    const exportData = {
      nodes: networkData.nodes.get(),
      edges: networkData.edges.get(),
      metadata: {
        totalNodes: networkData.nodes.length,
        totalEdges: networkData.edges.length,
        exportDate: new Date().toISOString()
      }
    };
    console.log('Export graph data:', exportData);
    // In real implementation, this would download as JSON
  };

  const exportImage = () => {
    if (network) {
      const canvas = network.canvas.frame.canvas;
      const link = document.createElement('a');
      link.download = 'knowledge-graph.png';
      link.href = canvas.toDataURL();
      link.click();
    }
  };

  // Render controls sidebar
  const renderSidebar = () => (
    <Sidebar
      as={Menu}
      animation="overlay"
      icon="labeled"
      inverted
      onHide={() => setSidebarVisible(false)}
      vertical
      visible={sidebarVisible}
      width="wide"
    >
      <Menu.Item>
        <Header inverted>Graph Controls</Header>
      </Menu.Item>
      
      <Menu.Item>
        <Header inverted size="small">Node Types</Header>
        {Object.entries(nodeTypes).map(([type, config]) => (
          <div key={type} style={{ margin: '0.5em 0' }}>
            <Checkbox
              label={type.replace('_', ' ')}
              checked={filterOptions.nodeTypes[type]}
              onChange={(e, { checked }) => 
                setFilterOptions(prev => ({
                  ...prev,
                  nodeTypes: { ...prev.nodeTypes, [type]: checked }
                }))
              }
            />
          </div>
        ))}
      </Menu.Item>

      <Menu.Item>
        <Header inverted size="small">Relationship Types</Header>
        {Object.entries(relationshipTypes).map(([type, config]) => (
          <div key={type} style={{ margin: '0.5em 0' }}>
            <Checkbox
              label={config.label}
              checked={filterOptions.relationshipTypes[type]}
              onChange={(e, { checked }) => 
                setFilterOptions(prev => ({
                  ...prev,
                  relationshipTypes: { ...prev.relationshipTypes, [type]: checked }
                }))
              }
            />
          </div>
        ))}
      </Menu.Item>

      <Menu.Item>
        <Header inverted size="small">Options</Header>
        <div style={{ margin: '0.5em 0' }}>
          <Checkbox
            label="Show Labels"
            checked={filterOptions.showLabels}
            onChange={(e, { checked }) => 
              setFilterOptions(prev => ({ ...prev, showLabels: checked }))
            }
          />
        </div>
        <div style={{ margin: '0.5em 0' }}>
          <Checkbox
            label="Enable Physics"
            checked={filterOptions.physics}
            onChange={(e, { checked }) => 
              setFilterOptions(prev => ({ ...prev, physics: checked }))
            }
          />
        </div>
      </Menu.Item>

      <Menu.Item>
        <Header inverted size="small">Min Strength</Header>
        <Input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={filterOptions.minStrength}
          onChange={(e) => 
            setFilterOptions(prev => ({ ...prev, minStrength: parseFloat(e.target.value) }))
          }
        />
        <div>{(filterOptions.minStrength * 100).toFixed(0)}%</div>
      </Menu.Item>
    </Sidebar>
  );

  // Render relationship modal
  const renderRelationshipModal = () => {
    const relationship = editingRelationship || {
      relationship_type: 'related',
      strength: 0.5,
      confidence: 1.0,
      metadata: {}
    };

    return (
      <Modal
        open={!!editingRelationship || addingRelationship}
        onClose={() => {
          setEditingRelationship(null);
          setAddingRelationship(false);
        }}
        size="small"
      >
        <Modal.Header>
          {editingRelationship ? 'Edit Relationship' : 'Add Relationship'}
        </Modal.Header>
        <Modal.Content>
          <Form>
            <Form.Field>
              <label>Relationship Type</label>
              <Dropdown
                placeholder="Select Type"
                fluid
                selection
                options={Object.entries(relationshipTypes).map(([key, config]) => ({
                  key,
                  text: config.label,
                  value: key
                }))}
                value={relationship.relationship_type}
                onChange={(e, { value }) => 
                  setEditingRelationship({ ...relationship, relationship_type: value })
                }
              />
            </Form.Field>
            <Form.Group widths="equal">
              <Form.Field>
                <label>Strength ({(relationship.strength * 100).toFixed(0)}%)</label>
                <Input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={relationship.strength}
                  onChange={(e) => 
                    setEditingRelationship({ ...relationship, strength: parseFloat(e.target.value) })
                  }
                />
              </Form.Field>
              <Form.Field>
                <label>Confidence ({(relationship.confidence * 100).toFixed(0)}%)</label>
                <Input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={relationship.confidence}
                  onChange={(e) => 
                    setEditingRelationship({ ...relationship, confidence: parseFloat(e.target.value) })
                  }
                />
              </Form.Field>
            </Form.Group>
            <Form.Field>
              <label>Reason/Notes</label>
              <Form.TextArea
                placeholder="Why this relationship exists..."
                value={relationship.metadata?.reason || ''}
                onChange={(e, { value }) => 
                  setEditingRelationship({ 
                    ...relationship, 
                    metadata: { ...relationship.metadata, reason: value }
                  })
                }
              />
            </Form.Field>
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => {
            setEditingRelationship(null);
            setAddingRelationship(false);
          }}>
            Cancel
          </Button>
          <Button 
            primary 
            onClick={() => {
              if (editingRelationship && onRelationshipEdit) {
                onRelationshipEdit(editingRelationship);
              } else if (addingRelationship && onRelationshipAdd) {
                onRelationshipAdd(relationship);
              }
              setEditingRelationship(null);
              setAddingRelationship(false);
            }}
          >
            Save
          </Button>
        </Modal.Actions>
      </Modal>
    );
  };

  return (
    <Segment>
      <Header as="h2">
        <Icon name="sitemap" />
        <Header.Content>
          Enhanced Knowledge Graph
          <Header.Subheader>Interactive visualization with typed relationships</Header.Subheader>
        </Header.Content>
      </Header>

      <Grid>
        <Grid.Row>
          <Grid.Column width={4}>
            <Button 
              icon="bars" 
              content="Filters" 
              onClick={() => setSidebarVisible(true)}
            />
          </Grid.Column>
          <Grid.Column width={4}>
            <Dropdown
              placeholder="Layout"
              selection
              options={[
                { key: 'hierarchical', text: 'Hierarchical', value: 'hierarchical' },
                { key: 'circular', text: 'Circular', value: 'circular' },
                { key: 'force', text: 'Force-Directed', value: 'force' }
              ]}
              value={layoutMode}
              onChange={(e, { value }) => applyLayout(value)}
            />
          </Grid.Column>
          <Grid.Column width={4}>
            <Dropdown
              placeholder="Cluster By"
              selection
              clearable
              options={[
                { key: 'type', text: 'Node Type', value: 'type' },
                { key: 'centrality', text: 'Centrality', value: 'centrality' }
              ]}
              value={clusterBy}
              onChange={(e, { value }) => {
                setClusterBy(value);
                if (value) {
                  applyCluster();
                } else {
                  clearClusters();
                }
              }}
            />
          </Grid.Column>
          <Grid.Column width={4}>
            <Button.Group fluid>
              <Popup
                trigger={<Button icon="download" onClick={exportGraph} />}
                content="Export as JSON"
              />
              <Popup
                trigger={<Button icon="image" onClick={exportImage} />}
                content="Export as Image"
              />
              <Popup
                trigger={<Button icon="expand arrows alternate" onClick={() => network?.fit()} />}
                content="Fit to Screen"
              />
            </Button.Group>
          </Grid.Column>
        </Grid.Row>
      </Grid>

      {/* Network Statistics */}
      <Card.Group itemsPerRow={4} style={{ marginTop: '1em', marginBottom: '1em' }}>
        <Card>
          <Card.Content textAlign="center">
            <Statistic size="tiny">
              <Statistic.Value>{networkData.nodes.length}</Statistic.Value>
              <Statistic.Label>Nodes</Statistic.Label>
            </Statistic>
          </Card.Content>
        </Card>
        <Card>
          <Card.Content textAlign="center">
            <Statistic size="tiny">
              <Statistic.Value>{networkData.edges.length}</Statistic.Value>
              <Statistic.Label>Relationships</Statistic.Label>
            </Statistic>
          </Card.Content>
        </Card>
        <Card>
          <Card.Content textAlign="center">
            <Statistic size="tiny">
              <Statistic.Value>
                {Object.values(filterOptions.nodeTypes).filter(v => v).length}
              </Statistic.Value>
              <Statistic.Label>Active Types</Statistic.Label>
            </Statistic>
          </Card.Content>
        </Card>
        <Card>
          <Card.Content textAlign="center">
            <Statistic size="tiny">
              <Statistic.Value>
                {(filterOptions.minStrength * 100).toFixed(0)}%
              </Statistic.Value>
              <Statistic.Label>Min Strength</Statistic.Label>
            </Statistic>
          </Card.Content>
        </Card>
      </Card.Group>

      {/* Graph Container */}
      <div style={{ position: 'relative' }}>
        <div 
          ref={networkRef} 
          style={{ 
            height: height, 
            border: '1px solid #ddd',
            borderRadius: '4px'
          }} 
        />
        
        {/* Selected Node/Edge Info */}
        {(selectedNode || selectedEdge) && (
          <Card style={{ position: 'absolute', top: 10, right: 10, maxWidth: '300px' }}>
            <Card.Content>
              <Card.Header>
                {selectedNode ? 'Node Details' : 'Relationship Details'}
              </Card.Header>
              <Card.Description>
                {selectedNode && (
                  <List>
                    <List.Item>
                      <strong>Title:</strong> {selectedNode.title}
                    </List.Item>
                    <List.Item>
                      <strong>Type:</strong> {selectedNode.type || 'knowledge_item'}
                    </List.Item>
                    <List.Item>
                      <strong>Centrality:</strong> {((selectedNode.centrality_score || 0.5) * 100).toFixed(0)}%
                    </List.Item>
                    {selectedNode.cluster_id && (
                      <List.Item>
                        <strong>Cluster:</strong> {selectedNode.cluster_id}
                      </List.Item>
                    )}
                  </List>
                )}
                {selectedEdge && (
                  <List>
                    <List.Item>
                      <strong>Type:</strong> {relationshipTypes[selectedEdge.relationship_type]?.label}
                    </List.Item>
                    <List.Item>
                      <strong>Strength:</strong> {((selectedEdge.strength || 0.5) * 100).toFixed(0)}%
                    </List.Item>
                    <List.Item>
                      <strong>Confidence:</strong> {((selectedEdge.confidence || 1) * 100).toFixed(0)}%
                    </List.Item>
                    {selectedEdge.metadata?.reason && (
                      <List.Item>
                        <strong>Reason:</strong> {selectedEdge.metadata.reason}
                      </List.Item>
                    )}
                  </List>
                )}
              </Card.Description>
            </Card.Content>
            {enableEditing && selectedEdge && (
              <Card.Content extra>
                <Button.Group size="tiny" fluid>
                  <Button 
                    icon="edit" 
                    content="Edit"
                    onClick={() => setEditingRelationship(selectedEdge)}
                  />
                  <Button 
                    icon="trash" 
                    content="Delete"
                    color="red"
                    onClick={() => {
                      if (onRelationshipDelete) {
                        setDeleteConfirm({
                          open: true,
                          relationshipId: selectedEdge.id,
                          relationshipTitle: `${relationshipTypes[selectedEdge.relationship_type]?.label || 'Unknown'} relationship`
                        });
                      }
                    }}
                  />
                </Button.Group>
              </Card.Content>
            )}
          </Card>
        )}
      </div>

      {/* Add Relationship Button */}
      {enableEditing && (
        <Button 
          primary 
          icon="plus" 
          content="Add Relationship" 
          style={{ marginTop: '1em' }}
          onClick={() => setAddingRelationship(true)}
        />
      )}

      {renderSidebar()}
      {renderRelationshipModal()}
      
      <DeleteConfirmationModal
        open={deleteConfirm.open}
        onClose={() => setDeleteConfirm({ open: false, relationshipId: null, relationshipTitle: '' })}
        onConfirm={handleConfirmDelete}
        itemTitle={deleteConfirm.relationshipTitle}
        itemType="relationship"
        severity="medium"
      />
    </Segment>
  );
};

EnhancedKnowledgeGraph.propTypes = {
  nodes: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    type: PropTypes.string,
    description: PropTypes.string,
    centrality_score: PropTypes.number,
    cluster_id: PropTypes.string
  })),
  relationships: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    source_uid: PropTypes.string.isRequired,
    target_uid: PropTypes.string.isRequired,
    relationship_type: PropTypes.string,
    strength: PropTypes.number,
    confidence: PropTypes.number,
    metadata: PropTypes.object
  })),
  onNodeClick: PropTypes.func,
  onRelationshipEdit: PropTypes.func,
  onRelationshipAdd: PropTypes.func,
  onRelationshipDelete: PropTypes.func,
  enableEditing: PropTypes.bool,
  height: PropTypes.string
};

export default EnhancedKnowledgeGraph;