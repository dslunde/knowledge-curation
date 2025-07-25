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

    def update_knowledge_item_progress(self, knowledge_item_uid, new_mastery_level):
        """Update the mastery level for a specific knowledge item.
        
        Args:
            knowledge_item_uid: The UID of the knowledge item
            new_mastery_level: The new mastery level (0.0-1.0)
            
        Returns:
            dict: Dictionary with 'success' bool and 'message' string
        """
        # Initialize knowledge_item_progress if it doesn't exist
        if not hasattr(self, 'knowledge_item_progress'):
            self.knowledge_item_progress = PersistentMapping()
        
        # Validate mastery level is within range
        if not isinstance(new_mastery_level, (int, float)):
            return {
                'success': False,
                'message': 'Mastery level must be a number'
            }
        
        if new_mastery_level < 0.0 or new_mastery_level > 1.0:
            return {
                'success': False,
                'message': 'Mastery level must be between 0.0 and 1.0'
            }
        
        # Check if knowledge item UID exists in the Learning Goal's target items
        # Note: In a real implementation, we'd validate against the actual knowledge items
        # For now, we'll accept any UID and let the system validate elsewhere
        if not knowledge_item_uid:
            return {
                'success': False,
                'message': 'Knowledge item UID cannot be empty'
            }
        
        # Get the old value for logging
        old_value = self.knowledge_item_progress.get(knowledge_item_uid, 0.0)
        
        # Update the progress
        self.knowledge_item_progress[knowledge_item_uid] = float(new_mastery_level)
        
        # Add a log entry about the progress update
        self.add_entry(
            description=f"Updated mastery level for knowledge item {knowledge_item_uid} from {old_value:.2f} to {new_mastery_level:.2f}",
            author="System",
            entry_type="progress_update"
        )
        
        # Sync progress to learning goal
        self._sync_progress_to_learning_goal()
        
        return {
            'success': True,
            'message': f'Successfully updated mastery level to {new_mastery_level}'
        }

    def add_learning_session(self, session_data):
        """Add a learning session and update knowledge item progress based on mastery gains.
        
        Args:
            session_data: Dictionary or ILearningSession object with session information
            
        Returns:
            dict: Dictionary with 'success' bool, 'message' string, and 'session' object
        """
        # Initialize learning_sessions if it doesn't exist
        if not hasattr(self, 'learning_sessions'):
            self.learning_sessions = PersistentList()
        
        # Initialize knowledge_item_progress if it doesn't exist
        if not hasattr(self, 'knowledge_item_progress'):
            self.knowledge_item_progress = PersistentMapping()
        
        # Convert dict to PersistentMapping if needed
        if isinstance(session_data, dict):
            session = PersistentMapping(session_data)
        else:
            # Assume it's already a proper object
            session = session_data
        
        # Validate required fields
        if not session.get('session_id'):
            session['session_id'] = f"session-{str(uuid.uuid4())[:8]}"
        
        if not session.get('start_time'):
            return {
                'success': False,
                'message': 'Learning session must have a start_time',
                'session': None
            }
        
        # Set defaults for optional fields
        if 'knowledge_items_studied' not in session:
            session['knowledge_items_studied'] = PersistentList()
        elif not isinstance(session['knowledge_items_studied'], PersistentList):
            session['knowledge_items_studied'] = PersistentList(session['knowledge_items_studied'])
        
        if 'progress_updates' not in session:
            session['progress_updates'] = PersistentMapping()
        elif not isinstance(session['progress_updates'], PersistentMapping):
            session['progress_updates'] = PersistentMapping(session['progress_updates'])
        
        # Update knowledge item progress based on session progress updates
        progress_summary = []
        for ki_uid, progress_delta in session['progress_updates'].items():
            # Validate progress delta
            if not isinstance(progress_delta, (int, float)):
                continue
            
            if progress_delta < 0.0 or progress_delta > 1.0:
                continue
            
            # Get current progress
            current_progress = self.knowledge_item_progress.get(ki_uid, 0.0)
            
            # Calculate new progress (capped at 1.0)
            new_progress = min(1.0, current_progress + progress_delta)
            
            # Update progress
            self.knowledge_item_progress[ki_uid] = new_progress
            
            # Track for summary
            progress_summary.append({
                'uid': ki_uid,
                'old': current_progress,
                'new': new_progress,
                'delta': progress_delta
            })
        
        # Add the session to the list
        self.learning_sessions.append(session)
        
        # Create a log entry for the session
        duration_str = ""
        if session.get('duration_minutes'):
            duration_str = f" ({session['duration_minutes']} minutes)"
        
        progress_str = ""
        if progress_summary:
            progress_items = [f"{p['uid']}: +{p['delta']:.2f} ({p['old']:.2f}→{p['new']:.2f})" 
                            for p in progress_summary]
            progress_str = f" Progress updates: {', '.join(progress_items)}"
        
        self.add_entry(
            description=f"Learning session completed{duration_str}.{progress_str}",
            author="System",
            entry_type="learning_session",
            related_items=list(session.get('knowledge_items_studied', []))
        )
        
        # Sync progress to learning goal after updating knowledge item progress
        if progress_summary:
            self._sync_progress_to_learning_goal()
        
        return {
            'success': True,
            'message': f'Successfully added learning session {session["session_id"]}',
            'session': session
        }
    
    def _sync_progress_to_learning_goal(self):
        """Synchronize Project Log progress with attached Learning Goal overall progress.
        
        This internal method calculates the overall Learning Goal progress based on
        Knowledge Item mastery levels tracked in this Project Log. It uses equal
        weighting for all tracked Knowledge Items, though the Learning Goal may
        contain additional Knowledge Items not tracked here.
        
        The method:
        1. Retrieves the attached Learning Goal
        2. Calculates average mastery across tracked Knowledge Items
        3. Updates the Learning Goal's overall_progress field
        4. Handles cases where Learning Goal has items not tracked in this log
        """
        from plone import api
        
        # Check if we have an attached learning goal
        if not hasattr(self, 'attached_learning_goal') or not self.attached_learning_goal:
            return
        
        # Get the learning goal object
        try:
            learning_goal = api.content.get(UID=self.attached_learning_goal)
            if not learning_goal:
                return
        except Exception:
            # Handle any API errors gracefully
            return
        
        # Check if we have any knowledge item progress to sync
        if not hasattr(self, 'knowledge_item_progress') or not self.knowledge_item_progress:
            # No progress tracked yet, nothing to sync
            return
        
        # Get all target knowledge items from the Learning Goal
        target_items = set()
        if hasattr(learning_goal, 'target_knowledge_items') and learning_goal.target_knowledge_items:
            target_items.update(learning_goal.target_knowledge_items)
        
        # Also include items from the learning path connections
        if hasattr(learning_goal, 'knowledge_item_connections') and learning_goal.knowledge_item_connections:
            for conn in learning_goal.knowledge_item_connections:
                source_uid = conn.get('source_item_uid')
                target_uid = conn.get('target_item_uid')
                if source_uid:
                    target_items.add(source_uid)
                if target_uid:
                    target_items.add(target_uid)
        
        # Include starting knowledge item
        if hasattr(learning_goal, 'starting_knowledge_item') and learning_goal.starting_knowledge_item:
            target_items.add(learning_goal.starting_knowledge_item)
        
        # Calculate progress based on tracked items that are in the Learning Goal
        tracked_items = set(self.knowledge_item_progress.keys())
        relevant_items = tracked_items.intersection(target_items)
        
        if not relevant_items:
            # No overlap between tracked items and Learning Goal items
            # Don't update the Learning Goal progress
            return
        
        # Calculate average mastery level for relevant items
        total_mastery = 0.0
        for item_uid in relevant_items:
            mastery_level = self.knowledge_item_progress.get(item_uid, 0.0)
            total_mastery += mastery_level
        
        # Calculate average (equal weighting)
        average_mastery = total_mastery / len(relevant_items)
        
        # Update the Learning Goal's overall_progress field
        try:
            # Use the learning goal's calculate_overall_progress method if available
            # to get a more sophisticated calculation
            if hasattr(learning_goal, 'calculate_overall_progress'):
                # Pass our knowledge item progress to get weighted calculation
                progress_result = learning_goal.calculate_overall_progress(
                    knowledge_item_mastery=dict(self.knowledge_item_progress)
                )
                new_progress = progress_result.get('weighted_progress', average_mastery)
            else:
                # Fallback to simple average
                new_progress = average_mastery
            
            # Update the overall_progress field
            if hasattr(learning_goal, 'overall_progress'):
                old_progress = getattr(learning_goal, 'overall_progress', 0.0)
                learning_goal.overall_progress = float(new_progress)
                
                # Also update the deprecated progress field for backward compatibility
                if hasattr(learning_goal, 'progress'):
                    learning_goal.progress = int(new_progress * 100)
                
                # Mark the learning goal as modified to ensure it's saved
                learning_goal._p_changed = True
                
                # Log the sync operation
                self.add_entry(
                    description=f"Synced progress to Learning Goal: {old_progress:.2f} → {new_progress:.2f} "
                               f"(based on {len(relevant_items)} of {len(target_items)} items)",
                    author="System",
                    entry_type="sync"
                )
        except Exception as e:
            # Log any errors but don't fail the operation
            self.add_entry(
                description=f"Failed to sync progress to Learning Goal: {str(e)}",
                author="System", 
                entry_type="error"
            )
    
    def get_learning_analytics(self):
        """Generate comprehensive learning analytics from Project Log data.
        
        Returns:
            dict: Comprehensive analytics object with progress trends, mastery velocity,
                  session effectiveness, milestone patterns, and predicted completion timeline.
        """
        from datetime import datetime, timedelta
        from collections import defaultdict
        import statistics
        
        analytics = {
            'generated_at': datetime.now().isoformat(),
            'project_duration_days': self.get_duration(),
            'overall_metrics': {},
            'progress_trends': {},
            'mastery_velocity': {},
            'session_effectiveness': {},
            'milestone_patterns': {},
            'knowledge_item_analytics': {},
            'predictions': {},
            'learning_approach_effectiveness': {},
            'retention_indicators': {}
        }
        
        # Initialize data structures
        if not hasattr(self, 'knowledge_item_progress'):
            self.knowledge_item_progress = PersistentMapping()
        if not hasattr(self, 'learning_sessions'):
            self.learning_sessions = PersistentList()
        if not hasattr(self, 'entries'):
            self.entries = PersistentList()
            
        # 1. Overall Metrics
        total_knowledge_items = len(self.knowledge_item_progress)
        mastered_items = sum(1 for mastery in self.knowledge_item_progress.values() if mastery >= 0.8)
        in_progress_items = sum(1 for mastery in self.knowledge_item_progress.values() if 0.2 <= mastery < 0.8)
        not_started_items = sum(1 for mastery in self.knowledge_item_progress.values() if mastery < 0.2)
        
        overall_progress = 0.0
        if total_knowledge_items > 0:
            overall_progress = sum(self.knowledge_item_progress.values()) / total_knowledge_items
        
        analytics['overall_metrics'] = {
            'total_knowledge_items': total_knowledge_items,
            'mastered_items': mastered_items,
            'in_progress_items': in_progress_items,
            'not_started_items': not_started_items,
            'overall_progress': round(overall_progress, 3),
            'total_learning_sessions': len(self.learning_sessions),
            'total_log_entries': len(self.entries)
        }
        
        # 2. Progress Trends Over Time
        progress_timeline = []
        progress_updates = [e for e in self.entries if e.get('entry_type') == 'progress_update']
        
        # Create a timeline of progress snapshots
        current_progress = {}
        for update in sorted(progress_updates, key=lambda x: x.get('timestamp', datetime.min)):
            # Parse progress update from description
            desc = update.get('description', '')
            if 'Updated mastery level' in desc:
                try:
                    # Extract knowledge item UID and new level from description
                    parts = desc.split()
                    ki_uid_idx = parts.index('item') + 1
                    ki_uid = parts[ki_uid_idx]
                    to_idx = parts.index('to')
                    new_level = float(parts[to_idx + 1])
                    
                    current_progress[ki_uid] = new_level
                    
                    # Calculate overall progress at this point
                    if current_progress:
                        avg_progress = sum(current_progress.values()) / len(current_progress)
                        progress_timeline.append({
                            'timestamp': update['timestamp'].isoformat(),
                            'overall_progress': round(avg_progress, 3),
                            'items_tracked': len(current_progress)
                        })
                except (ValueError, IndexError):
                    continue
        
        analytics['progress_trends'] = {
            'timeline': progress_timeline,
            'trend_direction': self._calculate_trend_direction(progress_timeline),
            'progress_variance': self._calculate_progress_variance(progress_timeline)
        }
        
        # 3. Knowledge Item Mastery Velocity
        ki_velocity = {}
        ki_first_seen = {}
        ki_last_updated = {}
        ki_update_count = defaultdict(int)
        
        for update in progress_updates:
            desc = update.get('description', '')
            if 'Updated mastery level' in desc:
                try:
                    parts = desc.split()
                    ki_uid_idx = parts.index('item') + 1
                    ki_uid = parts[ki_uid_idx]
                    timestamp = update['timestamp']
                    
                    if ki_uid not in ki_first_seen:
                        ki_first_seen[ki_uid] = timestamp
                    ki_last_updated[ki_uid] = timestamp
                    ki_update_count[ki_uid] += 1
                except (ValueError, IndexError):
                    continue
        
        # Calculate velocity for each knowledge item
        for ki_uid, current_mastery in self.knowledge_item_progress.items():
            if ki_uid in ki_first_seen and ki_uid in ki_last_updated:
                time_span = (ki_last_updated[ki_uid] - ki_first_seen[ki_uid]).total_seconds() / 86400  # days
                if time_span > 0:
                    velocity = current_mastery / time_span  # mastery per day
                    ki_velocity[ki_uid] = {
                        'current_mastery': round(current_mastery, 3),
                        'days_active': round(time_span, 1),
                        'mastery_per_day': round(velocity, 4),
                        'update_frequency': ki_update_count[ki_uid],
                        'estimated_days_to_mastery': round((1.0 - current_mastery) / velocity, 1) if velocity > 0 else None
                    }
        
        analytics['mastery_velocity'] = {
            'by_knowledge_item': ki_velocity,
            'average_velocity': round(statistics.mean([v['mastery_per_day'] for v in ki_velocity.values()]), 4) if ki_velocity else 0,
            'fastest_item': max(ki_velocity.items(), key=lambda x: x[1]['mastery_per_day'])[0] if ki_velocity else None,
            'slowest_item': min(ki_velocity.items(), key=lambda x: x[1]['mastery_per_day'])[0] if ki_velocity else None
        }
        
        # 4. Learning Session Effectiveness
        session_metrics = []
        for session in self.learning_sessions:
            duration = session.get('duration_minutes', 0)
            progress_updates = session.get('progress_updates', {})
            total_progress_gain = sum(progress_updates.values())
            items_studied = len(session.get('knowledge_items_studied', []))
            
            effectiveness = 0
            if duration > 0:
                effectiveness = total_progress_gain / (duration / 60)  # progress per hour
            
            session_metrics.append({
                'session_id': session.get('session_id'),
                'duration_minutes': duration,
                'items_studied': items_studied,
                'total_progress_gain': round(total_progress_gain, 3),
                'effectiveness_per_hour': round(effectiveness, 3),
                'average_gain_per_item': round(total_progress_gain / items_studied, 3) if items_studied > 0 else 0
            })
        
        if session_metrics:
            analytics['session_effectiveness'] = {
                'sessions': session_metrics,
                'average_session_duration': round(statistics.mean([s['duration_minutes'] for s in session_metrics]), 1),
                'average_effectiveness': round(statistics.mean([s['effectiveness_per_hour'] for s in session_metrics]), 3),
                'most_effective_session': max(session_metrics, key=lambda x: x['effectiveness_per_hour'])['session_id'],
                'total_study_time_hours': round(sum([s['duration_minutes'] for s in session_metrics]) / 60, 1)
            }
        else:
            analytics['session_effectiveness'] = {
                'sessions': [],
                'average_session_duration': 0,
                'average_effectiveness': 0,
                'most_effective_session': None,
                'total_study_time_hours': 0
            }
        
        # 5. Milestone Achievement Patterns
        milestone_entries = [e for e in self.entries if e.get('entry_type') == 'milestone']
        milestones_by_day = defaultdict(int)
        milestones_by_week = defaultdict(int)
        
        for milestone in milestone_entries:
            timestamp = milestone.get('timestamp')
            if timestamp:
                day_key = timestamp.strftime('%Y-%m-%d')
                week_key = timestamp.strftime('%Y-W%U')
                milestones_by_day[day_key] += 1
                milestones_by_week[week_key] += 1
        
        analytics['milestone_patterns'] = {
            'total_milestones': len(milestone_entries),
            'milestones_by_day': dict(milestones_by_day),
            'milestones_by_week': dict(milestones_by_week),
            'average_milestones_per_week': round(len(milestone_entries) / max(1, len(milestones_by_week)), 2) if milestones_by_week else 0,
            'most_productive_day': max(milestones_by_day.items(), key=lambda x: x[1])[0] if milestones_by_day else None
        }
        
        # 6. Predictions
        if ki_velocity and overall_progress < 1.0:
            # Calculate estimated completion based on current velocity
            remaining_progress = 1.0 - overall_progress
            avg_velocity = analytics['mastery_velocity']['average_velocity']
            
            if avg_velocity > 0:
                estimated_days = remaining_progress / avg_velocity
                estimated_completion = datetime.now() + timedelta(days=estimated_days)
                
                analytics['predictions'] = {
                    'estimated_completion_date': estimated_completion.isoformat(),
                    'estimated_days_remaining': round(estimated_days, 1),
                    'confidence_level': self._calculate_prediction_confidence(ki_velocity, session_metrics),
                    'recommended_daily_study_time': self._calculate_recommended_study_time(session_metrics, estimated_days)
                }
        else:
            analytics['predictions'] = {
                'estimated_completion_date': None,
                'estimated_days_remaining': None,
                'confidence_level': 'low',
                'recommended_daily_study_time': None
            }
        
        # 7. Learning Approach Effectiveness
        approach_effectiveness = defaultdict(lambda: {'sessions': 0, 'total_gain': 0})
        
        for session in self.learning_sessions:
            approach = session.get('learning_approach', 'unspecified')
            progress_updates = session.get('progress_updates', {})
            total_gain = sum(progress_updates.values())
            
            approach_effectiveness[approach]['sessions'] += 1
            approach_effectiveness[approach]['total_gain'] += total_gain
        
        analytics['learning_approach_effectiveness'] = {}
        for approach, data in approach_effectiveness.items():
            analytics['learning_approach_effectiveness'][approach] = {
                'sessions_count': data['sessions'],
                'total_progress_gain': round(data['total_gain'], 3),
                'average_gain_per_session': round(data['total_gain'] / data['sessions'], 3) if data['sessions'] > 0 else 0
            }
        
        # 8. Knowledge Retention Indicators
        retention_metrics = {}
        
        # Look for patterns in progress updates that might indicate forgetting
        for ki_uid in self.knowledge_item_progress:
            ki_updates = []
            for update in progress_updates:
                desc = update.get('description', '')
                if f'item {ki_uid}' in desc:
                    try:
                        parts = desc.split()
                        from_idx = parts.index('from')
                        to_idx = parts.index('to')
                        old_level = float(parts[from_idx + 1])
                        new_level = float(parts[to_idx + 1])
                        ki_updates.append({
                            'timestamp': update['timestamp'],
                            'old': old_level,
                            'new': new_level,
                            'delta': new_level - old_level
                        })
                    except (ValueError, IndexError):
                        continue
            
            if len(ki_updates) >= 2:
                # Check for any negative progress (forgetting)
                negative_updates = sum(1 for u in ki_updates if u['delta'] < 0)
                total_positive_gain = sum(u['delta'] for u in ki_updates if u['delta'] > 0)
                total_negative_loss = sum(abs(u['delta']) for u in ki_updates if u['delta'] < 0)
                
                retention_metrics[ki_uid] = {
                    'update_count': len(ki_updates),
                    'negative_updates': negative_updates,
                    'retention_rate': round(1 - (total_negative_loss / max(0.001, total_positive_gain)), 3) if total_positive_gain > 0 else 1.0,
                    'stability_indicator': 'stable' if negative_updates == 0 else ('unstable' if negative_updates > len(ki_updates) * 0.3 else 'moderate')
                }
        
        analytics['retention_indicators'] = {
            'by_knowledge_item': retention_metrics,
            'overall_retention_rate': round(statistics.mean([m['retention_rate'] for m in retention_metrics.values()]), 3) if retention_metrics else 1.0,
            'items_needing_review': [ki for ki, metrics in retention_metrics.items() if metrics['stability_indicator'] == 'unstable']
        }
        
        # 9. Individual Knowledge Item Analytics
        for ki_uid, mastery in self.knowledge_item_progress.items():
            ki_analytics = {
                'current_mastery': round(mastery, 3),
                'status': 'mastered' if mastery >= 0.8 else ('in_progress' if mastery >= 0.2 else 'not_started'),
                'velocity': ki_velocity.get(ki_uid, {}).get('mastery_per_day', 0),
                'estimated_completion': ki_velocity.get(ki_uid, {}).get('estimated_days_to_mastery'),
                'retention': retention_metrics.get(ki_uid, {}).get('retention_rate', 1.0),
                'last_updated': ki_last_updated.get(ki_uid).isoformat() if ki_uid in ki_last_updated else None
            }
            analytics['knowledge_item_analytics'][ki_uid] = ki_analytics
        
        return analytics
    
    def _calculate_trend_direction(self, timeline):
        """Calculate the overall trend direction from progress timeline."""
        if len(timeline) < 2:
            return 'insufficient_data'
        
        # Simple linear regression to determine trend
        progress_values = [p['overall_progress'] for p in timeline]
        n = len(progress_values)
        
        if n < 2:
            return 'insufficient_data'
        
        # Calculate slope
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(progress_values) / n
        
        numerator = sum((x[i] - x_mean) * (progress_values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_progress_variance(self, timeline):
        """Calculate variance in progress to identify consistency."""
        if len(timeline) < 2:
            return 0
        
        progress_values = [p['overall_progress'] for p in timeline]
        return round(statistics.variance(progress_values), 4) if len(progress_values) > 1 else 0
    
    def _calculate_prediction_confidence(self, ki_velocity, session_metrics):
        """Calculate confidence level for predictions based on data consistency."""
        if not ki_velocity or not session_metrics:
            return 'low'
        
        # Check consistency of velocity
        velocities = [v['mastery_per_day'] for v in ki_velocity.values()]
        if len(velocities) < 3:
            return 'low'
        
        cv = statistics.stdev(velocities) / statistics.mean(velocities) if statistics.mean(velocities) > 0 else 1
        
        # Check session regularity
        session_count = len(session_metrics)
        
        if session_count >= 10 and cv < 0.3:
            return 'high'
        elif session_count >= 5 and cv < 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_recommended_study_time(self, session_metrics, estimated_days):
        """Calculate recommended daily study time to meet completion estimate."""
        if not session_metrics or not estimated_days or estimated_days <= 0:
            return None
        
        avg_effectiveness = statistics.mean([s['effectiveness_per_hour'] for s in session_metrics]) if session_metrics else 0
        
        if avg_effectiveness <= 0:
            return None
        
        # Calculate required progress per day
        remaining_items = sum(1 for mastery in self.knowledge_item_progress.values() if mastery < 0.8)
        if remaining_items == 0:
            return 0
        
        # Estimate hours needed per day
        required_progress_per_day = (1.0 - sum(self.knowledge_item_progress.values()) / len(self.knowledge_item_progress)) / estimated_days
        recommended_hours = required_progress_per_day / avg_effectiveness
        
        return round(recommended_hours * 60, 0)  # Convert to minutes
