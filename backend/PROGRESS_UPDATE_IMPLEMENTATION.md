# Learning Goal Progress Update Implementation

## Overview

This document describes the implementation of the `update_learning_goal_progress()` function for subtask 8.3, which provides automatic progress calculation and updates for Learning Goals based on Knowledge Item mastery level changes.

## Implementation Details

### Core Function: `update_learning_goal_progress()`

**Location**: `/src/knowledge/curator/workflow_scripts.py` (lines 1320-1485)

**Purpose**: Automatically updates Learning Goal progress when Knowledge Item mastery levels change, considering weighted progress calculations, dependency chains, and mastery thresholds.

#### Function Signature

```python
def update_learning_goal_progress(knowledge_item=None, updated_mastery_levels=None, 
                                learning_goals=None, trigger_event=None):
```

#### Parameters

- `knowledge_item`: The Knowledge Item whose mastery changed (optional)
- `updated_mastery_levels`: Dict mapping Knowledge Item UIDs to new mastery levels (optional)  
- `learning_goals`: List of Learning Goal objects to update (optional, will find all if not provided)
- `trigger_event`: The event that triggered this update (for logging and tracking)

#### Return Value

Returns a comprehensive dictionary containing:
- `updated_goals`: List of updated Learning Goal objects
- `progress_changes`: Dict mapping goal UID to detailed progress change data
- `total_updated`: Number of goals successfully updated
- `errors`: List of any errors encountered during processing
- `trigger_info`: Metadata about what triggered the update

## Key Features Implemented

### 1. Weighted Progress Calculation

The function leverages the existing `Learning Goal.calculate_overall_progress()` method which:
- Calculates item weights based on graph position and connection types
- Considers distance from start and target items
- Applies connection type multipliers (prerequisites get higher weights)
- Accounts for prerequisite satisfaction percentages

### 2. Dependency Chain Handling

- **Prerequisite Tracking**: Monitors prerequisite completion requirements
- **Mastery Thresholds**: Respects individual Knowledge Item mastery thresholds
- **Connection Strength**: Uses connection strength values to weight relationships
- **Bottleneck Detection**: Identifies items blocking overall progress

### 3. Automatic Trigger Functionality

The function can be triggered in multiple ways:
- **Manual Updates**: Called directly with specific parameters
- **Event-Driven**: Triggered by workflow transitions or mastery changes
- **Batch Processing**: Handles updates for multiple Knowledge Items simultaneously
- **System-Wide Updates**: Can recalculate all Learning Goals based on current states

### 4. Comprehensive Progress Tracking

#### Progress History
- Maintains detailed update history in Learning Goal annotations
- Stores progress snapshots with mastery level data
- Tracks trigger events and timestamps
- Keeps last 50 updates for each Learning Goal

#### Milestone Detection
- Automatically detects progress milestones (25%, 50%, 75%, 90%, 100%)
- Records milestone achievements with metadata
- Logs significant progress events
- Triggers notifications for important thresholds

#### Completion Handling
- Automatically detects when Learning Goals reach 100% completion
- Records completion metadata and timestamps
- Attempts to transition goals to completed workflow state
- Provides comprehensive completion records

## Supporting Functions

### Helper Functions

1. **`_goal_references_knowledge_items()`** (lines 1488-1526)
   - Determines if a Learning Goal references specific Knowledge Items
   - Checks starting items, target items, and connections
   - Used to find affected Learning Goals efficiently

2. **`_store_progress_update_metadata()`** (lines 1529-1581)
   - Stores detailed metadata about each progress update
   - Maintains update history and current progress summaries
   - Enables progress tracking and debugging

3. **`_trigger_progress_milestones()`** (lines 1584-1626)
   - Handles milestone detection and notifications
   - Manages bottleneck alerts and completion events
   - Coordinates follow-up actions

4. **`_record_progress_milestone()`** (lines 1629-1665)
   - Records individual milestone achievements
   - Stores milestone metadata in Learning Goal annotations
   - Enables milestone tracking and reporting

5. **`_record_goal_completion()`** (lines 1668-1707)
   - Handles Learning Goal completion events
   - Records comprehensive completion data
   - Attempts automatic workflow transitions

6. **`get_learning_goal_progress_history()`** (lines 1710-1738)
   - Retrieves progress update history for a Learning Goal
   - Supports pagination and filtering
   - Returns chronologically ordered update records

## Integration Points

### Workflow Integration

The function is integrated with the Plone workflow system:
- **External Methods**: Available in `/instance/Extensions/workflow_scripts.py`
- **Fallback Functions**: Provides no-op fallbacks if import fails
- **Error Handling**: Comprehensive error handling for production use

### Database Integration

- **Persistent Storage**: Uses ZODB persistent objects for all data
- **Transactions**: Proper transaction handling with savepoints
- **Annotations**: Stores metadata in object annotations
- **Catalog Integration**: Works with Plone catalog for efficient queries

## Usage Examples

### 1. Single Knowledge Item Update
```python
# When a Knowledge Item's mastery level changes
result = update_learning_goal_progress(
    knowledge_item=knowledge_item_object,
    trigger_event='mastery_level_changed'
)
```

### 2. Batch Mastery Update
```python
# Update multiple items at once
mastery_data = {
    'item1_uid': 0.85,
    'item2_uid': 0.72,
    'item3_uid': 0.91
}
result = update_learning_goal_progress(
    updated_mastery_levels=mastery_data,
    trigger_event='batch_assessment_complete'
)
```

### 3. System-Wide Recalculation
```python
# Recalculate all Learning Goals based on current Knowledge Item states
result = update_learning_goal_progress()
```

### 4. Specific Learning Goals Update
```python
# Update only specific Learning Goals
result = update_learning_goal_progress(
    learning_goals=[goal1, goal2, goal3],
    trigger_event='manual_refresh'
)
```

## Error Handling

The implementation includes comprehensive error handling:
- **Graceful Degradation**: Continues processing even if individual items fail
- **Detailed Logging**: Extensive logging for debugging and monitoring
- **Error Collection**: Collects and reports all errors encountered
- **Transaction Safety**: Uses savepoints to ensure data consistency

## Performance Considerations

### Optimization Features
- **Selective Updates**: Only updates Learning Goals that reference changed Knowledge Items
- **Batch Processing**: Handles multiple updates efficiently
- **Cached Calculations**: Leverages existing calculation methods
- **Minimal Database Queries**: Optimized catalog queries

### Scalability
- **Incremental Updates**: Supports incremental progress updates
- **Metadata Limitation**: Limits stored history to prevent excessive growth
- **Efficient Lookups**: Uses UIDs for efficient object resolution

## Testing

A comprehensive test script is provided (`test_progress_update.py`) that:
- Verifies function structure and parameters
- Tests basic functionality with mock data
- Validates error handling and edge cases
- Demonstrates usage patterns

## Future Enhancements

### Potential Improvements
1. **Real-time Updates**: WebSocket integration for live progress updates
2. **Progress Visualization**: Enhanced visualization data structures
3. **Notification System**: Configurable notifications for milestones
4. **Analytics Integration**: Progress analytics and reporting features
5. **Caching Layer**: Redis caching for frequently accessed data

### Extension Points
- **Custom Weighting**: Pluggable weighting algorithms
- **External Triggers**: API endpoints for external system integration
- **Reporting**: Progress reporting and dashboard integration
- **Automation**: Automated workflows based on progress thresholds

## Conclusion

The `update_learning_goal_progress()` function provides a comprehensive solution for automatic Learning Goal progress updates based on Knowledge Item mastery changes. It includes:

✅ **Weighted Progress Calculations** - Considers item importance and dependencies  
✅ **Dependency Chain Handling** - Respects prerequisites and mastery thresholds  
✅ **Automatic Trigger Functionality** - Supports multiple trigger mechanisms  
✅ **Comprehensive Progress Tracking** - Detailed history and milestone detection  
✅ **Production-Ready Error Handling** - Robust error handling and logging  
✅ **Performance Optimization** - Efficient updates and scalable design  

The implementation is ready for integration with the existing workflow system and provides a solid foundation for advanced learning management features.