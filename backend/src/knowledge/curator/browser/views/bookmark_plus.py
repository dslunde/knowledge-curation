"""Views for BookmarkPlus content type."""

from datetime import datetime
from Products.Five.browser import BrowserView


class BookmarkPlusView(BrowserView):
    """Default view for BookmarkPlus."""

    def __call__(self):
        """Render the view."""
        return self.index()

    def get_status_class(self):
        """Get CSS class based on read status."""
        status_map = {
            "unread": "bookmark-unread",
            "reading": "bookmark-reading",
            "read": "bookmark-read",
        }
<<<<<<< HEAD
        return status_map.get(self.context.read_status, "bookmark-unread")
=======
        return status_map.get(self.context.read_status, 'bookmark-unread')
>>>>>>> fixing_linting_and_tests

    def get_importance_class(self):
        """Get CSS class based on importance."""
        importance_map = {
            "low": "importance-low",
            "medium": "importance-medium",
            "high": "importance-high",
            "critical": "importance-critical",
        }
<<<<<<< HEAD
        return importance_map.get(self.context.importance, "importance-medium")
=======
        return importance_map.get(self.context.importance, 'importance-medium')
>>>>>>> fixing_linting_and_tests

    def is_high_priority(self):
        """Check if this is a high priority bookmark."""
        return self.context.is_high_priority()

    def get_read_date_formatted(self):
        """Get formatted read date."""
        read_date = self.context.get_read_date()
        if read_date:
            try:
                dt = datetime.fromisoformat(read_date)
                return dt.strftime("%B %d, %Y")
            except (ValueError, TypeError):
                pass
        return None

    def get_reading_duration(self):
        """Calculate reading duration if applicable."""
        if self.context.read_status != "read":
            return None

        started = self.context.get_reading_started_date()
        finished = self.context.get_read_date()

        if started and finished:
            try:
                start_dt = datetime.fromisoformat(started)
                end_dt = datetime.fromisoformat(finished)
                duration = end_dt - start_dt
                return duration.days
            except (ValueError, TypeError):
                pass
        return None

    def has_notes(self):
        """Check if bookmark has notes."""
        return bool(self.context.notes and self.context.notes.raw)
