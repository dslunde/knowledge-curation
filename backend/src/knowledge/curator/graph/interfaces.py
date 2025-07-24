"""Interfaces for the knowledge graph system."""

from zope.interface import Interface


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

    def export_graph(format='json'):
        """Export graph to various formats."""

    def import_graph(data, format='json', merge=True):
        """Import graph from various formats."""
