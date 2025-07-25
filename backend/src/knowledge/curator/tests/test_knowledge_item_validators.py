"""Tests for Knowledge Item validators."""

import unittest
from zope.interface import Invalid
from knowledge.curator.content.validators import (
    validate_mastery_threshold,
    validate_learning_progress,
    validate_atomic_concepts,
    validate_uid_reference,
    validate_uid_references_list,
    validate_knowledge_type,
    validate_difficulty_level,
    validate_content_length,
    validate_title_length,
    validate_description_length,
    validate_tags,
    validate_embedding_vector,
    validate_no_self_reference,
    validate_circular_dependencies,
    validate_prerequisite_enables_consistency,
    validate_mastery_threshold_progress_consistency,
)


class TestKnowledgeItemValidators(unittest.TestCase):
    """Test Knowledge Item field validators."""
    
    def test_validate_mastery_threshold(self):
        """Test mastery threshold validation."""
        # Valid values
        self.assertTrue(validate_mastery_threshold(0.0))
        self.assertTrue(validate_mastery_threshold(0.5))
        self.assertTrue(validate_mastery_threshold(1.0))
        self.assertTrue(validate_mastery_threshold(None))  # Optional
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_mastery_threshold(-0.1)
        with self.assertRaises(Invalid):
            validate_mastery_threshold(1.1)
        with self.assertRaises(Invalid):
            validate_mastery_threshold("not a number")
    
    def test_validate_learning_progress(self):
        """Test learning progress validation."""
        # Valid values
        self.assertTrue(validate_learning_progress(0.0))
        self.assertTrue(validate_learning_progress(0.75))
        self.assertTrue(validate_learning_progress(1.0))
        self.assertTrue(validate_learning_progress(None))  # Optional
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_learning_progress(-0.5)
        with self.assertRaises(Invalid):
            validate_learning_progress(2.0)
        with self.assertRaises(Invalid):
            validate_learning_progress("invalid")
    
    def test_validate_atomic_concepts(self):
        """Test atomic concepts validation."""
        # Valid values
        self.assertTrue(validate_atomic_concepts(["Concept 1", "Concept 2"]))
        self.assertTrue(validate_atomic_concepts(["Single concept"]))
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_atomic_concepts([])  # Empty list
        with self.assertRaises(Invalid):
            validate_atomic_concepts("not a list")
        with self.assertRaises(Invalid):
            validate_atomic_concepts([123])  # Not strings
        with self.assertRaises(Invalid):
            validate_atomic_concepts(["ab"])  # Too short
        with self.assertRaises(Invalid):
            validate_atomic_concepts(["a" * 201])  # Too long
        with self.assertRaises(Invalid):
            validate_atomic_concepts(["valid", "valid"])  # Duplicates
        with self.assertRaises(Invalid):
            validate_atomic_concepts(["invalid@#$%"])  # Invalid characters
    
    def test_validate_knowledge_type(self):
        """Test knowledge type validation."""
        # Valid values
        self.assertTrue(validate_knowledge_type("factual"))
        self.assertTrue(validate_knowledge_type("conceptual"))
        self.assertTrue(validate_knowledge_type("procedural"))
        self.assertTrue(validate_knowledge_type("metacognitive"))
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_knowledge_type("invalid_type")
        with self.assertRaises(Invalid):
            validate_knowledge_type("")
        with self.assertRaises(Invalid):
            validate_knowledge_type(None)
    
    def test_validate_difficulty_level(self):
        """Test difficulty level validation."""
        # Valid values
        self.assertTrue(validate_difficulty_level("beginner"))
        self.assertTrue(validate_difficulty_level("intermediate"))
        self.assertTrue(validate_difficulty_level("advanced"))
        self.assertTrue(validate_difficulty_level("expert"))
        self.assertTrue(validate_difficulty_level(None))  # Optional
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_difficulty_level("super_easy")
        with self.assertRaises(Invalid):
            validate_difficulty_level("impossible")
    
    def test_validate_title_length(self):
        """Test title length validation."""
        # Valid values
        self.assertTrue(validate_title_length("Valid Title"))
        self.assertTrue(validate_title_length("A" * 100))
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_title_length("AB")  # Too short
        with self.assertRaises(Invalid):
            validate_title_length("A" * 201)  # Too long
        with self.assertRaises(Invalid):
            validate_title_length("")
        with self.assertRaises(Invalid):
            validate_title_length(None)
    
    def test_validate_description_length(self):
        """Test description length validation."""
        # Valid values
        self.assertTrue(validate_description_length("This is a valid description"))
        self.assertTrue(validate_description_length("A" * 1000))
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_description_length("Too short")  # Less than 10 chars
        with self.assertRaises(Invalid):
            validate_description_length("A" * 2001)  # Too long
        with self.assertRaises(Invalid):
            validate_description_length("")
        with self.assertRaises(Invalid):
            validate_description_length(None)
    
    def test_validate_tags(self):
        """Test tags validation."""
        # Valid values
        self.assertTrue(validate_tags(["tag1", "tag2", "tag-3", "tag_4"]))
        self.assertTrue(validate_tags([]))  # Empty is valid (optional)
        self.assertTrue(validate_tags(None))  # None is valid (optional)
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_tags("not a list")
        with self.assertRaises(Invalid):
            validate_tags(["a"])  # Too short
        with self.assertRaises(Invalid):
            validate_tags(["a" * 51])  # Too long
        with self.assertRaises(Invalid):
            validate_tags(["tag1", "tag1"])  # Duplicates
        with self.assertRaises(Invalid):
            validate_tags(["invalid@tag"])  # Invalid characters
    
    def test_validate_embedding_vector(self):
        """Test embedding vector validation."""
        # Valid values
        self.assertTrue(validate_embedding_vector([0.1] * 384))  # Common dimension
        self.assertTrue(validate_embedding_vector([0.5] * 768))  # BERT dimension
        self.assertTrue(validate_embedding_vector([-1.0, 0.0, 1.0] * 128))
        self.assertTrue(validate_embedding_vector(None))  # Optional
        
        # Invalid values
        with self.assertRaises(Invalid):
            validate_embedding_vector("not a list")
        with self.assertRaises(Invalid):
            validate_embedding_vector([])  # Empty
        with self.assertRaises(Invalid):
            validate_embedding_vector([0.1] * 100)  # Unusual dimension
        with self.assertRaises(Invalid):
            validate_embedding_vector(["not", "numbers"])
        with self.assertRaises(Invalid):
            validate_embedding_vector([200.0] * 384)  # Out of range


class TestKnowledgeItemInvariants(unittest.TestCase):
    """Test Knowledge Item invariant validators."""
    
    def test_validate_prerequisite_enables_consistency(self):
        """Test prerequisite/enables consistency validation."""
        # Mock data object
        class MockData:
            def __init__(self, prereqs=None, enables=None):
                self.prerequisite_items = prereqs or []
                self.enables_items = enables or []
        
        # Valid: no overlap
        data = MockData(["uid1", "uid2"], ["uid3", "uid4"])
        self.assertTrue(validate_prerequisite_enables_consistency(data))
        
        # Valid: empty lists
        data = MockData([], [])
        self.assertTrue(validate_prerequisite_enables_consistency(data))
        
        # Invalid: overlap
        data = MockData(["uid1", "uid2"], ["uid2", "uid3"])
        with self.assertRaises(Invalid):
            validate_prerequisite_enables_consistency(data)
    
    def test_validate_mastery_threshold_progress_consistency(self):
        """Test mastery threshold/progress consistency validation."""
        # Mock data object
        class MockData:
            def __init__(self, threshold=None, progress=None):
                self.mastery_threshold = threshold
                self.learning_progress = progress
        
        # Valid cases
        data = MockData(0.8, 0.5)
        self.assertTrue(validate_mastery_threshold_progress_consistency(data))
        
        data = MockData(0.8, 0.9)  # Progress can exceed threshold
        self.assertTrue(validate_mastery_threshold_progress_consistency(data))
        
        data = MockData(None, None)  # Both None is valid
        self.assertTrue(validate_mastery_threshold_progress_consistency(data))
        
        # Invalid cases
        data = MockData(1.5, 0.5)  # Threshold out of range
        with self.assertRaises(Invalid):
            validate_mastery_threshold_progress_consistency(data)
        
        data = MockData(0.8, -0.1)  # Progress out of range
        with self.assertRaises(Invalid):
            validate_mastery_threshold_progress_consistency(data)


if __name__ == '__main__':
    unittest.main()