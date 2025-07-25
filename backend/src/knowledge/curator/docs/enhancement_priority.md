# Enhancement Priority System

## Overview

The Knowledge Curator system implements an automatic enhancement workflow priority system that ensures Knowledge Items receive priority processing in all enhancement operations. This system manages AI-powered enhancements including content analysis, embedding generation, connection suggestions, and concept extraction.

## Priority Calculation

### Base Priority Scores

Content types are assigned base priority scores:

- **Knowledge Items**: 100 (highest priority)
- **BookmarkPlus**: 75
- **ResearchNote**: 60
- **LearningGoal**: 50
- **ProjectLog**: 40
- **Other types**: 30

### Priority Factors

The final priority score is calculated using multiple factors:

1. **Workflow State Multiplier**
   - Knowledge Items in "process" state: 2.0x multiplier
   - Knowledge Items in "connect" state: 1.5x multiplier
   - Published items receive lower priority (0.8x)

2. **Age Decay Factor**
   - Newer items receive higher priority
   - Knowledge Items decay at 5% per day (0.95 factor)
   - Other types decay faster

3. **AI Confidence Boost**
   - Items with low AI confidence (<0.7) receive 1.5x boost
   - Ensures re-analysis of uncertain content

4. **Special Factors (Knowledge Items only)**
   - No AI summary: 1.5x boost
   - No extracted concepts: 1.3x boost
   - No connections: 1.2x boost

### Priority Formula

```python
priority = base_priority * workflow_multiplier * age_decay * confidence_boost * special_factors
```

## Queue Management

### Processing Order

1. Knowledge Items are always processed first
2. At least 50% of each batch must be Knowledge Items (if available)
3. Remaining capacity is filled with other high-priority items

### Batch Sizes

- Default: 20 items
- Knowledge Items only: 10 items
- High priority batch: 30 items
- Scheduled processing: 50 items

### Queue Operations

#### Adding to Queue

Items are automatically queued when:
- Entering the "process" workflow state
- Requesting connection suggestions
- Failing validation before publishing
- Manually triggered via API or UI

#### Processing Queue

The queue processor:
1. Sorts all items by priority score
2. Selects Knowledge Items first
3. Fills remaining batch with other items
4. Processes items in priority order

## API Endpoints

### REST API

```
GET /@enhancement-queue
  - List queue items with filtering
  - Parameters: limit, content_type, min_priority

POST /@enhancement-queue
  - Add items to queue
  - Body: {uids: [...], operation: "full", priority_boost: 1.5}

POST /@enhancement-queue/process
  - Process batch of items
  - Body: {batch_size: 20, content_type: "KnowledgeItem"}

GET /@enhancement-queue/stats
  - Get queue statistics and recommendations

GET /@enhancement-queue/priority?uid=...
  - Calculate priority for specific item

DELETE /@enhancement-queue/clear
  - Clear entire queue (admin only)
```

### Python API

```python
from knowledge.curator.workflow_scripts import (
    queue_for_enhancement,
    calculate_enhancement_priority,
    process_enhancement_queue,
    get_queue_statistics
)

# Queue a Knowledge Item with boosted priority
priority = calculate_enhancement_priority(obj) * 1.5
queue_for_enhancement(obj, operation="full", priority_override=priority)

# Process Knowledge Items only
process_enhancement_queue(batch_size=10, content_type_filter="KnowledgeItem")

# Get queue statistics
stats = get_queue_statistics()
```

## UI Access

### Enhancement Queue Management

Access the queue management interface at:
```
http://your-site/@@enhancement-queue
```

Features:
- View separate queues for Knowledge Items and other content
- Process items individually or in batches
- View real-time statistics
- Clear or requeue items

### Batch Enhancement

For bulk operations:
```
http://your-site/@@batch-enhancement?uids=uid1,uid2,uid3
```

## Scheduled Processing

### Automatic Processing

Configure scheduled processing using Plone's clock server or cron:

```python
from knowledge.curator.tasks.enhancement_scheduler import run_enhancement_scheduler

# Run every 30 minutes
run_enhancement_scheduler(context)
```

### Scheduler Features

1. **Priority Processing**
   - Processes high-priority items first
   - Ensures Knowledge Items quota

2. **Stale Entry Cleanup**
   - Removes entries older than 7 days
   - Cleans failed entries after 3 attempts

3. **Recent Item Boost**
   - Boosts priority of Knowledge Items created in last 24 hours
   - Ensures new content is processed quickly

## Configuration

### Environment Variables

```bash
# Override Knowledge Item base priority
KNOWLEDGE_ITEM_PRIORITY=150

# Set batch sizes
VECTOR_BATCH_SIZE=50
EMBEDDING_BATCH_SIZE=32
```

### Registry Settings

```
knowledge.curator.enhancement.knowledge_item_priority: 100
knowledge.curator.enhancement.knowledge_item_ratio: 0.5
knowledge.curator.enhancement.batch_size: 20
```

## Monitoring and Troubleshooting

### Queue Statistics

Monitor queue health:
- Total items in queue
- Knowledge Items count
- Average priority score
- Oldest item age
- Processing recommendations

### Common Issues

1. **Queue Growing Too Large**
   - Increase batch size
   - Run scheduler more frequently
   - Check for processing errors

2. **Knowledge Items Not Prioritized**
   - Verify priority configuration
   - Check workflow states
   - Review special factors

3. **Processing Failures**
   - Check logs for errors
   - Verify AI service connectivity
   - Review failed items in queue

### Logging

Enhancement operations are logged to:
```
knowledge.curator.workflow
knowledge.curator.scheduler
```

Enable debug logging:
```python
import logging
logging.getLogger('knowledge.curator.workflow').setLevel(logging.DEBUG)
```

## Best Practices

1. **Regular Monitoring**
   - Check queue statistics daily
   - Monitor Knowledge Items backlog
   - Review processing errors

2. **Batch Processing**
   - Process during low-traffic periods
   - Use appropriate batch sizes
   - Monitor system resources

3. **Priority Tuning**
   - Adjust base priorities based on content volume
   - Tune decay factors for your workflow
   - Configure special factors as needed

4. **Integration**
   - Hook into content creation events
   - Automate workflow transitions
   - Use API for external integrations