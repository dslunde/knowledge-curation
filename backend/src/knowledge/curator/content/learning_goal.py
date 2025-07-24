"""Learning Goal content type."""

from datetime import datetime
from knowledge.curator.interfaces import ILearningGoal
from plone.dexterity.content import Container
from zope.interface import implementer


@implementer(ILearningGoal)
class LearningGoal(Container):
    """Learning Goal content type implementation."""

    def add_milestone(self, title, description, target_date=None, completed=False):
        """Add a milestone to the learning goal."""
        if not self.milestones:
            self.milestones = []

        milestone = {
            "id": f"milestone-{len(self.milestones) + 1}",
            "title": title,
            "description": description,
            "target_date": target_date,
            "completed": completed,
            "completed_date": None,
        }
        self.milestones.append(milestone)
        return milestone

    def update_milestone(self, milestone_id, **kwargs):
        """Update a specific milestone."""
        if not self.milestones:
            return None

        for milestone in self.milestones:
            if milestone.get("id") == milestone_id:
                milestone.update(kwargs)
                if kwargs.get("completed") and not milestone.get("completed_date"):
                    milestone["completed_date"] = datetime.now().isoformat()
                return milestone
        return None

    def complete_milestone(self, milestone_id):
        """Mark a milestone as completed."""
        return self.update_milestone(milestone_id, completed=True)

    def calculate_progress(self):
        """Calculate progress based on completed milestones."""
        if not self.milestones:
            return 0

<<<<<<< HEAD
        completed = sum(1 for m in self.milestones if m.get("completed", False))
=======
        completed = sum(1 for m in self.milestones if m.get('completed', False))
>>>>>>> fixing_linting_and_tests
        total = len(self.milestones)

        if total == 0:
            return 0

        return int((completed / total) * 100)

    def update_progress(self):
        """Update the progress field based on milestones."""
        self.progress = self.calculate_progress()

    def add_related_note(self, note_uid):
        """Add a related research note."""
        if not self.related_notes:
            self.related_notes = []
        if note_uid not in self.related_notes:
            self.related_notes.append(note_uid)

    def remove_related_note(self, note_uid):
        """Remove a related research note."""
        if self.related_notes and note_uid in self.related_notes:
            self.related_notes.remove(note_uid)

    def is_overdue(self):
        """Check if the goal is overdue."""
        if not self.target_date:
            return False
        return datetime.now().date() > self.target_date and self.progress < 100
