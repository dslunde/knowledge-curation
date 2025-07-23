# Knowledge Management API Documentation

## Overview

The Knowledge Management API provides RESTful endpoints for managing knowledge content in Plone. All endpoints follow REST best practices and return JSON responses.

## Authentication

All API endpoints require authentication using standard Plone authentication methods:
- Basic Authentication
- JWT Token (if plone.restapi JWT support is enabled)
- Session Cookie

## Base URL

All API endpoints are relative to your Plone site URL:
```
https://your-site.com/plone-site/@endpoint-name
```

## API Endpoints

### 1. Knowledge Graph API

**Endpoint:** `@knowledge-graph`

#### Get Knowledge Graph
```http
GET /@knowledge-graph
```

Returns the complete knowledge graph with nodes and edges.

**Response:**
```json
{
  "nodes": [
    {
      "id": "uid-123",
      "title": "Research Note Title",
      "type": "ResearchNote",
      "url": "http://site/research-note",
      "description": "Note description",
      "review_state": "published",
      "created": "2024-01-01T10:00:00",
      "modified": "2024-01-02T15:30:00",
      "tags": ["tag1", "tag2"],
      "progress": 75
    }
  ],
  "edges": [
    {
      "source": "uid-123",
      "target": "uid-456",
      "type": "connection"
    }
  ],
  "count": 42
}
```

#### Get Connections for Item
```http
GET /path/to/item/@knowledge-graph/connections
```

Returns all connections for a specific item.

**Response:**
```json
{
  "connections": [
    {
      "uid": "uid-456",
      "title": "Connected Item",
      "type": "LearningGoal",
      "url": "http://site/learning-goal",
      "connection_type": "direct"
    }
  ],
  "count": 5
}
```

#### Suggest Connections
```http
GET /path/to/item/@knowledge-graph/suggest
```

Suggests potential connections based on content similarity.

**Response:**
```json
{
  "suggestions": [
    {
      "uid": "uid-789",
      "title": "Similar Content",
      "type": "ResearchNote",
      "url": "http://site/similar-note",
      "similarity": 0.892,
      "description": "Description of similar content"
    }
  ],
  "count": 10
}
```

#### Visualize Graph
```http
GET /@knowledge-graph/visualize
```

Returns graph data optimized for visualization.

**Response:**
```json
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "visualization": {
    "width": 1200,
    "height": 800,
    "force": {
      "charge": -300,
      "linkDistance": 100,
      "gravity": 0.05
    }
  }
}
```

### 2. Search API

**Endpoint:** `@knowledge-search`

#### Semantic Search
```http
POST /@knowledge-search
Content-Type: application/json

{
  "type": "semantic",
  "query": "machine learning algorithms",
  "limit": 20,
  "portal_types": ["ResearchNote", "BookmarkPlus"],
  "filters": {
    "review_state": ["published", "private"],
    "tags": ["AI", "ML"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**Response:**
```json
{
  "items": [
    {
      "uid": "uid-123",
      "title": "Introduction to ML",
      "description": "Basic concepts of machine learning",
      "url": "http://site/intro-ml",
      "portal_type": "ResearchNote",
      "review_state": "published",
      "created": "2024-01-15T10:00:00",
      "modified": "2024-01-20T14:30:00",
      "similarity_score": 0.945,
      "tags": ["ML", "AI", "algorithms"]
    }
  ],
  "items_total": 15,
  "query": "machine learning algorithms",
  "search_type": "semantic"
}
```

#### Similarity Search
```http
POST /@knowledge-search
Content-Type: application/json

{
  "type": "similarity",
  "uid": "source-item-uid",
  "limit": 10,
  "threshold": 0.7
}
```

#### Full-text Search
```http
POST /@knowledge-search
Content-Type: application/json

{
  "type": "fulltext",
  "query": "python programming",
  "limit": 20,
  "portal_types": ["ResearchNote"],
  "filters": {
    "tags": ["python", "programming"]
  }
}
```

#### GET Methods
```http
GET /@knowledge-search/semantic?q=search+term&limit=10&types=ResearchNote,BookmarkPlus
GET /path/to/item/@knowledge-search/similar?limit=5&threshold=0.8
```

### 3. Analytics API

**Endpoint:** `@knowledge-analytics`

#### Get Overview
```http
GET /@knowledge-analytics
```

Returns overview statistics of the knowledge base.

**Response:**
```json
{
  "total_items": 156,
  "by_type": {
    "ResearchNote": 89,
    "LearningGoal": 23,
    "ProjectLog": 12,
    "BookmarkPlus": 32
  },
  "by_state": {
    "published": 120,
    "private": 36
  },
  "recent_activity": [...],
  "top_tags": [
    ["python", 45],
    ["machine-learning", 38]
  ],
  "connections": 234
}
```

#### Get Learning Statistics
```http
GET /@knowledge-analytics/statistics?days=30
```

Returns detailed learning statistics for the specified period.

**Response:**
```json
{
  "period_days": 30,
  "learning_goals": {
    "total": 23,
    "completed": 8,
    "in_progress": 12,
    "planned": 3,
    "average_progress": 65.4,
    "by_priority": {
      "low": 5,
      "medium": 12,
      "high": 6
    }
  },
  "research_notes": {
    "total": 45,
    "with_insights": 38,
    "with_connections": 32,
    "average_connections": 2.7
  },
  "bookmarks": {
    "total": 28,
    "by_status": {
      "unread": 8,
      "reading": 5,
      "read": 15
    },
    "by_importance": {
      "low": 3,
      "medium": 18,
      "high": 5,
      "critical": 2
    }
  },
  "generated_at": "2024-02-15T10:30:00"
}
```

#### Get Forgetting Curve Data
```http
GET /@knowledge-analytics/forgetting-curve
```

Returns items sorted by retention score for spaced repetition.

**Response:**
```json
{
  "forgetting_curve": [
    {
      "uid": "uid-123",
      "title": "Python Decorators",
      "type": "ResearchNote",
      "days_since_review": 15,
      "retention_score": 0.423,
      "review_recommended": true,
      "last_review": "2024-01-31T14:00:00",
      "url": "http://site/python-decorators"
    }
  ],
  "review_groups": {
    "urgent": [...],
    "soon": [...],
    "later": [...],
    "good": 45
  },
  "total_items": 89
}
```

#### Get Progress Timeline
```http
GET /@knowledge-analytics/progress?days=90&interval=week
```

Returns learning progress over time.

**Parameters:**
- `days`: Number of days to include (default: 90)
- `interval`: Grouping interval - "day", "week", or "month" (default: "week")

#### Get Activity Heatmap
```http
GET /@knowledge-analytics/activity
```

Returns activity data for the last 365 days.

#### Get AI Insights
```http
GET /@knowledge-analytics/insights
```

Returns AI-generated insights about knowledge patterns.

### 4. Bulk Operations API

**Endpoint:** `@knowledge-bulk`

All bulk operations require POST method and return operation results.

#### Bulk Workflow Transition
```http
POST /@knowledge-bulk/workflow
Content-Type: application/json

{
  "uids": ["uid-1", "uid-2", "uid-3"],
  "transition": "publish",
  "comment": "Publishing reviewed content"
}
```

**Response:**
```json
{
  "operation": "workflow_transition",
  "transition": "publish",
  "results": {
    "successful": [...],
    "failed": [...],
    "unauthorized": [...]
  },
  "summary": {
    "total": 3,
    "successful": 2,
    "failed": 0,
    "unauthorized": 1
  }
}
```

#### Bulk Tag Operations
```http
POST /@knowledge-bulk/tag
Content-Type: application/json

{
  "uids": ["uid-1", "uid-2"],
  "mode": "add",  // "add", "remove", or "replace"
  "add_tags": ["python", "tutorial"],
  "remove_tags": ["draft"]
}
```

#### Bulk Delete
```http
POST /@knowledge-bulk/delete
Content-Type: application/json

{
  "uids": ["uid-1", "uid-2"]
}
```

#### Bulk Move
```http
POST /@knowledge-bulk/move
Content-Type: application/json

{
  "uids": ["uid-1", "uid-2"],
  "target_path": "/knowledge/archive"
}
```

#### Bulk Update Fields
```http
POST /@knowledge-bulk/update
Content-Type: application/json

{
  "uids": ["uid-1", "uid-2"],
  "updates": {
    "priority": "high",
    "status": "active"
  }
}
```

#### Bulk Connect Items
```http
POST /@knowledge-bulk/connect
Content-Type: application/json

{
  "source_uids": ["uid-1", "uid-2"],
  "target_uids": ["uid-3", "uid-4"],
  "connection_type": "bidirectional"  // or "unidirectional"
}
```

### 5. Spaced Repetition API

**Endpoint:** `@spaced-repetition`

#### Get Review Items
```http
GET /@spaced-repetition/review?limit=20
```

Returns items due for review.

**Response:**
```json
{
  "items": [
    {
      "uid": "uid-123",
      "title": "Python Generators",
      "type": "ResearchNote",
      "url": "http://site/python-generators",
      "description": "Understanding Python generators",
      "sr_data": {
        "interval": 7,
        "repetitions": 3,
        "ease_factor": 2.5,
        "last_review": "2024-02-08T10:00:00",
        "next_review": "2024-02-15T10:00:00",
        "retention_score": 0.623
      }
    }
  ],
  "total_due": 12,
  "next_review_date": "2024-02-15T10:00:00"
}
```

#### Update Review Performance
```http
POST /@spaced-repetition/review
Content-Type: application/json

{
  "uid": "uid-123",
  "quality": 4,  // 0-5 scale
  "time_spent": 180  // seconds
}
```

**Response:**
```json
{
  "success": true,
  "uid": "uid-123",
  "sr_data": {
    "interval": 15,
    "repetitions": 4,
    "ease_factor": 2.6,
    "next_review": "2024-03-01T10:00:00",
    "quality": 4
  }
}
```

#### Get Review Schedule
```http
GET /@spaced-repetition/schedule
```

Returns upcoming review schedule grouped by date.

#### Get Performance Statistics
```http
GET /@spaced-repetition/performance?days=30
```

Returns spaced repetition performance metrics.

#### Get/Update Settings
```http
GET /@spaced-repetition/settings
POST /@spaced-repetition/settings

{
  "daily_review_limit": 25,
  "new_items_per_day": 5,
  "review_order": "urgency",
  "minimum_ease_factor": 1.3,
  "initial_intervals": [1, 6],
  "notification_enabled": true,
  "notification_time": "09:00"
}
```

### 6. Import/Export API

**Endpoint:** `@knowledge-io`

#### Export Content
```http
GET /@knowledge-io/export?format=json&types=ResearchNote,BookmarkPlus&include_embeddings=false
```

**Parameters:**
- `format`: Export format - "json", "csv", "opml", "markdown", "roam"
- `types`: Comma-separated list of content types to export
- `include_embeddings`: Include embedding vectors (json format only)
- `include_connections`: Include connection data (default: true)

**Response:** File download with appropriate content type

#### Import Content
```http
POST /@knowledge-io/import
Content-Type: multipart/form-data

file: [file data]
format: json
merge_strategy: skip  // "skip", "update", or "duplicate"
```

**Response:**
```json
{
  "success": true,
  "results": {
    "imported": 15,
    "skipped": 3,
    "updated": 0,
    "errors": []
  }
}
```

#### Validate Import File
```http
POST /@knowledge-io/validate
Content-Type: multipart/form-data

file: [file data]
format: json
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Item 5 missing description field"],
  "summary": {
    "total_items": 20,
    "by_type": {
      "ResearchNote": 15,
      "BookmarkPlus": 5
    },
    "version": "1.0"
  }
}
```

#### Get Supported Formats
```http
GET /@knowledge-io/formats
```

Returns list of supported import and export formats with details.

## Error Responses

All endpoints follow standard HTTP status codes:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: HTTP method not supported
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "error": "Error message",
  "type": "BadRequest",
  "details": {
    "field": "Additional error details"
  }
}
```

## Rate Limiting

API endpoints may be subject to rate limiting based on your Plone configuration. Check response headers for rate limit information:

- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

## Pagination

For endpoints returning lists, use these parameters:
- `b_start`: Starting index (default: 0)
- `b_size`: Number of items to return (default: 25, max: 100)

## Filtering and Sorting

Many endpoints support filtering and sorting:
- `sort_on`: Field to sort by
- `sort_order`: "ascending" or "descending"
- Additional filters vary by endpoint

## Content Negotiation

All endpoints support JSON format. Some endpoints (like export) support additional formats specified via the `format` parameter or `Accept` header.

## Webhooks

Webhook support can be added for real-time notifications of knowledge base changes. Contact your administrator for webhook configuration.

## SDK Examples

### Python
```python
import requests

# Basic authentication
auth = ('username', 'password')
base_url = 'https://your-site.com/plone'

# Semantic search
response = requests.post(
    f'{base_url}/@knowledge-search',
    json={
        'type': 'semantic',
        'query': 'machine learning',
        'limit': 10
    },
    auth=auth
)
results = response.json()

# Get knowledge graph
response = requests.get(
    f'{base_url}/@knowledge-graph',
    auth=auth
)
graph = response.json()
```

### JavaScript
```javascript
// Using fetch API
const baseUrl = 'https://your-site.com/plone';
const headers = {
  'Authorization': 'Basic ' + btoa('username:password'),
  'Content-Type': 'application/json',
  'Accept': 'application/json'
};

// Semantic search
fetch(`${baseUrl}/@knowledge-search`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    type: 'semantic',
    query: 'machine learning',
    limit: 10
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Get review items
fetch(`${baseUrl}/@spaced-repetition/review?limit=20`, {
  headers: headers
})
.then(response => response.json())
.then(data => console.log(data));
```

## Best Practices

1. **Authentication**: Always use HTTPS in production
2. **Caching**: Implement appropriate caching for read operations
3. **Batch Operations**: Use bulk endpoints for multiple operations
4. **Error Handling**: Implement retry logic for transient errors
5. **Pagination**: Use pagination for large result sets
6. **Filtering**: Apply filters to reduce data transfer

## Version History

- v1.0.0: Initial API release with all core endpoints

## Support

For API support and bug reports, please contact your system administrator or file an issue in the project repository.