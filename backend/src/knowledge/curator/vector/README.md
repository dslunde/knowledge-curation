# Vector Database Integration for Plone Knowledge System

This module provides semantic search and similarity operations using Qdrant vector database and sentence-transformers for embedding generation.

## Features

- **Semantic Search**: Find content based on meaning rather than exact keyword matches
- **Similar Content Discovery**: Automatically find related knowledge items
- **Content Recommendations**: Personalized suggestions based on user interactions
- **Duplicate Detection**: Identify potentially duplicate content
- **Semantic Clustering**: Group content by topic/theme
- **Automatic Indexing**: Content is automatically vectorized on creation/modification

## Architecture

### Components

1. **Embedding Generator** (`embeddings.py`)
   - Uses sentence-transformers for text embeddings
   - Default model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
   - Supports batch processing for efficiency
   - Handles content-specific text preparation

2. **Qdrant Adapter** (`adapter.py`)
   - Manages connection to Qdrant vector database
   - Handles vector CRUD operations
   - Supports batch operations and filtering

3. **Similarity Search** (`search.py`)
   - Text-based similarity search
   - Find related content
   - Duplicate detection
   - Semantic clustering
   - Personalized recommendations

4. **Collection Manager** (`management.py`)
   - Database initialization
   - Index rebuilding
   - Health checks
   - Backup/restore operations

5. **Event Subscribers** (`events.py`)
   - Automatic vector generation on content creation
   - Vector updates on content modification
   - Vector deletion on content removal
   - Workflow-aware indexing

## Setup

### Prerequisites

1. **Install Qdrant**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Install Python Dependencies**
   ```bash
   pip install qdrant-client sentence-transformers
   ```

### Configuration

Configuration can be set via environment variables in `buildout.cfg`:

```ini
environment-vars =
    QDRANT_HOST localhost
    QDRANT_PORT 6333
    QDRANT_API_KEY your-api-key-if-needed
    QDRANT_HTTPS false
    EMBEDDING_MODEL sentence-transformers/all-MiniLM-L6-v2
    VECTOR_SEARCH_LIMIT 10
    VECTOR_SCORE_THRESHOLD 0.5
    VECTOR_BATCH_SIZE 100
    EMBEDDING_BATCH_SIZE 32
    VECTOR_AUTO_INDEX_CREATE true
    VECTOR_AUTO_INDEX_MODIFY true
    VECTOR_AUTO_DELETE true
```

### Initial Setup

1. **Initialize the Database**
   ```
   Navigate to: /@@vector-management
   Click "Initialize Database"
   ```

2. **Build Initial Index**
   ```
   Navigate to: /@@vector-management
   Click "Rebuild Index"
   ```

## Usage

### Web Interface

#### Vector Management (`/@@vector-management`)
- View system health status
- Initialize/rebuild vector index
- View database statistics
- Manage vector operations

#### Vector Search (`/@@vector-search`)
- Semantic search interface
- Find similar content
- Adjust similarity thresholds

### REST API

#### Search for Similar Content
```bash
POST /@vector-search
Content-Type: application/json

{
    "query": "machine learning algorithms",
    "limit": 10,
    "score_threshold": 0.5,
    "content_types": ["ResearchNote", "BookmarkPlus"]
}
```

#### Find Similar to Specific Content
```bash
GET /@similar-content/{uid}?limit=5&score_threshold=0.6
```

#### Get Recommendations
```bash
GET /@vector-recommendations?limit=20&min_score=0.5
```

#### Semantic Clustering
```bash
POST /@vector-clustering
Content-Type: application/json

{
    "content_types": ["ResearchNote"],
    "n_clusters": 5
}
```

#### Management Operations
```bash
# Health check
GET /@vector-management/health

# Database stats
GET /@vector-management/stats

# Initialize database
POST /@vector-management/initialize

# Rebuild index
POST /@vector-management/rebuild
{
    "content_types": ["BookmarkPlus", "ResearchNote"],
    "clear_first": true
}
```

### Python API

```python
from knowledge.curator.vector.search import SimilaritySearch
from knowledge.curator.vector.management import VectorCollectionManager

# Search for similar content
search = SimilaritySearch()
results = search.search_by_text(
    "artificial intelligence",
    limit=10,
    score_threshold=0.6
)

# Find similar to existing content
similar = search.find_similar_content(
    content_uid="abc123",
    limit=5
)

# Rebuild index
manager = VectorCollectionManager()
manager.rebuild_index(content_types=["ResearchNote"])
```

## Content Types Support

The following content types are automatically indexed:
- **BookmarkPlus**: URL, title, description, notes, tags
- **ResearchNote**: Title, content, key findings, tags
- **LearningGoal**: Goal description, success criteria, target date
- **ProjectLog**: Status, latest update, next steps

## Workflow Integration

Content is automatically indexed when entering these workflow states:
- `private`
- `process`
- `reviewed`
- `published`

Content is removed from the index when transitioning to other states.

## Performance Considerations

1. **Batch Processing**: Use batch operations for bulk updates
2. **Embedding Model**: Choose model based on quality/speed tradeoff
3. **Index Size**: Monitor vector database size and performance
4. **Caching**: Embeddings are cached by Qdrant

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check Qdrant is running: `curl http://localhost:6333`
   - Verify host/port configuration

2. **Dimension Mismatch**
   - Ensure consistent embedding model
   - Rebuild index after model change

3. **Memory Issues**
   - Reduce batch sizes
   - Use smaller embedding model

### Health Check

Access `/@@vector-management` to check:
- Qdrant connection status
- Embedding model status
- Collection existence
- Vector count statistics

## Model Options

Available embedding models:

1. **all-MiniLM-L6-v2** (Default)
   - Dimension: 384
   - Fast and efficient
   - Good for general use

2. **all-mpnet-base-v2**
   - Dimension: 768
   - Higher quality
   - Slower processing

3. **paraphrase-multilingual-MiniLM-L12-v2**
   - Dimension: 384
   - Multilingual support
   - Slightly slower

## Security

- API key authentication supported for Qdrant
- Management operations require `cmf.ManagePortal` permission
- Search operations respect content permissions

## Backup and Restore

```python
# Backup vectors
manager = VectorCollectionManager()
manager.backup_vectors("/path/to/backup.json")

# Restore vectors
manager.restore_vectors("/path/to/backup.json")
```

## Development

### Running Tests
```bash
bin/test -s knowledge.curator -t test_vector_operations
```

### Extending

To add support for new content types:
1. Add type to `SUPPORTED_CONTENT_TYPES` in `config.py`
2. Extend `prepare_content_text()` in `embeddings.py`
3. Update event subscribers if needed