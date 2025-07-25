# BookmarkPlus Resource Quality Assessment System

## Overview

The Resource Quality Assessment System provides comprehensive functionality to evaluate and track the quality of Bookmark+ resources within the Knowledge Curator application. This system considers multiple factors to calculate quality scores and provides tools for monitoring quality trends over time.

## Features

### 1. Quality Score Calculation

The system calculates an overall quality score (0.0-1.0) based on multiple weighted factors:

- **Content Quality** (50% base score): User-assigned quality rating (low/medium/high/excellent)
- **User Engagement** (25% weight): Based on read status and interaction patterns
- **Content Completeness** (15% weight): Availability of descriptions, notes, quotes, AI summaries  
- **Learning Correlation** (35% weight): Relationship strength with knowledge items and learning goals
- **Freshness** (10% weight): Time-sensitivity assessment based on resource type and age
- **Annotation Quality** (15% weight): Quality and depth of personal notes and key quotes

### 2. Quality Tracking Over Time

- Maintains historical quality metrics (last 10 measurements)
- Calculates quality trends (improving/declining/stable)
- Automatic flagging of resources with declining quality
- Periodic quality assessment updates

### 3. Quality Review System

- Automatic flagging of low-quality resources (score < 0.3)
- Manual flagging with custom reasons
- Flag management (set/clear/check status)
- Review workflow integration

## API Methods

### BookmarkPlus Content Type Methods

```python
# Core quality assessment
calculate_quality_score() -> float
get_quality_metrics() -> dict
update_quality_tracking() -> None

# Quality history and trends
get_quality_history() -> list
get_quality_trend() -> str  # 'improving'|'declining'|'stable'

# Quality flagging system
flag_for_quality_review(reason=None) -> None
clear_quality_flag() -> None
is_flagged_for_review() -> bool
get_quality_flag_info() -> dict
```

### Utility Class Methods

```python
from knowledge.curator.utilities.quality_assessment import BookmarkQualityAssessment

qa = BookmarkQualityAssessment(context)

# Bulk operations
qa.assess_all_bookmarks() -> dict
qa.get_quality_report(min_score=None, max_score=None) -> list
qa.identify_outdated_resources(days_threshold=365) -> list
qa.get_learning_correlation_analysis() -> dict
qa.update_quality_for_modified_resources(days=7) -> dict
qa.clear_quality_flags(uids=None) -> int
```

## Web Interface

### Quality Dashboard

Access via: `/@@quality-dashboard`

Features:
- Overview statistics (total resources, quality distribution)
- List of flagged resources requiring review
- Top quality resources display
- Quality trend visualizations

### API Endpoints

Access via: `/@@quality-assessment-api`

POST actions:
- `assess_all`: Run quality assessment on all resources
- `clear_flags`: Clear quality review flags
- `update_tracking`: Update quality tracking for recent changes
- `generate_report`: Generate detailed quality report

### Individual Resource Quality View

Access via: `/path/to/bookmark/@@resource-quality-detail`

Features:
- Detailed quality metrics breakdown
- Quality history timeline
- Trend analysis
- Flag management

## Quality Metrics Breakdown

### Engagement Score Factors
- `completed`: 0.8-0.9 (higher if reading time matches estimate)
- `in_progress`: 0.5
- `archived`: 0.7 (valuable enough to archive)
- `unread`: 0.1

### Completeness Score Components
- Description present: +0.2
- Personal notes: +0.3
- Key quotes: +0.3
- AI summary: +0.2

### Learning Correlation Factors
- Related knowledge items (70% weight): Up to 1.0 for 5+ items
- Supporting learning goals (30% weight): Up to 1.0 for 3+ goals

### Freshness Score by Resource Type
- **Books/Courses/References**: 0.8 (age-resistant)
- **News/Blog posts**: Rapid decay (1.0 < 30 days, 0.2 > 1 year)
- **Other content**: Gradual decay (1.0 < 6 months, 0.4 > 2 years)

### Annotation Score Calculation
- Personal notes: 0.1-0.5 based on length and detail
- Key quotes: 0.1-0.5 based on quantity (1-5+)

## Usage Examples

### Basic Quality Assessment

```python
# Get quality metrics for a bookmark
bookmark = portal['my-bookmark']
metrics = bookmark.get_quality_metrics()

print(f"Overall Quality: {metrics['overall_score']}")
print(f"Engagement: {metrics['engagement_score']}")
print(f"Learning Correlation: {metrics['learning_correlation_score']}")
```

### Bulk Quality Assessment

```python
from knowledge.curator.utilities.quality_assessment import BookmarkQualityAssessment

qa = BookmarkQualityAssessment(portal)
results = qa.assess_all_bookmarks()

print(f"Assessed {results['assessed']} resources")
print(f"Flagged {results['flagged']} for review")
```

### Quality Reporting

```python
# Get report for low-quality resources
report = qa.get_quality_report(max_score=0.4)

for resource in report:
    print(f"{resource['title']}: {resource['metrics']['overall_score']}")
```

### Learning Correlation Analysis

```python
analysis = qa.get_learning_correlation_analysis()

print(f"Resources with knowledge items: {analysis['resources_with_knowledge_items']}")
print(f"Average quality with items: {analysis['average_quality_with_items']}")
print(f"Average quality without items: {analysis['average_quality_without_items']}")
```

## Quality Improvement Recommendations

### For Low-Quality Resources (< 0.4)
1. Add detailed personal notes and insights
2. Extract key quotes from the content
3. Link to relevant knowledge items
4. Associate with learning goals
5. Update read status as you engage with content

### For Medium-Quality Resources (0.4-0.7)
1. Enhance existing notes with deeper analysis
2. Add more relevant knowledge item connections
3. Include supporting evidence in notes
4. Review and update content quality rating

### For High-Quality Resources (> 0.7)
1. Share insights with others
2. Create knowledge items based on key concepts
3. Reference in learning goals and projects
4. Use as examples for quality standards

## Monitoring and Maintenance

### Automated Quality Monitoring
- Run periodic assessments (weekly/monthly)
- Monitor quality trends for declining resources
- Review flagged resources regularly
- Update quality tracking for modified content

### Quality Metrics Dashboard
- Track overall system quality trends
- Identify patterns in high/low quality resources
- Monitor correlation between quality and learning outcomes
- Analyze resource type effectiveness

## Integration Points

### With Knowledge Items
- Quality scores influence recommendation algorithms
- High-quality resources boost related knowledge item scores
- Learning correlation affects knowledge graph weighting

### With Learning Goals
- Resources supporting active goals receive quality boosts
- Quality metrics inform learning path optimization
- Progress tracking influences engagement scores

### With Spaced Repetition
- Quality scores affect review scheduling
- High-quality resources get prioritized for review
- Quality trends influence retention predictions

## Testing

Run quality assessment tests:

```bash
python -m unittest knowledge.curator.tests.test_quality_assessment
```

The test suite covers:
- Quality score calculation accuracy
- Component score calculations
- Quality tracking and history
- Flag management functionality
- Trend analysis
- Edge cases and error handling

## Future Enhancements

### Planned Features
1. Machine learning-based quality prediction
2. User feedback integration for quality scoring
3. Collaborative quality ratings
4. Content freshness auto-detection via web scraping
5. Integration with external quality metrics (citations, social signals)
6. Advanced analytics and quality insights dashboard

### Extension Points
- Custom quality factors via plugins
- Domain-specific quality models
- Integration with external quality assessment services
- Automated content quality improvement suggestions