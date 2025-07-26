"""Knowledge graph behavior for content types."""

from knowledge.curator import _
from knowledge.curator.behaviors.interfaces import IKnowledgeRelationship, ISuggestedRelationship
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import directives
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from datetime import datetime
import uuid


@provider(IFormFieldProvider)
class IKnowledgeGraphBehavior(model.Schema):
    """Behavior for knowledge graph relationships with typed relationships."""

    directives.fieldset(
        "knowledge_graph",
        label=_("Knowledge Graph"),
        fields=[
            "relationships",
            "suggested_relationships",
            "embedding_vector",
            "related_concepts",
            "concept_weight",
            "graph_metadata",
            "centrality_score",
            "connection_strength",
        ],
    )

    # Legacy field for backward compatibility
    connections = schema.List(
        title=_("Legacy Connections"),
        description=_("Legacy simple connections - will be migrated to typed relationships"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    relationships = schema.List(
        title=_("Relationships"),
        description=_("Typed relationships to other content items"),
        value_type=schema.Object(schema=IKnowledgeRelationship),
        required=False,
        default=[],
    )

    suggested_relationships = schema.List(
        title=_("Suggested Relationships"),
        description=_("AI-suggested relationships pending review"),
        value_type=schema.Object(schema=ISuggestedRelationship),
        required=False,
        default=[],
    )

    embedding_vector = schema.List(
        title=_("Embedding Vector"),
        description=_("AI-generated embedding vector for similarity search"),
        value_type=schema.Float(),
        required=False,
        readonly=True,
    )

    related_concepts = schema.List(
        title=_("Related Concepts"),
        description=_("Concepts related to this content"),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    concept_weight = schema.Float(
        title=_("Concept Weight"),
        description=_("Weight of this content in the knowledge graph"),
        required=False,
        default=1.0,
        min=0.0,
        max=10.0,
    )

    graph_metadata = schema.Dict(
        title=_("Graph Metadata"),
        description=_("Additional metadata for knowledge graph"),
        key_type=schema.TextLine(),
        value_type=schema.TextLine(),
        required=False,
        default={},
    )

    centrality_score = schema.Float(
        title=_("Centrality Score"),
        description=_("Node centrality in the knowledge graph"),
        min=0.0,
        max=1.0,
        required=False,
        readonly=True,
    )

    connection_strength = schema.Dict(
        title=_("Connection Strength"),
        description=_("Strength of connections to other nodes"),
        key_type=schema.TextLine(),
        value_type=schema.Float(),
        required=False,
        default={},
    )


@implementer(IKnowledgeGraphBehavior)
@adapter(Interface)
class KnowledgeGraphBehavior:
    """Knowledge graph behavior adapter with typed relationships."""

    def __init__(self, context):
        self.context = context
        self._ensure_persistent_storage()

    def _ensure_persistent_storage(self):
        """Ensure all lists use persistent storage."""
        if not hasattr(self.context, 'relationships'):
            self.context.relationships = PersistentList()
        if not hasattr(self.context, 'suggested_relationships'):
            self.context.suggested_relationships = PersistentList()
        if not hasattr(self.context, 'connection_strength'):
            self.context.connection_strength = PersistentMapping()

    @property
    def connections(self):
        """Get legacy connections for backward compatibility."""
        return getattr(self.context, "connections", [])

    @connections.setter
    def connections(self, value):
        """Set connections."""
        self.context.connections = value

    @property
    def relationships(self):
        """Get typed relationships."""
        return getattr(self.context, "relationships", PersistentList())

    @relationships.setter
    def relationships(self, value):
        """Set typed relationships."""
        self.context.relationships = PersistentList(value) if not isinstance(value, PersistentList) else value

    @property
    def suggested_relationships(self):
        """Get suggested relationships."""
        return getattr(self.context, "suggested_relationships", PersistentList())

    @suggested_relationships.setter
    def suggested_relationships(self, value):
        """Set suggested relationships."""
        self.context.suggested_relationships = PersistentList(value) if not isinstance(value, PersistentList) else value

    @property
    def embedding_vector(self):
        """Get embedding vector."""
        return getattr(self.context, "embedding_vector", [])

    @embedding_vector.setter
    def embedding_vector(self, value):
        """Set embedding vector."""
        self.context.embedding_vector = value

    @property
    def related_concepts(self):
        """Get related concepts."""
        return getattr(self.context, "related_concepts", [])

    @related_concepts.setter
    def related_concepts(self, value):
        """Set related concepts."""
        self.context.related_concepts = value

    @property
    def concept_weight(self):
        """Get concept weight."""
        return getattr(self.context, "concept_weight", 1.0)

    @concept_weight.setter
    def concept_weight(self, value):
        """Set concept weight."""
        self.context.concept_weight = value

    @property
    def graph_metadata(self):
        """Get graph metadata."""
        return getattr(self.context, "graph_metadata", {})

    @graph_metadata.setter
    def graph_metadata(self, value):
        """Set graph metadata."""
        self.context.graph_metadata = value

    @property
    def centrality_score(self):
        """Get centrality score."""
        return getattr(self.context, "centrality_score", 0.0)

    @centrality_score.setter
    def centrality_score(self, value):
        """Set centrality score."""
        self.context.centrality_score = value

    @property
    def connection_strength(self):
        """Get connection strength mapping."""
        return getattr(self.context, "connection_strength", PersistentMapping())

    @connection_strength.setter
    def connection_strength(self, value):
        """Set connection strength mapping."""
        self.context.connection_strength = PersistentMapping(value) if not isinstance(value, PersistentMapping) else value

    def add_relationship(self, target_uid, relationship_type='related', strength=0.5, metadata=None):
        """Add a typed relationship."""
        self._ensure_persistent_storage()
        
        # Check if relationship already exists
        for rel in self.relationships:
            if rel.get('target_uid') == target_uid and rel.get('relationship_type') == relationship_type:
                return rel
        
        relationship = PersistentMapping()
        relationship['source_uid'] = self.context.UID()
        relationship['target_uid'] = target_uid
        relationship['relationship_type'] = relationship_type
        relationship['strength'] = strength
        relationship['metadata'] = metadata or {}
        relationship['created'] = datetime.now()
        relationship['confidence'] = 1.0  # Manual relationships have full confidence
        
        self.relationships.append(relationship)
        return relationship

    def remove_relationship(self, target_uid, relationship_type=None):
        """Remove a relationship."""
        self._ensure_persistent_storage()
        
        to_remove = []
        for idx, rel in enumerate(self.relationships):
            if rel.get('target_uid') == target_uid:
                if relationship_type is None or rel.get('relationship_type') == relationship_type:
                    to_remove.append(idx)
        
        # Remove in reverse order to maintain indices
        for idx in reversed(to_remove):
            del self.relationships[idx]

    def get_relationships_by_type(self, relationship_type):
        """Get all relationships of a specific type."""
        return [rel for rel in self.relationships if rel.get('relationship_type') == relationship_type]

    def calculate_centrality(self):
        """Calculate and update centrality score."""
        # Simple degree centrality based on number of relationships
        total_relationships = len(self.relationships) + len(self.suggested_relationships)
        # Normalize to 0-1 range (assuming max 100 relationships)
        self.centrality_score = min(total_relationships / 100.0, 1.0)
        return self.centrality_score

    def update_connection_strengths(self):
        """Update connection strength mapping."""
        self._ensure_persistent_storage()
        
        strengths = PersistentMapping()
        for rel in self.relationships:
            target_uid = rel.get('target_uid')
            strength = rel.get('strength', 0.5)
            
            # If multiple relationships to same target, use max strength
            if target_uid in strengths:
                strengths[target_uid] = max(strengths[target_uid], strength)
            else:
                strengths[target_uid] = strength
        
        self.connection_strength = strengths
        return strengths

    def migrate_legacy_connections(self):
        """Migrate legacy connections to typed relationships."""
        if hasattr(self.context, 'connections') and self.connections:
            for uid in self.connections:
                # Check if already migrated
                existing = False
                for rel in self.relationships:
                    if rel.get('target_uid') == uid:
                        existing = True
                        break
                
                if not existing:
                    self.add_relationship(uid, 'related', 0.5)
            
            # Clear legacy connections after migration
            self.connections = []
            return True
        return False
