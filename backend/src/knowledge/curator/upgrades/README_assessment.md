# Assessment Infrastructure Documentation

## Overview

The `assess_current_state.py` module provides comprehensive assessment infrastructure for evaluating existing data structure and migration readiness. It analyzes current content types, identifies migration patterns, detects potential conflicts, and generates detailed reports.

## Main Components

### DataAssessment Class

The core class that performs all assessment operations:

- **assess_knowledge_items()** - Analyzes Knowledge Items for migration patterns
- **assess_research_notes()** - Evaluates Research Notes for text-to-structured migration needs
- **assess_learning_goals()** - Assesses Learning Goals for graph integration readiness
- **assess_project_logs()** - Evaluates Project Logs for learning integration
- **detect_migration_conflicts()** - Identifies potential migration conflicts
- **analyze_data_relationships()** - Analyzes cross-content relationships
- **count_entities()** - Counts all entities by type
- **generate_assessment_report()** - Creates comprehensive assessment report

### Key Assessment Functions

#### assess_current_state(context)
Main assessment function that generates a comprehensive report including:
- Entity counts and complexity scoring
- Content type assessments
- Migration conflict detection
- Data relationship analysis
- Migration readiness calculation
- Actionable recommendations

#### Quick Assessment Functions
- **quick_entity_count(context)** - Fast entity counting for planning
- **check_migration_conflicts(context)** - Focused conflict detection
- **assess_content_type(context, content_type)** - Individual content type assessment

## Assessment Categories

### 1. Entity Analysis
- Counts all content types
- Calculates migration complexity score
- Estimates migration effort

### 2. Field Analysis
- Analyzes field population patterns
- Identifies data types and structures
- Detects migration patterns in text fields

### 3. Migration Conflict Detection
- UID conflicts (duplicates)
- Circular dependencies in knowledge graph
- Invalid UID references
- Data type mismatches
- Schema violations (missing required fields)

### 4. Data Relationship Analysis
- Cross-content type references
- Dependency chain analysis
- Orphaned item detection
- Relationship integrity verification

### 5. Content Quality Assessment
- Title and content validation
- Field completeness analysis
- Data structure consistency

## Migration Readiness Scoring

The system calculates a migration readiness score (0-100) based on:

- **Blocking Issues** (-20 points each): Critical problems that must be fixed
- **Warning Issues** (-5 points each): Issues that should be addressed
- **Complexity Factor**: Adjustment based on data complexity ratio

### Readiness Levels
- **Excellent** (90-100): Ready for migration with minimal issues
- **Good** (75-89): Migration-ready with minor preparation
- **Fair** (50-74): Requires moderate preparation
- **Poor** (25-49): Significant issues need resolution
- **Critical** (0-24): Major problems require immediate attention

## Conflict Types and Severity

### High Severity (Blocking)
- UID conflicts
- Circular dependencies
- Missing required fields
- Schema violations

### Medium Severity (Warning)
- Invalid references
- Data type mismatches
- Content quality issues

## Usage Examples

### Basic Assessment
```python
from knowledge.curator.upgrades.assess_current_state import assess_current_state

# Get comprehensive assessment
report = assess_current_state(context)
print(f"Migration readiness: {report['migration_readiness']['readiness_level']}")
```

### Quick Entity Count
```python
from knowledge.curator.upgrades.assess_current_state import quick_entity_count

counts = quick_entity_count(context)
print(f"Total items to migrate: {counts['total_items']}")
```

### Conflict Detection
```python
from knowledge.curator.upgrades.assess_current_state import check_migration_conflicts

conflicts = check_migration_conflicts(context)
blocking_issues = [c for c in conflicts if c['severity'] == 'high']
print(f"Blocking issues: {len(blocking_issues)}")
```

### Individual Content Type Assessment
```python
from knowledge.curator.upgrades.assess_current_state import assess_content_type

# Assess Knowledge Items specifically
ki_assessment = assess_content_type(context, 'KnowledgeItem')
print(f"Knowledge Items with relationship issues: {len(ki_assessment['content_quality']['items_with_issues'])}")
```

## Testing

Use the provided test script to validate assessment functionality:

```python
from knowledge.curator.upgrades.test_assessment import test_assessment_functions

# Run all assessment tests
success = test_assessment_functions()
```

## Report Structure

The comprehensive assessment report includes:

```python
{
    'assessment_metadata': {
        'timestamp': '2024-01-01T12:00:00',
        'plone_version': '6.0.0',
        'catalog_version': 'unknown',
        'assessor_version': '1.0.0'
    },
    'entity_counts': {
        'KnowledgeItem': 150,
        'ResearchNote': 75,
        'LearningGoal': 25,
        'ProjectLog': 10,
        'BookmarkPlus': 200,
        'total_items': 460,
        'migration_complexity_score': 890.5
    },
    'content_assessments': {
        'knowledge_items': { ... },
        'research_notes': { ... },
        'learning_goals': { ... },
        'project_logs': { ... }
    },
    'migration_conflicts': [
        {
            'type': 'circular_dependency',
            'affected_item': 'uuid-123',
            'severity': 'high'
        }
    ],
    'data_relationships': {
        'cross_content_references': { ... },
        'relationship_integrity': { ... }
    },
    'migration_readiness': {
        'overall_score': 85,
        'readiness_level': 'good',
        'blocking_issues': 0,
        'warning_issues': 3,
        'estimated_migration_time': 'medium'
    },
    'recommendations': [
        {
            'priority': 'high',
            'category': 'data_integrity',
            'recommendation': 'Fix invalid references',
            'action': 'Review and update UID references'
        }
    ]
}
```

## Integration with Migration System

The assessment system integrates with the migration infrastructure by:

1. Storing reports in Plone registry for persistence
2. Providing targeted assessments for specific migration steps
3. Offering conflict detection before migration execution
4. Generating actionable recommendations for migration preparation

## Performance Considerations

- Large datasets (>1000 items) may require batch processing
- Assessment includes sampling to limit memory usage
- Relationship analysis uses efficient graph algorithms
- Reports are limited in size to prevent memory issues

## Logging

All assessment operations include comprehensive logging:
- Info level: Progress updates and completion status
- Warning level: Non-critical issues found
- Error level: Assessment failures and exceptions
- Debug level: Detailed field analysis information