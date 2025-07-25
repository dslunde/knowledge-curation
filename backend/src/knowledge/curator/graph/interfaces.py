"""Interfaces for the knowledge graph system."""

from zope.interface import Interface, invariant
from zope import schema

from knowledge.curator import _
from knowledge.curator.graph.validators import (
    validate_connection_strength,
    validate_mastery_requirement,
    validate_uids_different,
    validate_connection_type_constraints,
)


class IKnowledgeItemConnection(Interface):
    """Interface for graph edges that connect Knowledge Items with learning relationships."""
    
    source_item_uid = schema.TextLine(
        title=_("Source Item UID"),
        description=_("UUID of the source knowledge item"),
        required=True,
    )
    
    target_item_uid = schema.TextLine(
        title=_("Target Item UID"),
        description=_("UUID of the target knowledge item"),
        required=True,
    )
    
    connection_type = schema.Choice(
        title=_("Connection Type"),
        description=_("Type of connection between knowledge items"),
        vocabulary="knowledge.curator.connection_types",
        required=True,
    )
    
    strength = schema.Float(
        title=_("Connection Strength"),
        description=_("Strength of the connection (0.0-1.0)"),
        required=True,
        default=0.5,
        min=0.0,
        max=1.0,
        constraint=validate_connection_strength,
    )
    
    mastery_requirement = schema.Float(
        title=_("Mastery Requirement"),
        description=_("Required mastery level of source before target (0.0-1.0)"),
        required=False,
        default=0.8,
        min=0.0,
        max=1.0,
        constraint=validate_mastery_requirement,
    )
    
    # Invariants for cross-field validation
    @invariant
    def validate_different_uids(data):
        """Ensure source and target UIDs are different."""
        validate_uids_different(data)
    
    @invariant
    def validate_type_specific_constraints(data):
        """Ensure connection type constraints are met."""
        validate_connection_type_constraints(data)
    
    def validate_connection_integrity():
        """Validate that the connection is valid and maintains graph integrity.
        
        Checks:
        - Source and target UIDs are different
        - UIDs reference existing knowledge items
        - No circular dependencies for prerequisite connections
        """
    
    def validate_type_constraints():
        """Validate type-specific constraints for the connection.
        
        Checks:
        - Prerequisite connections have high mastery requirements
        - Builds_on connections have moderate strength
        - Connection type is appropriate for the content
        """


class IGraphStorage(Interface):
    """Interface for graph storage adapter."""

    def save_graph(graph):
        """Save a graph to persistent storage."""

    def load_graph():
        """Load graph from persistent storage."""

    def sync_with_catalog():
        """Synchronize graph with catalog content."""

    def query_nodes(node_type=None, properties=None):
        """Query nodes by type and properties."""

    def query_relationships(relationship_type=None, source_uid=None, target_uid=None):
        """Query relationships by type and endpoints."""

    def export_graph(file_format="json"):
        """Export graph to various formats."""

    def import_graph(data, file_format="json", merge=True):
        """Import graph from various formats."""
