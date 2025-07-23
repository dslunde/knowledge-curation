"""Analytics API endpoints for learning statistics and progress tracking."""

from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from datetime import datetime, timedelta
import json
import math


@implementer(IPublishTraverse)
class AnalyticsService(Service):
    """Service for analytics and learning statistics."""

    def __init__(self, context, request):
        super(AnalyticsService, self).__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if len(self.params) == 0:
            return self.get_overview()
        elif self.params[0] == 'statistics':
            return self.get_statistics()
        elif self.params[0] == 'forgetting-curve':
            return self.get_forgetting_curve()
        elif self.params[0] == 'progress':
            return self.get_progress()
        elif self.params[0] == 'activity':
            return self.get_activity()
        elif self.params[0] == 'insights':
            return self.get_insights()
        else:
            self.request.response.setStatus(404)
            return {'error': 'Not found'}

    def get_overview(self):
        """Get overview of knowledge base statistics."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Get user's content
        query = {
            'Creator': user.getId(),
            'portal_type': ['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
        }
        
        brains = catalog(**query)
        
        # Calculate statistics
        stats = {
            'total_items': len(brains),
            'by_type': {},
            'by_state': {},
            'recent_activity': [],
            'tags': {},
            'connections': 0
        }
        
        # Process items
        for brain in brains:
            # Count by type
            portal_type = brain.portal_type
            stats['by_type'][portal_type] = stats['by_type'].get(portal_type, 0) + 1
            
            # Count by state
            state = brain.review_state
            stats['by_state'][state] = stats['by_state'].get(state, 0) + 1
            
            # Count tags
            for tag in brain.Subject:
                stats['tags'][tag] = stats['tags'].get(tag, 0) + 1
            
            # Count connections
            obj = brain.getObject()
            if hasattr(obj, 'connections'):
                stats['connections'] += len(getattr(obj, 'connections', []))
            if hasattr(obj, 'related_notes'):
                stats['connections'] += len(getattr(obj, 'related_notes', []))
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus'],
            modified={'query': thirty_days_ago, 'range': 'min'},
            sort_on='modified',
            sort_order='descending',
            sort_limit=10
        )
        
        stats['recent_activity'] = [{
            'uid': brain.UID,
            'title': brain.Title,
            'type': brain.portal_type,
            'modified': brain.modified.ISO8601(),
            'url': brain.getURL()
        } for brain in recent_brains[:10]]
        
        # Top tags
        stats['top_tags'] = sorted(
            stats['tags'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats

    def get_statistics(self):
        """Get detailed learning statistics."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Time range from query parameters
        days = int(self.request.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type='LearningGoal',
            created={'query': start_date, 'range': 'min'}
        )
        
        # Calculate goal statistics
        goal_stats = {
            'total': len(goals),
            'completed': 0,
            'in_progress': 0,
            'planned': 0,
            'average_progress': 0,
            'by_priority': {'low': 0, 'medium': 0, 'high': 0}
        }
        
        total_progress = 0
        
        for brain in goals:
            obj = brain.getObject()
            progress = getattr(obj, 'progress', 0)
            priority = getattr(obj, 'priority', 'medium')
            
            total_progress += progress
            goal_stats['by_priority'][priority] += 1
            
            if progress == 100:
                goal_stats['completed'] += 1
            elif progress > 0:
                goal_stats['in_progress'] += 1
            else:
                goal_stats['planned'] += 1
        
        if goals:
            goal_stats['average_progress'] = total_progress / len(goals)
        
        # Get research notes statistics
        notes = catalog(
            Creator=user.getId(),
            portal_type='ResearchNote',
            created={'query': start_date, 'range': 'min'}
        )
        
        note_stats = {
            'total': len(notes),
            'with_insights': 0,
            'with_connections': 0,
            'average_connections': 0
        }
        
        total_connections = 0
        
        for brain in notes:
            obj = brain.getObject()
            
            if getattr(obj, 'key_insights', []):
                note_stats['with_insights'] += 1
            
            connections = len(getattr(obj, 'connections', []))
            if connections > 0:
                note_stats['with_connections'] += 1
            total_connections += connections
        
        if notes:
            note_stats['average_connections'] = total_connections / len(notes)
        
        # Get bookmark statistics
        bookmarks = catalog(
            Creator=user.getId(),
            portal_type='BookmarkPlus',
            created={'query': start_date, 'range': 'min'}
        )
        
        bookmark_stats = {
            'total': len(bookmarks),
            'by_status': {'unread': 0, 'reading': 0, 'read': 0},
            'by_importance': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        }
        
        for brain in bookmarks:
            obj = brain.getObject()
            status = getattr(obj, 'read_status', 'unread')
            importance = getattr(obj, 'importance', 'medium')
            
            bookmark_stats['by_status'][status] += 1
            bookmark_stats['by_importance'][importance] += 1
        
        return {
            'period_days': days,
            'learning_goals': goal_stats,
            'research_notes': note_stats,
            'bookmarks': bookmark_stats,
            'generated_at': datetime.now().isoformat()
        }

    def get_forgetting_curve(self):
        """Get forgetting curve data for spaced repetition."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Get items with review data
        brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'BookmarkPlus']
        )
        
        curve_data = []
        
        for brain in brains:
            obj = brain.getObject()
            
            # Calculate retention based on last review
            last_review = brain.modified
            days_since_review = (datetime.now() - last_review.asdatetime()).days
            
            # Ebbinghaus forgetting curve formula
            # R = e^(-t/S) where t is time and S is strength
            strength = 1.0  # Default strength
            
            # Adjust strength based on connections and importance
            if hasattr(obj, 'connections'):
                strength += len(getattr(obj, 'connections', [])) * 0.1
            
            if hasattr(obj, 'importance'):
                importance_weights = {'low': 0.5, 'medium': 1.0, 'high': 1.5, 'critical': 2.0}
                strength *= importance_weights.get(getattr(obj, 'importance', 'medium'), 1.0)
            
            retention = math.exp(-days_since_review / (strength * 5))  # 5 day half-life
            
            curve_data.append({
                'uid': brain.UID,
                'title': brain.Title,
                'type': brain.portal_type,
                'days_since_review': days_since_review,
                'retention_score': round(retention, 3),
                'review_recommended': retention < 0.8,
                'last_review': brain.modified.ISO8601(),
                'url': brain.getURL()
            })
        
        # Sort by retention score (lowest first - needs review)
        curve_data.sort(key=lambda x: x['retention_score'])
        
        # Group by review urgency
        review_groups = {
            'urgent': [],  # < 0.5 retention
            'soon': [],    # 0.5 - 0.7 retention
            'later': [],   # 0.7 - 0.8 retention
            'good': []     # > 0.8 retention
        }
        
        for item in curve_data:
            retention = item['retention_score']
            if retention < 0.5:
                review_groups['urgent'].append(item)
            elif retention < 0.7:
                review_groups['soon'].append(item)
            elif retention < 0.8:
                review_groups['later'].append(item)
            else:
                review_groups['good'].append(item)
        
        return {
            'forgetting_curve': curve_data[:50],  # Top 50 items
            'review_groups': {
                'urgent': review_groups['urgent'][:10],
                'soon': review_groups['soon'][:10],
                'later': review_groups['later'][:10],
                'good': len(review_groups['good'])
            },
            'total_items': len(curve_data)
        }

    def get_progress(self):
        """Get learning progress over time."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Time range
        days = int(self.request.get('days', 90))
        interval = self.request.get('interval', 'week')  # day, week, month
        
        # Calculate intervals
        intervals = []
        end_date = datetime.now()
        
        if interval == 'day':
            for i in range(days):
                date = end_date - timedelta(days=i)
                intervals.append({
                    'start': date.replace(hour=0, minute=0, second=0),
                    'end': date.replace(hour=23, minute=59, second=59),
                    'label': date.strftime('%Y-%m-%d')
                })
        elif interval == 'week':
            weeks = days // 7
            for i in range(weeks):
                week_end = end_date - timedelta(days=i*7)
                week_start = week_end - timedelta(days=6)
                intervals.append({
                    'start': week_start.replace(hour=0, minute=0, second=0),
                    'end': week_end.replace(hour=23, minute=59, second=59),
                    'label': f"Week {weeks - i}"
                })
        elif interval == 'month':
            months = days // 30
            for i in range(months):
                month_end = end_date - timedelta(days=i*30)
                month_start = month_end - timedelta(days=29)
                intervals.append({
                    'start': month_start.replace(hour=0, minute=0, second=0),
                    'end': month_end.replace(hour=23, minute=59, second=59),
                    'label': month_end.strftime('%B %Y')
                })
        
        intervals.reverse()
        
        # Get progress data for each interval
        progress_data = []
        
        for interval_data in intervals:
            # Count items created in this interval
            created = catalog(
                Creator=user.getId(),
                portal_type=['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus'],
                created={
                    'query': [interval_data['start'], interval_data['end']],
                    'range': 'min:max'
                }
            )
            
            # Count items modified in this interval
            modified = catalog(
                Creator=user.getId(),
                portal_type=['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus'],
                modified={
                    'query': [interval_data['start'], interval_data['end']],
                    'range': 'min:max'
                }
            )
            
            progress_data.append({
                'period': interval_data['label'],
                'created': len(created),
                'modified': len(modified),
                'by_type': {
                    'ResearchNote': len([b for b in created if b.portal_type == 'ResearchNote']),
                    'LearningGoal': len([b for b in created if b.portal_type == 'LearningGoal']),
                    'ProjectLog': len([b for b in created if b.portal_type == 'ProjectLog']),
                    'BookmarkPlus': len([b for b in created if b.portal_type == 'BookmarkPlus'])
                }
            })
        
        return {
            'progress': progress_data,
            'interval': interval,
            'days': days
        }

    def get_activity(self):
        """Get user activity heatmap data."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Get last 365 days of activity
        start_date = datetime.now() - timedelta(days=365)
        
        brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus'],
            modified={'query': start_date, 'range': 'min'}
        )
        
        # Group by date
        activity_map = {}
        
        for brain in brains:
            date = brain.modified.asdatetime().date()
            date_str = date.isoformat()
            
            if date_str not in activity_map:
                activity_map[date_str] = {
                    'count': 0,
                    'types': []
                }
            
            activity_map[date_str]['count'] += 1
            activity_map[date_str]['types'].append(brain.portal_type)
        
        # Convert to list format
        activity_data = []
        for date_str, data in activity_map.items():
            activity_data.append({
                'date': date_str,
                'count': data['count'],
                'level': min(4, data['count'] // 2),  # 0-4 activity level
                'types': list(set(data['types']))
            })
        
        activity_data.sort(key=lambda x: x['date'])
        
        return {
            'activity': activity_data,
            'total_days': len(activity_data),
            'most_active_day': max(activity_data, key=lambda x: x['count']) if activity_data else None
        }

    def get_insights(self):
        """Get AI-generated insights from the knowledge base."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        insights = {
            'patterns': [],
            'recommendations': [],
            'connections': []
        }
        
        # Analyze tag patterns
        brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
        )
        
        tag_cooccurrence = {}
        tag_frequency = {}
        
        for brain in brains:
            tags = list(brain.Subject)
            
            # Count individual tags
            for tag in tags:
                tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
            
            # Count tag co-occurrences
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    pair = tuple(sorted([tag1, tag2]))
                    tag_cooccurrence[pair] = tag_cooccurrence.get(pair, 0) + 1
        
        # Find strong tag relationships
        for pair, count in sorted(tag_cooccurrence.items(), key=lambda x: x[1], reverse=True)[:5]:
            insights['patterns'].append({
                'type': 'tag_correlation',
                'tags': list(pair),
                'strength': count,
                'message': f"Tags '{pair[0]}' and '{pair[1]}' frequently appear together ({count} times)"
            })
        
        # Analyze learning goal completion
        goals = catalog(
            Creator=user.getId(),
            portal_type='LearningGoal'
        )
        
        completion_rates = {'low': [], 'medium': [], 'high': []}
        
        for brain in goals:
            obj = brain.getObject()
            priority = getattr(obj, 'priority', 'medium')
            progress = getattr(obj, 'progress', 0)
            completion_rates[priority].append(progress)
        
        for priority, rates in completion_rates.items():
            if rates:
                avg_completion = sum(rates) / len(rates)
                insights['recommendations'].append({
                    'type': 'goal_completion',
                    'priority': priority,
                    'average_completion': round(avg_completion, 1),
                    'message': f"{priority.capitalize()} priority goals have {avg_completion:.1f}% average completion"
                })
        
        # Find isolated content
        isolated_items = []
        for brain in brains[:100]:  # Check first 100 items
            obj = brain.getObject()
            connections = len(getattr(obj, 'connections', []))
            if connections == 0 and brain.portal_type == 'ResearchNote':
                isolated_items.append({
                    'uid': brain.UID,
                    'title': brain.Title,
                    'url': brain.getURL()
                })
        
        if isolated_items:
            insights['connections'].append({
                'type': 'isolated_content',
                'count': len(isolated_items),
                'items': isolated_items[:5],
                'message': f"Found {len(isolated_items)} research notes without connections"
            })
        
        return insights