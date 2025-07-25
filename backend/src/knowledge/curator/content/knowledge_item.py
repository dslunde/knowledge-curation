"""Knowledge Item content type."""

from knowledge.curator.interfaces import IKnowledgeItem
from plone.dexterity.content import Container
from zope.interface import implementer
from knowledge.curator.content.validators import (
    validate_uid_reference,
    validate_uid_references_list,
    validate_atomic_concepts,
    validate_knowledge_type,
    validate_difficulty_level,
    validate_mastery_threshold,
    validate_learning_progress,
    validate_tags,
    validate_embedding_vector,
    validate_circular_dependencies,
    validate_no_self_reference,
)


@implementer(IKnowledgeItem)
class KnowledgeItem(Container):
    """Knowledge Item content type implementation."""

    def get_embedding(self):
        """Get the embedding vector for this item."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector

    # Relationship management methods
    def add_prerequisite(self, item_uid):
        """Add a prerequisite knowledge item.
        
        Args:
            item_uid: UID of the prerequisite knowledge item
            
        Raises:
            ValueError: If adding would create a circular dependency
        """
        if not hasattr(self, 'prerequisite_items'):
            self.prerequisite_items = []
        
        if item_uid not in self.prerequisite_items:
            # Check for circular dependencies before adding
            if self._would_create_circular_dependency(item_uid):
                raise ValueError(f"Adding prerequisite {item_uid} would create a circular dependency")
            
            self.prerequisite_items.append(item_uid)
            self._p_changed = True
            
            # Also update the enables_items of the prerequisite
            from plone import api
            prerequisite = api.content.get(UID=item_uid)
            if prerequisite and hasattr(prerequisite, 'enables_items'):
                if not hasattr(prerequisite, 'enables_items') or prerequisite.enables_items is None:
                    prerequisite.enables_items = []
                if self.UID() not in prerequisite.enables_items:
                    prerequisite.enables_items.append(self.UID())
                    prerequisite._p_changed = True

    def remove_prerequisite(self, item_uid):
        """Remove a prerequisite knowledge item.
        
        Args:
            item_uid: UID of the prerequisite to remove
        """
        if hasattr(self, 'prerequisite_items') and item_uid in self.prerequisite_items:
            self.prerequisite_items.remove(item_uid)
            self._p_changed = True
            
            # Also update the enables_items of the prerequisite
            from plone import api
            prerequisite = api.content.get(UID=item_uid)
            if prerequisite and hasattr(prerequisite, 'enables_items') and self.UID() in prerequisite.enables_items:
                prerequisite.enables_items.remove(self.UID())
                prerequisite._p_changed = True

    def add_enabled_item(self, item_uid):
        """Add an enabled knowledge item.
        
        Args:
            item_uid: UID of the knowledge item this one enables
        """
        if not hasattr(self, 'enables_items'):
            self.enables_items = []
        
        if item_uid not in self.enables_items:
            self.enables_items.append(item_uid)
            self._p_changed = True
            
            # Also update the prerequisite_items of the enabled item
            from plone import api
            enabled_item = api.content.get(UID=item_uid)
            if enabled_item and hasattr(enabled_item, 'prerequisite_items'):
                if not hasattr(enabled_item, 'prerequisite_items') or enabled_item.prerequisite_items is None:
                    enabled_item.prerequisite_items = []
                if self.UID() not in enabled_item.prerequisite_items:
                    enabled_item.prerequisite_items.append(self.UID())
                    enabled_item._p_changed = True

    def remove_enabled_item(self, item_uid):
        """Remove an enabled knowledge item.
        
        Args:
            item_uid: UID of the enabled item to remove
        """
        if hasattr(self, 'enables_items') and item_uid in self.enables_items:
            self.enables_items.remove(item_uid)
            self._p_changed = True
            
            # Also update the prerequisite_items of the enabled item
            from plone import api
            enabled_item = api.content.get(UID=item_uid)
            if enabled_item and hasattr(enabled_item, 'prerequisite_items') and self.UID() in enabled_item.prerequisite_items:
                enabled_item.prerequisite_items.remove(self.UID())
                enabled_item._p_changed = True

    def get_prerequisites(self):
        """Get all prerequisite knowledge items.
        
        Returns:
            List of prerequisite knowledge item objects
        """
        from plone import api
        prerequisites = []
        if hasattr(self, 'prerequisite_items') and self.prerequisite_items:
            for uid in self.prerequisite_items:
                item = api.content.get(UID=uid)
                if item:
                    prerequisites.append(item)
        return prerequisites

    def get_enabled_items(self):
        """Get all enabled knowledge items.
        
        Returns:
            List of enabled knowledge item objects
        """
        from plone import api
        enabled = []
        if hasattr(self, 'enables_items') and self.enables_items:
            for uid in self.enables_items:
                item = api.content.get(UID=uid)
                if item:
                    enabled.append(item)
        return enabled

    def get_all_prerequisites(self, visited=None):
        """Recursively get all prerequisites including indirect ones.
        
        Args:
            visited: Set of already visited UIDs to prevent infinite loops
            
        Returns:
            List of all prerequisite knowledge items (direct and indirect)
        """
        if visited is None:
            visited = set()
        
        all_prerequisites = []
        current_uid = self.UID()
        
        if current_uid in visited:
            return all_prerequisites
        
        visited.add(current_uid)
        
        # Get direct prerequisites
        direct_prerequisites = self.get_prerequisites()
        
        for prereq in direct_prerequisites:
            if prereq.UID() not in visited:
                all_prerequisites.append(prereq)
                # Recursively get prerequisites of prerequisites
                if hasattr(prereq, 'get_all_prerequisites'):
                    indirect_prerequisites = prereq.get_all_prerequisites(visited)
                    for indirect in indirect_prerequisites:
                        if indirect not in all_prerequisites:
                            all_prerequisites.append(indirect)
        
        return all_prerequisites

    def get_all_enabled_items(self, visited=None):
        """Recursively get all enabled items including indirect ones.
        
        Args:
            visited: Set of already visited UIDs to prevent infinite loops
            
        Returns:
            List of all enabled knowledge items (direct and indirect)
        """
        if visited is None:
            visited = set()
        
        all_enabled = []
        current_uid = self.UID()
        
        if current_uid in visited:
            return all_enabled
        
        visited.add(current_uid)
        
        # Get direct enabled items
        direct_enabled = self.get_enabled_items()
        
        for enabled in direct_enabled:
            if enabled.UID() not in visited:
                all_enabled.append(enabled)
                # Recursively get enabled items of enabled items
                if hasattr(enabled, 'get_all_enabled_items'):
                    indirect_enabled = enabled.get_all_enabled_items(visited)
                    for indirect in indirect_enabled:
                        if indirect not in all_enabled:
                            all_enabled.append(indirect)
        
        return all_enabled

    def _would_create_circular_dependency(self, new_prerequisite_uid):
        """Check if adding a prerequisite would create a circular dependency.
        
        Args:
            new_prerequisite_uid: UID of the proposed prerequisite
            
        Returns:
            True if adding would create a circular dependency, False otherwise
        """
        from plone import api
        
        # If the new prerequisite is this item itself, that's circular
        if new_prerequisite_uid == self.UID():
            return True
        
        # Get the proposed prerequisite item
        prerequisite = api.content.get(UID=new_prerequisite_uid)
        if not prerequisite:
            return False
        
        # Check if this item is in the prerequisite's dependency chain
        if hasattr(prerequisite, 'get_all_prerequisites'):
            all_prereq_prerequisites = prerequisite.get_all_prerequisites()
            for item in all_prereq_prerequisites:
                if item.UID() == self.UID():
                    return True
        
        return False

    def validate_relationships(self):
        """Validate all relationships for this knowledge item.
        
        Returns:
            dict with 'valid' (bool) and 'errors' (list of error messages)
        """
        errors = []
        
        # Check for circular dependencies
        if hasattr(self, 'prerequisite_items') and self.prerequisite_items:
            for prereq_uid in self.prerequisite_items:
                if self._would_create_circular_dependency(prereq_uid):
                    errors.append(f"Circular dependency detected with prerequisite {prereq_uid}")
        
        # Validate that referenced items exist
        from plone import api
        
        if hasattr(self, 'prerequisite_items') and self.prerequisite_items:
            for uid in self.prerequisite_items:
                if not api.content.get(UID=uid):
                    errors.append(f"Prerequisite with UID {uid} not found")
        
        if hasattr(self, 'enables_items') and self.enables_items:
            for uid in self.enables_items:
                if not api.content.get(UID=uid):
                    errors.append(f"Enabled item with UID {uid} not found")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def validate_all_fields(self):
        """Validate all fields of this knowledge item.
        
        Returns:
            dict with 'valid' (bool) and 'errors' (dict of field: error messages)
        """
        field_errors = {}
        
        # Validate title
        try:
            from knowledge.curator.content.validators import validate_title_length
            validate_title_length(self.title)
        except Exception as e:
            field_errors['title'] = str(e)
        
        # Validate description
        try:
            from knowledge.curator.content.validators import validate_description_length
            validate_description_length(self.description)
        except Exception as e:
            field_errors['description'] = str(e)
        
        # Validate content
        try:
            from knowledge.curator.content.validators import validate_content_length
            validate_content_length(self.content)
        except Exception as e:
            field_errors['content'] = str(e)
        
        # Validate knowledge_type
        try:
            validate_knowledge_type(self.knowledge_type)
        except Exception as e:
            field_errors['knowledge_type'] = str(e)
        
        # Validate atomic_concepts
        try:
            validate_atomic_concepts(self.atomic_concepts)
        except Exception as e:
            field_errors['atomic_concepts'] = str(e)
        
        # Validate tags
        if hasattr(self, 'tags') and self.tags:
            try:
                validate_tags(self.tags)
            except Exception as e:
                field_errors['tags'] = str(e)
        
        # Validate mastery_threshold
        if hasattr(self, 'mastery_threshold') and self.mastery_threshold is not None:
            try:
                validate_mastery_threshold(self.mastery_threshold)
            except Exception as e:
                field_errors['mastery_threshold'] = str(e)
        
        # Validate learning_progress
        if hasattr(self, 'learning_progress') and self.learning_progress is not None:
            try:
                validate_learning_progress(self.learning_progress)
            except Exception as e:
                field_errors['learning_progress'] = str(e)
        
        # Validate difficulty_level
        if hasattr(self, 'difficulty_level') and self.difficulty_level:
            try:
                validate_difficulty_level(self.difficulty_level)
            except Exception as e:
                field_errors['difficulty_level'] = str(e)
        
        # Validate embedding_vector
        if hasattr(self, 'embedding_vector') and self.embedding_vector:
            try:
                validate_embedding_vector(self.embedding_vector)
            except Exception as e:
                field_errors['embedding_vector'] = str(e)
        
        # Validate prerequisite_items
        if hasattr(self, 'prerequisite_items') and self.prerequisite_items:
            try:
                validate_uid_references_list(self.prerequisite_items)
                validate_no_self_reference(self, self.prerequisite_items)
                validate_circular_dependencies(self, self.prerequisite_items)
            except Exception as e:
                field_errors['prerequisite_items'] = str(e)
        
        # Validate enables_items
        if hasattr(self, 'enables_items') and self.enables_items:
            try:
                validate_uid_references_list(self.enables_items)
                validate_no_self_reference(self, self.enables_items)
            except Exception as e:
                field_errors['enables_items'] = str(e)
        
        # Validate relationship consistency
        relationship_validation = self.validate_relationships()
        if not relationship_validation['valid']:
            field_errors['relationships'] = relationship_validation['errors']
        
        return {
            'valid': len(field_errors) == 0,
            'errors': field_errors
        }

    def set_field_value_with_validation(self, field_name, value):
        """Set a field value with validation.
        
        Args:
            field_name: Name of the field to set
            value: Value to set
            
        Returns:
            dict with 'success' (bool) and 'error' (str if validation failed)
        """
        # Map field names to validators
        field_validators = {
            'title': validate_title_length,
            'description': validate_description_length,
            'content': validate_content_length,
            'knowledge_type': validate_knowledge_type,
            'atomic_concepts': validate_atomic_concepts,
            'tags': validate_tags,
            'mastery_threshold': validate_mastery_threshold,
            'learning_progress': validate_learning_progress,
            'difficulty_level': validate_difficulty_level,
            'embedding_vector': validate_embedding_vector,
            'prerequisite_items': validate_uid_references_list,
            'enables_items': validate_uid_references_list,
        }
        
        # Special handling for relationship fields
        if field_name in ['prerequisite_items', 'enables_items']:
            try:
                validate_uid_references_list(value)
                validate_no_self_reference(self, value)
                if field_name == 'prerequisite_items':
                    validate_circular_dependencies(self, value)
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Regular field validation
        elif field_name in field_validators:
            try:
                field_validators[field_name](value)
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Set the value if validation passed
        setattr(self, field_name, value)
        self._p_changed = True
        
        return {'success': True}
