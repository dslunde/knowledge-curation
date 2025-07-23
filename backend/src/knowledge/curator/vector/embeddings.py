# -*- coding: utf-8 -*-
"""Embedding generation utilities using sentence-transformers."""

from plone import api
from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional, Dict, Any
import logging
import numpy as np

logger = logging.getLogger("knowledge.curator.vector")


class EmbeddingGenerator:
    """Generate embeddings for text content using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the embedding model."""
        self.model_name = model_name
        self._model = None
        self._model_info = None
        
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self._model_info = {
                "max_seq_length": self._model.max_seq_length,
                "embedding_dimension": self._model.get_sentence_embedding_dimension()
            }
        return self._model
        
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        if self._model_info is None:
            _ = self.model  # Force model loading
        return self._model_info["embedding_dimension"]
        
    @property
    def max_sequence_length(self) -> int:
        """Get the maximum sequence length."""
        if self._model_info is None:
            _ = self.model  # Force model loading
        return self._model_info["max_seq_length"]
        
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dimension
            
        try:
            # Truncate text if needed
            if len(text) > self.max_sequence_length * 4:  # Rough character estimate
                text = text[:self.max_sequence_length * 4]
                
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.embedding_dimension
            
    def generate_embeddings(self, texts: List[str], batch_size: int = 32,
                          show_progress: bool = False) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        if not texts:
            return []
            
        try:
            # Filter empty texts and remember their indices
            valid_indices = []
            valid_texts = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_indices.append(i)
                    # Truncate if needed
                    if len(text) > self.max_sequence_length * 4:
                        text = text[:self.max_sequence_length * 4]
                    valid_texts.append(text)
                    
            # Generate embeddings for valid texts
            if valid_texts:
                embeddings = self.model.encode(
                    valid_texts,
                    batch_size=batch_size,
                    show_progress_bar=show_progress,
                    convert_to_numpy=True
                )
                embeddings_list = embeddings.tolist()
            else:
                embeddings_list = []
                
            # Create result list with zero vectors for empty texts
            result = []
            valid_idx = 0
            for i in range(len(texts)):
                if i in valid_indices:
                    result.append(embeddings_list[valid_idx])
                    valid_idx += 1
                else:
                    result.append([0.0] * self.embedding_dimension)
                    
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [[0.0] * self.embedding_dimension] * len(texts)
            
    def prepare_content_text(self, content_object) -> str:
        """Prepare text from a Plone content object for embedding."""
        try:
            parts = []
            
            # Add title
            title = getattr(content_object, "title", "")
            if title:
                parts.append(f"Title: {title}")
                
            # Add description
            description = getattr(content_object, "description", "")
            if description:
                parts.append(f"Description: {description}")
                
            # Add content type specific fields
            content_type = content_object.portal_type
            
            if content_type == "BookmarkPlus":
                # Add URL and notes
                url = getattr(content_object, "url", "")
                if url:
                    parts.append(f"URL: {url}")
                    
                notes = getattr(content_object, "notes", None)
                if notes and hasattr(notes, "output"):
                    parts.append(f"Notes: {notes.output}")
                    
                # Add tags
                tags = getattr(content_object, "tags", [])
                if tags:
                    parts.append(f"Tags: {', '.join(tags)}")
                    
            elif content_type == "ResearchNote":
                # Add content
                content = getattr(content_object, "content", None)
                if content and hasattr(content, "output"):
                    parts.append(f"Content: {content.output[:2000]}")  # Limit length
                    
                # Add key findings
                key_findings = getattr(content_object, "key_findings", [])
                if key_findings:
                    parts.append(f"Key Findings: {'; '.join(key_findings)}")
                    
                # Add tags
                tags = getattr(content_object, "tags", [])
                if tags:
                    parts.append(f"Tags: {', '.join(tags)}")
                    
            elif content_type == "LearningGoal":
                # Add goal description
                goal_description = getattr(content_object, "goal_description", None)
                if goal_description and hasattr(goal_description, "output"):
                    parts.append(f"Goal: {goal_description.output}")
                    
                # Add target date
                target_date = getattr(content_object, "target_date", None)
                if target_date:
                    parts.append(f"Target Date: {target_date}")
                    
                # Add success criteria
                success_criteria = getattr(content_object, "success_criteria", [])
                if success_criteria:
                    parts.append(f"Success Criteria: {'; '.join(success_criteria)}")
                    
            elif content_type == "ProjectLog":
                # Add project status
                project_status = getattr(content_object, "project_status", "")
                if project_status:
                    parts.append(f"Status: {project_status}")
                    
                # Add latest update
                latest_update = getattr(content_object, "latest_update", None)
                if latest_update and hasattr(latest_update, "output"):
                    parts.append(f"Latest Update: {latest_update.output[:1000]}")
                    
                # Add next steps
                next_steps = getattr(content_object, "next_steps", [])
                if next_steps:
                    parts.append(f"Next Steps: {'; '.join(next_steps[:5])}")
                    
            # Join all parts
            text = "\n\n".join(parts)
            return text
            
        except Exception as e:
            logger.error(f"Failed to prepare content text: {e}")
            return ""
            
    def calculate_similarity(self, embedding1: List[float], 
                           embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0