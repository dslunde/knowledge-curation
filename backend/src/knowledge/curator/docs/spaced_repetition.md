# Spaced Repetition System Documentation

## Overview

The Knowledge Management System includes a comprehensive spaced repetition engine based on the SM-2 (SuperMemo 2) algorithm. This system helps users retain information more effectively by scheduling reviews at optimal intervals based on performance.

## Key Features

### 1. SM-2 Algorithm Implementation
- **Adaptive Intervals**: Review intervals adjust based on recall quality (0-5 scale)
- **Ease Factor**: Tracks item difficulty (1.3-2.5, lower = harder)
- **Forgetting Curve**: Models memory decay over time
- **Optimal Scheduling**: Calculates best review times to maintain retention

### 2. Content Integration
- **Behavior-Based**: Available on all knowledge content types via `ISpacedRepetition` behavior
- **Automatic Tracking**: Review history and performance metrics stored with each item
- **Flexible Activation**: Can be enabled/disabled per item

### 3. Review Interface
- **Review Queue**: Prioritized list of items due for review
- **Review Cards**: Focused review interface with question/answer phases
- **Keyboard Shortcuts**: Efficient review with keyboard controls
- **Progress Tracking**: Real-time session progress and statistics

### 4. Performance Analytics
- **Comprehensive Metrics**: Success rate, streaks, learning velocity
- **Forgetting Curves**: Visualize retention over time
- **Time Patterns**: Identify optimal review times
- **Adaptive Scheduling**: Personalized review schedules based on performance

## How It Works

### The SM-2 Algorithm

The system uses the SuperMemo 2 algorithm to calculate optimal review intervals:

1. **Quality Rating** (0-5 scale):
   - 0: Complete blackout
   - 1: Incorrect, but remembered when seeing answer
   - 2: Incorrect, but close
   - 3: Correct with difficulty
   - 4: Correct with hesitation
   - 5: Perfect response

2. **Interval Calculation**:
   - First review: 1 day
   - Second review: 6 days
   - Subsequent: Previous interval × ease factor

3. **Ease Factor Updates**:
   - Increases for good performance (quality ≥ 4)
   - Decreases for poor performance (quality = 3)
   - Stays constant for failures (quality < 3)

### Forgetting Curve

The system models memory retention using the Ebbinghaus forgetting curve:

```
Retention = e^(-t/S)
```

Where:
- t = time elapsed since last review
- S = stability factor (based on interval, ease factor, and repetitions)

### Review Scheduling

Items are prioritized for review based on:
1. **Urgency**: Days overdue
2. **Retention**: Current retention probability
3. **Difficulty**: Ease factor
4. **User Settings**: Daily limits, order preference

## User Guide

### Starting Reviews

1. Navigate to the Review Queue (`/@@review-queue`)
2. View items due for review with retention indicators
3. Click "Start Review" on any item

### Review Process

1. **Question Phase**: Read the question/prompt
2. **Recall**: Try to remember the answer
3. **Show Answer**: Click or press spacebar
4. **Rate Quality**: Select 0-5 based on recall quality
5. **Next Item**: Automatically proceed to next review

### Keyboard Shortcuts

- **Space**: Show answer
- **0-5**: Rate quality
- **Escape**: Return to queue

### Performance Dashboard

Access performance metrics at `/@@review-performance`:
- Review statistics over time
- Quality distribution charts
- Forgetting curves for items
- Workload forecast

### Statistics Dashboard

View detailed analytics at `/@@review-statistics`:
- Adaptive learning schedule
- Items at risk of being forgotten
- Learning velocity metrics
- Performance by time patterns

## Configuration

### User Settings

Configure review preferences:
- **Daily Review Limit**: Maximum reviews per day (default: 20)
- **New Items Per Day**: Limit for new items (default: 5)
- **Review Order**: urgency, random, oldest, difficulty, interleaved
- **Break Settings**: Interval and duration for breaks
- **Notification Settings**: Review reminders

### Content Configuration

Enable spaced repetition on content:
1. Edit content item
2. Navigate to "Spaced Repetition" fieldset
3. Check "Enable Spaced Repetition"

## API Usage

### REST API Endpoints

```
GET /@@API/spaced-repetition
  - Get items due for review

POST /@@API/spaced-repetition/review
  - Submit review result
  - Body: {uid, quality, time_spent}

GET /@@API/spaced-repetition/schedule
  - Get review schedule forecast

GET /@@API/spaced-repetition/performance
  - Get performance statistics

GET/POST /@@API/spaced-repetition/settings
  - Get/update user settings
```

### Python API

```python
from knowledge.curator.repetition.utilities import ReviewUtilities

# Get items due for review
items = ReviewUtilities.get_items_due_for_review()

# Handle review response
result = ReviewUtilities.handle_review_response(
    uid='item-uid',
    quality=4,
    time_spent=60
)

# Get adaptive schedule
schedule = ReviewUtilities.get_adaptive_schedule()

# Get items at risk
at_risk = ReviewUtilities.get_items_at_risk(
    retention_threshold=0.8
)
```

## Best Practices

### Creating Reviewable Content

1. **Clear Questions**: Use descriptive titles that work as prompts
2. **Concise Answers**: Key findings or summaries work best
3. **Atomic Information**: Break complex topics into smaller pieces
4. **Context**: Include enough description for understanding

### Review Habits

1. **Consistency**: Review daily at the same time
2. **Honesty**: Rate quality accurately for optimal intervals
3. **Focus**: Minimize distractions during reviews
4. **Breaks**: Take breaks every 10-15 reviews

### Optimizing Performance

1. **Monitor Statistics**: Check performance dashboard regularly
2. **Adjust Settings**: Customize based on your schedule
3. **Review Promptly**: Don't let items become overdue
4. **Quality Over Quantity**: Focus on understanding, not speed

## Troubleshooting

### Common Issues

**Items not appearing in queue:**
- Check if spaced repetition is enabled
- Verify items have been reviewed at least once
- Check daily review limit hasn't been reached

**Poor retention rates:**
- Review more frequently (adjust settings)
- Break down complex items
- Ensure quality ratings are accurate

**Overwhelming workload:**
- Reduce new items per day
- Increase daily review limit temporarily
- Use bulk reschedule for overdue items

## Technical Details

### Data Storage

Review data is stored using:
- **Persistent Attributes**: Core SR data on content objects
- **Review History**: PersistentList of review sessions
- **User Settings**: Member properties

### Performance Optimization

- **Catalog Queries**: Efficient filtering of due items
- **Batch Processing**: Limited queue sizes
- **Caching**: Review calculations cached where appropriate

### Extension Points

The system is designed for extensibility:
- **Custom Algorithms**: Implement alternative spacing algorithms
- **Review Interfaces**: Create specialized review UIs
- **Analytics**: Add custom performance metrics
- **Integrations**: Connect with external learning systems