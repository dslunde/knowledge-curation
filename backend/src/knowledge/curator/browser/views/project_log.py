"""Views for Project Log content type."""

from Products.Five.browser import BrowserView


class ProjectLogView(BrowserView):
    """Default view for Project Log."""

    def __call__(self):
        """Render the view."""
        return self.index()

    def get_recent_entries(self, limit=10):
        """Get recent log entries."""
        return self.context.get_recent_entries(limit)

    def get_all_entries(self):
        """Get all log entries sorted by date."""
        entries = self.context.entries or []
        return sorted(entries, key=lambda x: x.get("timestamp", ""), reverse=True)

    def get_entries_by_tag(self, tag):
        """Get entries filtered by tag."""
        return self.context.get_entries_by_tag(tag)

    def get_all_tags(self):
        """Get all unique tags from entries."""
        tags = set()
        for entry in self.context.entries or []:
            tags.update(entry.get("tags", []))
        return sorted(tags)

    def get_status_class(self):
        """Get CSS class based on status."""
        status_map = {
            "planning": "status-planning",
            "active": "status-active",
            "paused": "status-paused",
            "completed": "status-completed",
            "archived": "status-archived",
        }
        return status_map.get(self.context.status, "status-planning")

    def get_duration_days(self):
        """Get project duration in days."""
        return self.context.get_duration()

    def format_duration(self):
        """Format duration in human-readable format."""
        days = self.get_duration_days()
        if days == 0:
            return "Just started"
        elif days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''}"
