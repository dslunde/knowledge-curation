"""Field validators for Knowledge Item that require context access."""

from zope.interface import implementer
from zope.schema.interfaces import IContextAwareDefaultFactory
from z3c.form import validator
from zope.interface import Invalid
from knowledge.curator import _
from knowledge.curator.interfaces import IKnowledgeItem
from plone import api


class NoSelfReferenceValidator(validator.SimpleFieldValidator):
    """Validator to ensure Knowledge Items don't reference themselves."""
    
    def validate(self, value):
        """Validate that the Knowledge Item doesn't reference itself.
        
        Args:
            value: List of UIDs
            
        Raises:
            Invalid: If self-reference detected
        """
        super().validate(value)
        
        if not value or not hasattr(self.context, 'UID'):
            return
        
        current_uid = self.context.UID()
        
        if current_uid in value:
            raise Invalid(_("A Knowledge Item cannot reference itself"))


class CircularDependencyValidator(validator.SimpleFieldValidator):
    """Validator to prevent circular dependencies in prerequisites."""
    
    def validate(self, value):
        """Validate that adding prerequisites won't create circular dependencies.
        
        Args:
            value: List of prerequisite UIDs
            
        Raises:
            Invalid: If circular dependency would be created
        """
        super().validate(value)
        
        if not value or not hasattr(self.context, 'UID'):
            return
        
        current_uid = self.context.UID()
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
        for prereq_uid in value:
            if check_circular(prereq_uid):
                raise Invalid(
                    _("Adding prerequisite '{0}' would create a circular dependency").format(prereq_uid)
                )


# Register validators for specific fields
validator.WidgetValidatorDiscriminators(
    NoSelfReferenceValidator,
    field=IKnowledgeItem['prerequisite_items']
)

validator.WidgetValidatorDiscriminators(
    NoSelfReferenceValidator,
    field=IKnowledgeItem['enables_items']
)

validator.WidgetValidatorDiscriminators(
    CircularDependencyValidator,
    field=IKnowledgeItem['prerequisite_items']
)


# Context-aware default factory for mastery threshold
@implementer(IContextAwareDefaultFactory)
class MasteryThresholdDefaultFactory:
    """Provide context-aware default for mastery threshold based on difficulty."""
    
    def __call__(self, context):
        """Return default mastery threshold based on difficulty level."""
        if hasattr(context, 'difficulty_level'):
            difficulty_defaults = {
                'beginner': 0.7,
                'intermediate': 0.8,
                'advanced': 0.85,
                'expert': 0.9
            }
            return difficulty_defaults.get(context.difficulty_level, 0.8)
        return 0.8