# Knowledge Curator API Endpoints Summary

## Enhanced REST API Endpoints

### 1. Knowledge Graph API (`@knowledge-graph`)

**Base URL**: `/api/@knowledge-graph`

#### GET Endpoints:
- `/` - Get the full knowledge graph
- `/connections` - Get connections for a specific item
- `/suggest` - Get AI-suggested connections based on similarity
- `/visualize` - Get graph data optimized for visualization
- `/metrics` - Get graph metrics (node-specific or overall)
- `/analysis` - Perform advanced graph analysis

#### POST Endpoints:
- `/relationship` - Create a typed relationship between content items
- `/accept-suggestion` - Accept an AI-suggested relationship

#### PUT Endpoints:
- `/relationship` - Update an existing relationship

#### DELETE Endpoints:
- `/relationship` - Delete a relationship

**Key Features**:
- Typed relationships with IKnowledgeRelationship objects
- Relationship strength calculation (0.0-1.0)
- Graph analysis including centrality and clustering
- Support for relationship metadata and confidence tracking

### 2. Learning Progression API (`@learning-progression`)

**Base URL**: `/api/@learning-progression`

#### GET Endpoints:
- `/` - Get learning progression overview
- `/milestones` - Get milestones across all learning goals
- `/path` - Get recommended learning path based on prerequisites
- `/competencies` - Get competency assessment
- `/objectives` - Get learning objectives and progress
- `/prerequisites` - Check prerequisites for a specific goal
- `/recommendations` - Get learning recommendations

#### POST Endpoints:
- `/milestones` - Create a new milestone
- `/objectives` - Create a new learning objective
- `/competencies` - Assess or update a competency level

#### PUT Endpoints:
- `/milestones` - Update an existing milestone
- `/objectives` - Update a learning objective

**Key Features**:
- Milestone tracking with progress percentages
- Learning path recommendations based on prerequisites
- Competency assessment and tracking
- SMART objective management
- Prerequisite validation

### 3. Enhanced Analytics API (`@knowledge-analytics`)

**Base URL**: `/api/@knowledge-analytics`

#### GET Endpoints (Existing):
- `/` - Get overview of knowledge base statistics
- `/statistics` - Get detailed learning statistics
- `/forgetting-curve` - Get forgetting curve data for spaced repetition
- `/progress` - Get learning progress over time
- `/activity` - Get user activity heatmap data
- `/insights` - Get AI-generated insights

#### GET Endpoints (New):
- `/learning-effectiveness` - Analyze learning effectiveness metrics
- `/knowledge-gaps` - Identify and analyze knowledge gaps
- `/learning-velocity` - Track learning velocity and momentum
- `/bloom-taxonomy` - Analyze content according to Bloom's Taxonomy
- `/cognitive-load` - Assess cognitive load across learning materials

**Key Features**:
- Learning effectiveness metrics (completion rates, time to complete)
- Knowledge gap analysis with AI integration
- Learning velocity tracking with trend analysis
- Bloom's taxonomy progress analysis
- Cognitive load assessment with recommendations

## Data Serialization

All endpoints properly serialize/deserialize structured objects:

### Research Note Serialization:
- Structured `IKeyInsight` objects with text, importance, evidence, timestamp
- Structured `IAuthor` objects with name, email, orcid, affiliation
- Typed relationships with strength and metadata
- Full bibliographic metadata support

### Learning Goal Serialization:
- Structured `ILearningMilestone` objects with progress tracking
- Structured `ILearningObjective` objects with SMART criteria
- Structured `ICompetency` objects with levels and categories
- Assessment criteria with weights

### Project Log Serialization:
- Structured `IProjectLogEntry` objects with timestamps and types
- Structured `IProjectDeliverable` objects with status tracking
- Structured `IStakeholder` objects with interest/influence levels
- Success metrics and lessons learned

## Permission and Validation

All endpoints implement:
- Proper permission checking (View/Modify portal content)
- Request validation with appropriate error responses
- HTTP status codes for different scenarios
- JSON request/response handling

## Integration with New Schema Fields

The APIs fully support:
- Enhanced content types from IKnowledgeObjectBase
- Learning metadata (difficulty level, cognitive load, learning styles)
- Bibliographic metadata (authors, DOI, ISBN, etc.)
- Knowledge status and review tracking
- Confidence scoring

## Usage Example

```javascript
// Create a typed relationship
fetch('/api/@knowledge-graph/relationship', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    source_uid: 'abc123',
    target_uid: 'def456',
    relationship_type: 'builds_upon',
    strength: 0.8,
    metadata: {
      reason: 'Extends concepts from previous research'
    }
  })
});

// Get learning path recommendations
fetch('/api/@learning-progression/path')
  .then(response => response.json())
  .then(data => {
    console.log('Recommended learning path:', data.learning_path);
    console.log('Ready to learn:', data.ready_to_learn);
  });

// Analyze cognitive load
fetch('/api/@knowledge-analytics/cognitive-load')
  .then(response => response.json())
  .then(data => {
    console.log('Overall load:', data.overall_load);
    console.log('Recommendations:', data.recommendations);
  });
```