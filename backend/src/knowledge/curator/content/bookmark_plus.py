"""BookmarkPlus content type."""

from datetime import datetime
from knowledge.curator.interfaces import IBookmarkPlus
from plone.dexterity.content import Item
from zope.interface import implementer
from zope.lifecycleevent import modified


@implementer(IBookmarkPlus)
class BookmarkPlus(Item):
    """BookmarkPlus content type implementation."""

    def __init__(self, *args, **kwargs):
        """Initialize the bookmark with proper defaults."""
        super(BookmarkPlus, self).__init__(*args, **kwargs)
        # Set access_date on creation if not already set
        if not hasattr(self, 'access_date') or self.access_date is None:
            self.access_date = datetime.now()

    def get_embedding(self):
        """Get the embedding vector for this bookmark."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector

    def update_read_status(self, new_status):
        """Update read status with automatic timestamp updates.
        
        Args:
            new_status: One of 'unread', 'in_progress', 'completed', 'archived'
        """
        valid_statuses = ["unread", "in_progress", "completed", "archived"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
        
        old_status = getattr(self, 'read_status', 'unread')
        self.read_status = new_status
        
        # Update timestamps based on status changes
        now = datetime.now()
        
        # Set access_date on first access (if moving from unread)
        if old_status == "unread" and new_status != "unread":
            if not hasattr(self, 'access_date') or self.access_date is None:
                self.access_date = now
        
        # Update last_reviewed_date when marking as completed or archived
        if new_status in ["completed", "archived"]:
            self.last_reviewed_date = now
        
        # Notify that object has been modified
        modified(self)

    def mark_as_read(self):
        """Mark the bookmark as completed (for backwards compatibility)."""
        self.update_read_status("completed")

    def mark_as_reading(self):
        """Mark the bookmark as in progress (for backwards compatibility)."""
        self.update_read_status("in_progress")

    def get_read_date(self):
        """Get the date when bookmark was marked as read."""
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(self)
        return annotations.get("bookmark_read_date", None)

    def get_reading_started_date(self):
        """Get the date when started reading."""
        from zope.annotation.interfaces import IAnnotations

        annotations = IAnnotations(self)
        return annotations.get("bookmark_reading_started", None)

    def add_tag(self, tag):
        """Add a tag to the bookmark."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag):
        """Remove a tag from the bookmark."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def update_importance(self, new_importance):
        """Update bookmark importance with validation."""
        valid_levels = ["low", "medium", "high", "critical"]
        if new_importance in valid_levels:
            self.importance = new_importance
            return True
        return False

    def is_high_priority(self):
        """Check if bookmark is high priority (unread and high/critical importance)."""
        return self.read_status == "unread" and self.importance in ["high", "critical"]

    def get_summary_text(self):
        """Get text for generating embeddings/summaries."""
        # Combine title, description, and notes for embedding generation
        parts = [self.title]
        if self.description:
            parts.append(self.description)
        if self.notes and self.notes.raw:
            parts.append(self.notes.raw)
        return " ".join(parts)

    # Quality Assessment Methods
    def calculate_quality_score(self):
        """Calculate overall quality score for this resource.
        
        Returns:
            float: Quality score between 0.0 and 1.0
        """
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
        
        # For other types, check age
        from datetime import datetime, timedelta
        
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
        """Get detailed quality metrics for this resource.
        
        Returns:
            dict: Detailed breakdown of quality metrics
        """
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
        """Update quality tracking metadata.
        
        This method should be called periodically to track quality changes over time.
        """
        from zope.annotation.interfaces import IAnnotations
        from datetime import datetime
        
        annotations = IAnnotations(self)
        quality_history = annotations.get('quality_history', [])
        
        # Add current quality metrics to history
        current_metrics = self.get_quality_metrics()
        current_metrics['timestamp'] = datetime.now().isoformat()
        
        quality_history.append(current_metrics)
        
        # Keep only last 10 entries to avoid unbounded growth
        if len(quality_history) > 10:
            quality_history = quality_history[-10:]
        
        annotations['quality_history'] = quality_history
        
        # Update quality trend
        self._update_quality_trend(quality_history)
    
    def _update_quality_trend(self, history):
        """Calculate and store quality trend."""
        from zope.annotation.interfaces import IAnnotations
        
        if len(history) < 2:
            return
        
        # Calculate trend over last 3 measurements
        recent_scores = [h['overall_score'] for h in history[-3:]]
        
        if len(recent_scores) >= 2:
            # Simple linear trend
            trend = recent_scores[-1] - recent_scores[0]
            
            annotations = IAnnotations(self)
            if trend > 0.1:
                annotations['quality_trend'] = 'improving'
            elif trend < -0.1:
                annotations['quality_trend'] = 'declining'
            else:
                annotations['quality_trend'] = 'stable'
    
    def get_quality_history(self):
        """Get historical quality metrics.
        
        Returns:
            list: List of historical quality measurements
        """
        from zope.annotation.interfaces import IAnnotations
        
        annotations = IAnnotations(self)
        return annotations.get('quality_history', [])
    
    def get_quality_trend(self):
        """Get current quality trend.
        
        Returns:
            str: 'improving', 'declining', or 'stable'
        """
        from zope.annotation.interfaces import IAnnotations
        
        annotations = IAnnotations(self)
        return annotations.get('quality_trend', 'stable')
    
    def flag_for_quality_review(self, reason=None):
        """Flag this resource for quality review.
        
        Args:
            reason (str): Optional reason for flagging
        """
        from zope.annotation.interfaces import IAnnotations
        from datetime import datetime
        
        annotations = IAnnotations(self)
        annotations['quality_flag'] = {
            'flagged': True,
            'reason': reason or 'Low quality score',
            'timestamp': datetime.now().isoformat()
        }
        
        # Notify that object has been modified
        modified(self)
    
    def clear_quality_flag(self):
        """Clear quality review flag."""
        from zope.annotation.interfaces import IAnnotations
        
        annotations = IAnnotations(self)
        if 'quality_flag' in annotations:
            del annotations['quality_flag']
            modified(self)
    
    def is_flagged_for_review(self):
        """Check if resource is flagged for quality review.
        
        Returns:
            bool: True if flagged for review
        """
        from zope.annotation.interfaces import IAnnotations
        
        annotations = IAnnotations(self)
        flag_info = annotations.get('quality_flag', {})
        return flag_info.get('flagged', False)
    
    def get_quality_flag_info(self):
        """Get quality flag information.
        
        Returns:
            dict: Flag information or None
        """
        from zope.annotation.interfaces import IAnnotations
        
        annotations = IAnnotations(self)
        return annotations.get('quality_flag', None)
    
    # Learning Goal Support Tracking Methods
    def track_learning_goal_support(self, learning_goal_uid, effectiveness_score=None, user_satisfaction=None, notes=None):
        """Track how this resource supports a specific learning goal.
        
        Args:
            learning_goal_uid (str): UID of the learning goal
            effectiveness_score (float): Score between 0.0 and 1.0 indicating effectiveness
            user_satisfaction (int): Satisfaction rating between 1 and 5
            notes (str): Optional notes about the support relationship
        
        Returns:
            bool: True if tracking was successful
        """
        from zope.annotation.interfaces import IAnnotations
        from datetime import datetime
        
        if learning_goal_uid not in getattr(self, 'supports_learning_goals', []):
            return False
        
        annotations = IAnnotations(self)
        tracking_key = f'learning_goal_tracking_{learning_goal_uid}'
        
        # Get existing tracking data
        tracking_data = annotations.get(tracking_key, {
            'learning_goal_uid': learning_goal_uid,
            'effectiveness_scores': [],
            'satisfaction_ratings': [],
            'support_sessions': [],
            'total_time_spent': 0,
            'completion_contributed': False,
            'mastery_improvement': 0.0,
            'created': datetime.now().isoformat()
        })
        
        # Update tracking data
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'read_status': getattr(self, 'read_status', 'unread'),
            'notes': notes
        }
        
        if effectiveness_score is not None:
            if 0.0 <= effectiveness_score <= 1.0:
                tracking_data['effectiveness_scores'].append({
                    'score': effectiveness_score,
                    'timestamp': datetime.now().isoformat()
                })
                session_data['effectiveness_score'] = effectiveness_score
        
        if user_satisfaction is not None:
            if 1 <= user_satisfaction <= 5:
                tracking_data['satisfaction_ratings'].append({
                    'rating': user_satisfaction,
                    'timestamp': datetime.now().isoformat()
                })
                session_data['user_satisfaction'] = user_satisfaction
        
        tracking_data['support_sessions'].append(session_data)
        tracking_data['last_accessed'] = datetime.now().isoformat()
        
        annotations[tracking_key] = tracking_data
        modified(self)
        
        return True
    
    def get_learning_goal_support_data(self, learning_goal_uid):
        """Get support tracking data for a specific learning goal.
        
        Args:
            learning_goal_uid (str): UID of the learning goal
            
        Returns:
            dict: Support tracking data or None if not found
        """
        from zope.annotation.interfaces import IAnnotations
        
        annotations = IAnnotations(self)
        tracking_key = f'learning_goal_tracking_{learning_goal_uid}'
        return annotations.get(tracking_key, None)
    
    def calculate_learning_goal_effectiveness(self, learning_goal_uid):
        """Calculate effectiveness metrics for supporting a learning goal.
        
        Args:
            learning_goal_uid (str): UID of the learning goal
            
        Returns:
            dict: Effectiveness metrics
        """
        tracking_data = self.get_learning_goal_support_data(learning_goal_uid)
        if not tracking_data:
            return None
            
        from statistics import mean
        from datetime import datetime, timedelta
        
        metrics = {
            'average_effectiveness': 0.0,
            'average_satisfaction': 0.0,
            'engagement_score': 0.0,
            'consistency_score': 0.0,
            'recent_trend': 'stable',
            'total_sessions': len(tracking_data.get('support_sessions', [])),
            'completion_rate': 0.0,
            'time_to_impact': None,
            'recommendation_strength': 'medium'
        }
        
        # Calculate average effectiveness
        effectiveness_scores = tracking_data.get('effectiveness_scores', [])
        if effectiveness_scores:
            scores = [s['score'] for s in effectiveness_scores]
            metrics['average_effectiveness'] = round(mean(scores), 3)
        
        # Calculate average satisfaction
        satisfaction_ratings = tracking_data.get('satisfaction_ratings', [])
        if satisfaction_ratings:
            ratings = [r['rating'] for r in satisfaction_ratings]
            metrics['average_satisfaction'] = round(mean(ratings), 1)
        
        # Calculate engagement score based on session frequency and read status
        sessions = tracking_data.get('support_sessions', [])
        if sessions:
            # Check read status progression
            read_statuses = [s.get('read_status', 'unread') for s in sessions]
            status_progression = {
                'unread': 0, 'in_progress': 0.5, 'completed': 1.0, 'archived': 0.8
            }
            engagement_values = [status_progression.get(status, 0) for status in read_statuses]
            if engagement_values:
                metrics['engagement_score'] = round(max(engagement_values), 2)
        
        # Calculate consistency score based on session frequency
        if len(sessions) >= 2:
            session_dates = []
            for session in sessions:
                try:
                    session_dates.append(datetime.fromisoformat(session['timestamp']))
                except:
                    continue
            
            if len(session_dates) >= 2:
                session_dates.sort()
                intervals = []
                for i in range(1, len(session_dates)):
                    interval = (session_dates[i] - session_dates[i-1]).days
                    intervals.append(interval)
                
                # Consistency is higher with regular intervals
                if intervals:
                    avg_interval = mean(intervals)
                    if avg_interval <= 7:  # Weekly or more frequent
                        metrics['consistency_score'] = 1.0
                    elif avg_interval <= 14:  # Bi-weekly
                        metrics['consistency_score'] = 0.8
                    elif avg_interval <= 30:  # Monthly
                        metrics['consistency_score'] = 0.6
                    else:
                        metrics['consistency_score'] = 0.3
        
        # Calculate completion rate
        completed_sessions = sum(1 for s in sessions if s.get('read_status') == 'completed')
        if sessions:
            metrics['completion_rate'] = round(completed_sessions / len(sessions), 2)
        
        # Determine recent trend
        if len(effectiveness_scores) >= 3:
            recent_scores = [s['score'] for s in effectiveness_scores[-3:]]
            if recent_scores[-1] > recent_scores[0] + 0.1:
                metrics['recent_trend'] = 'improving'
            elif recent_scores[-1] < recent_scores[0] - 0.1:
                metrics['recent_trend'] = 'declining'
        
        # Calculate time to impact
        if effectiveness_scores and sessions:
            try:
                first_session = datetime.fromisoformat(sessions[0]['timestamp'])
                first_effective_score = next(
                    (s for s in effectiveness_scores if s['score'] >= 0.7), None
                )
                if first_effective_score:
                    effective_date = datetime.fromisoformat(first_effective_score['timestamp'])
                    metrics['time_to_impact'] = (effective_date - first_session).days
            except:
                pass
        
        # Determine recommendation strength
        overall_score = (
            metrics['average_effectiveness'] * 0.4 +
            (metrics['average_satisfaction'] / 5.0) * 0.3 +
            metrics['engagement_score'] * 0.2 +
            metrics['consistency_score'] * 0.1
        )
        
        if overall_score >= 0.8:
            metrics['recommendation_strength'] = 'high'
        elif overall_score >= 0.6:
            metrics['recommendation_strength'] = 'medium'
        else:
            metrics['recommendation_strength'] = 'low'
        
        return metrics
    
    def get_all_learning_goal_metrics(self):
        """Get effectiveness metrics for all supported learning goals.
        
        Returns:
            dict: Learning goal UIDs mapped to their effectiveness metrics
        """
        supported_goals = getattr(self, 'supports_learning_goals', [])
        metrics = {}
        
        for goal_uid in supported_goals:
            goal_metrics = self.calculate_learning_goal_effectiveness(goal_uid)
            if goal_metrics:
                metrics[goal_uid] = goal_metrics
        
        return metrics
    
    def update_mastery_improvement(self, learning_goal_uid, improvement_score):
        """Update the mastery improvement score for a learning goal.
        
        Args:
            learning_goal_uid (str): UID of the learning goal
            improvement_score (float): Improvement in mastery (0.0-1.0)
        """
        from zope.annotation.interfaces import IAnnotations
        from datetime import datetime
        
        annotations = IAnnotations(self)
        tracking_key = f'learning_goal_tracking_{learning_goal_uid}'
        tracking_data = annotations.get(tracking_key, {})
        
        if tracking_data:
            tracking_data['mastery_improvement'] = improvement_score
            tracking_data['mastery_updated'] = datetime.now().isoformat()
            annotations[tracking_key] = tracking_data
            modified(self)
    
    def mark_completion_contributed(self, learning_goal_uid):
        """Mark that this resource contributed to completing a learning goal.
        
        Args:
            learning_goal_uid (str): UID of the learning goal
        """
        from zope.annotation.interfaces import IAnnotations
        from datetime import datetime
        
        annotations = IAnnotations(self)
        tracking_key = f'learning_goal_tracking_{learning_goal_uid}'
        tracking_data = annotations.get(tracking_key, {})
        
        if tracking_data:
            tracking_data['completion_contributed'] = True
            tracking_data['completion_date'] = datetime.now().isoformat()
            annotations[tracking_key] = tracking_data
            modified(self)
    
    def get_learning_goal_support_summary(self):
        """Get a summary of learning goal support effectiveness.
        
        Returns:
            dict: Summary of support metrics across all learning goals
        """
        supported_goals = getattr(self, 'supports_learning_goals', [])
        if not supported_goals:
            return {
                'total_goals_supported': 0,
                'average_effectiveness': 0.0,
                'average_satisfaction': 0.0,
                'high_impact_goals': [],
                'low_impact_goals': [],
                'completion_contributions': 0,
                'overall_support_rating': 'none'
            }
        
        all_metrics = self.get_all_learning_goal_metrics()
        
        summary = {
            'total_goals_supported': len(supported_goals),
            'goals_with_data': len(all_metrics),
            'average_effectiveness': 0.0,
            'average_satisfaction': 0.0,
            'high_impact_goals': [],
            'low_impact_goals': [],
            'completion_contributions': 0,
            'overall_support_rating': 'low'
        }
        
        if all_metrics:
            # Calculate averages
            effectiveness_scores = [m['average_effectiveness'] for m in all_metrics.values() if m['average_effectiveness'] > 0]
            satisfaction_scores = [m['average_satisfaction'] for m in all_metrics.values() if m['average_satisfaction'] > 0]
            
            if effectiveness_scores:
                from statistics import mean
                summary['average_effectiveness'] = round(mean(effectiveness_scores), 3)
            
            if satisfaction_scores:
                from statistics import mean
                summary['average_satisfaction'] = round(mean(satisfaction_scores), 1)
            
            # Identify high and low impact goals
            for goal_uid, metrics in all_metrics.items():
                if metrics['recommendation_strength'] == 'high':
                    summary['high_impact_goals'].append(goal_uid)
                elif metrics['recommendation_strength'] == 'low':
                    summary['low_impact_goals'].append(goal_uid)
            
            # Count completion contributions
            from zope.annotation.interfaces import IAnnotations
            annotations = IAnnotations(self)
            
            for goal_uid in supported_goals:
                tracking_key = f'learning_goal_tracking_{goal_uid}'
                tracking_data = annotations.get(tracking_key, {})
                if tracking_data.get('completion_contributed', False):
                    summary['completion_contributions'] += 1
            
            # Overall support rating
            overall_score = summary['average_effectiveness']
            if overall_score >= 0.8:
                summary['overall_support_rating'] = 'excellent'
            elif overall_score >= 0.6:
                summary['overall_support_rating'] = 'good'
            elif overall_score >= 0.4:
                summary['overall_support_rating'] = 'fair'
            else:
                summary['overall_support_rating'] = 'poor'
        
        return summary
    
    # Utility methods for easier integration
    def get_supported_learning_goals_with_data(self):
        """Get learning goals this resource supports along with their effectiveness data.
        
        Returns:
            list: List of dicts with goal info and support metrics
        """
        from plone import api
        
        supported_goals = getattr(self, 'supports_learning_goals', [])
        if not supported_goals:
            return []
        
        catalog = api.portal.get_tool("portal_catalog")
        goals_with_data = []
        
        for goal_uid in supported_goals:
            goal_brains = catalog(UID=goal_uid)
            if goal_brains:
                goal_brain = goal_brains[0]
                effectiveness_data = self.calculate_learning_goal_effectiveness(goal_uid)
                
                goal_info = {
                    'uid': goal_uid,
                    'title': goal_brain.Title,
                    'url': goal_brain.getURL(),
                    'priority': getattr(goal_brain.getObject(), 'priority', 'medium'),
                    'progress': getattr(goal_brain.getObject(), 'progress', 0),
                    'effectiveness_score': effectiveness_data['average_effectiveness'] if effectiveness_data else 0.0,
                    'satisfaction_score': effectiveness_data['average_satisfaction'] if effectiveness_data else 0.0,
                    'recommendation_strength': effectiveness_data['recommendation_strength'] if effectiveness_data else 'low',
                    'has_tracking_data': effectiveness_data is not None
                }
                goals_with_data.append(goal_info)
        
        # Sort by effectiveness score
        goals_with_data.sort(key=lambda x: x['effectiveness_score'], reverse=True)
        return goals_with_data
    
    def add_learning_goal_support(self, learning_goal_uid):
        """Add support for a learning goal (bidirectional linking helper).
        
        Args:
            learning_goal_uid (str): UID of the learning goal to support
            
        Returns:
            bool: True if successfully added
        """
        from plone import api
        
        # Check if goal exists
        catalog = api.portal.get_tool("portal_catalog")
        goal_brains = catalog(UID=learning_goal_uid)
        if not goal_brains:
            return False
        
        # Add to supports_learning_goals if not already there
        current_goals = list(getattr(self, 'supports_learning_goals', []))
        if learning_goal_uid not in current_goals:
            current_goals.append(learning_goal_uid)
            self.supports_learning_goals = current_goals
            modified(self)
            return True
        
        return False
    
    def remove_learning_goal_support(self, learning_goal_uid):
        """Remove support for a learning goal and clean up tracking data.
        
        Args:
            learning_goal_uid (str): UID of the learning goal to remove support for
            
        Returns:
            bool: True if successfully removed
        """
        current_goals = list(getattr(self, 'supports_learning_goals', []))
        if learning_goal_uid in current_goals:
            current_goals.remove(learning_goal_uid)
            self.supports_learning_goals = current_goals
            
            # Clean up tracking data
            from zope.annotation.interfaces import IAnnotations
            annotations = IAnnotations(self)
            tracking_key = f'learning_goal_tracking_{learning_goal_uid}'
            if tracking_key in annotations:
                del annotations[tracking_key]
            
            modified(self)
            return True
        
        return False
    
    def get_learning_goal_impact_report(self):
        """Generate a comprehensive impact report for this resource.
        
        Returns:
            dict: Detailed impact analysis
        """
        summary = self.get_learning_goal_support_summary()
        all_metrics = self.get_all_learning_goal_metrics()
        
        report = {
            'resource_info': {
                'title': self.title,
                'url': getattr(self, 'absolute_url', lambda: '#')(),
                'resource_type': getattr(self, 'resource_type', 'unknown'),
                'content_quality': getattr(self, 'content_quality', 'medium'),
                'read_status': getattr(self, 'read_status', 'unread'),
                'creation_date': getattr(self, 'created', lambda: None)(),
                'last_modified': getattr(self, 'modified', lambda: None)()
            },
            'overall_impact': {
                'support_rating': summary['overall_support_rating'],
                'total_goals_supported': summary['total_goals_supported'],
                'average_effectiveness': summary['average_effectiveness'],
                'average_satisfaction': summary['average_satisfaction'],
                'completion_contributions': summary['completion_contributions']
            },
            'goal_breakdown': [],
            'usage_insights': {
                'most_effective_goal': None,
                'least_effective_goal': None,
                'consistency_patterns': [],
                'engagement_trends': []
            },
            'recommendations': []
        }
        
        # Process individual goal metrics
        best_effectiveness = 0
        worst_effectiveness = 1
        best_goal = None
        worst_goal = None
        
        for goal_uid, metrics in all_metrics.items():
            goal_data = {
                'goal_uid': goal_uid,
                'effectiveness': metrics['average_effectiveness'],
                'satisfaction': metrics['average_satisfaction'],
                'sessions': metrics['total_sessions'],
                'engagement': metrics['engagement_score'],
                'consistency': metrics['consistency_score'],
                'trend': metrics['recent_trend'],
                'recommendation_strength': metrics['recommendation_strength']
            }
            
            # Track best and worst performing goals
            if metrics['average_effectiveness'] > best_effectiveness:
                best_effectiveness = metrics['average_effectiveness']
                best_goal = goal_uid
            
            if metrics['average_effectiveness'] < worst_effectiveness and metrics['average_effectiveness'] > 0:
                worst_effectiveness = metrics['average_effectiveness']
                worst_goal = goal_uid
            
            report['goal_breakdown'].append(goal_data)
        
        # Add insights
        if best_goal:
            report['usage_insights']['most_effective_goal'] = best_goal
        if worst_goal:
            report['usage_insights']['least_effective_goal'] = worst_goal
        
        # Generate recommendations
        if summary['average_effectiveness'] < 0.5:
            report['recommendations'].append({
                'type': 'quality_improvement',
                'priority': 'high',
                'message': 'This resource has low overall effectiveness. Consider supplementing with additional materials or improving content quality.',
                'suggested_actions': ['Add complementary resources', 'Review content quality', 'Gather user feedback']
            })
        
        if summary['completion_contributions'] == 0 and summary['total_goals_supported'] > 0:
            report['recommendations'].append({
                'type': 'engagement_improvement',
                'priority': 'medium',
                'message': 'This resource has not contributed to any learning goal completions yet.',
                'suggested_actions': ['Add practical exercises', 'Create assessment materials', 'Set completion milestones']
            })
        
        declining_goals = [g for g in report['goal_breakdown'] if g['trend'] == 'declining']
        if declining_goals:
            report['recommendations'].append({
                'type': 'trend_alert',
                'priority': 'medium',
                'message': f'Effectiveness is declining for {len(declining_goals)} learning goals.',
                'suggested_actions': ['Review recent usage patterns', 'Update resource content', 'Add fresh perspectives'],
                'affected_goals': [g['goal_uid'] for g in declining_goals]
            })
        
        return report
