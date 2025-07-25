# Knowledge Item Validation System

## Overview

The Knowledge Item content type includes comprehensive validation rules to ensure data integrity and consistency. Validation occurs at multiple levels:

1. **Field-level validation** - Individual field constraints
2. **Cross-field validation** - Invariants that check multiple fields
3. **Relationship validation** - Ensures graph integrity

## Field Validators

### Numeric Range Validators

#### `validate_mastery_threshold(value)`
- Ensures value is between 0.0 and 1.0
- Allows None (optional field)
- Used for: `mastery_threshold` field

#### `validate_learning_progress(value)`
- Ensures value is between 0.0 and 1.0
- Allows None (optional field)
- Used for: `learning_progress` field

### Text Length Validators

#### `validate_title_length(value)`
- Minimum: 3 characters
- Maximum: 200 characters
- Required field
- Used for: `title` field

#### `validate_description_length(value)`
- Minimum: 10 characters
- Maximum: 2000 characters
- Required field
- Used for: `description` field

#### `validate_content_length(value)`
- Minimum: 10 characters
- Maximum: 1,000,000 characters
- Strips HTML tags for accurate counting
- Required field
- Used for: `content` field

### List Validators

#### `validate_atomic_concepts(value)`
- Requires at least one concept
- Each concept: 3-200 characters
- Alphanumeric + common punctuation only
- No duplicates (case-insensitive)
- Used for: `atomic_concepts` field

#### `validate_tags(value)`
- Each tag: 2-50 characters
- Alphanumeric, spaces, hyphens, underscores only
- No duplicates (case-insensitive)
- Optional field
- Used for: `tags` field

#### `validate_embedding_vector(value)`
- Must be a list of floats
- Common dimensions: 128, 256, 384, 512, 768, 1024, 1536
- Values expected between -100 and 100
- Optional field
- Used for: `embedding_vector` field

### Vocabulary Validators

#### `validate_knowledge_type(value)`
- Valid values: "factual", "conceptual", "procedural", "metacognitive"
- Required field
- Used for: `knowledge_type` field

#### `validate_difficulty_level(value)`
- Valid values: "beginner", "intermediate", "advanced", "expert"
- Optional field
- Used for: `difficulty_level` field

### Reference Validators

#### `validate_uid_reference(value)`
- Ensures UID points to existing Knowledge Item
- Checks catalog for existence
- Used for individual UID validation

#### `validate_uid_references_list(value)`
- Validates list of UIDs
- No duplicates allowed
- Each UID must exist
- Used for: `prerequisite_items`, `enables_items` fields

### Relationship Validators

#### `validate_no_self_reference(context, value)`
- Prevents Knowledge Item from referencing itself
- Requires context (the item being validated)
- Used for: `prerequisite_items`, `enables_items` fields

#### `validate_circular_dependencies(context, prerequisite_uids)`
- Prevents circular dependency chains
- Recursively checks prerequisite graph
- Used for: `prerequisite_items` field

## Invariant Validators

### `validate_prerequisite_enables_consistency(data)`
- Ensures no overlap between prerequisite and enables lists
- A Knowledge Item cannot both require and enable the same items
- Applied to entire form data

### `validate_mastery_threshold_progress_consistency(data)`
- Validates both values are in valid range (0.0-1.0)
- Progress can exceed threshold (indicates mastery)
- Applied to entire form data

## Usage in Content Type

### Automatic Validation

When creating or editing Knowledge Items through the Plone UI:
- Field validators run automatically on form submission
- Invariants check cross-field consistency
- Validation errors display user-friendly messages

### Programmatic Validation

The Knowledge Item class provides methods for manual validation:

```python
# Validate all fields
item = api.content.get(UID='...')
validation_result = item.validate_all_fields()
if not validation_result['valid']:
    for field, error in validation_result['errors'].items():
        print(f"{field}: {error}")

# Set field with validation
result = item.set_field_value_with_validation('mastery_threshold', 0.85)
if not result['success']:
    print(f"Validation error: {result['error']}")

# Validate relationships only
rel_result = item.validate_relationships()
if not rel_result['valid']:
    for error in rel_result['errors']:
        print(error)
```

### Adding Prerequisites with Validation

The `add_prerequisite` method includes built-in circular dependency checking:

```python
try:
    item.add_prerequisite(prerequisite_uid)
except ValueError as e:
    # Handle circular dependency error
    print(str(e))
```

## Error Messages

All validators provide descriptive error messages:
- Include field name and constraint details
- Localized using Plone's translation system
- Show specific values that caused the error

## Testing

Comprehensive test coverage in `test_knowledge_item_validators.py`:
- Unit tests for each validator
- Boundary condition testing
- Invalid input handling
- Cross-field validation scenarios

## Extending Validation

To add new validators:

1. Add validator function to `validators.py`
2. Add constraint to field in `interfaces.py`
3. Update field validators map in `knowledge_item.py`
4. Add unit tests
5. Update this documentation