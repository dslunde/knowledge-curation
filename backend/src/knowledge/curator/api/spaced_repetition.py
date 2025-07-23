"""Spaced Repetition API endpoints."""

from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from datetime import datetime, timedelta
import json
import math
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from knowledge.curator.repetition import (
    SM2Algorithm, ForgettingCurve, ReviewScheduler, PerformanceTracker
)
from knowledge.curator.repetition.utilities import ReviewUtilities


@implementer(IPublishTraverse)
class SpacedRepetitionService(Service):
    """Service for spaced repetition learning system."""

    def __init__(self, context, request):
        super(SpacedRepetitionService, self).__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if len(self.params) == 0:
            if self.request.method == 'GET':
                return self.get_review_items()
            else:
                self.request.response.setStatus(405)
                return {'error': 'Method not allowed'}
        elif self.params[0] == 'review':
            if self.request.method == 'POST':
                return self.update_review()
            else:
                return self.get_review_items()
        elif self.params[0] == 'schedule':
            return self.get_review_schedule()
        elif self.params[0] == 'performance':
            return self.get_performance_stats()
        elif self.params[0] == 'settings':
            if self.request.method == 'GET':
                return self.get_settings()
            elif self.request.method == 'POST':
                return self.update_settings()
        else:
            self.request.response.setStatus(404)
            return {'error': 'Not found'}

    def get_review_items(self):
        """Get items due for review."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Get user's items
        brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'BookmarkPlus']
        )
        
        now = datetime.now()
        review_items = []
        
        for brain in brains:
            obj = brain.getObject()
            
            # Get or initialize SR data
            sr_data = self._get_sr_data(obj)
            
            # Calculate if review is due
            if self._is_review_due(sr_data, now):
                review_items.append({
                    'uid': brain.UID,
                    'title': brain.Title,
                    'type': brain.portal_type,
                    'url': brain.getURL(),
                    'description': brain.Description,
                    'sr_data': {
                        'interval': sr_data.get('interval', 1),
                        'repetitions': sr_data.get('repetitions', 0),
                        'ease_factor': sr_data.get('ease_factor', 2.5),
                        'last_review': sr_data.get('last_review', '').isoformat() if sr_data.get('last_review') else None,
                        'next_review': sr_data.get('next_review', '').isoformat() if sr_data.get('next_review') else None,
                        'retention_score': self._calculate_retention(sr_data, now)
                    }
                })
        
        # Sort by urgency (retention score)
        review_items.sort(key=lambda x: x['sr_data']['retention_score'])
        
        # Limit to reasonable number per session
        limit = int(self.request.get('limit', 20))
        review_items = review_items[:limit]
        
        return {
            'items': review_items,
            'total_due': len(review_items),
            'next_review_date': self._get_next_review_date(brains)
        }

    def update_review(self):
        """Update review performance for an item."""
        if not api.user.has_permission('Modify portal content', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        data = json.loads(self.request.get('BODY', '{}'))
        uid = data.get('uid')
        quality = data.get('quality')  # 0-5 scale (SM-2 algorithm)
        time_spent = data.get('time_spent', 0)  # seconds
        
        if not uid:
            self.request.response.setStatus(400)
            return {'error': 'UID required'}
        
        if quality is None or quality < 0 or quality > 5:
            self.request.response.setStatus(400)
            return {'error': 'Quality must be between 0 and 5'}
        
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(UID=uid)
        
        if not brains:
            self.request.response.setStatus(404)
            return {'error': 'Item not found'}
        
        obj = brains[0].getObject()
        
        # Get current SR data
        sr_data = self._get_sr_data(obj)
        
        # Apply SM-2 algorithm
        ease_factor = sr_data.get('ease_factor', 2.5)
        interval = sr_data.get('interval', 1)
        repetitions = sr_data.get('repetitions', 0)
        
        if quality >= 3:  # Successful recall
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(interval * ease_factor)
            
            repetitions += 1
            
            # Update ease factor
            ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            ease_factor = max(1.3, ease_factor)  # Minimum ease factor
        else:  # Failed recall
            repetitions = 0
            interval = 1
        
        # Update SR data
        now = datetime.now()
        next_review = now + timedelta(days=interval)
        
        sr_data['quality'] = quality
        sr_data['ease_factor'] = ease_factor
        sr_data['interval'] = interval
        sr_data['repetitions'] = repetitions
        sr_data['last_review'] = now
        sr_data['next_review'] = next_review
        sr_data['time_spent'] = time_spent
        
        # Add to history
        if 'history' not in sr_data:
            sr_data['history'] = PersistentList()
        
        sr_data['history'].append({
            'date': now.isoformat(),
            'quality': quality,
            'interval': interval,
            'time_spent': time_spent
        })
        
        # Keep only last 50 history entries
        if len(sr_data['history']) > 50:
            sr_data['history'] = PersistentList(sr_data['history'][-50:])
        
        # Save SR data
        self._set_sr_data(obj, sr_data)
        obj.reindexObject()
        
        return {
            'success': True,
            'uid': uid,
            'sr_data': {
                'interval': interval,
                'repetitions': repetitions,
                'ease_factor': round(ease_factor, 2),
                'next_review': next_review.isoformat(),
                'quality': quality
            }
        }

    def get_review_schedule(self):
        """Get upcoming review schedule."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Get user's items
        brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'BookmarkPlus']
        )
        
        # Group by date
        schedule = {}
        today = datetime.now().date()
        
        for brain in brains:
            obj = brain.getObject()
            sr_data = self._get_sr_data(obj)
            
            if sr_data.get('next_review'):
                review_date = sr_data['next_review'].date()
                date_key = review_date.isoformat()
                
                if date_key not in schedule:
                    schedule[date_key] = {
                        'date': date_key,
                        'items': [],
                        'overdue': review_date < today
                    }
                
                schedule[date_key]['items'].append({
                    'uid': brain.UID,
                    'title': brain.Title,
                    'type': brain.portal_type,
                    'interval': sr_data.get('interval', 1),
                    'repetitions': sr_data.get('repetitions', 0)
                })
        
        # Convert to sorted list
        schedule_list = sorted(schedule.values(), key=lambda x: x['date'])
        
        # Calculate statistics
        total_scheduled = sum(len(day['items']) for day in schedule_list)
        overdue_count = sum(len(day['items']) for day in schedule_list if day['overdue'])
        
        # Next 7 days forecast
        forecast = []
        for i in range(7):
            date = (today + timedelta(days=i)).isoformat()
            day_data = schedule.get(date, {'date': date, 'items': []})
            forecast.append({
                'date': date,
                'count': len(day_data.get('items', [])),
                'is_today': i == 0
            })
        
        return {
            'schedule': schedule_list[:30],  # Next 30 days
            'forecast': forecast,
            'statistics': {
                'total_scheduled': total_scheduled,
                'overdue': overdue_count,
                'today': len(schedule.get(today.isoformat(), {}).get('items', []))
            }
        }

    def get_performance_stats(self):
        """Get spaced repetition performance statistics."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        catalog = api.portal.get_tool('portal_catalog')
        user = api.user.get_current()
        
        # Time range
        days = int(self.request.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get user's items
        brains = catalog(
            Creator=user.getId(),
            portal_type=['ResearchNote', 'BookmarkPlus']
        )
        
        # Aggregate statistics
        stats = {
            'total_reviews': 0,
            'successful_reviews': 0,
            'failed_reviews': 0,
            'average_quality': 0,
            'average_time_spent': 0,
            'items_in_system': 0,
            'mature_items': 0,  # interval > 21 days
            'daily_stats': {},
            'quality_distribution': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }
        
        total_quality = 0
        total_time = 0
        
        for brain in brains:
            obj = brain.getObject()
            sr_data = self._get_sr_data(obj)
            
            if sr_data.get('repetitions', 0) > 0:
                stats['items_in_system'] += 1
                
                if sr_data.get('interval', 0) > 21:
                    stats['mature_items'] += 1
                
                # Process history
                for entry in sr_data.get('history', []):
                    entry_date = datetime.fromisoformat(entry['date'])
                    
                    if entry_date >= start_date:
                        stats['total_reviews'] += 1
                        quality = entry['quality']
                        
                        if quality >= 3:
                            stats['successful_reviews'] += 1
                        else:
                            stats['failed_reviews'] += 1
                        
                        total_quality += quality
                        total_time += entry.get('time_spent', 0)
                        
                        # Daily aggregation
                        date_key = entry_date.date().isoformat()
                        if date_key not in stats['daily_stats']:
                            stats['daily_stats'][date_key] = {
                                'reviews': 0,
                                'successful': 0,
                                'time_spent': 0
                            }
                        
                        stats['daily_stats'][date_key]['reviews'] += 1
                        if quality >= 3:
                            stats['daily_stats'][date_key]['successful'] += 1
                        stats['daily_stats'][date_key]['time_spent'] += entry.get('time_spent', 0)
                        
                        # Quality distribution
                        stats['quality_distribution'][quality] += 1
        
        # Calculate averages
        if stats['total_reviews'] > 0:
            stats['average_quality'] = round(total_quality / stats['total_reviews'], 2)
            stats['average_time_spent'] = round(total_time / stats['total_reviews'], 1)
            stats['success_rate'] = round(stats['successful_reviews'] / stats['total_reviews'] * 100, 1)
        else:
            stats['success_rate'] = 0
        
        # Convert daily stats to list
        daily_list = []
        for date, data in sorted(stats['daily_stats'].items()):
            daily_list.append({
                'date': date,
                'reviews': data['reviews'],
                'successful': data['successful'],
                'success_rate': round(data['successful'] / data['reviews'] * 100, 1) if data['reviews'] > 0 else 0,
                'time_spent': data['time_spent']
            })
        
        stats['daily_stats'] = daily_list
        
        return {
            'period_days': days,
            'statistics': stats
        }

    def get_settings(self):
        """Get user's spaced repetition settings."""
        if not api.user.has_permission('View', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        user = api.user.get_current()
        member = api.user.get(user.getId())
        
        # Get or create settings
        settings = member.getProperty('sr_settings', {})
        
        if not settings:
            # Default settings
            settings = {
                'daily_review_limit': 20,
                'new_items_per_day': 5,
                'review_order': 'urgency',  # urgency, random, oldest
                'minimum_ease_factor': 1.3,
                'initial_intervals': [1, 6],  # days
                'notification_enabled': True,
                'notification_time': '09:00'
            }
        
        return settings

    def update_settings(self):
        """Update user's spaced repetition settings."""
        if not api.user.has_permission('Modify portal content', obj=self.context):
            self.request.response.setStatus(403)
            return {'error': 'Unauthorized'}

        data = json.loads(self.request.get('BODY', '{}'))
        
        # Validate settings
        allowed_keys = {
            'daily_review_limit', 'new_items_per_day', 'review_order',
            'minimum_ease_factor', 'initial_intervals', 'notification_enabled',
            'notification_time'
        }
        
        settings = {k: v for k, v in data.items() if k in allowed_keys}
        
        # Apply constraints
        if 'daily_review_limit' in settings:
            settings['daily_review_limit'] = max(1, min(100, int(settings['daily_review_limit'])))
        
        if 'new_items_per_day' in settings:
            settings['new_items_per_day'] = max(0, min(50, int(settings['new_items_per_day'])))
        
        if 'minimum_ease_factor' in settings:
            settings['minimum_ease_factor'] = max(1.0, min(3.0, float(settings['minimum_ease_factor'])))
        
        # Save settings
        user = api.user.get_current()
        member = api.user.get(user.getId())
        member.setMemberProperties(mapping={'sr_settings': settings})
        
        return {
            'success': True,
            'settings': settings
        }

    def _get_sr_data(self, obj):
        """Get spaced repetition data for an object."""
        if not hasattr(obj, '_sr_data'):
            obj._sr_data = PersistentMapping()
        return obj._sr_data

    def _set_sr_data(self, obj, data):
        """Set spaced repetition data for an object."""
        obj._sr_data = PersistentMapping(data)

    def _is_review_due(self, sr_data, now):
        """Check if review is due based on SR data."""
        if not sr_data.get('next_review'):
            return True  # New item
        
        return sr_data['next_review'] <= now

    def _calculate_retention(self, sr_data, now):
        """Calculate retention score based on forgetting curve."""
        if not sr_data.get('last_review'):
            return 0.0
        
        days_since = (now - sr_data['last_review']).days
        interval = sr_data.get('interval', 1)
        
        # Forgetting curve: R = e^(-t/S)
        retention = math.exp(-days_since / (interval * 5))
        return round(retention, 3)

    def _get_next_review_date(self, brains):
        """Get the next upcoming review date."""
        next_date = None
        
        for brain in brains:
            obj = brain.getObject()
            sr_data = self._get_sr_data(obj)
            
            if sr_data.get('next_review'):
                if next_date is None or sr_data['next_review'] < next_date:
                    next_date = sr_data['next_review']
        
        return next_date.isoformat() if next_date else None