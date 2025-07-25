"""Project Log content type."""

from datetime import datetime
from knowledge.curator.interfaces import (IProjectLog, IProjectLogEntry, 
                                         IProjectDeliverable, IStakeholder, 
                                         IProjectResource, ISuccessMetric, 
                                         ILessonLearned)
from plone.dexterity.content import Container
from zope.interface import implementer
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import uuid


@implementer(IProjectLog)
class ProjectLog(Container):
    """Project Log content type implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize structured lists
        if not hasattr(self, 'entries'):
            self.entries = PersistentList()
        if not hasattr(self, 'deliverables'):
            self.deliverables = PersistentList()
        if not hasattr(self, 'stakeholders'):
            self.stakeholders = PersistentList()
        if not hasattr(self, 'resources_used'):
            self.resources_used = PersistentList()
        if not hasattr(self, 'success_metrics'):
            self.success_metrics = PersistentList()
        if not hasattr(self, 'lessons_learned'):
            self.lessons_learned = PersistentList()

    def add_entry(self, description, author, entry_type='note', related_items=None):
        """Add a new structured log entry."""
        if not hasattr(self, 'entries'):
            self.entries = PersistentList()

        entry = PersistentMapping()
        entry['id'] = f"entry-{str(uuid.uuid4())[:8]}"
        entry['timestamp'] = datetime.now()
        entry['author'] = author
        entry['entry_type'] = entry_type
        entry['description'] = description
        entry['related_items'] = related_items or []
        
        self.entries.append(entry)
        return entry

    def update_entry(self, entry_id, **kwargs):
        """Update a specific log entry."""
        if not hasattr(self, 'entries'):
            return None

        for entry in self.entries:
            if entry.get("id") == entry_id:
                # Preserve original timestamp
                kwargs["timestamp"] = entry["timestamp"]
                kwargs["modified"] = datetime.now()
                entry.update(kwargs)
                return entry
        return None

    def get_entries_by_type(self, entry_type):
        """Get all entries with a specific type."""
        if not hasattr(self, 'entries'):
            return []

        return [entry for entry in self.entries if entry.get("entry_type") == entry_type]

    def get_recent_entries(self, limit=10):
        """Get the most recent log entries."""
        if not hasattr(self, 'entries'):
            return []

        # Sort by timestamp descending
        sorted_entries = sorted(
            self.entries, key=lambda x: x.get("timestamp", datetime.min), reverse=True
        )
        return sorted_entries[:limit]

    def add_deliverable(self, title, description=None, due_date=None, status='not_started', assigned_to=None):
        """Add a structured project deliverable."""
        if not hasattr(self, 'deliverables'):
            self.deliverables = PersistentList()
        
        deliverable = PersistentMapping()
        deliverable['title'] = title
        deliverable['description'] = description
        deliverable['due_date'] = due_date
        deliverable['status'] = status
        deliverable['assigned_to'] = assigned_to
        deliverable['completion_percentage'] = 0
        
        self.deliverables.append(deliverable)
        return deliverable

    def add_stakeholder(self, name, role=None, interest_level='medium', influence_level='medium', contact_info=None):
        """Add a project stakeholder."""
        if not hasattr(self, 'stakeholders'):
            self.stakeholders = PersistentList()
        
        stakeholder = PersistentMapping()
        stakeholder['name'] = name
        stakeholder['role'] = role
        stakeholder['interest_level'] = interest_level
        stakeholder['influence_level'] = influence_level
        stakeholder['contact_info'] = contact_info
        
        self.stakeholders.append(stakeholder)
        return stakeholder

    def add_resource(self, resource_type, name, quantity=None, availability='available', cost=None):
        """Add a project resource."""
        if not hasattr(self, 'resources_used'):
            self.resources_used = PersistentList()
        
        resource = PersistentMapping()
        resource['resource_type'] = resource_type
        resource['name'] = name
        resource['quantity'] = quantity
        resource['availability'] = availability
        resource['cost'] = cost
        
        self.resources_used.append(resource)
        return resource

    def add_success_metric(self, metric_name, target_value, current_value=None, unit=None, measurement_method=None):
        """Add a success metric."""
        if not hasattr(self, 'success_metrics'):
            self.success_metrics = PersistentList()
        
        metric = PersistentMapping()
        metric['metric_name'] = metric_name
        metric['target_value'] = target_value
        metric['current_value'] = current_value
        metric['unit'] = unit
        metric['measurement_method'] = measurement_method
        
        self.success_metrics.append(metric)
        return metric

    def add_lesson_learned(self, lesson, context=None, impact='medium', recommendations=None):
        """Add a lesson learned."""
        if not hasattr(self, 'lessons_learned'):
            self.lessons_learned = PersistentList()
        
        lesson_obj = PersistentMapping()
        lesson_obj['lesson'] = lesson
        lesson_obj['context'] = context
        lesson_obj['impact'] = impact
        lesson_obj['recommendations'] = recommendations
        
        self.lessons_learned.append(lesson_obj)
        return lesson_obj

    def update_status(self, new_status):
        """Update project status with validation."""
        valid_statuses = ["planning", "active", "paused", "completed", "archived"]
        if new_status in valid_statuses:
            old_status = self.status
            self.status = new_status
            # Add status change to log
            self.add_entry(
                description=f"Project status updated from {old_status} to {new_status}",
                author="System",
                entry_type="milestone"
            )
            return True
        return False

    def get_duration(self):
        """Calculate project duration in days."""
        if not self.start_date:
            return 0

        end_date = datetime.now().date()
        if self.status == "completed" and hasattr(self, 'entries'):
            # Find entries marked as project completion
            for entry in reversed(self.entries):
                if entry.get("entry_type") == "milestone" and "completed" in entry.get("description", "").lower():
                    try:
                        end_date = entry["timestamp"].date()
                        break
                    except (AttributeError, TypeError):
                        pass

        duration = (end_date - self.start_date).days
        return max(0, duration)

    def migrate_legacy_entries(self):
        """Migrate legacy text entries to structured format."""
        # Check if we have old-style entries
        if hasattr(self, 'entries') and self.entries:
            # Check if first item is a string or old dict format
            if self.entries and (isinstance(self.entries[0], str) or 
                               (isinstance(self.entries[0], dict) and 
                                'entry_type' not in self.entries[0])):
                old_entries = list(self.entries)
                self.entries = PersistentList()
                
                for entry in old_entries:
                    if isinstance(entry, str):
                        self.add_entry(
                            description=entry,
                            author="Unknown",
                            entry_type="note"
                        )
                    elif isinstance(entry, dict):
                        # Old dict format migration
                        self.add_entry(
                            description=entry.get('content', entry.get('title', '')),
                            author="Unknown",
                            entry_type="note"
                        )
                return True
        return False

    def migrate_legacy_deliverables(self):
        """Migrate legacy text deliverables to structured format."""
        # Check if we have old-style deliverables
        if hasattr(self, 'deliverables') and self.deliverables:
            # Check if first item is a string
            if self.deliverables and isinstance(self.deliverables[0], str):
                old_deliverables = list(self.deliverables)
                self.deliverables = PersistentList()
                
                for deliverable in old_deliverables:
                    self.add_deliverable(
                        title=deliverable,
                        status='not_started'
                    )
                return True
        return False
