"""Views for Learning Goal content type."""

from plone import api


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
        return [m for m in self.get_milestones() if m.get('completed', False)]

    def get_pending_milestones(self):
        """Get only pending milestones."""
        return [m for m in self.get_milestones() if not m.get('completed', False)]

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
                    pass
        return notes

    def get_priority_class(self):
        """Get CSS class based on priority."""
        priority_map = {
            "low": "priority-low",
            "medium": "priority-medium",
            "high": "priority-high",
        }
        return priority_map.get(self.context.priority, 'priority-medium')
