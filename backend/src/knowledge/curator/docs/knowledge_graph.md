# Knowledge Graph Documentation

## Overview

The Knowledge Graph system provides a powerful way to visualize, analyze, and navigate relationships between knowledge items in your Plone site. It uses graph theory algorithms to help discover patterns, find knowledge gaps, and suggest connections.

## Features

### Core Features

1. **Interactive Visualization**
   - D3.js-based force-directed graph
   - Multiple layout options (force, radial, hierarchical, circular)
   - Zoom, pan, and node selection
   - Real-time filtering and search

2. **Relationship Types**
   - Related to
   - Prerequisite of / Requires
   - Builds on / Foundation for
   - Supports / Supported by
   - Contains / Part of
   - And many more...

3. **Graph Analysis**
   - Centrality measures (degree, betweenness, closeness, PageRank)
   - Community detection
   - Knowledge gap identification
   - Cluster analysis

4. **Navigation**
   - Path finding between concepts
   - Breadcrumb navigation
   - Related content suggestions
   - Learning path generation

## Architecture

### Data Model

```python
# Node Types
- ResearchNote
- LearningGoal
- ProjectLog
- BookmarkPlus
- Concept
- Tag
- Person
- Organization

# Edge Properties
- source: Source node UID
- target: Target node UID
- type: Relationship type
- weight: Connection strength (0.0-1.0)
- properties: Additional metadata
```

### Storage

The graph is stored using Plone's annotation storage with efficient indexing:

```python
# Storage structure
{
    'nodes': {uid: node_data},
    'edges': [edge_data],
    'indexes': {
        'by_type': {type: [uids]},
        'by_relationship': {rel_type: [(source, target)]},
        'by_tag': {tag: [uids]}
    }
}
```

## API Endpoints

### Get Graph Data
```
GET /@knowledge-graph
```

Returns the full knowledge graph or subgraph based on context.

### Get Node Connections
```
GET /@knowledge-graph/connections
```

Returns all connections for the current content item.

### Suggest Connections
```
GET /@knowledge-graph/suggest
```

Returns AI-powered connection suggestions based on content similarity.

### Visualize Graph
```
GET /@knowledge-graph/visualize
```

Returns graph data optimized for visualization with layout hints.

## Usage

### Viewing the Knowledge Graph

1. Navigate to any folder or the site root
2. Append `/@@knowledge-graph` to the URL
3. The interactive graph will load showing all knowledge items

### Graph Controls

- **Layout**: Switch between force, radial, hierarchical, and circular layouts
- **Filter**: Toggle visibility of different node types
- **Search**: Find specific nodes by title
- **Zoom**: Use mouse wheel or buttons to zoom in/out

### Creating Relationships

1. Edit a knowledge item
2. Use the "Connections" or "Related Notes" field
3. Select target items
4. Save the content

### Analyzing the Graph

The analysis panel shows:
- **Central Concepts**: Most important nodes by centrality
- **Knowledge Gaps**: Suggested missing connections
- **Clusters**: Groups of related content

## Graph Algorithms

### Shortest Path
Find the shortest path between two concepts:
```python
from knowledge.curator.graph import GraphAlgorithms

algo = GraphAlgorithms(graph)
path = algo.shortest_path(start_uid, end_uid)
```

### Centrality Analysis
Identify important nodes:
```python
# Degree centrality
degree_scores = algo.degree_centrality()

# PageRank
pagerank_scores = algo.pagerank()

# Betweenness centrality
betweenness_scores = algo.betweenness_centrality()
```

### Community Detection
Find clusters of related content:
```python
communities = algo.find_communities()
```

### Knowledge Gap Detection
Find missing connections:
```python
gaps = algo.find_knowledge_gaps(min_importance=0.5)
```

## Customization

### Custom Relationship Types

Register custom relationships:
```python
from knowledge.curator.graph import RelationshipManager

manager = RelationshipManager()
manager.register_custom_relationship(
    'mentions',
    {
        'bidirectional': False,
        'transitive': False,
        'weight_range': (0.0, 1.0),
        'description': 'Mentions another item',
        'reverse_name': 'mentioned_by'
    }
)
```

### Custom Node Types

Add new node types by extending the NodeType enum:
```python
class CustomNodeType(NodeType):
    CUSTOM_TYPE = "CustomType"
```

### Graph Styling

Customize node colors in JavaScript:
```javascript
KnowledgeGraph.options.nodeColors = {
    'ResearchNote': '#3498db',
    'CustomType': '#ff6b6b'
};
```

## Best Practices

1. **Meaningful Relationships**
   - Use specific relationship types
   - Set appropriate weights
   - Avoid creating too many weak connections

2. **Graph Maintenance**
   - Regularly review suggested connections
   - Prune orphan nodes
   - Merge duplicate concepts

3. **Performance**
   - Use subgraphs for large datasets
   - Enable graph caching
   - Limit visualization depth

## Examples

### Creating a Learning Path

```python
from knowledge.curator.graph import GraphOperations, GraphTraversal

# Create nodes
ops = GraphOperations(graph)
ops.add_content_node('basics', 'Python Basics', 'ResearchNote')
ops.add_content_node('advanced', 'Advanced Python', 'ResearchNote')
ops.add_content_node('expert', 'Python Expert', 'LearningGoal')

# Create prerequisite relationships
ops.create_relationship('basics', 'advanced', RelationshipType.PREREQUISITE_OF)
ops.create_relationship('advanced', 'expert', RelationshipType.PREREQUISITE_OF)

# Find learning path
traversal = GraphTraversal(graph)
path = traversal.get_learning_path('basics', 'expert')
```

### Finding Related Content

```python
# Get neighborhood around a topic
neighborhood = traversal.get_neighborhood('python_basics', radius=2)

# Explore related topics
related = traversal.explore_topic('machine_learning', max_nodes=20)
```

### Analyzing Knowledge Structure

```python
# Find knowledge clusters
clusters = traversal.find_knowledge_clusters(min_size=3)

# Identify central concepts
central = algo.find_central_concepts(top_n=10)

# Calculate knowledge density
density = algo.calculate_knowledge_density()
```

## Troubleshooting

### Graph Not Loading

1. Check browser console for errors
2. Verify D3.js is loaded
3. Check permissions on content

### Missing Connections

1. Verify content has connections field
2. Check relationship constraints
3. Run catalog sync

### Performance Issues

1. Reduce graph size with filters
2. Use subgraph views
3. Enable browser caching

## Export/Import

### Export Formats

- **JSON**: Complete graph data with metadata
- **GEXF**: For use with Gephi
- **GraphML**: Standard graph format

### Export Example

```python
storage = GraphStorage(context)
json_data = storage.export_graph(format='json')
```

### Import Example

```python
storage.import_graph(json_data, format='json', merge=True)
```