"""Validators for Knowledge Item Connection fields."""

from plone import api
from zope.interface import Invalid
from knowledge.curator import _


def validate_connection_strength(value):
    """Validate that connection strength is between 0.0 and 1.0.
    
    Args:
        value: The connection strength value
        
    Raises:
        Invalid: If value is not between 0.0 and 1.0
    """
    if value is None:
        raise Invalid(_("Connection strength is required"))
    
    if not isinstance(value, (int, float)):
        raise Invalid(_("Connection strength must be a number"))
    
    if value < 0.0 or value > 1.0:
        raise Invalid(_("Connection strength must be between 0.0 and 1.0"))
    
    return True


def validate_mastery_requirement(value):
    """Validate that mastery requirement is between 0.0 and 1.0.
    
    Args:
        value: The mastery requirement value
        
    Raises:
        Invalid: If value is not between 0.0 and 1.0
    """
    if value is None:
        return True  # Optional field
    
    if not isinstance(value, (int, float)):
        raise Invalid(_("Mastery requirement must be a number"))
    
    if value < 0.0 or value > 1.0:
        raise Invalid(_("Mastery requirement must be between 0.0 and 1.0"))
    
    return True


def validate_uids_different(data):
    """Validate that source and target UIDs are different.
    
    Args:
        data: The connection data object
        
    Raises:
        Invalid: If source and target UIDs are the same
    """
    if hasattr(data, 'source_item_uid') and hasattr(data, 'target_item_uid'):
        if data.source_item_uid == data.target_item_uid:
            raise Invalid(_("Source and target knowledge items must be different"))
    
    return True


def validate_uid_exists(uid):
    """Validate that a UID references an existing knowledge item.
    
    Args:
        uid: The UID to validate
        
    Raises:
        Invalid: If UID doesn't reference an existing knowledge item
    """
    if not uid:
        raise Invalid(_("UID is required"))
    
    catalog = api.portal.get_tool('portal_catalog')
    results = catalog(UID=uid, portal_type='KnowledgeItem')
    
    if not results:
        raise Invalid(_("Knowledge item with UID ${uid} not found", 
                       mapping={'uid': uid}))
    
    return True


def validate_connection_type_constraints(data):
    """Validate type-specific constraints for connections.
    
    Args:
        data: The connection data object
        
    Raises:
        Invalid: If type-specific constraints are not met
    """
    if not hasattr(data, 'connection_type'):
        return True
    
    connection_type = data.connection_type
    strength = getattr(data, 'strength', 0.5)
    mastery_requirement = getattr(data, 'mastery_requirement', 0.8)
    
    # Type-specific validation rules
    if connection_type == 'prerequisite':
        # Prerequisites should have high mastery requirements
        if mastery_requirement < 0.7:
            raise Invalid(_(
                "Prerequisite connections should have mastery requirement >= 0.7"
            ))
        # Prerequisites should have strong connections
        if strength < 0.6:
            raise Invalid(_(
                "Prerequisite connections should have strength >= 0.6"
            ))
    
    elif connection_type == 'builds_on':
        # Builds_on should have moderate to high strength
        if strength < 0.4:
            raise Invalid(_(
                "Builds_on connections should have strength >= 0.4"
            ))
        # Builds_on should have moderate mastery requirements
        if mastery_requirement < 0.5:
            raise Invalid(_(
                "Builds_on connections should have mastery requirement >= 0.5"
            ))
    
    elif connection_type == 'reinforces':
        # Reinforces can have lower mastery requirements
        if mastery_requirement < 0.3:
            raise Invalid(_(
                "Reinforces connections should have mastery requirement >= 0.3"
            ))
    
    elif connection_type == 'applies':
        # Applied knowledge should have high mastery of prerequisites
        if mastery_requirement < 0.6:
            raise Invalid(_(
                "Applies connections should have mastery requirement >= 0.6"
            ))
    
    return True


def validate_no_circular_prerequisites(graph, source_uid, target_uid, connection_type):
    """Validate that adding a connection doesn't create circular dependencies.
    
    This is especially important for prerequisite connections.
    
    Args:
        graph: The knowledge graph object
        source_uid: Source knowledge item UID
        target_uid: Target knowledge item UID
        connection_type: Type of connection being added
        
    Raises:
        Invalid: If adding this connection would create a circular dependency
    """
    if connection_type != 'prerequisite':
        return True  # Only check prerequisites for circular dependencies
    
    # Check if target_uid can reach source_uid through prerequisite connections
    # This would create a cycle if we add source -> target prerequisite
    visited = set()
    queue = [target_uid]
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        
        if current == source_uid:
            raise Invalid(_(
                "Cannot add prerequisite connection: would create circular dependency"
            ))
        
        visited.add(current)
        
        # Get all prerequisite connections from current node
        if hasattr(graph, 'get_edges_from_node'):
            edges = graph.get_edges_from_node(current)
            for edge in edges:
                if edge.relationship_type == 'prerequisite_of':
                    queue.append(edge.target_uid)
    
    return True