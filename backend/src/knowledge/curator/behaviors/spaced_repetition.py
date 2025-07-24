"""Spaced Repetition Behavior for Content Types."""

from datetime import datetime
from knowledge.curator.repetition import ForgettingCurve
from knowledge.curator.repetition import SM2Algorithm
from persistent.list import PersistentList
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from persistent.list import PersistentList
from datetime import datetime
from knowledge.curator.repetition import SM2Algorithm, ForgettingCurve


@provider(IFormFieldProvider)
class ISpacedRepetition(model.Schema):
    """Behavior for spaced repetition learning."""

    model.fieldset(
        "spaced_repetition",
        label="Spaced Repetition",
        fields=[
            "sr_enabled",
            "ease_factor",
            "interval",
            "repetitions",
            "last_review",
            "next_review",
            "total_reviews",
            "average_quality",
            "retention_score",
        ],
    )

    sr_enabled = schema.Bool(
        title="Enable Spaced Repetition",
        description="Enable spaced repetition learning for this item",
        default=True,
        required=False,
    )

    directives.mode(ease_factor='display')
    ease_factor = schema.Float(
        title="Ease Factor",
        description="Difficulty factor (1.3-2.5, lower is harder)",
        default=2.5,
        min=1.3,
        max=2.5,
        required=False,
    )

    directives.mode(interval='display')
    interval = schema.Int(
        title="Current Interval",
        description="Days until next review",
        default=0,
        required=False,
    )

    directives.mode(repetitions='display')
    repetitions = schema.Int(
        title="Successful Repetitions",
        description="Number of successful reviews",
        default=0,
        required=False,
    )

    directives.mode(last_review='display')
    last_review = schema.Datetime(
        title="Last Review", description="Date of last review", required=False
    )

    directives.mode(next_review='display')
    next_review = schema.Datetime(
        title="Next Review", description="Scheduled next review date", required=False
    )

    directives.mode(total_reviews='display')
    total_reviews = schema.Int(
        title="Total Reviews",
        description="Total number of reviews",
        default=0,
        required=False,
    )

    directives.mode(average_quality='display')
    average_quality = schema.Float(
        title="Average Quality",
        description="Average review quality (0-5)",
        default=0.0,
        required=False,
    )

    directives.mode(retention_score='display')
    retention_score = schema.Float(
        title="Current Retention",
        description="Estimated retention probability",
        default=1.0,
        min=0.0,
        max=1.0,
        required=False,
    )


@implementer(ISpacedRepetition)
@adapter(ISpacedRepetition)
class SpacedRepetition:
    """Adapter for spaced repetition functionality."""

    def __init__(self, context):
        self.context = context

    @property
    def sr_enabled(self):
        return getattr(self.context, 'sr_enabled', True)

    @sr_enabled.setter
    def sr_enabled(self, value):
        self.context.sr_enabled = value

    @property
    def ease_factor(self):
        return getattr(self.context, 'ease_factor', 2.5)

    @ease_factor.setter
    def ease_factor(self, value):
        self.context.ease_factor = max(1.3, min(2.5, value))

    @property
    def interval(self):
        return getattr(self.context, 'interval', 0)

    @interval.setter
    def interval(self, value):
        self.context.interval = max(0, value)

    @property
    def repetitions(self):
        return getattr(self.context, 'repetitions', 0)

    @repetitions.setter
    def repetitions(self, value):
        self.context.repetitions = max(0, value)

    @property
    def last_review(self):
        return getattr(self.context, 'last_review', None)

    @last_review.setter
    def last_review(self, value):
        self.context.last_review = value

    @property
    def next_review(self):
        return getattr(self.context, 'next_review', None)

    @next_review.setter
    def next_review(self, value):
        self.context.next_review = value

    @property
    def total_reviews(self):
        return getattr(self.context, 'total_reviews', 0)

    @total_reviews.setter
    def total_reviews(self, value):
        self.context.total_reviews = value

    @property
    def average_quality(self):
        return getattr(self.context, 'average_quality', 0.0)

    @average_quality.setter
    def average_quality(self, value):
        self.context.average_quality = value

    @property
    def retention_score(self):
        """Calculate current retention score."""
        if not self.last_review:
            return 1.0

        days_elapsed = (datetime.now() - self.last_review).days
        retention = ForgettingCurve.calculate_retention(
            days_elapsed, self.interval, self.ease_factor, self.repetitions
        )
        return retention

    @property
    def review_history(self):
        """Get review history."""
        if not hasattr(self.context, "_review_history"):
            self.context._review_history = PersistentList()
        return self.context._review_history

    def update_review(self, quality, time_spent=None):
        """
        Update review with quality rating.

        Args:
            quality: Quality of recall (0-5)
            time_spent: Time spent on review in seconds

        Returns:
            Updated review parameters
        """
        if not self.sr_enabled:
            return None

        # Calculate next review parameters
        result = SM2Algorithm.calculate_next_review(
            quality=quality,
            repetitions=self.repetitions,
            ease_factor=self.ease_factor,
            interval=self.interval,
        )

        # Update attributes
        self.ease_factor = result["ease_factor"]
        self.interval = result["interval"]
        self.repetitions = result["repetitions"]
        self.last_review = datetime.now()
        self.next_review = result["next_review_date"]
        self.total_reviews += 1

        # Add to history
        review_entry = {
            "date": datetime.now().isoformat(),
            "quality": quality,
            "interval": result["interval"],
            "ease_factor": result["ease_factor"],
            "time_spent": time_spent,
        }
        self.review_history.append(review_entry)

        # Keep only last 100 entries
        if len(self.review_history) > 100:
            self.context._review_history = PersistentList(self.review_history[-100:])

        # Update average quality
        qualities = [r["quality"] for r in self.review_history]
        self.average_quality = sum(qualities) / len(qualities) if qualities else 0

        return result

    def get_review_stats(self):
        """Get review statistics."""
        if not self.review_history:
            return {
                "total_reviews": 0,
                "average_quality": 0,
                "success_rate": 0,
                "current_streak": 0,
            }

        qualities = [r['quality'] for r in self.review_history]
        successful = sum(1 for q in qualities if q >= 3)

        # Calculate current streak
        current_streak = 0
        for review in reversed(self.review_history):
            if review["quality"] >= 3:
                current_streak += 1
            else:
                break

        return {
            "total_reviews": len(self.review_history),
            "average_quality": sum(qualities) / len(qualities),
            "success_rate": successful / len(qualities) * 100,
            "current_streak": current_streak,
            "ease_factor": self.ease_factor,
            "interval": self.interval,
            "retention": self.retention_score,
        }

    def reset_repetition(self):
        """Reset spaced repetition data."""
        self.ease_factor = 2.5
        self.interval = 0
        self.repetitions = 0
        self.last_review = None
        self.next_review = None
        self.total_reviews = 0
        self.average_quality = 0.0
        if hasattr(self.context, "_review_history"):
            self.context._review_history = PersistentList()

    def is_due_for_review(self):
        """Check if item is due for review."""
        if not self.sr_enabled:
            return False

        if not self.next_review:
            return True

        return datetime.now() >= self.next_review

    def get_urgency_level(self):
        """Get urgency level for review."""
        if not self.is_due_for_review():
            return 'not_due'

        if not self.next_review:
            return 'new'

        days_overdue = (datetime.now() - self.next_review).days

        if days_overdue == 0:
            return "due_today"
        elif days_overdue <= 3:
            return "overdue"
        else:
            return 'very_overdue'

    def get_mastery_level(self):
        """Get mastery level based on interval."""
        if self.interval == 0:
            return "not_started"
        elif self.interval < 7:
            return "learning"
        elif self.interval < 21:
            return "young"
        elif self.interval < 90:
            return "mature"
        else:
            return 'mastered'
