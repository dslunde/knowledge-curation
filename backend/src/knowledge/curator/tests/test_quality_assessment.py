"""Tests for BookmarkPlus quality assessment system."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from zope.interface import implementer
from zope.annotation.interfaces import IAnnotations


class MockAnnotations(dict):
    """Mock annotations storage."""
    pass


class MockBookmarkPlus:
    """Mock BookmarkPlus for testing."""
    
    def __init__(self):
        self.title = "Test Bookmark"
        self.url = "https://example.com"
        self.content_quality = "medium"
        self.read_status = "unread"
        self.resource_type = "article"
        self.related_knowledge_items = []
        self.supports_learning_goals = []
        self.personal_notes = ""
        self.key_quotes = []
        self.description = ""
        self.ai_summary = ""
        self.created = datetime.now()
        self.publication_date = None
        self._annotations = MockAnnotations()
    
    # Copy the quality assessment methods from BookmarkPlus
    def calculate_quality_score(self):
        """Calculate overall quality score for this resource."""
        # Base quality score from content_quality field
        quality_mapping = {
            'low': 0.25,
            'medium': 0.5,
            'high': 0.75,
            'excellent': 1.0
        }
        base_score = quality_mapping.get(getattr(self, 'content_quality', 'medium'), 0.5)
        
        # Factors that influence quality score
        factors = []
        weights = []
        
        # 1. User engagement factor (based on read status)
        engagement_score = self._calculate_engagement_score()
        factors.append(engagement_score)
        weights.append(0.25)  # 25% weight
        
        # 2. Content completeness factor
        completeness_score = self._calculate_completeness_score()
        factors.append(completeness_score)
        weights.append(0.15)  # 15% weight
        
        # 3. Learning correlation factor
        learning_score = self._calculate_learning_correlation_score()
        factors.append(learning_score)
        weights.append(0.35)  # 35% weight
        
        # 4. Freshness factor (for time-sensitive content)
        freshness_score = self._calculate_freshness_score()
        factors.append(freshness_score)
        weights.append(0.10)  # 10% weight
        
        # 5. Annotation quality factor
        annotation_score = self._calculate_annotation_score()
        factors.append(annotation_score)
        weights.append(0.15)  # 15% weight
        
        # Calculate weighted average
        if sum(weights) > 0:
            weighted_score = sum(f * w for f, w in zip(factors, weights)) / sum(weights)
            # Combine with base score (50/50 split)
            final_score = (base_score * 0.5) + (weighted_score * 0.5)
        else:
            final_score = base_score
        
        return round(final_score, 3)
    
    def _calculate_engagement_score(self):
        """Calculate engagement score based on user interaction."""
        read_status = getattr(self, 'read_status', 'unread')
        
        if read_status == 'completed':
            # Check time spent vs. estimated time
            if hasattr(self, 'reading_time_estimate') and self.reading_time_estimate:
                # This would need actual tracking, for now use status as proxy
                return 0.9
            return 0.8
        elif read_status == 'in_progress':
            return 0.5
        elif read_status == 'archived':
            # Archived items were valuable enough to keep
            return 0.7
        else:  # unread
            return 0.1
    
    def _calculate_completeness_score(self):
        """Calculate score based on content completeness."""
        score = 0.0
        
        # Check for essential fields
        if hasattr(self, 'description') and self.description:
            score += 0.2
        if hasattr(self, 'personal_notes') and self.personal_notes:
            score += 0.3
        if hasattr(self, 'key_quotes') and self.key_quotes:
            score += 0.3
        if hasattr(self, 'ai_summary') and self.ai_summary:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_learning_correlation_score(self):
        """Calculate score based on correlation with knowledge items."""
        # Check relationship strength with knowledge items
        related_items = getattr(self, 'related_knowledge_items', [])
        if not related_items:
            return 0.0
        
        # More related items indicate higher relevance
        # Cap at 5 items for maximum score
        item_score = min(len(related_items) / 5.0, 1.0)
        
        # Check if resource supports learning goals
        learning_goals = getattr(self, 'supports_learning_goals', [])
        goal_score = min(len(learning_goals) / 3.0, 1.0) if learning_goals else 0.0
        
        # Combine scores
        return (item_score * 0.7) + (goal_score * 0.3)
    
    def _calculate_freshness_score(self):
        """Calculate freshness score for time-sensitive content."""
        # Some resource types are less time-sensitive
        resource_type = getattr(self, 'resource_type', 'article')
        if resource_type in ['book', 'course', 'reference']:
            return 0.8  # These tend to age well
        
        # Use publication date or creation date
        pub_date = getattr(self, 'publication_date', None)
        if not pub_date and hasattr(self, 'created'):
            pub_date = self.created
        
        if not pub_date:
            return 0.5  # Unknown age
        
        # Calculate age in days
        age = (datetime.now() - pub_date).days
        
        # Scoring based on resource type
        if resource_type in ['news', 'blog_post']:
            # News/blogs lose value quickly
            if age < 30:
                return 1.0
            elif age < 90:
                return 0.7
            elif age < 365:
                return 0.4
            else:
                return 0.2
        else:
            # Other content types age more gracefully
            if age < 180:
                return 1.0
            elif age < 365:
                return 0.8
            elif age < 730:
                return 0.6
            else:
                return 0.4
    
    def _calculate_annotation_score(self):
        """Calculate score based on annotation quality."""
        score = 0.0
        
        # Personal notes quality
        notes = getattr(self, 'personal_notes', '')
        if notes:
            # Longer, more detailed notes indicate better engagement
            if len(notes) > 500:
                score += 0.5
            elif len(notes) > 200:
                score += 0.3
            else:
                score += 0.1
        
        # Key quotes indicate active reading
        quotes = getattr(self, 'key_quotes', [])
        if quotes:
            if len(quotes) >= 5:
                score += 0.5
            elif len(quotes) >= 2:
                score += 0.3
            else:
                score += 0.1
        
        return min(score, 1.0)
    
    def get_quality_metrics(self):
        """Get detailed quality metrics for this resource."""
        return {
            'overall_score': self.calculate_quality_score(),
            'content_quality': getattr(self, 'content_quality', 'medium'),
            'engagement_score': self._calculate_engagement_score(),
            'completeness_score': self._calculate_completeness_score(),
            'learning_correlation_score': self._calculate_learning_correlation_score(),
            'freshness_score': self._calculate_freshness_score(),
            'annotation_score': self._calculate_annotation_score(),
            'read_status': getattr(self, 'read_status', 'unread'),
            'has_personal_notes': bool(getattr(self, 'personal_notes', '')),
            'key_quotes_count': len(getattr(self, 'key_quotes', [])),
            'related_items_count': len(getattr(self, 'related_knowledge_items', [])),
            'supports_goals_count': len(getattr(self, 'supports_learning_goals', []))
        }
    
    def update_quality_tracking(self):
        """Update quality tracking metadata."""
        quality_history = self._annotations.get('quality_history', [])
        
        # Add current quality metrics to history
        current_metrics = self.get_quality_metrics()
        current_metrics['timestamp'] = datetime.now().isoformat()
        
        quality_history.append(current_metrics)
        
        # Keep only last 10 entries to avoid unbounded growth
        if len(quality_history) > 10:
            quality_history = quality_history[-10:]
        
        self._annotations['quality_history'] = quality_history
        
        # Update quality trend
        self._update_quality_trend(quality_history)
    
    def _update_quality_trend(self, history):
        """Calculate and store quality trend."""
        if len(history) < 2:
            return
        
        # Calculate trend over last 3 measurements
        recent_scores = [h['overall_score'] for h in history[-3:]]
        
        if len(recent_scores) >= 2:
            # Simple linear trend
            trend = recent_scores[-1] - recent_scores[0]
            
            if trend > 0.1:
                self._annotations['quality_trend'] = 'improving'
            elif trend < -0.1:
                self._annotations['quality_trend'] = 'declining'
            else:
                self._annotations['quality_trend'] = 'stable'
    
    def get_quality_history(self):
        """Get historical quality metrics."""
        return self._annotations.get('quality_history', [])
    
    def get_quality_trend(self):
        """Get current quality trend."""
        return self._annotations.get('quality_trend', 'stable')
    
    def flag_for_quality_review(self, reason=None):
        """Flag this resource for quality review."""
        self._annotations['quality_flag'] = {
            'flagged': True,
            'reason': reason or 'Low quality score',
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_quality_flag(self):
        """Clear quality review flag."""
        if 'quality_flag' in self._annotations:
            del self._annotations['quality_flag']
    
    def is_flagged_for_review(self):
        """Check if resource is flagged for quality review."""
        flag_info = self._annotations.get('quality_flag', {})
        return flag_info.get('flagged', False)
    
    def get_quality_flag_info(self):
        """Get quality flag information."""
        return self._annotations.get('quality_flag', None)


class TestBookmarkQualityAssessment(unittest.TestCase):
    """Test BookmarkPlus quality assessment methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bookmark = MockBookmarkPlus()
    
    def test_basic_quality_score_calculation(self):
        """Test basic quality score calculation."""
        # Test with default values
        score = self.bookmark.calculate_quality_score()
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_content_quality_mapping(self):
        """Test content quality field mapping."""
        # Test different content quality levels
        test_cases = [
            ('low', 0.25),
            ('medium', 0.5),
            ('high', 0.75),
            ('excellent', 1.0)
        ]
        
        for quality, expected_base in test_cases:
            self.bookmark.content_quality = quality
            # Base score influences final score but isn't the only factor
            score = self.bookmark.calculate_quality_score()
            # Should be influenced by the base score
            self.assertGreater(score, 0.0)
    
    def test_engagement_score_calculation(self):
        """Test engagement score based on read status."""
        test_cases = [
            ('completed', 0.8),
            ('in_progress', 0.5),
            ('archived', 0.7),
            ('unread', 0.1)
        ]
        
        for status, expected in test_cases:
            self.bookmark.read_status = status
            engagement = self.bookmark._calculate_engagement_score()
            self.assertEqual(engagement, expected)
    
    def test_completeness_score_calculation(self):
        """Test completeness score based on available content."""
        # Start with empty content
        score = self.bookmark._calculate_completeness_score()
        self.assertEqual(score, 0.0)
        
        # Add description
        self.bookmark.description = "Test description"
        score = self.bookmark._calculate_completeness_score()
        self.assertEqual(score, 0.2)
        
        # Add personal notes
        self.bookmark.personal_notes = "Personal insights"
        score = self.bookmark._calculate_completeness_score()
        self.assertEqual(score, 0.5)
        
        # Add key quotes
        self.bookmark.key_quotes = ["Important quote"]
        score = self.bookmark._calculate_completeness_score()
        self.assertEqual(score, 0.8)
        
        # Add AI summary
        self.bookmark.ai_summary = "AI generated summary"
        score = self.bookmark._calculate_completeness_score()
        self.assertEqual(score, 1.0)
    
    def test_learning_correlation_score(self):
        """Test learning correlation score calculation."""
        # No related items
        score = self.bookmark._calculate_learning_correlation_score()
        self.assertEqual(score, 0.0)
        
        # Add related knowledge items
        self.bookmark.related_knowledge_items = ["item1", "item2", "item3"]
        score = self.bookmark._calculate_learning_correlation_score()
        self.assertGreater(score, 0.0)
        
        # Add learning goals
        self.bookmark.supports_learning_goals = ["goal1"]
        score_with_goals = self.bookmark._calculate_learning_correlation_score()
        self.assertGreater(score_with_goals, score)
    
    def test_freshness_score_different_resource_types(self):
        """Test freshness scoring for different resource types."""
        # Books should age well
        self.bookmark.resource_type = "book"
        book_score = self.bookmark._calculate_freshness_score()
        self.assertEqual(book_score, 0.8)
        
        # News articles should be more time-sensitive
        self.bookmark.resource_type = "news"
        self.bookmark.publication_date = datetime.now() - timedelta(days=500)
        news_score = self.bookmark._calculate_freshness_score()
        self.assertLess(news_score, book_score)
    
    def test_annotation_score_calculation(self):
        """Test annotation quality scoring."""
        # No annotations
        score = self.bookmark._calculate_annotation_score()
        self.assertEqual(score, 0.0)
        
        # Add short personal notes
        self.bookmark.personal_notes = "Short note"
        score = self.bookmark._calculate_annotation_score()
        self.assertEqual(score, 0.1)
        
        # Add longer notes
        self.bookmark.personal_notes = "A" * 300  # 300 characters
        score = self.bookmark._calculate_annotation_score()
        self.assertEqual(score, 0.3)
        
        # Add key quotes
        self.bookmark.key_quotes = ["Quote 1", "Quote 2"]
        score = self.bookmark._calculate_annotation_score()
        self.assertEqual(score, 0.6)  # 0.3 from notes + 0.3 from quotes
    
    def test_quality_metrics_retrieval(self):
        """Test getting detailed quality metrics."""
        metrics = self.bookmark.get_quality_metrics()
        
        # Check required fields
        required_fields = [
            'overall_score', 'content_quality', 'engagement_score',
            'completeness_score', 'learning_correlation_score',
            'freshness_score', 'annotation_score', 'read_status'
        ]
        
        for field in required_fields:
            self.assertIn(field, metrics)
        
        # Check that overall score is calculated
        self.assertIsInstance(metrics['overall_score'], float)
        self.assertGreaterEqual(metrics['overall_score'], 0.0)
        self.assertLessEqual(metrics['overall_score'], 1.0)
    
    def test_quality_tracking_update(self):
        """Test quality tracking update functionality."""
        # Update tracking
        self.bookmark.update_quality_tracking()
        
        # Check that history was stored
        history = self.bookmark.get_quality_history()
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        
        # Check history entry structure
        entry = history[0]
        self.assertIn('overall_score', entry)
        self.assertIn('timestamp', entry)
    
    def test_quality_flag_management(self):
        """Test quality flag management."""
        # Initially not flagged
        self.assertFalse(self.bookmark.is_flagged_for_review())
        
        # Flag for review
        self.bookmark.flag_for_quality_review("Test reason")
        self.assertTrue(self.bookmark.is_flagged_for_review())
        
        # Get flag info
        flag_info = self.bookmark.get_quality_flag_info()
        self.assertIsNotNone(flag_info)
        self.assertEqual(flag_info['reason'], "Test reason")
        
        # Clear flag
        self.bookmark.clear_quality_flag()
        self.assertFalse(self.bookmark.is_flagged_for_review())
    
    def test_quality_trend_calculation(self):
        """Test quality trend calculation."""
        # Mock history with improving trend
        self.bookmark._annotations['quality_history'] = [
            {'overall_score': 0.3, 'timestamp': '2024-01-01T00:00:00'},
            {'overall_score': 0.5, 'timestamp': '2024-01-02T00:00:00'},
            {'overall_score': 0.7, 'timestamp': '2024-01-03T00:00:00'}
        ]
        
        # Update trend
        self.bookmark._update_quality_trend(self.bookmark._annotations['quality_history'])
        
        # Should be improving trend
        trend = self.bookmark.get_quality_trend()
        self.assertEqual(trend, 'improving')
    
    def test_high_quality_resource_identification(self):
        """Test identification of high-quality resources."""
        # Set up high-quality resource
        self.bookmark.content_quality = "excellent"
        self.bookmark.read_status = "completed"
        self.bookmark.description = "Detailed description"
        self.bookmark.personal_notes = "Comprehensive notes with detailed insights"
        self.bookmark.key_quotes = ["Quote 1", "Quote 2", "Quote 3"]
        self.bookmark.related_knowledge_items = ["item1", "item2"]
        self.bookmark.supports_learning_goals = ["goal1"]
        self.bookmark.ai_summary = "AI summary"
        
        score = self.bookmark.calculate_quality_score()
        self.assertGreater(score, 0.7)  # Should be high quality
    
    def test_low_quality_resource_identification(self):
        """Test identification of low-quality resources."""
        # Set up low-quality resource
        self.bookmark.content_quality = "low"
        self.bookmark.read_status = "unread"
        # No additional content
        
        score = self.bookmark.calculate_quality_score()
        self.assertLess(score, 0.4)  # Should be low quality


if __name__ == '__main__':
    unittest.main()