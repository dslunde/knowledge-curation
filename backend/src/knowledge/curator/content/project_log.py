"""Project Log content type."""

from datetime import datetime
from knowledge.curator.interfaces import IProjectLog
from plone.dexterity.content import Container
from zope.interface import implementer


@implementer(IProjectLog)
class ProjectLog(Container):
    """Project Log content type implementation."""

    def add_entry(self, title, content, tags=None):
        """Add a new log entry."""
        if not self.entries:
            self.entries = []

        entry = {
            "id": f"entry-{len(self.entries) + 1}",
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "content": content,
            "tags": tags or [],
            "attachments": [],
        }
        self.entries.append(entry)
        return entry

    def update_entry(self, entry_id, **kwargs):
        """Update a specific log entry."""
        if not self.entries:
            return None

        for entry in self.entries:
            if entry.get("id") == entry_id:
                # Preserve original timestamp
                kwargs["timestamp"] = entry["timestamp"]
                kwargs["modified"] = datetime.now().isoformat()
                entry.update(kwargs)
                return entry
        return None

    def get_entries_by_tag(self, tag):
        """Get all entries with a specific tag."""
        if not self.entries:
            return []

<<<<<<< HEAD
        return [entry for entry in self.entries if tag in entry.get("tags", [])]
=======
        return [entry for entry in self.entries
                if tag in entry.get('tags', [])]
>>>>>>> fixing_linting_and_tests

    def get_recent_entries(self, limit=10):
        """Get the most recent log entries."""
        if not self.entries:
            return []

        # Sort by timestamp descending
        sorted_entries = sorted(
            self.entries, key=lambda x: x.get("timestamp", ""), reverse=True
        )
        return sorted_entries[:limit]

    def add_deliverable(self, deliverable):
        """Add a project deliverable."""
        if not self.deliverables:
            self.deliverables = []
        self.deliverables.append(deliverable)

    def add_learning(self, learning):
        """Add a key learning."""
        if not self.learnings:
            self.learnings = []
        self.learnings.append(learning)

    def update_status(self, new_status):
        """Update project status with validation."""
        valid_statuses = ["planning", "active", "paused", "completed", "archived"]
        if new_status in valid_statuses:
            self.status = new_status
            # Add status change to log
            self.add_entry(
                f"Status changed to {new_status}",
                f"Project status updated from {self.status} to {new_status}",
                tags=["status-change"],
            )
            return True
        return False

    def get_duration(self):
        """Calculate project duration in days."""
        if not self.start_date:
            return 0

        end_date = datetime.now().date()
        if self.status == "completed" and self.entries:
            # Find the last entry date
            for entry in reversed(self.entries):
                if "completed" in entry.get("tags", []):
                    try:
                        end_date = datetime.fromisoformat(entry["timestamp"]).date()
                        break
                    except (ValueError, TypeError):
                        pass

        duration = (end_date - self.start_date).days
        return max(0, duration)
