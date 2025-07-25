#!/usr/bin/env python3
"""
Demo script for the BookmarkPlus Resource Quality Assessment System.

This script demonstrates the quality assessment functionality including:
- Quality score calculation
- Quality metrics analysis  
- Quality tracking over time
- Quality flagging system

Run with: python demo_quality_assessment.py
"""

from datetime import datetime, timedelta
from knowledge.curator.content.bookmark_plus import BookmarkPlus


def create_mock_bookmark(quality='medium', status='unread', has_content=False):
    """Create a mock bookmark for demonstration."""
    
    # Create a basic BookmarkPlus object (simplified for demo)
    class MockBookmark:
        def __init__(self):
            self.title = "Demo Resource"
            self.url = "https://example.com/resource"
            self.content_quality = quality
            self.read_status = status
            self.resource_type = "article"
            self.related_knowledge_items = []
            self.supports_learning_goals = []
            self.personal_notes = ""
            self.key_quotes = []
            self.description = ""
            self.ai_summary = ""
            self.created = datetime.now()
            self.publication_date = None
            self._annotations = {}
            
            if has_content:
                self.description = "A comprehensive resource about advanced topics"
                self.personal_notes = "This resource provides excellent insights into the subject matter. The author's approach is methodical and the examples are practical."
                self.key_quotes = [
                    "The key to understanding this concept is to break it down systematically",
                    "Real-world applications demonstrate the practical value of this approach",
                    "The relationship between theory and practice becomes clear through examples"
                ]
                self.related_knowledge_items = ["item1", "item2", "item3"]
                self.supports_learning_goals = ["goal1"]
                self.ai_summary = "AI-generated summary of the key concepts and insights"
        
        # Copy quality assessment methods from BookmarkPlus
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
                return 0.8
            elif read_status == 'in_progress':
                return 0.5
            elif read_status == 'archived':
                return 0.7
            else:  # unread
                return 0.1
        
        def _calculate_completeness_score(self):
            """Calculate score based on content completeness."""
            score = 0.0
            
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
            related_items = getattr(self, 'related_knowledge_items', [])
            if not related_items:
                return 0.0
            
            item_score = min(len(related_items) / 5.0, 1.0)
            learning_goals = getattr(self, 'supports_learning_goals', [])
            goal_score = min(len(learning_goals) / 3.0, 1.0) if learning_goals else 0.0
            
            return (item_score * 0.7) + (goal_score * 0.3)
        
        def _calculate_freshness_score(self):
            """Calculate freshness score for time-sensitive content."""
            resource_type = getattr(self, 'resource_type', 'article')
            if resource_type in ['book', 'course', 'reference']:
                return 0.8
            
            pub_date = getattr(self, 'publication_date', None)
            if not pub_date and hasattr(self, 'created'):
                pub_date = self.created
                
            if not pub_date:
                return 0.5
                
            age = (datetime.now() - pub_date).days
            
            if resource_type in ['news', 'blog_post']:
                if age < 30:
                    return 1.0
                elif age < 90:
                    return 0.7
                elif age < 365:
                    return 0.4
                else:
                    return 0.2
            else:
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
            
            notes = getattr(self, 'personal_notes', '')
            if notes:
                if len(notes) > 500:
                    score += 0.5
                elif len(notes) > 200:
                    score += 0.3
                else:
                    score += 0.1
            
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
            
            current_metrics = self.get_quality_metrics()
            current_metrics['timestamp'] = datetime.now().isoformat()
            
            quality_history.append(current_metrics)
            
            if len(quality_history) > 10:
                quality_history = quality_history[-10:]
            
            self._annotations['quality_history'] = quality_history
            self._update_quality_trend(quality_history)
        
        def _update_quality_trend(self, history):
            """Calculate and store quality trend."""
            if len(history) < 2:
                return
            
            recent_scores = [h['overall_score'] for h in history[-3:]]
            
            if len(recent_scores) >= 2:
                trend = recent_scores[-1] - recent_scores[0]
                
                if trend > 0.1:
                    self._annotations['quality_trend'] = 'improving'
                elif trend < -0.1:
                    self._annotations['quality_trend'] = 'declining'
                else:
                    self._annotations['quality_trend'] = 'stable'
        
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
        
        def is_flagged_for_review(self):
            """Check if resource is flagged for quality review."""
            flag_info = self._annotations.get('quality_flag', {})
            return flag_info.get('flagged', False)
    
    return MockBookmark()


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_metrics(bookmark, title):
    """Print quality metrics for a bookmark."""
    print(f"\n--- {title} ---")
    metrics = bookmark.get_quality_metrics()
    
    print(f"Overall Quality Score: {metrics['overall_score']:.3f}")
    print(f"Content Quality: {metrics['content_quality']}")
    print(f"Read Status: {metrics['read_status']}")
    print(f"Related Items: {metrics['related_items_count']}")
    print(f"Learning Goals: {metrics['supports_goals_count']}")
    print(f"Has Notes: {metrics['has_personal_notes']}")
    print(f"Key Quotes: {metrics['key_quotes_count']}")
    
    print("\nDetailed Scores:")
    print(f"  Engagement: {metrics['engagement_score']:.3f}")
    print(f"  Completeness: {metrics['completeness_score']:.3f}")
    print(f"  Learning Correlation: {metrics['learning_correlation_score']:.3f}")
    print(f"  Freshness: {metrics['freshness_score']:.3f}")
    print(f"  Annotation Quality: {metrics['annotation_score']:.3f}")


def demonstrate_quality_assessment():
    """Main demonstration function."""
    
    print_section("BookmarkPlus Resource Quality Assessment System Demo")
    
    print("""
This demo shows how the quality assessment system evaluates resources based on:
- Content quality rating
- User engagement (read status)
- Content completeness (notes, quotes, summaries)
- Learning correlation (knowledge items, goals)
- Content freshness (age and type)
- Annotation quality (depth of notes and quotes)
    """)
    
    # 1. Low-quality resource
    print_section("1. Low-Quality Resource Example")
    low_quality = create_mock_bookmark(quality='low', status='unread', has_content=False)
    print_metrics(low_quality, "Minimal Content Resource")
    
    # 2. Medium-quality resource
    print_section("2. Medium-Quality Resource Example")
    medium_quality = create_mock_bookmark(quality='medium', status='in_progress', has_content=False)
    medium_quality.description = "Basic description of the resource"
    medium_quality.related_knowledge_items = ["item1"]
    print_metrics(medium_quality, "Partially Developed Resource")
    
    # 3. High-quality resource
    print_section("3. High-Quality Resource Example")
    high_quality = create_mock_bookmark(quality='excellent', status='completed', has_content=True)
    print_metrics(high_quality, "Fully Developed Resource")
    
    # 4. Quality tracking over time
    print_section("4. Quality Tracking Over Time")
    print("\nDemonstrating quality improvement over time...")
    
    tracking_resource = create_mock_bookmark(quality='medium', status='unread', has_content=False)
    
    # Initial state
    tracking_resource.update_quality_tracking()
    initial_score = tracking_resource.get_quality_metrics()['overall_score']
    print(f"Initial quality score: {initial_score:.3f}")
    
    # Add some content
    tracking_resource.description = "Added description"
    tracking_resource.read_status = 'in_progress'
    tracking_resource.update_quality_tracking()
    mid_score = tracking_resource.get_quality_metrics()['overall_score']
    print(f"After adding description and starting: {mid_score:.3f}")
    
    # Complete with notes and quotes
    tracking_resource.read_status = 'completed'
    tracking_resource.personal_notes = "Detailed personal insights and analysis of the content"
    tracking_resource.key_quotes = ["Important insight", "Key takeaway"]
    tracking_resource.related_knowledge_items = ["item1", "item2"]
    tracking_resource.update_quality_tracking()
    final_score = tracking_resource.get_quality_metrics()['overall_score']
    print(f"After completion with annotations: {final_score:.3f}")
    print(f"Quality trend: {tracking_resource.get_quality_trend()}")
    
    # 5. Quality flagging system
    print_section("5. Quality Flagging System")
    
    # Flag low-quality resource
    if low_quality.get_quality_metrics()['overall_score'] < 0.3:
        low_quality.flag_for_quality_review("Automatically flagged for low quality score")
    
    print(f"Low-quality resource flagged: {low_quality.is_flagged_for_review()}")
    print(f"High-quality resource flagged: {high_quality.is_flagged_for_review()}")
    
    # 6. Different resource types and freshness
    print_section("6. Resource Type Impact on Quality")
    
    # Old news article
    old_news = create_mock_bookmark(quality='high', status='completed', has_content=True)
    old_news.resource_type = 'news'
    old_news.publication_date = datetime.now() - timedelta(days=400)
    
    # Timeless book
    book = create_mock_bookmark(quality='high', status='completed', has_content=True)
    book.resource_type = 'book'
    book.publication_date = datetime.now() - timedelta(days=400)
    
    print_metrics(old_news, "Old News Article")
    print_metrics(book, "Book (Age-Resistant)")
    
    print_section("Summary")
    print("""
The Quality Assessment System provides:

✓ Comprehensive quality scoring (0.0-1.0)
✓ Multi-factor analysis (engagement, completeness, correlation, freshness, annotations)
✓ Quality tracking over time
✓ Automatic flagging of low-quality resources
✓ Resource type-aware freshness scoring
✓ Learning correlation assessment

This helps identify high-value resources and flag content needing attention.
    """)


if __name__ == "__main__":
    demonstrate_quality_assessment()