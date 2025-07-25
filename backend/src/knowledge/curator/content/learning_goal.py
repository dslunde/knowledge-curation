"""Learning Goal content type."""

from datetime import datetime
from knowledge.curator.interfaces import ILearningGoal, ILearningMilestone, ILearningObjective, IAssessmentCriterion, ICompetency
from plone.dexterity.content import Container
from zope.interface import implementer
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import uuid


@implementer(ILearningGoal)
class LearningGoal(Container):
    """Learning Goal content type implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize structured lists
        if not hasattr(self, 'milestones'):
            self.milestones = PersistentList()
        if not hasattr(self, 'learning_objectives'):
            self.learning_objectives = PersistentList()
        if not hasattr(self, 'assessment_criteria'):
            self.assessment_criteria = PersistentList()
        if not hasattr(self, 'competencies'):
            self.competencies = PersistentList()
        if not hasattr(self, 'prerequisite_knowledge'):
            self.prerequisite_knowledge = PersistentList()

    def add_milestone(self, title, description, target_date=None, status='not_started', progress_percentage=0, completion_criteria=None):
        """Add a structured milestone to the learning goal."""
        if not hasattr(self, 'milestones'):
            self.milestones = PersistentList()

        milestone = PersistentMapping()
        milestone['id'] = f"milestone-{str(uuid.uuid4())[:8]}"
        milestone['title'] = title
        milestone['description'] = description
        milestone['target_date'] = target_date
        milestone['status'] = status
        milestone['progress_percentage'] = progress_percentage
        milestone['completion_criteria'] = completion_criteria
        
        self.milestones.append(milestone)
        return milestone

    def update_milestone(self, milestone_id, **kwargs):
        """Update a specific milestone."""
        if not hasattr(self, 'milestones'):
            return None

        for milestone in self.milestones:
            if milestone.get("id") == milestone_id:
                milestone.update(kwargs)
                if kwargs.get("status") == 'completed' and milestone['status'] != 'completed':
                    milestone["completed_date"] = datetime.now()
                return milestone
        return None

    def complete_milestone(self, milestone_id):
        """Mark a milestone as completed."""
        return self.update_milestone(milestone_id, status='completed', progress_percentage=100)

    def add_learning_objective(self, objective_text, measurable=False, achievable=False, 
                             relevant=False, time_bound=False, success_metrics=None):
        """Add a SMART learning objective."""
        if not hasattr(self, 'learning_objectives'):
            self.learning_objectives = PersistentList()
        
        objective = PersistentMapping()
        objective['objective_text'] = objective_text
        objective['measurable'] = measurable
        objective['achievable'] = achievable
        objective['relevant'] = relevant
        objective['time_bound'] = time_bound
        objective['success_metrics'] = success_metrics or []
        
        self.learning_objectives.append(objective)
        return objective

    def add_assessment_criterion(self, criterion, weight=1.0, description=None):
        """Add an assessment criterion."""
        if not hasattr(self, 'assessment_criteria'):
            self.assessment_criteria = PersistentList()
        
        assessment = PersistentMapping()
        assessment['criterion'] = criterion
        assessment['weight'] = weight
        assessment['description'] = description
        
        self.assessment_criteria.append(assessment)
        return assessment

    def add_competency(self, name, description=None, level='beginner', category=None):
        """Add a competency to be developed."""
        if not hasattr(self, 'competencies'):
            self.competencies = PersistentList()
        
        competency = PersistentMapping()
        competency['name'] = name
        competency['description'] = description
        competency['level'] = level
        competency['category'] = category
        
        self.competencies.append(competency)
        return competency

    def calculate_progress(self):
        """Calculate progress based on milestone completion."""
        if not hasattr(self, 'milestones') or not self.milestones:
            return 0

        total_progress = sum(m.get('progress_percentage', 0) for m in self.milestones)
        total_milestones = len(self.milestones)

        if total_milestones == 0:
            return 0

        return int(total_progress / total_milestones)

    def update_progress(self):
        """Update the progress field based on milestones."""
        self.progress = self.calculate_progress()

    def add_related_note(self, note_uid):
        """Add a related research note."""
        if not hasattr(self, 'related_notes'):
            self.related_notes = PersistentList()
        if note_uid not in self.related_notes:
            self.related_notes.append(note_uid)

    def remove_related_note(self, note_uid):
        """Remove a related research note."""
        if hasattr(self, 'related_notes') and note_uid in self.related_notes:
            self.related_notes.remove(note_uid)

    def is_overdue(self):
        """Check if the goal is overdue."""
        if not self.target_date:
            return False
        return datetime.now().date() > self.target_date and self.progress < 100

    def migrate_legacy_milestones(self):
        """Migrate legacy text milestones to structured format."""
        # Check if we have old-style milestones
        if hasattr(self, 'milestones') and self.milestones:
            # Check if first item is a string or dict without proper structure
            if self.milestones and (isinstance(self.milestones[0], str) or 
                                   (isinstance(self.milestones[0], dict) and 
                                    'status' not in self.milestones[0])):
                old_milestones = list(self.milestones)
                self.milestones = PersistentList()
                
                for idx, milestone in enumerate(old_milestones):
                    if isinstance(milestone, str):
                        self.add_milestone(
                            title=milestone,
                            description='',
                            status='not_started'
                        )
                    elif isinstance(milestone, dict):
                        # Old dict format migration
                        self.add_milestone(
                            title=milestone.get('title', f'Milestone {idx+1}'),
                            description=milestone.get('description', ''),
                            target_date=milestone.get('target_date'),
                            status='completed' if milestone.get('completed') else 'not_started',
                            progress_percentage=100 if milestone.get('completed') else 0
                        )
                return True
        return False
