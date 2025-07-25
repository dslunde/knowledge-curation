"""Views for Learning Goal content type."""

import logging

from plone import api
from Products.Five.browser import BrowserView

logger = logging.getLogger(__name__)


class LearningGoalView(BrowserView):
    """Default view for Learning Goal."""

    def __call__(self):
        """Render the view."""
        return self.index()

    def get_progress_percentage(self):
        """Get the current progress percentage."""
        return self.context.progress or 0

    def get_milestones(self):
        """Get all milestones sorted by target date."""
        milestones = self.context.milestones or []
        # Sort by target date, with None dates at the end
        return sorted(
            milestones,
            key=lambda m: (m.get("target_date") is None, m.get("target_date")),
        )

    def get_completed_milestones(self):
        """Get only completed milestones."""
        return [m for m in self.get_milestones() if m.get("completed", False)]

    def get_pending_milestones(self):
        """Get only pending milestones."""
        return [m for m in self.get_milestones() if not m.get("completed", False)]

    def is_overdue(self):
        """Check if the goal is overdue."""
        return self.context.is_overdue()

    def get_related_notes(self):
        """Get related research notes."""
        notes = []
        if self.context.related_notes:
            for uid in self.context.related_notes:
                try:
                    brain = api.content.find(UID=uid)
                    if brain:
                        notes.append(brain[0])
                except Exception:
                    logger.exception("Error finding related note with UID: %s", uid)
        return notes

    def get_priority_class(self):
        """Get CSS class based on priority."""
        priority_map = {
            "low": "priority-low",
            "medium": "priority-medium",
            "high": "priority-high",
        }
        return priority_map.get(self.context.priority, "priority-medium")
    
    def get_overall_progress(self, knowledge_item_mastery=None):
        """Get overall progress calculation for the learning goal.
        
        Args:
            knowledge_item_mastery: Optional dict mapping knowledge item UIDs to mastery levels
                                  If not provided, will attempt to get from current user's progress
        
        Returns:
            dict with overall progress data including visualization information
        """
        if hasattr(self.context, 'calculate_overall_progress'):
            # If no mastery levels provided, try to get from user's learning progress
            if knowledge_item_mastery is None:
                # This could be extended to fetch from a user progress tracking system
                # For now, just use empty dict
                knowledge_item_mastery = {}
            
            return self.context.calculate_overall_progress(knowledge_item_mastery)
        else:
            # Return empty result if method not available
            return {
                'overall_percentage': 0,
                'weighted_progress': 0.0,
                'items_mastered': 0,
                'total_items': 0,
                'prerequisite_satisfaction': 0.0,
                'path_segments': [],
                'visualization_data': {
                    'nodes': [],
                    'edges': [],
                    'progress_by_level': {}
                },
                'bottlenecks': [],
                'next_milestones': []
            }
