"""Interfaces for knowledge.curator behaviors."""

from datetime import datetime
from typing import Dict, List, Optional
from zope.interface import Interface
from zope import schema


# Knowledge Relationship Interfaces

class IKnowledgeRelationship(Interface):
    """Interface for typed knowledge relationships."""
    
    source_uid = schema.TextLine(
        title="Source UID",
        description="UID of the source content item",
        required=True
    )
    
    target_uid = schema.TextLine(
        title="Target UID", 
        description="UID of the target content item",
        required=True
    )
    
    relationship_type = schema.Choice(
        title="Relationship Type",
        description="Type of relationship between items",
        vocabulary="knowledge.curator.relationship_types",
        required=True,
        default="related"
    )
    
    strength = schema.Float(
        title="Strength",
        description="Strength of the relationship (0.0-1.0)",
        min=0.0,
        max=1.0,
        default=0.5
    )
    
    metadata = schema.Dict(
        title="Metadata",
        description="Additional metadata about the relationship",
        key_type=schema.TextLine(),
        value_type=schema.TextLine(),
        required=False,
        default={}
    )
    
    created = schema.Datetime(
        title="Created",
        description="When the relationship was created",
        required=True
    )
    
    confidence = schema.Float(
        title="Confidence",
        description="Confidence score for this relationship",
        min=0.0,
        max=1.0,
        default=1.0
    )


class ISuggestedRelationship(IKnowledgeRelationship):
    """Interface for AI-suggested relationships."""
    
    suggestion_reason = schema.Text(
        title="Suggestion Reason",
        description="Why this relationship was suggested",
        required=False
    )
    
    similarity_score = schema.Float(
        title="Similarity Score",
        description="Semantic similarity score",
        min=0.0,
        max=1.0,
        required=False
    )
    
    is_accepted = schema.Bool(
        title="Is Accepted",
        description="Whether the suggestion has been accepted",
        default=False
    )
    
    review_date = schema.Datetime(
        title="Review Date",
        description="When the suggestion was reviewed",
        required=False
    )


# Enhanced Knowledge Graph Behavior Interface

class IEnhancedKnowledgeGraphBehavior(Interface):
    """Enhanced behavior for knowledge graph relationships with typed relationships."""
    
    relationships = schema.List(
        title="Relationships",
        description="Typed relationships to other content items",
        value_type=schema.Object(IKnowledgeRelationship),
        required=False,
        default=[]
    )
    
    suggested_relationships = schema.List(
        title="Suggested Relationships",
        description="AI-suggested relationships pending review",
        value_type=schema.Object(ISuggestedRelationship),
        required=False,
        default=[]
    )
    
    embedding_vector = schema.List(
        title="Embedding Vector",
        description="AI-generated embedding vector for similarity search",
        value_type=schema.Float(),
        required=False,
        readonly=True
    )
    
    related_concepts = schema.List(
        title="Related Concepts",
        description="Concepts related to this content",
        value_type=schema.TextLine(),
        required=False,
        default=[]
    )
    
    concept_weight = schema.Float(
        title="Concept Weight",
        description="Weight of this content in the knowledge graph",
        required=False,
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    graph_metadata = schema.Dict(
        title="Graph Metadata",
        description="Additional metadata for knowledge graph",
        key_type=schema.TextLine(),
        value_type=schema.TextLine(),
        required=False,
        default={}
    )
    
    centrality_score = schema.Float(
        title="Centrality Score",
        description="Node centrality in the knowledge graph",
        min=0.0,
        max=1.0,
        required=False,
        readonly=True
    )
    
    cluster_id = schema.TextLine(
        title="Cluster ID",
        description="ID of the knowledge cluster this item belongs to",
        required=False
    )


# AI Enhancement Interfaces

class IExtractedConcept(Interface):
    """Interface for concepts extracted from content."""
    
    concept = schema.TextLine(
        title="Concept",
        description="The extracted concept",
        required=True
    )
    
    relevance_score = schema.Float(
        title="Relevance Score",
        description="How relevant this concept is to the content",
        min=0.0,
        max=1.0,
        required=True
    )
    
    frequency = schema.Int(
        title="Frequency",
        description="How often the concept appears",
        min=0,
        required=False,
        default=1
    )
    
    context = schema.Text(
        title="Context",
        description="Context in which the concept was found",
        required=False
    )
    
    confidence = schema.Float(
        title="Confidence",
        description="Extraction confidence score",
        min=0.0,
        max=1.0,
        default=0.8
    )


class IKnowledgeGap(Interface):
    """Interface for identified knowledge gaps."""
    
    gap_description = schema.Text(
        title="Gap Description",
        description="Description of the knowledge gap",
        required=True
    )
    
    importance = schema.Choice(
        title="Importance",
        description="Importance of filling this gap",
        vocabulary="knowledge.curator.importance_vocabulary",
        required=True,
        default="medium"
    )
    
    suggested_topics = schema.List(
        title="Suggested Topics",
        description="Topics that could help fill this gap",
        value_type=schema.TextLine(),
        required=False,
        default=[]
    )
    
    confidence = schema.Float(
        title="Confidence",
        description="Confidence in this gap identification",
        min=0.0,
        max=1.0,
        default=0.7
    )


class IEnhancedAIBehavior(Interface):
    """Enhanced AI behavior with confidence tracking."""
    
    ai_summary = schema.Text(
        title="AI Summary",
        description="AI-generated summary of the content",
        required=False,
        readonly=True
    )
    
    ai_summary_confidence = schema.Float(
        title="Summary Confidence",
        description="Confidence score for the AI summary",
        min=0.0,
        max=1.0,
        required=False,
        readonly=True
    )
    
    ai_tags = schema.List(
        title="AI Suggested Tags",
        description="Tags suggested by AI analysis",
        value_type=schema.TextLine(),
        required=False,
        readonly=True,
        default=[]
    )
    
    ai_tags_confidence = schema.Float(
        title="Tags Confidence",
        description="Confidence score for the AI tags",
        min=0.0,
        max=1.0,
        required=False,
        readonly=True
    )
    
    extracted_concepts = schema.List(
        title="Extracted Concepts",
        description="Concepts extracted from the content",
        value_type=schema.Object(IExtractedConcept),
        required=False,
        default=[]
    )
    
    knowledge_gaps = schema.List(
        title="Knowledge Gaps",
        description="Identified gaps in knowledge",
        value_type=schema.Object(IKnowledgeGap),
        required=False,
        default=[]
    )
    
    sentiment_score = schema.Float(
        title="Sentiment Score",
        description="AI-calculated sentiment score (-1 to 1)",
        required=False,
        readonly=True,
        min=-1.0,
        max=1.0
    )
    
    sentiment_confidence = schema.Float(
        title="Sentiment Confidence",
        description="Confidence in sentiment analysis",
        min=0.0,
        max=1.0,
        required=False,
        readonly=True
    )
    
    readability_score = schema.Float(
        title="Readability Score",
        description="AI-calculated readability score (0-100)",
        required=False,
        readonly=True,
        min=0.0,
        max=100.0
    )
    
    last_ai_analysis = schema.Datetime(
        title="Last AI Analysis",
        description="When the content was last analyzed by AI",
        required=False,
        readonly=True
    )


# Graph Metrics Interfaces

class IGraphMetrics(Interface):
    """Interface for graph metrics calculation."""
    
    def calculate_centrality(node_uid):
        """Calculate centrality score for a node."""
    
    def calculate_clustering_coefficient(node_uid):
        """Calculate local clustering coefficient."""
    
    def find_communities():
        """Detect communities in the knowledge graph."""
    
    def calculate_path_length(source_uid, target_uid):
        """Calculate shortest path between two nodes."""
    
    def get_node_metrics(node_uid):
        """Get comprehensive metrics for a node."""
    
    def get_graph_statistics():
        """Get overall graph statistics."""


class IGraphAnalytics(Interface):
    """Interface for advanced graph analytics."""
    
    def identify_knowledge_hubs():
        """Identify highly connected knowledge hubs."""
    
    def find_bridge_nodes():
        """Find nodes that bridge different communities."""
    
    def detect_knowledge_gaps():
        """Detect gaps in the knowledge graph."""
    
    def suggest_connections(node_uid, limit=10):
        """Suggest new connections for a node."""
    
    def analyze_knowledge_flow():
        """Analyze how knowledge flows through the graph."""