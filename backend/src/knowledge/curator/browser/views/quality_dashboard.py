"""Quality assessment dashboard views for BookmarkPlus resources."""

import json
from datetime import datetime
from plone import api
from Products.Five.browser import BrowserView
from knowledge.curator.utilities.quality_assessment import BookmarkQualityAssessment
from knowledge.curator.interfaces import IBookmarkPlus


class QualityDashboardView(BrowserView):
    """Main quality dashboard view."""
    
    def __call__(self):
        """Render the quality dashboard."""
        self.quality_assessment = BookmarkQualityAssessment(self.context)
        return super(QualityDashboardView, self).__call__()
    
    def get_quality_overview(self):
        """Get overview statistics for quality dashboard."""
        try:
            catalog = api.portal.get_tool('portal_catalog')
            brains = catalog(portal_type='BookmarkPlus')
            
            overview = {
                'total_resources': len(brains),
                'high_quality': 0,
                'medium_quality': 0,
                'low_quality': 0,
                'flagged_for_review': 0,
                'average_quality': 0.0,
                'quality_distribution': []
            }
            
            scores = []
            distribution_buckets = {
                '0.0-0.2': 0,
                '0.2-0.4': 0,
                '0.4-0.6': 0,
                '0.6-0.8': 0,
                '0.8-1.0': 0
            }
            
            for brain in brains:
                try:
                    obj = brain.getObject()
                    if IBookmarkPlus.providedBy(obj):
                        score = obj.calculate_quality_score()
                        scores.append(score)
                        
                        # Categorize
                        if score >= 0.7:
                            overview['high_quality'] += 1
                        elif score >= 0.4:
                            overview['medium_quality'] += 1
                        else:
                            overview['low_quality'] += 1
                        
                        # Check flags
                        if obj.is_flagged_for_review():
                            overview['flagged_for_review'] += 1
                        
                        # Distribution
                        if score < 0.2:
                            distribution_buckets['0.0-0.2'] += 1
                        elif score < 0.4:
                            distribution_buckets['0.2-0.4'] += 1
                        elif score < 0.6:
                            distribution_buckets['0.4-0.6'] += 1
                        elif score < 0.8:
                            distribution_buckets['0.6-0.8'] += 1
                        else:
                            distribution_buckets['0.8-1.0'] += 1
                            
                except Exception:
                    continue
            
            if scores:
                overview['average_quality'] = round(sum(scores) / len(scores), 3)
            
            # Convert distribution to list for easier JSON serialization
            overview['quality_distribution'] = [
                {'range': k, 'count': v} for k, v in distribution_buckets.items()
            ]
            
            return overview
            
        except Exception as e:
            api.portal.show_message(
                message=f'Error generating overview: {str(e)}',
                request=self.request,
                type='error'
            )
            return {}
    
    def get_flagged_resources(self):
        """Get resources flagged for quality review."""
        try:
            catalog = api.portal.get_tool('portal_catalog')
            brains = catalog(portal_type='BookmarkPlus')
            
            flagged = []
            for brain in brains:
                try:
                    obj = brain.getObject()
                    if IBookmarkPlus.providedBy(obj) and obj.is_flagged_for_review():
                        flag_info = obj.get_quality_flag_info()
                        metrics = obj.get_quality_metrics()
                        
                        flagged.append({
                            'uid': brain.UID,
                            'title': brain.Title,
                            'url': brain.getURL(),
                            'resource_url': getattr(obj, 'url', ''),
                            'quality_score': metrics['overall_score'],
                            'flag_reason': flag_info.get('reason', ''),
                            'flag_date': flag_info.get('timestamp', ''),
                            'read_status': metrics.get('read_status', 'unread')
                        })
                        
                except Exception:
                    continue
            
            # Sort by quality score (lowest first)
            flagged.sort(key=lambda x: x['quality_score'])
            return flagged
            
        except Exception as e:
            api.portal.show_message(
                message=f'Error getting flagged resources: {str(e)}',
                request=self.request,
                type='error'
            )
            return []
    
    def get_top_quality_resources(self, limit=10):
        """Get top quality resources."""
        try:
            catalog = api.portal.get_tool('portal_catalog')
            brains = catalog(portal_type='BookmarkPlus')
            
            resources = []
            for brain in brains:
                try:
                    obj = brain.getObject()
                    if IBookmarkPlus.providedBy(obj):
                        metrics = obj.get_quality_metrics()
                        
                        resources.append({
                            'uid': brain.UID,
                            'title': brain.Title,
                            'url': brain.getURL(),
                            'resource_url': getattr(obj, 'url', ''),
                            'quality_score': metrics['overall_score'],
                            'content_quality': metrics['content_quality'],
                            'read_status': metrics.get('read_status', 'unread'),
                            'related_items_count': metrics.get('related_items_count', 0),
                            'supports_goals_count': metrics.get('supports_goals_count', 0)
                        })
                        
                except Exception:
                    continue
            
            # Sort by quality score (highest first)
            resources.sort(key=lambda x: x['quality_score'], reverse=True)
            return resources[:limit]
            
        except Exception as e:
            api.portal.show_message(
                message=f'Error getting top resources: {str(e)}',
                request=self.request,
                type='error'
            )
            return []


class QualityAssessmentAPIView(BrowserView):
    """API view for quality assessment operations."""
    
    def __call__(self):
        """Handle API requests."""
        if self.request.method == 'POST':
            action = self.request.get('action')
            
            if action == 'assess_all':
                return self.assess_all_resources()
            elif action == 'clear_flags':
                return self.clear_quality_flags()
            elif action == 'update_tracking':
                return self.update_quality_tracking()
            elif action == 'generate_report':
                return self.generate_quality_report()
        
        self.request.response.setStatus(400)
        return json.dumps({'error': 'Invalid request'})
    
    def assess_all_resources(self):
        """Assess quality of all BookmarkPlus resources."""
        try:
            quality_assessment = BookmarkQualityAssessment(self.context)
            results = quality_assessment.assess_all_bookmarks()
            
            api.portal.show_message(
                message=f'Quality assessment completed. '
                        f'Assessed {results["assessed"]} resources, '
                        f'flagged {results["flagged"]} for review.',
                request=self.request,
                type='info'
            )
            
            self.request.response.setHeader('Content-Type', 'application/json')
            return json.dumps({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    def clear_quality_flags(self):
        """Clear quality review flags."""
        try:
            uids = self.request.get('uids', None)
            if uids and isinstance(uids, str):
                uids = uids.split(',')
            
            quality_assessment = BookmarkQualityAssessment(self.context)
            cleared = quality_assessment.clear_quality_flags(uids)
            
            api.portal.show_message(
                message=f'Cleared {cleared} quality flags.',
                request=self.request,
                type='info'
            )
            
            self.request.response.setHeader('Content-Type', 'application/json')
            return json.dumps({
                'success': True,
                'cleared': cleared
            })
            
        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    def update_quality_tracking(self):
        """Update quality tracking for recently modified resources."""
        try:
            days = int(self.request.get('days', 7))
            
            quality_assessment = BookmarkQualityAssessment(self.context)
            summary = quality_assessment.update_quality_for_modified_resources(days)
            
            api.portal.show_message(
                message=f'Updated quality tracking for {summary["updated"]} resources. '
                        f'Flagged {summary["flagged"]} for review.',
                request=self.request,
                type='info'
            )
            
            self.request.response.setHeader('Content-Type', 'application/json')
            return json.dumps({
                'success': True,
                'summary': summary
            })
            
        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    def generate_quality_report(self):
        """Generate detailed quality report."""
        try:
            min_score = self.request.get('min_score')
            max_score = self.request.get('max_score')
            
            if min_score:
                min_score = float(min_score)
            if max_score:
                max_score = float(max_score)
            
            quality_assessment = BookmarkQualityAssessment(self.context)
            report = quality_assessment.get_quality_report(min_score, max_score)
            
            self.request.response.setHeader('Content-Type', 'application/json')
            return json.dumps({
                'success': True,
                'report': report,
                'generated_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({
                'success': False,
                'error': str(e)
            })


class ResourceQualityDetailView(BrowserView):
    """Detailed quality view for individual resources."""
    
    def __call__(self):
        """Render detailed quality information."""
        if not IBookmarkPlus.providedBy(self.context):
            self.request.response.setStatus(404)
            return "Resource not found or not a BookmarkPlus item"
        
        return super(ResourceQualityDetailView, self).__call__()
    
    def get_quality_metrics(self):
        """Get detailed quality metrics for the current resource."""
        if IBookmarkPlus.providedBy(self.context):
            return self.context.get_quality_metrics()
        return {}
    
    def get_quality_history(self):
        """Get quality history for the current resource."""
        if IBookmarkPlus.providedBy(self.context):
            history = self.context.get_quality_history()
            # Convert timestamps to readable format
            for entry in history:
                if 'timestamp' in entry:
                    try:
                        dt = datetime.fromisoformat(entry['timestamp'])
                        entry['timestamp_readable'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        entry['timestamp_readable'] = entry['timestamp']
            return history
        return []
    
    def get_quality_trend(self):
        """Get quality trend for the current resource."""
        if IBookmarkPlus.providedBy(self.context):
            return self.context.get_quality_trend()
        return 'stable'
    
    def is_flagged_for_review(self):
        """Check if resource is flagged for review."""
        if IBookmarkPlus.providedBy(self.context):
            return self.context.is_flagged_for_review()
        return False
    
    def get_flag_info(self):
        """Get flag information."""
        if IBookmarkPlus.providedBy(self.context):
            return self.context.get_quality_flag_info()
        return None
    
    def update_quality_tracking(self):
        """Update quality tracking for this resource."""
        if IBookmarkPlus.providedBy(self.context):
            self.context.update_quality_tracking()
            api.portal.show_message(
                message='Quality tracking updated.',
                request=self.request,
                type='info'
            )
        else:
            api.portal.show_message(
                message='Cannot update quality tracking for this resource.',
                request=self.request,
                type='error'
            )