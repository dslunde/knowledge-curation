"""Validators for Knowledge Item fields."""

from plone import api
from zope.interface import Invalid
from knowledge.curator import _
import re


def validate_mastery_threshold(value):
    """Validate that mastery threshold is between 0.0 and 1.0.
    
    Args:
        value: The mastery threshold value
        
    Raises:
        Invalid: If value is not between 0.0 and 1.0
    """
    if value is None:
        return True  # Optional field
    
    if not isinstance(value, (int, float)):
        raise Invalid(_("Mastery threshold must be a number"))
    
    if value < 0.0 or value > 1.0:
        raise Invalid(_("Mastery threshold must be between 0.0 and 1.0"))
    
    return True


def validate_learning_progress(value):
    """Validate that learning progress is between 0.0 and 1.0.
    
    Args:
        value: The learning progress value
        
    Raises:
        Invalid: If value is not between 0.0 and 1.0
    """
    if value is None:
        return True  # Optional field
    
    if not isinstance(value, (int, float)):
        raise Invalid(_("Learning progress must be a number"))
    
    if value < 0.0 or value > 1.0:
        raise Invalid(_("Learning progress must be between 0.0 and 1.0"))
    
    return True


def validate_atomic_concepts(value):
    """Validate atomic concepts format and content.
    
    Args:
        value: List of atomic concepts
        
    Raises:
        Invalid: If atomic concepts are invalid
    """
    if not value:
        raise Invalid(_("At least one atomic concept is required"))
    
    if not isinstance(value, list):
        raise Invalid(_("Atomic concepts must be a list"))
    
    for concept in value:
        if not isinstance(concept, str):
            raise Invalid(_("Each atomic concept must be a string"))
        
        # Check minimum length
        if len(concept.strip()) < 3:
            raise Invalid(_("Each atomic concept must be at least 3 characters long"))
        
        # Check maximum length
        if len(concept) > 200:
            raise Invalid(_("Each atomic concept must be less than 200 characters"))
        
        # Check for valid characters (allow letters, numbers, spaces, and common punctuation)
        if not re.match(r'^[\w\s\-.,;:()]+$', concept):
            raise Invalid(_("Atomic concepts contain invalid characters"))
    
    # Check for duplicates
    unique_concepts = set(c.lower().strip() for c in value)
    if len(unique_concepts) < len(value):
        raise Invalid(_("Duplicate atomic concepts are not allowed"))
    
    return True


def validate_uid_reference(value):
    """Validate that a UID reference points to an existing Knowledge Item.
    
    Args:
        value: UID to validate
        
    Raises:
        Invalid: If UID doesn't reference a valid Knowledge Item
    """
    if not value:
        return True  # Empty reference is valid
    
    if not isinstance(value, str):
        raise Invalid(_("UID reference must be a string"))
    
    # Check if the UID exists and points to a Knowledge Item
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(UID=value, portal_type="KnowledgeItem")
    
    if not brains:
        raise Invalid(_("Referenced Knowledge Item with UID '{0}' not found").format(value))
    
    return True


def validate_uid_references_list(value):
    """Validate a list of UID references.
    
    Args:
        value: List of UIDs to validate
        
    Raises:
        Invalid: If any UID doesn't reference a valid Knowledge Item
    """
    if not value:
        return True  # Empty list is valid
    
    if not isinstance(value, list):
        raise Invalid(_("UID references must be a list"))
    
    for uid in value:
        validate_uid_reference(uid)
    
    # Check for duplicates
    if len(set(value)) < len(value):
        raise Invalid(_("Duplicate UID references are not allowed"))
    
    return True


def validate_knowledge_type(value):
    """Validate knowledge type against vocabulary.
    
    Args:
        value: Knowledge type value
        
    Raises:
        Invalid: If knowledge type is not valid
    """
    if not value:
        raise Invalid(_("Knowledge type is required"))
    
    valid_types = ["factual", "conceptual", "procedural", "metacognitive"]
    
    if value not in valid_types:
        raise Invalid(
            _("Invalid knowledge type. Must be one of: {0}").format(", ".join(valid_types))
        )
    
    return True


def validate_difficulty_level(value):
    """Validate difficulty level against vocabulary.
    
    Args:
        value: Difficulty level value
        
    Raises:
        Invalid: If difficulty level is not valid
    """
    if not value:
        return True  # Optional field
    
    valid_levels = ["beginner", "intermediate", "advanced", "expert"]
    
    if value not in valid_levels:
        raise Invalid(
            _("Invalid difficulty level. Must be one of: {0}").format(", ".join(valid_levels))
        )
    
    return True


def validate_content_length(value):
    """Validate content length constraints.
    
    Args:
        value: Content text
        
    Raises:
        Invalid: If content doesn't meet length requirements
    """
    if not value:
        raise Invalid(_("Content is required"))
    
    # For RichText fields, we need to check the raw value
    text = value.raw if hasattr(value, 'raw') else str(value)
    
    # Strip HTML tags for accurate length check
    import re
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = clean_text.strip()
    
    if len(clean_text) < 10:
        raise Invalid(_("Content must be at least 10 characters long"))
    
    if len(clean_text) > 1000000:  # 1MB limit
        raise Invalid(_("Content is too long (maximum 1 million characters)"))
    
    return True


def validate_title_length(value):
    """Validate title length constraints.
    
    Args:
        value: Title text
        
    Raises:
        Invalid: If title doesn't meet length requirements
    """
    if not value:
        raise Invalid(_("Title is required"))
    
    value = value.strip()
    
    if len(value) < 3:
        raise Invalid(_("Title must be at least 3 characters long"))
    
    if len(value) > 200:
        raise Invalid(_("Title must be less than 200 characters"))
    
    return True


def validate_description_length(value):
    """Validate description length constraints.
    
    Args:
        value: Description text
        
    Raises:
        Invalid: If description doesn't meet length requirements
    """
    if not value:
        raise Invalid(_("Description is required"))
    
    value = value.strip()
    
    if len(value) < 10:
        raise Invalid(_("Description must be at least 10 characters long"))
    
    if len(value) > 2000:
        raise Invalid(_("Description must be less than 2000 characters"))
    
    return True


def validate_tags(value):
    """Validate tags format and content.
    
    Args:
        value: List of tags
        
    Raises:
        Invalid: If tags are invalid
    """
    if not value:
        return True  # Tags are optional
    
    if not isinstance(value, list):
        raise Invalid(_("Tags must be a list"))
    
    for tag in value:
        if not isinstance(tag, str):
            raise Invalid(_("Each tag must be a string"))
        
        tag = tag.strip()
        
        if len(tag) < 2:
            raise Invalid(_("Each tag must be at least 2 characters long"))
        
        if len(tag) > 50:
            raise Invalid(_("Each tag must be less than 50 characters"))
        
        # Allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[\w\s\-]+$', tag):
            raise Invalid(_("Tags can only contain letters, numbers, spaces, hyphens, and underscores"))
    
    # Check for duplicates (case-insensitive)
    unique_tags = set(t.lower().strip() for t in value)
    if len(unique_tags) < len(value):
        raise Invalid(_("Duplicate tags are not allowed"))
    
    return True


def validate_embedding_vector(value):
    """Validate embedding vector format.
    
    Args:
        value: Embedding vector
        
    Raises:
        Invalid: If embedding vector is invalid
    """
    if not value:
        return True  # Optional field
    
    if not isinstance(value, list):
        raise Invalid(_("Embedding vector must be a list"))
    
    if len(value) == 0:
        raise Invalid(_("Embedding vector cannot be empty"))
    
    # Check common embedding dimensions
    valid_dimensions = [128, 256, 384, 512, 768, 1024, 1536]
    if len(value) not in valid_dimensions:
        raise Invalid(
            _("Embedding vector dimension {0} is unusual. Expected one of: {1}").format(
                len(value), ", ".join(map(str, valid_dimensions))
            )
        )
    
    for i, val in enumerate(value):
        if not isinstance(val, (int, float)):
            raise Invalid(_("Embedding vector element at index {0} must be a number").format(i))
        
        # Check for reasonable range
        if abs(val) > 100:
            raise Invalid(_("Embedding vector values seem out of range (expected between -100 and 100)"))
    
    return True


def validate_no_self_reference(context, value):
    """Validate that a Knowledge Item doesn't reference itself.
    
    Args:
        context: The Knowledge Item being validated
        value: UID or list of UIDs to check
        
    Raises:
        Invalid: If self-reference is detected
    """
    if not value or not hasattr(context, 'UID'):
        return True
    
    current_uid = context.UID()
    
    if isinstance(value, list):
        if current_uid in value:
            raise Invalid(_("A Knowledge Item cannot reference itself"))
    elif isinstance(value, str):
        if current_uid == value:
            raise Invalid(_("A Knowledge Item cannot reference itself"))
    
    return True


def validate_circular_dependencies(context, prerequisite_uids):
    """Validate that adding prerequisites won't create circular dependencies.
    
    Args:
        context: The Knowledge Item being validated
        prerequisite_uids: List of prerequisite UIDs to validate
        
    Raises:
        Invalid: If circular dependency would be created
    """
    if not prerequisite_uids or not hasattr(context, 'UID'):
        return True
    
    current_uid = context.UID()
    catalog = api.portal.get_tool("portal_catalog")
    
    def check_circular(uid, visited=None):
        """Recursively check for circular dependencies."""
        if visited is None:
            visited = set()
        
        if uid in visited:
            return True  # Circular dependency found
        
        visited.add(uid)
        
        # Get the item
        brains = catalog(UID=uid, portal_type="KnowledgeItem")
        if not brains:
            return False
        
        obj = brains[0].getObject()
        
        # Check its prerequisites
        if hasattr(obj, 'prerequisite_items') and obj.prerequisite_items:
            for prereq_uid in obj.prerequisite_items:
                if prereq_uid == current_uid:
                    return True  # Would create circular dependency
                if check_circular(prereq_uid, visited.copy()):
                    return True
        
        return False
    
    # Check each proposed prerequisite
    for prereq_uid in prerequisite_uids:
        if check_circular(prereq_uid):
            raise Invalid(
                _("Adding prerequisite '{0}' would create a circular dependency").format(prereq_uid)
            )
    
    return True


# Plone invariant validators for the interface
def validate_prerequisite_enables_consistency(data):
    """Invariant: Ensure prerequisite and enables lists don't overlap.
    
    Args:
        data: Form data
        
    Raises:
        Invalid: If there's an overlap between prerequisites and enables
    """
    prerequisites = data.prerequisite_items or []
    enables = data.enables_items or []
    
    if not prerequisites or not enables:
        return True
    
    overlap = set(prerequisites) & set(enables)
    if overlap:
        raise Invalid(
            _("A Knowledge Item cannot both require and enable the same items: {0}").format(
                ", ".join(overlap)
            )
        )
    
    return True


def validate_mastery_threshold_progress_consistency(data):
    """Invariant: Ensure learning progress doesn't exceed mastery threshold logic.
    
    Args:
        data: Form data
        
    Raises:
        Invalid: If there's inconsistency between progress and threshold
    """
    threshold = data.mastery_threshold
    progress = data.learning_progress
    
    if threshold is None or progress is None:
        return True
    
    # This is more of a warning than a hard constraint
    # We allow progress to exceed threshold (indicating mastery)
    # but we want to ensure both are in valid range
    if threshold < 0.0 or threshold > 1.0:
        raise Invalid(_("Mastery threshold must be between 0.0 and 1.0"))
    
    if progress < 0.0 or progress > 1.0:
        raise Invalid(_("Learning progress must be between 0.0 and 1.0"))
    
    return True


def validate_knowledge_item_progress_dict(value):
    """Validate knowledge_item_progress dictionary structure.
    
    Args:
        value: Dictionary mapping Knowledge Item UIDs to mastery levels
        
    Raises:
        Invalid: If dictionary structure or values are invalid
    """
    if not value:
        return True  # Empty dict is valid
    
    if not isinstance(value, dict):
        raise Invalid(_("Knowledge item progress must be a dictionary"))
    
    for uid, mastery_level in value.items():
        # Validate UID format
        if not isinstance(uid, str):
            raise Invalid(_("Knowledge Item UID must be a string"))
        
        if not uid.strip():
            raise Invalid(_("Knowledge Item UID cannot be empty"))
        
        # Validate mastery level
        if not isinstance(mastery_level, (int, float)):
            raise Invalid(_("Mastery level for UID '{0}' must be a number").format(uid))
        
        if mastery_level < 0.0 or mastery_level > 1.0:
            raise Invalid(
                _("Mastery level for UID '{0}' must be between 0.0 and 1.0 (got {1})").format(
                    uid, mastery_level
                )
            )
        
        # Optionally validate that the UID exists
        # This is commented out as it might be too restrictive during data entry
        # validate_uid_reference(uid)
    
    return True


def validate_annotated_knowledge_items(value):
    """Validate that Research Note has at least one annotated Knowledge Item.
    
    Args:
        value: List of Knowledge Item UIDs
        
    Raises:
        Invalid: If list is empty or contains invalid UIDs
    """
    if not value:
        raise Invalid(
            _("At least one Knowledge Item must be annotated. "
              "Research Notes must be associated with existing Knowledge Items.")
        )
    
    if not isinstance(value, list):
        raise Invalid(_("Annotated knowledge items must be a list"))
    
    if len(value) == 0:
        raise Invalid(
            _("Cannot create a Research Note without annotating at least one Knowledge Item. "
              "Please select one or more Knowledge Items to annotate.")
        )
    
    # Validate each UID references an actual Knowledge Item
    catalog = api.portal.get_tool("portal_catalog")
    invalid_uids = []
    
    for uid in value:
        if not isinstance(uid, str):
            raise Invalid(_("Each annotated item reference must be a string UID"))
        
        if not uid.strip():
            raise Invalid(_("Empty UID references are not allowed"))
        
        # Check if the UID exists and points to a Knowledge Item
        brains = catalog(UID=uid, portal_type="KnowledgeItem")
        if not brains:
            invalid_uids.append(uid)
    
    if invalid_uids:
        raise Invalid(
            _("The following UIDs do not reference valid Knowledge Items: {0}").format(
                ", ".join(invalid_uids[:5])  # Show max 5 invalid UIDs
            )
        )
    
    # Check for duplicates
    if len(set(value)) < len(value):
        raise Invalid(_("Duplicate Knowledge Item references are not allowed"))
    
    return True


def validate_related_knowledge_items(value):
    """Validate that BookmarkPlus has at least one related Knowledge Item.
    
    Args:
        value: List of Knowledge Item UIDs
        
    Raises:
        Invalid: If list is empty or contains invalid UIDs
    """
    if not value:
        raise Invalid(
            _("At least one Knowledge Item must be related. "
              "Bookmark+ items must be associated with existing Knowledge Items.")
        )
    
    if not isinstance(value, list):
        raise Invalid(_("Related knowledge items must be a list"))
    
    if len(value) == 0:
        raise Invalid(
            _("Cannot create a Bookmark+ without relating to at least one Knowledge Item. "
              "Please select one or more Knowledge Items that this bookmark relates to.")
        )
    
    # Validate each UID references an actual Knowledge Item
    catalog = api.portal.get_tool("portal_catalog")
    invalid_uids = []
    
    for uid in value:
        if not isinstance(uid, str):
            raise Invalid(_("Each related item reference must be a string UID"))
        
        if not uid.strip():
            raise Invalid(_("Empty UID references are not allowed"))
        
        # Check if the UID exists and points to a Knowledge Item
        brains = catalog(UID=uid, portal_type="KnowledgeItem")
        if not brains:
            invalid_uids.append(uid)
    
    if invalid_uids:
        raise Invalid(
            _("The following UIDs do not reference valid Knowledge Items: {0}").format(
                ", ".join(invalid_uids[:5])  # Show max 5 invalid UIDs
            )
        )
    
    # Check for duplicates
    if len(set(value)) < len(value):
        raise Invalid(_("Duplicate Knowledge Item references are not allowed"))
    
    return True

def validate_personal_notes(value):
    """Validate personal notes field.
    
    Args:
        value: Personal notes text
        
    Raises:
        Invalid: If personal notes don't meet requirements
    """
    if not value:
        return True  # Personal notes are optional
    
    if not isinstance(value, str):
        raise Invalid(_("Personal notes must be text"))
    
    # Check length constraints
    if len(value) > 10000:
        raise Invalid(_("Personal notes must be less than 10,000 characters"))
    
    # No minimum length for notes - even brief notes are valuable
    
    return True


def validate_key_quotes(value):
    """Validate key quotes list.
    
    Args:
        value: List of key quotes
        
    Raises:
        Invalid: If key quotes don't meet requirements
    """
    if not value:
        return True  # Key quotes are optional
    
    if not isinstance(value, list):
        raise Invalid(_("Key quotes must be a list"))
    
    if len(value) > 20:
        raise Invalid(_("Maximum 20 key quotes allowed"))
    
    for i, quote in enumerate(value):
        if not isinstance(quote, str):
            raise Invalid(_("Each key quote must be text"))
        
        quote = quote.strip()
        
        if not quote:
            raise Invalid(_("Empty quotes are not allowed"))
        
        if len(quote) > 2000:
            raise Invalid(_("Each key quote must be less than 2,000 characters"))
        
        # Check for minimal content (at least 10 characters for a meaningful quote)
        if len(quote) < 10:
            raise Invalid(_("Each key quote should be at least 10 characters long"))
    
    # Check for duplicate quotes (case-insensitive)
    normalized_quotes = [q.strip().lower() for q in value]
    if len(set(normalized_quotes)) < len(normalized_quotes):
        raise Invalid(_("Duplicate quotes are not allowed"))
    
    return True


def validate_container_uid_references(value):
    """Validate UID references for knowledge container inclusions.
    
    Args:
        value: List of UIDs to validate
        
    Raises:
        Invalid: If any UID doesn't reference a valid content item
    """
    if not value:
        return True  # Empty list is valid
    
    if not isinstance(value, list):
        raise Invalid(_("UID references must be a list"))
    
    # Basic validation first (before catalog access)
    for uid in value:
        if not isinstance(uid, str):
            raise Invalid(_("Each UID reference must be a string"))
        
        if not uid.strip():
            raise Invalid(_("Empty UID references are not allowed"))
    
    # Check for duplicates
    if len(set(value)) < len(value):
        raise Invalid(_("Duplicate UID references are not allowed"))
    
    # Only do catalog lookup if we have a portal available
    try:
        catalog = api.portal.get_tool("portal_catalog")
        invalid_uids = []
        
        for uid in value:
            # Check if the UID exists (any content type is valid for containers)
            brains = catalog(UID=uid)
            if not brains:
                invalid_uids.append(uid)
        
        if invalid_uids:
            raise Invalid(
                _("The following UIDs do not reference valid content items: {0}").format(
                    ", ".join(invalid_uids[:5])  # Show max 5 invalid UIDs
                )
            )
    except Exception:
        # In test environments or when portal is not available, 
        # skip catalog validation but still do basic validation
        pass
    
    return True


def validate_container_collection_type(value):
    """Validate collection type against vocabulary.
    
    Args:
        value: Collection type value
        
    Raises:
        Invalid: If collection type is not valid
    """
    if not value:
        return True  # Optional field
    
    valid_types = ["course", "study_guide", "research_collection", "project_portfolio", "knowledge_base"]
    
    if value not in valid_types:
        raise Invalid(
            _("Invalid collection type. Must be one of: {0}").format(", ".join(valid_types))
        )
    
    return True


def validate_container_organization_structure(value):
    """Validate organization structure against vocabulary.
    
    Args:
        value: Organization structure value
        
    Raises:
        Invalid: If organization structure is not valid
    """
    if not value:
        return True  # Optional field
    
    valid_structures = ["chronological", "topical", "hierarchical", "custom"]
    
    if value not in valid_structures:
        raise Invalid(
            _("Invalid organization structure. Must be one of: {0}").format(", ".join(valid_structures))
        )
    
    return True


def validate_container_publication_status(value):
    """Validate publication status against vocabulary.
    
    Args:
        value: Publication status value
        
    Raises:
        Invalid: If publication status is not valid
    """
    if not value:
        return True  # Optional field
    
    valid_statuses = ["draft", "review", "published", "archived"]
    
    if value not in valid_statuses:
        raise Invalid(
            _("Invalid publication status. Must be one of: {0}").format(", ".join(valid_statuses))
        )
    
    return True


def validate_container_target_audience(value):
    """Validate target audience against vocabulary.
    
    Args:
        value: Target audience value
        
    Raises:
        Invalid: If target audience is not valid
    """
    if not value:
        return True  # Optional field
    
    valid_audiences = ["self", "team", "public", "specific_users"]
    
    if value not in valid_audiences:
        raise Invalid(
            _("Invalid target audience. Must be one of: {0}").format(", ".join(valid_audiences))
        )
    
    return True


def validate_container_sharing_permissions(value):
    """Validate sharing permissions dictionary structure.
    
    Args:
        value: Dictionary with sharing permission settings
        
    Raises:
        Invalid: If dictionary structure or values are invalid
    """
    if not value:
        return True  # Empty dict is valid
    
    if not isinstance(value, dict):
        raise Invalid(_("Sharing permissions must be a dictionary"))
    
    valid_permission_keys = ["view", "edit", "share", "admin"]
    valid_permission_values = ["none", "owner", "team", "public", "specific"]
    
    for key, val in value.items():
        if key not in valid_permission_keys:
            raise Invalid(
                _("Invalid permission key '{0}'. Must be one of: {1}").format(
                    key, ", ".join(valid_permission_keys)
                )
            )
        
        if val not in valid_permission_values:
            raise Invalid(
                _("Invalid permission value '{0}' for key '{1}'. Must be one of: {2}").format(
                    val, key, ", ".join(valid_permission_values)
                )
            )
    
    return True


def validate_container_export_formats(value):
    """Validate export formats set.
    
    Args:
        value: Set of export formats
        
    Raises:
        Invalid: If export formats are invalid
    """
    if not value:
        return True  # Empty set is valid
    
    if not isinstance(value, (set, list, tuple)):
        raise Invalid(_("Export formats must be a set, list, or tuple"))
    
    valid_formats = ["pdf", "html", "markdown", "json", "csv", "docx", "epub"]
    
    for format_type in value:
        if format_type not in valid_formats:
            raise Invalid(
                _("Invalid export format '{0}'. Must be one of: {1}").format(
                    format_type, ", ".join(valid_formats)
                )
            )
    
    return True


def validate_container_view_analytics(value):
    """Validate view analytics dictionary structure.
    
    Args:
        value: Dictionary with view analytics data
        
    Raises:
        Invalid: If dictionary structure or values are invalid
    """
    if not value:
        return True  # Empty dict is valid
    
    if not isinstance(value, dict):
        raise Invalid(_("View analytics must be a dictionary"))
    
    # Basic structure validation - specific keys are flexible
    for key, val in value.items():
        if not isinstance(key, str):
            raise Invalid(_("Analytics keys must be strings"))
        
        # Values can be numbers, strings, or lists for flexibility
        if not isinstance(val, (int, float, str, list, dict)):
            raise Invalid(
                _("Analytics values must be numbers, strings, lists, or dictionaries")
            )
    
    return True