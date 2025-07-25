"""Quality assessment utilities for Bookmark+ resources."""

from datetime import datetime, timedelta
from plone import api
from Products.CMFCore.utils import getToolByName
from knowledge.curator.interfaces import IBookmarkPlus
import logging

logger = logging.getLogger('knowledge.curator.quality')


class BookmarkQualityAssessment:
    """Utility class for assessing and managing Bookmark+ resource quality."""
    
    def __init__(self, context):
        """Initialize with portal context."""
        self.context = context
        self.catalog = api.portal.get_tool('portal_catalog')
    
    def assess_all_bookmarks(self):
        """Assess quality of all BookmarkPlus resources.
        
        Returns:
            dict: Summary of assessment results
        """
        results = {
            'total': 0,
            'assessed': 0,
            'high_quality': 0,
            'medium_quality': 0,
            'low_quality': 0,
            'flagged': 0,
            'errors': []
        }
        
        # Query for all BookmarkPlus items
        brains = self.catalog(portal_type='BookmarkPlus')
        results['total'] = len(brains)
        
        for brain in brains:
            try:
                obj = brain.getObject()
                if IBookmarkPlus.providedBy(obj):
                    # Calculate quality score
                    score = obj.calculate_quality_score()
                    
                    # Update tracking
                    obj.update_quality_tracking()
                    
                    # Categorize
                    if score >= 0.7:
                        results['high_quality'] += 1
                    elif score >= 0.4:
                        results['medium_quality'] += 1
                    else:
                        results['low_quality'] += 1
                        # Flag low quality resources
                        if score < 0.3:
                            obj.flag_for_quality_review(
                                reason=f'Low quality score: {score}'
                            )
                            results['flagged'] += 1
                    
                    results['assessed'] += 1
                    
            except Exception as e:
                logger.error(f"Error assessing bookmark {brain.getURL()}: {str(e)}")
                results['errors'].append({
                    'url': brain.getURL(),
                    'error': str(e)
                })
        
        return results
    
    def get_quality_report(self, min_score=None, max_score=None):
        """Generate quality report for BookmarkPlus resources.
        
        Args:
            min_score (float): Minimum quality score to include
            max_score (float): Maximum quality score to include
        
        Returns:
            list: List of resource quality data
        """
        report = []
        
        brains = self.catalog(portal_type='BookmarkPlus')
        
        for brain in brains:
            try:
                obj = brain.getObject()
                if IBookmarkPlus.providedBy(obj):
                    metrics = obj.get_quality_metrics()
                    score = metrics['overall_score']
                    
                    # Apply filters
                    if min_score and score < min_score:
                        continue
                    if max_score and score > max_score:
                        continue
                    
                    report.append({
                        'uid': brain.UID,
                        'title': brain.Title,
                        'url': brain.getURL(),
                        'resource_url': getattr(obj, 'url', ''),
                        'metrics': metrics,
                        'trend': obj.get_quality_trend(),
                        'flagged': obj.is_flagged_for_review(),
                        'created': brain.created.isoformat() if brain.created else None,
                        'modified': brain.modified.isoformat() if brain.modified else None
                    })
                    
            except Exception as e:
                logger.error(f"Error generating report for {brain.getURL()}: {str(e)}")
        
        # Sort by quality score
        report.sort(key=lambda x: x['metrics']['overall_score'], reverse=True)
        
        return report
    
    def identify_outdated_resources(self, days_threshold=365):
        """Identify potentially outdated resources.
        
        Args:
            days_threshold (int): Age threshold in days
        
        Returns:
            list: List of potentially outdated resources
        """
        outdated = []
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        brains = self.catalog(
            portal_type='BookmarkPlus',
            created={'query': cutoff_date, 'range': 'max'}
        )
        
        for brain in brains:
            try:
                obj = brain.getObject()
                if IBookmarkPlus.providedBy(obj):
                    # Check freshness score
                    metrics = obj.get_quality_metrics()
                    if metrics['freshness_score'] < 0.5:
                        outdated.append({
                            'uid': brain.UID,
                            'title': brain.Title,
                            'url': brain.getURL(),
                            'created': brain.created.isoformat() if brain.created else None,
                            'freshness_score': metrics['freshness_score'],
                            'resource_type': getattr(obj, 'resource_type', 'unknown')
                        })
                        
            except Exception as e:
                logger.error(f"Error checking resource age for {brain.getURL()}: {str(e)}")
        
        return outdated
    
    def get_learning_correlation_analysis(self):
        """Analyze correlation between resource quality and learning outcomes.
        
        Returns:
            dict: Analysis results
        """
        analysis = {
            'total_resources': 0,
            'resources_with_knowledge_items': 0,
            'resources_with_goals': 0,
            'average_quality_with_items': 0.0,
            'average_quality_without_items': 0.0,
            'quality_by_engagement': {},
            'top_resources_for_learning': []
        }
        
        brains = self.catalog(portal_type='BookmarkPlus')
        analysis['total_resources'] = len(brains)
        
        scores_with_items = []
        scores_without_items = []
        engagement_scores = {
            'completed': [],
            'in_progress': [],
            'archived': [],
            'unread': []
        }
        
        for brain in brains:
            try:
                obj = brain.getObject()
                if IBookmarkPlus.providedBy(obj):
                    metrics = obj.get_quality_metrics()
                    score = metrics['overall_score']
                    
                    # Check knowledge item relationships
                    related_items = getattr(obj, 'related_knowledge_items', [])
                    if related_items:
                        analysis['resources_with_knowledge_items'] += 1
                        scores_with_items.append(score)
                    else:
                        scores_without_items.append(score)
                    
                    # Check learning goal support
                    if getattr(obj, 'supports_learning_goals', []):
                        analysis['resources_with_goals'] += 1
                    
                    # Track by engagement
                    read_status = metrics.get('read_status', 'unread')
                    if read_status in engagement_scores:
                        engagement_scores[read_status].append(score)
                    
                    # Identify top learning resources
                    if metrics['learning_correlation_score'] > 0.7:
                        analysis['top_resources_for_learning'].append({
                            'title': brain.Title,
                            'url': brain.getURL(),
                            'learning_score': metrics['learning_correlation_score'],
                            'overall_quality': score
                        })
                        
            except Exception as e:
                logger.error(f"Error analyzing {brain.getURL()}: {str(e)}")
        
        # Calculate averages
        if scores_with_items:
            analysis['average_quality_with_items'] = \
                sum(scores_with_items) / len(scores_with_items)
        
        if scores_without_items:
            analysis['average_quality_without_items'] = \
                sum(scores_without_items) / len(scores_without_items)
        
        # Calculate engagement averages
        for status, scores in engagement_scores.items():
            if scores:
                analysis['quality_by_engagement'][status] = {
                    'count': len(scores),
                    'average_quality': sum(scores) / len(scores)
                }
        
        # Sort top resources
        analysis['top_resources_for_learning'].sort(
            key=lambda x: x['learning_score'], 
            reverse=True
        )
        analysis['top_resources_for_learning'] = \
            analysis['top_resources_for_learning'][:20]  # Top 20
        
        return analysis
    
    def update_quality_for_modified_resources(self, days=7):
        """Update quality tracking for recently modified resources.
        
        Args:
            days (int): Number of days to look back
        
        Returns:
            dict: Update summary
        """
        summary = {
            'checked': 0,
            'updated': 0,
            'flagged': 0,
            'errors': []
        }
        
        # Query for recently modified BookmarkPlus items
        since = datetime.now() - timedelta(days=days)
        brains = self.catalog(
            portal_type='BookmarkPlus',
            modified={'query': since, 'range': 'min'}
        )
        
        for brain in brains:
            try:
                obj = brain.getObject()
                if IBookmarkPlus.providedBy(obj):
                    summary['checked'] += 1
                    
                    # Get previous and current scores
                    history = obj.get_quality_history()
                    old_score = history[-1]['overall_score'] if history else None
                    new_score = obj.calculate_quality_score()
                    
                    # Update tracking
                    obj.update_quality_tracking()
                    summary['updated'] += 1
                    
                    # Check if quality dropped significantly
                    if old_score and (old_score - new_score) > 0.2:
                        obj.flag_for_quality_review(
                            reason=f'Quality dropped from {old_score} to {new_score}'
                        )
                        summary['flagged'] += 1
                        
            except Exception as e:
                logger.error(f"Error updating quality for {brain.getURL()}: {str(e)}")
                summary['errors'].append({
                    'url': brain.getURL(),
                    'error': str(e)
                })
        
        return summary
    
    def clear_quality_flags(self, uids=None):
        """Clear quality review flags.
        
        Args:
            uids (list): Optional list of UIDs to clear flags for
        
        Returns:
            int: Number of flags cleared
        """
        cleared = 0
        
        if uids:
            # Clear specific UIDs
            for uid in uids:
                brain = self.catalog(UID=uid)
                if brain:
                    obj = brain[0].getObject()
                    if IBookmarkPlus.providedBy(obj) and obj.is_flagged_for_review():
                        obj.clear_quality_flag()
                        cleared += 1
        else:
            # Clear all flags
            brains = self.catalog(portal_type='BookmarkPlus')
            for brain in brains:
                try:
                    obj = brain.getObject()
                    if IBookmarkPlus.providedBy(obj) and obj.is_flagged_for_review():
                        obj.clear_quality_flag()
                        cleared += 1
                except Exception as e:
                    logger.error(f"Error clearing flag for {brain.getURL()}: {str(e)}")
        
        return cleared