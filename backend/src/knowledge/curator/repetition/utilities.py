"""Review Utilities for Spaced Repetition System."""

from datetime import datetime
from datetime import timedelta
from knowledge.curator.repetition import ForgettingCurve
from knowledge.curator.repetition import PerformanceTracker
from knowledge.curator.repetition import ReviewScheduler
from plone import api


class ReviewUtilities:
    """Utilities for managing spaced repetition reviews."""

    @classmethod
    def get_items_due_for_review(
        cls,
        user_id: str | None = None,
        portal_types: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """
        Get items due for review.

        Args:
            user_id: User ID (defaults to current user)
            portal_types: List of portal types to include
            limit: Maximum number of items to return

        Returns:
            List of items due for review with metadata
        """
        if user_id is None:
            user = api.user.get_current()
            user_id = user.getId()

        if portal_types is None:
            portal_types = ["ResearchNote", "BookmarkPlus", "LearningGoal"]

        catalog = api.portal.get_tool("portal_catalog")

        # Query for user's items
        brains = catalog(Creator=user_id, portal_type=portal_types)

        due_items = []
        now = datetime.now()

        for brain in brains:
            try:
                obj = brain.getObject()

                # Check if object has spaced repetition behavior
                if not hasattr(obj, "sr_enabled"):
                    continue

                # Skip if SR is disabled
                if not obj.sr_enabled:
                    continue

                # Check if due for review
                if obj.next_review is None or obj.next_review <= now:
                    # Calculate retention and urgency
                    retention = 1.0
                    if obj.last_review:
                        days_elapsed = (now - obj.last_review).days
                        retention = ForgettingCurve.calculate_retention(
                            days_elapsed,
                            obj.interval or 1,
                            obj.ease_factor or 2.5,
                            obj.repetitions or 0,
                        )

                    due_items.append({
                        "uid": brain.UID,
                        "title": brain.Title,
                        "description": brain.Description,
                        "portal_type": brain.portal_type,
                        "url": brain.getURL(),
                        "created": brain.created,
                        "modified": brain.modified,
                        "sr_data": {
                            "ease_factor": obj.ease_factor,
                            "interval": obj.interval,
                            "repetitions": obj.repetitions,
                            "last_review": obj.last_review.isoformat()
                            if obj.last_review
                            else None,
                            "next_review": obj.next_review.isoformat()
                            if obj.next_review
                            else None,
                            "total_reviews": obj.total_reviews,
                            "average_quality": obj.average_quality,
                            "retention_score": retention,
                            "mastery_level": cls._get_mastery_level(obj.interval),
                        },
                        "urgency_score": cls._calculate_urgency_score(obj, now),
                    })
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing item {brain.UID}: {e!s}")
                continue

        # Sort by urgency (highest first)
        due_items.sort(key=lambda x: x["urgency_score"], reverse=True)

        # Apply limit if specified
        if limit:
            due_items = due_items[:limit]

        return due_items

    @classmethod
    def _calculate_urgency_score(cls, obj, now):
        """Calculate urgency score for an item."""
        if not obj.next_review:
            return 999  # New items have highest urgency

        days_overdue = (now - obj.next_review).days

        # Factor in retention score
        retention = 1.0
        if obj.last_review:
            days_elapsed = (now - obj.last_review).days
            retention = ForgettingCurve.calculate_retention(
                days_elapsed,
                obj.interval or 1,
                obj.ease_factor or 2.5,
                obj.repetitions or 0,
            )

        # Urgency increases with days overdue and decreases with retention
        urgency = days_overdue * (2 - retention)

        return urgency

    @classmethod
    def _get_mastery_level(cls, interval):
        """Get mastery level based on interval."""
        if interval == 0:
            return "not_started"
        elif interval < 7:
            return "learning"
        elif interval < 21:
            return "young"
        elif interval < 90:
            return "mature"
        else:
            return "mastered"

    @classmethod
    def calculate_optimal_review_times(
        cls, items: list[dict], target_retention: float = 0.9
    ) -> list[dict]:
        """
        Calculate optimal review times for items.

        Args:
            items: List of items with SR data
            target_retention: Target retention probability

        Returns:
            List of items with optimal review times
        """
        results = []

        for item in items:
            sr_data = item.get("sr_data", {})

            optimal_days = ForgettingCurve.find_optimal_review_day(
                interval=sr_data.get("interval", 1),
                ease_factor=sr_data.get("ease_factor", 2.5),
                repetitions=sr_data.get("repetitions", 0),
                target_retention=target_retention,
            )

            if sr_data.get("last_review"):
                last_review = datetime.fromisoformat(sr_data["last_review"])
                optimal_date = last_review + timedelta(days=optimal_days)
            else:
                optimal_date = datetime.now()

            results.append({
                "item": item,
                "optimal_days": optimal_days,
                "optimal_date": optimal_date.isoformat(),
                "current_retention": sr_data.get("retention_score", 1.0),
            })

        return results

    @classmethod
    def handle_review_response(
        cls, uid: str, quality: int, time_spent: int | None = None
    ) -> dict:
        """
        Handle a review response and update the item.

        Args:
            uid: UID of the item
            quality: Quality rating (0-5)
            time_spent: Time spent in seconds

        Returns:
            Updated review data
        """
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(UID=uid)

        if not brains:
            raise ValueError(f"Item with UID {uid} not found")

        obj = brains[0].getObject()

        # Check permissions
        if not api.user.has_permission("Modify portal content", obj=obj):
            raise PermissionError("User does not have permission to modify this item")

        # Update review using the behavior
        if hasattr(obj, "update_review"):
            result = obj.update_review(quality, time_spent)
            obj.reindexObject()

            return {
                "success": True,
                "uid": uid,
                "title": obj.Title(),
                "new_interval": result["interval"],
                "new_ease_factor": result["ease_factor"],
                "next_review_date": result["next_review_date"].isoformat(),
                "repetitions": result["repetitions"],
                "quality": quality,
            }
        else:
            raise ValueError("Item does not have spaced repetition behavior")

    @classmethod
    def get_adaptive_schedule(
        cls, user_id: str | None = None, days_ahead: int = 30
    ) -> dict:
        """
        Get adaptive review schedule based on performance.

        Args:
            user_id: User ID
            days_ahead: Number of days to forecast

        Returns:
            Adaptive schedule with recommendations
        """
        if user_id is None:
            user = api.user.get_current()
            user_id = user.getId()

        # Get user's items
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(
            Creator=user_id,
            portal_type=["ResearchNote", "BookmarkPlus", "LearningGoal"],
        )

        items = []
        review_history = []

        for brain in brains:
            try:
                obj = brain.getObject()
                if hasattr(obj, "sr_enabled") and obj.sr_enabled:
                    item_data = {
                        "uid": brain.UID,
                        "title": brain.Title,
                        "sr_data": {
                            "ease_factor": obj.ease_factor,
                            "interval": obj.interval,
                            "repetitions": obj.repetitions,
                            "last_review": obj.last_review,
                            "next_review": obj.next_review,
                        },
                    }
                    items.append(item_data)

                    # Collect review history
                    if hasattr(obj, "review_history"):
                        for review in obj.review_history:
                            review_copy = dict(review)
                            review_copy["item_id"] = brain.UID
                            review_history.append(review_copy)
            except (AttributeError, KeyError, TypeError):
                continue

        # Get user settings
        member = api.user.get(user_id)
        settings = member.getProperty("sr_settings", {})
        if not settings:
            settings = {
                "daily_review_limit": 20,
                "review_order": "urgency",
                "break_interval": 10,
                "session_duration": 20,
            }

        # Calculate performance metrics
        performance = PerformanceTracker.calculate_performance_metrics(
            review_history, 30
        )

        # Get workload prediction
        workload = ForgettingCurve.predict_workload(items, days_ahead)

        # Get optimal review times
        optimal_times = PerformanceTracker.optimize_review_time(
            settings, review_history
        )

        # Create learning sessions for next 7 days
        sessions = []
        for i in range(7):
            date = datetime.now().date() + timedelta(days=i)
            day_items = [
                item
                for item in items
                if item["sr_data"].get("next_review")
                and item["sr_data"]["next_review"].date() == date
            ]

            if day_items:
                session = ReviewScheduler.create_learning_session(day_items, settings)
                session["date"] = date.isoformat()
                sessions.append(session)

        return {
            "performance": performance,
            "workload_forecast": workload,
            "optimal_times": optimal_times,
            "upcoming_sessions": sessions,
            "recommendations": cls._generate_schedule_recommendations(
                performance, workload, optimal_times
            ),
        }

    @classmethod
    def _generate_schedule_recommendations(
        cls, performance: dict, workload: list[dict], optimal_times: dict
    ) -> list[str]:
        """Generate schedule recommendations."""
        recommendations = []

        # Check for overload days
        avg_daily = sum(day["count"] for day in workload[:30]) / 30
        overload_days = [day for day in workload[:7] if day["count"] > avg_daily * 1.5]

        if overload_days:
            recommendations.append(
                f"You have {len(overload_days)} days with heavy review load. "
                "Consider spreading reviews more evenly."
            )

        # Performance-based recommendations
        if performance["summary"]["success_rate"] < 80:
            recommendations.append(
                "Your success rate is below 80%. Consider reviewing items "
                "more frequently or breaking down complex topics."
            )

        # Time-based recommendations
        if optimal_times.get("best_review_times"):
            best_time = optimal_times["best_review_times"][0]
            recommendations.append(
                f"Your best performance is at {best_time['time']}. "
                "Try to schedule important reviews during this time."
            )

        return recommendations

    @classmethod
    def get_items_at_risk(
        cls, user_id: str | None = None, retention_threshold: float = 0.8
    ) -> list[dict]:
        """
        Get items at risk of being forgotten.

        Args:
            user_id: User ID
            retention_threshold: Retention threshold

        Returns:
            List of items below retention threshold
        """
        items = cls.get_items_due_for_review(user_id, limit=None)

        # Filter by retention
        at_risk = [
            item
            for item in items
            if item["sr_data"]["retention_score"] < retention_threshold
        ]

        # Sort by retention (lowest first)
        at_risk.sort(key=lambda x: x["sr_data"]["retention_score"])

        # Add risk level
        for item in at_risk:
            retention = item["sr_data"]["retention_score"]
            if retention < 0.2:
                item["risk_level"] = "critical"
            elif retention < 0.5:
                item["risk_level"] = "high"
            elif retention < 0.8:
                item["risk_level"] = "medium"
            else:
                item["risk_level"] = "low"

        return at_risk

    @classmethod
    def bulk_reschedule(cls, uids: list[str], strategy: str = "optimal") -> dict:
        """
        Bulk reschedule items.

        Args:
            uids: List of item UIDs
            strategy: Rescheduling strategy (optimal, reset, postpone)

        Returns:
            Results of rescheduling
        """
        results = {"success": [], "failed": [], "total": len(uids)}

        catalog = api.portal.get_tool("portal_catalog")

        for uid in uids:
            try:
                brains = catalog(UID=uid)
                if not brains:
                    results["failed"].append({"uid": uid, "error": "Item not found"})
                    continue

                obj = brains[0].getObject()

                if not api.user.has_permission("Modify portal content", obj=obj):
                    results["failed"].append({"uid": uid, "error": "Permission denied"})
                    continue

                if strategy == "optimal":
                    # Calculate optimal interval
                    optimal_days = ForgettingCurve.find_optimal_review_day(
                        interval=obj.interval or 1,
                        ease_factor=obj.ease_factor or 2.5,
                        repetitions=obj.repetitions or 0,
                    )
                    obj.next_review = datetime.now() + timedelta(days=optimal_days)

                elif strategy == "reset":
                    # Reset to beginning
                    obj.reset_repetition()

                elif strategy == "postpone":
                    # Postpone by current interval
                    days = obj.interval or 1
                    obj.next_review = datetime.now() + timedelta(days=days)

                obj.reindexObject()

                results["success"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "new_review_date": obj.next_review.isoformat()
                    if obj.next_review
                    else None,
                })

            except Exception as e:
                results["failed"].append({"uid": uid, "error": str(e)})

        return results
