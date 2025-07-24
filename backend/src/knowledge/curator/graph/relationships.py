"""Relationship types and management for knowledge graph."""

from enum import Enum


class RelationshipType(Enum):
    """Standard relationship types in the knowledge graph."""

    # Knowledge relationships
    RELATED_TO = "related_to"
    PREREQUISITE_OF = "prerequisite_of"
    BUILDS_ON = "builds_on"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    REFUTES = "refutes"

    # Hierarchical relationships
    PART_OF = "part_of"
    CONTAINS = "contains"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"

    # Temporal relationships
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    CONCURRENT_WITH = "concurrent_with"

    # Learning relationships
    TEACHES = "teaches"
    LEARNED_FROM = "learned_from"
    APPLIED_IN = "applied_in"
    DERIVED_FROM = "derived_from"

    # Project relationships
    USED_IN = "used_in"
    PRODUCED_BY = "produced_by"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"

    # Reference relationships
    CITES = "cites"
    CITED_BY = "cited_by"
    REFERENCES = "references"
    MENTIONED_IN = "mentioned_in"

    # Tagging relationships
    TAGGED_WITH = "tagged_with"
    HAS_TAG = "has_tag"

    # Authorship relationships
    AUTHORED_BY = "authored_by"
    CONTRIBUTED_TO = "contributed_to"
    REVIEWED_BY = "reviewed_by"

    # Custom relationship
    CUSTOM = "custom"


class RelationshipMetadata:
    """Metadata for relationship types."""

    RELATIONSHIP_METADATA = {
        RelationshipType.RELATED_TO: {
            "bidirectional": True,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "General relationship between concepts",
            "reverse_name": "related_to",
        },
        RelationshipType.PREREQUISITE_OF: {
            "bidirectional": False,
            "transitive": True,
            "weight_range": (0.0, 1.0),
            "description": "Required knowledge before understanding",
            "reverse_name": "requires",
        },
        RelationshipType.BUILDS_ON: {
            "bidirectional": False,
            "transitive": True,
            "weight_range": (0.0, 1.0),
            "description": "Extends or develops from",
            "reverse_name": "foundation_for",
        },
        RelationshipType.CONTRADICTS: {
            "bidirectional": True,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Conflicts with or opposes",
            "reverse_name": "contradicts",
        },
        RelationshipType.SUPPORTS: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Provides evidence or backing",
            "reverse_name": "supported_by",
        },
        RelationshipType.REFUTES: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Disproves or challenges",
            "reverse_name": "refuted_by",
        },
        RelationshipType.PART_OF: {
            "bidirectional": False,
            "transitive": True,
            "weight_range": (0.0, 1.0),
            "description": "Component or subset of",
            "reverse_name": "contains",
        },
        RelationshipType.CONTAINS: {
            "bidirectional": False,
            "transitive": True,
            "weight_range": (0.0, 1.0),
            "description": "Includes or encompasses",
            "reverse_name": "part_of",
        },
        RelationshipType.FOLLOWS: {
            "bidirectional": False,
            "transitive": True,
            "weight_range": (0.0, 1.0),
            "description": "Comes after in sequence",
            "reverse_name": "precedes",
        },
        RelationshipType.PRECEDES: {
            "bidirectional": False,
            "transitive": True,
            "weight_range": (0.0, 1.0),
            "description": "Comes before in sequence",
            "reverse_name": "follows",
        },
        RelationshipType.TEACHES: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Provides instruction about",
            "reverse_name": "taught_by",
        },
        RelationshipType.LEARNED_FROM: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Knowledge gained from",
            "reverse_name": "taught_to",
        },
        RelationshipType.APPLIED_IN: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Put into practice in",
            "reverse_name": "applies",
        },
        RelationshipType.USED_IN: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "Utilized or employed in",
            "reverse_name": "uses",
        },
        RelationshipType.CITES: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "References as source",
            "reverse_name": "cited_by",
        },
        RelationshipType.TAGGED_WITH: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (1.0, 1.0),
            "description": "Categorized with tag",
            "reverse_name": "tags",
        },
        RelationshipType.AUTHORED_BY: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (1.0, 1.0),
            "description": "Created or written by",
            "reverse_name": "authored",
        },
        RelationshipType.CUSTOM: {
            "bidirectional": False,
            "transitive": False,
            "weight_range": (0.0, 1.0),
            "description": "User-defined relationship",
            "reverse_name": "custom_reverse",
        },
    }

    @classmethod
    def get_metadata(cls, relationship_type: RelationshipType) -> dict:
        """Get metadata for a relationship type."""
        return cls.RELATIONSHIP_METADATA.get(
            relationship_type, cls.RELATIONSHIP_METADATA[RelationshipType.CUSTOM]
        )

    @classmethod
    def is_bidirectional(cls, relationship_type: RelationshipType) -> bool:
        """Check if relationship is bidirectional."""
<<<<<<< HEAD
        return cls.get_metadata(relationship_type)["bidirectional"]
=======
        return cls.get_metadata(relationship_type)['bidirectional']
>>>>>>> fixing_linting_and_tests

    @classmethod
    def is_transitive(cls, relationship_type: RelationshipType) -> bool:
        """Check if relationship is transitive."""
<<<<<<< HEAD
        return cls.get_metadata(relationship_type)["transitive"]
=======
        return cls.get_metadata(relationship_type)['transitive']
>>>>>>> fixing_linting_and_tests

    @classmethod
    def get_reverse_name(cls, relationship_type: RelationshipType) -> str:
        """Get the reverse relationship name."""
        return cls.get_metadata(relationship_type)["reverse_name"]


class RelationshipManager:
    """Manages relationships and their properties."""

    def __init__(self):
        """Initialize relationship manager."""
        self.custom_relationships: dict[str, dict] = {}
        self.relationship_constraints: dict[str, list[tuple[str, str]]] = {}
        self._initialize_constraints()

    def _initialize_constraints(self):
        """Initialize relationship constraints."""
        # Define which node types can have which relationships
        self.relationship_constraints = {
            RelationshipType.PREREQUISITE_OF.value: [
                ("ResearchNote", "ResearchNote"),
                ("ResearchNote", "LearningGoal"),
                ("LearningGoal", "LearningGoal"),
                ("Concept", "Concept"),
                ("Concept", "ResearchNote"),
                ("Concept", "LearningGoal"),
            ],
            RelationshipType.TEACHES.value: [
                ("ResearchNote", "Concept"),
                ("LearningGoal", "Concept"),
                ("Person", "Concept"),
                ("Person", "ResearchNote"),
            ],
            RelationshipType.TAGGED_WITH.value: [
                ("ResearchNote", "Tag"),
                ("LearningGoal", "Tag"),
                ("ProjectLog", "Tag"),
                ("BookmarkPlus", "Tag"),
            ],
            RelationshipType.AUTHORED_BY.value: [
                ("ResearchNote", "Person"),
                ("ProjectLog", "Person"),
                ("BookmarkPlus", "Person"),
            ],
        }

    def register_custom_relationship(self, name: str, metadata: dict):
        """Register a custom relationship type.

        Args:
            name: Name of the custom relationship
            metadata: Metadata dictionary with properties
        """
        required_fields = [
            "bidirectional",
            "transitive",
            "weight_range",
            "description",
            "reverse_name",
        ]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required field '{field}' in metadata")

        self.custom_relationships[name] = metadata

<<<<<<< HEAD
    def validate_relationship(
        self, source_type: str, target_type: str, relationship_type: str
    ) -> bool:
=======
    def validate_relationship(self, source_type: str, target_type: str,
                            relationship_type: str) -> bool:
>>>>>>> fixing_linting_and_tests
        """Validate if a relationship is allowed between node types.

        Args:
            source_type: Type of source node
            target_type: Type of target node
            relationship_type: Type of relationship

        Returns:
            True if relationship is valid
        """
        # Check if relationship type has constraints
        if relationship_type not in self.relationship_constraints:
            # No constraints defined, allow all
            return True

        # Check if the type pair is allowed
        allowed_pairs = self.relationship_constraints[relationship_type]
        return (source_type, target_type) in allowed_pairs

<<<<<<< HEAD
    def get_allowed_relationships(
        self, source_type: str, target_type: str
    ) -> list[str]:
=======
    def get_allowed_relationships(self, source_type: str, target_type: str) -> list[str]:
>>>>>>> fixing_linting_and_tests
        """Get allowed relationship types between two node types.

        Args:
            source_type: Type of source node
            target_type: Type of target node

        Returns:
            List of allowed relationship types
        """
        allowed = []

        # Check standard relationships
        for rel_type in RelationshipType:
            if rel_type.value in self.relationship_constraints:
                if (source_type, target_type) in self.relationship_constraints[
                    rel_type.value
                ]:
                    allowed.append(rel_type.value)
            else:
                # No constraints, allow
                allowed.append(rel_type.value)

        # Add custom relationships
        allowed.extend(self.custom_relationships.keys())

        return allowed

<<<<<<< HEAD
    def suggest_relationship_type(
        self, source_type: str, target_type: str, context: dict | None = None
    ) -> list[tuple[str, float]]:
=======
    def suggest_relationship_type(self, source_type: str, target_type: str,
                                 context: dict | None = None) -> list[tuple[str, float]]:
>>>>>>> fixing_linting_and_tests
        """Suggest appropriate relationship types with confidence scores.

        Args:
            source_type: Type of source node
            target_type: Type of target node
            context: Optional context information

        Returns:
            List of (relationship_type, confidence) tuples
        """
        suggestions = []

        # Get allowed relationships
        allowed = self.get_allowed_relationships(source_type, target_type)

        # Score based on common patterns
        scoring_rules = {
            ("ResearchNote", "ResearchNote"): {
                RelationshipType.RELATED_TO.value: 0.8,
                RelationshipType.BUILDS_ON.value: 0.7,
                RelationshipType.SUPPORTS.value: 0.6,
                RelationshipType.CITES.value: 0.6,
            },
            ("ResearchNote", "LearningGoal"): {
                RelationshipType.APPLIED_IN.value: 0.9,
                RelationshipType.SUPPORTS.value: 0.7,
                RelationshipType.RELATED_TO.value: 0.6,
            },
            ("LearningGoal", "ResearchNote"): {
                RelationshipType.LEARNED_FROM.value: 0.9,
                RelationshipType.DEPENDS_ON.value: 0.7,
                RelationshipType.RELATED_TO.value: 0.6,
            },
            ("ProjectLog", "ResearchNote"): {
                RelationshipType.USED_IN.value: 0.8,
                RelationshipType.APPLIED_IN.value: 0.7,
                RelationshipType.REFERENCES.value: 0.6,
            },
        }

        # Get scores for this type pair
        type_pair = (source_type, target_type)
        if type_pair in scoring_rules:
            for rel_type, score in scoring_rules[type_pair].items():
                if rel_type in allowed:
                    suggestions.append((rel_type, score))

        # Add remaining allowed relationships with lower scores
        suggested_types = {s[0] for s in suggestions}
        for rel_type in allowed:
            if rel_type not in suggested_types:
                suggestions.append((rel_type, 0.5))

        # Sort by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions

<<<<<<< HEAD
    def create_bidirectional_relationship(
        self,
        graph,
        source_uid: str,
        target_uid: str,
        relationship_type: RelationshipType,
        weight: float = 1.0,
    ):
=======
    def create_bidirectional_relationship(self, graph, source_uid: str, target_uid: str,
                                        relationship_type: RelationshipType, weight: float = 1.0):
>>>>>>> fixing_linting_and_tests
        """Create a bidirectional relationship if applicable.

        Args:
            graph: Graph instance
            source_uid: Source node UID
            target_uid: Target node UID
            relationship_type: Type of relationship
            weight: Relationship weight
        """
        from .model import Edge

        # Create forward edge
        forward_edge = Edge(source_uid, target_uid, relationship_type.value, weight)
        graph.add_edge(forward_edge)

        # Create reverse edge if bidirectional
        if RelationshipMetadata.is_bidirectional(relationship_type):
            reverse_edge = Edge(target_uid, source_uid, relationship_type.value, weight)
            graph.add_edge(reverse_edge)

<<<<<<< HEAD
    def infer_transitive_relationships(
        self, graph, relationship_type: RelationshipType
    ) -> list[tuple[str, str]]:
=======
    def infer_transitive_relationships(self, graph, relationship_type: RelationshipType) -> list[tuple[str, str]]:
>>>>>>> fixing_linting_and_tests
        """Infer transitive relationships in the graph.

        Args:
            graph: Graph instance
            relationship_type: Type of relationship to check

        Returns:
            List of (source_uid, target_uid) pairs for inferred relationships
        """
        if not RelationshipMetadata.is_transitive(relationship_type):
            return []

        inferred = []
        rel_type_value = relationship_type.value

        # Find all paths of this relationship type
        for node_uid in graph.nodes:
            # Do depth-first search for transitive paths
            visited = set()
            reachable = set()

            def dfs(current_uid: str, path_start: str):
                if current_uid in visited:
                    return
                visited.add(current_uid)

                # Get neighbors through this relationship type
                edges = graph.get_edges_from_node(current_uid, rel_type_value)
                for edge in edges:
                    if edge.target_uid != path_start:
                        reachable.add(edge.target_uid)
                        dfs(edge.target_uid, path_start)

            # Start DFS from this node
            dfs(node_uid, node_uid)

            # Check which relationships are missing
            for target_uid in reachable:
                if not graph.get_edge(node_uid, target_uid, rel_type_value):
                    inferred.append((node_uid, target_uid))

        return inferred
