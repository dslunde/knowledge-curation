"""Review Interface Views for Spaced Repetition."""

from datetime import datetime
from knowledge.curator.repetition import ForgettingCurve
from knowledge.curator.repetition import PerformanceTracker
from knowledge.curator.repetition.utilities import ReviewUtilities
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.interface import alsoProvides



class ReviewQueueView(BrowserView):
    """Review queue interface."""

    template = ViewPageTemplateFile("templates/review_queue.pt")

    def __call__(self):
        return self.template()

    def get_review_items(self):
        """Get items due for review."""
        limit = int(self.request.get("limit", 20))
        portal_types = self.request.get("types", "ResearchNote,BookmarkPlus").split(",")

        items = ReviewUtilities.get_items_due_for_review(
            portal_types=portal_types, limit=limit
        )

        # Add session metadata
        user = api.user.get_current()
        member = api.user.get(user.getId())
        settings = member.getProperty(
            "sr_settings", {"daily_review_limit": 20, "review_order": "urgency"}
        )

        # Get today's review count
        today_count = self._get_today_review_count()
        remaining = settings.get("daily_review_limit", 20) - today_count

        return {
            "items": items[:remaining] if remaining > 0 else [],
            "total_due": len(items),
            "today_completed": today_count,
            "daily_limit": settings.get("daily_review_limit", 20),
            "remaining_today": max(0, remaining),
        }

    def _get_today_review_count(self):
        """Get number of reviews completed today."""
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        count = 0
        brains = catalog(Creator=user.getId())

        today = datetime.now().date()
        for brain in brains:
            try:
                obj = brain.getObject()
                if hasattr(obj, "last_review") and obj.last_review:
                    if obj.last_review.date() == today:
                        count += 1
            except (AttributeError, TypeError):
                continue

        return count

    def get_queue_stats(self):
        """Get review queue statistics."""
        items = ReviewUtilities.get_items_due_for_review(limit=None)

        stats = {
            "total_due": len(items),
            "new_items": sum(1 for i in items if i["sr_data"]["repetitions"] == 0),
            "learning_items": sum(
                1 for i in items if 0 < i["sr_data"]["repetitions"] < 3
            ),
            "mature_items": sum(1 for i in items if i["sr_data"]["repetitions"] >= 3),
            "critical_items": sum(
                1 for i in items if i["sr_data"]["retention_score"] < 0.5
            ),
        }

        return stats


class ReviewCardView(BrowserView):
    """Individual review card interface."""

    template = ViewPageTemplateFile("templates/review_card.pt")

    def __call__(self):
        # Disable CSRF for AJAX calls
        alsoProvides(self.request, IDisableCSRFProtection)

        uid = self.request.get("uid")
        if not uid:
            return self.request.response.redirect(self.context.absolute_url())

        return self.template()

    def get_item_data(self):
        """Get item data for review."""
        uid = self.request.get("uid")
        if not uid:
            return None

        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(UID=uid)

        if not brains:
            return None

        brain = brains[0]
        obj = brain.getObject()

        # Check permissions
        if not api.user.has_permission("View", obj=obj):
            return None

        # Get content based on type
        content = self._get_content_for_review(obj)

        return {
            "uid": uid,
            "title": brain.Title,
            "description": brain.Description,
            "portal_type": brain.portal_type,
            "url": brain.getURL(),
            "content": content,
            "sr_data": {
                "ease_factor": obj.ease_factor,
                "interval": obj.interval,
                "repetitions": obj.repetitions,
                "last_review": obj.last_review.isoformat() if obj.last_review else None,
                "average_quality": obj.average_quality,
                "mastery_level": self._get_mastery_level(obj.interval),
            },
            "show_answer": self.request.get("show_answer", False),
        }

    def _get_content_for_review(self, obj):
        """Get appropriate content for review based on type."""
        if obj.portal_type == "ResearchNote":
            # For research notes, show key findings or summary
            if hasattr(obj, "key_findings") and obj.key_findings:
                return {
                    "question": "What are the key findings?",
                    "answer": obj.key_findings,
                    "full_content": obj.body.output if hasattr(obj, "body") else "",
                }
            elif hasattr(obj, "ai_summary") and obj.ai_summary:
                return {
                    "question": "What is the summary of this research?",
                    "answer": obj.ai_summary,
                    "full_content": obj.body.output if hasattr(obj, "body") else "",
                }

        elif obj.portal_type == "BookmarkPlus":
            # For bookmarks, test on key concepts
            if hasattr(obj, "key_concepts") and obj.key_concepts:
                return {
                    "question": "What are the key concepts?",
                    "answer": ", ".join(obj.key_concepts),
                    "full_content": obj.notes if hasattr(obj, "notes") else "",
                }

        # Default: use title and description
        return {
            "question": obj.Title(),
            "answer": obj.Description(),
            "full_content": getattr(obj, "text", {}).output
            if hasattr(obj, "text")
            else "",
        }

    def _get_mastery_level(self, interval):
        """Get mastery level description."""
        if interval == 0:
            return "New"
        elif interval < 7:
            return "Learning"
        elif interval < 21:
            return "Young"
        elif interval < 90:
            return "Mature"
        else:
            return "Mastered"

    def submit_review(self):
        """Handle review submission."""
        uid = self.request.form.get("uid")
        quality = int(self.request.form.get("quality", 0))
        time_spent = int(self.request.form.get("time_spent", 60))

        try:
            result = ReviewUtilities.handle_review_response(uid, quality, time_spent)

            self.request.response.setHeader("Content-Type", "application/json")
            return json.dumps({
                "success": True,
                "result": result,
                "next_item": self._get_next_item(uid),
            })

        except Exception as e:
            self.request.response.setStatus(400)
            self.request.response.setHeader("Content-Type", "application/json")
            return json.dumps({"success": False, "error": str(e)})

    def _get_next_item(self, current_uid):
        """Get next item in queue."""
        items = ReviewUtilities.get_items_due_for_review(limit=10)

        # Filter out current item
        items = [i for i in items if i["uid"] != current_uid]

        if items:
            return {"uid": items[0]["uid"], "title": items[0]["title"]}

        return None


class ReviewPerformanceView(BrowserView):
    """Performance visualization dashboard."""

    template = ViewPageTemplateFile("templates/review_performance.pt")

    def __call__(self):
        return self.template()

    def get_performance_data(self):
        """Get performance metrics and visualizations."""
        days = int(self.request.get("days", 30))

        # Get user's review history
        review_history = self._get_user_review_history()

        # Calculate metrics
        metrics = PerformanceTracker.calculate_performance_metrics(review_history, days)

        # Get forgetting curves for current items
        items = ReviewUtilities.get_items_due_for_review(limit=10)
        forgetting_curves = []

        for item in items[:5]:  # Top 5 items
            sr_data = item["sr_data"]
            curve_data = ForgettingCurve.get_forgetting_curve_data(
                interval=sr_data["interval"],
                ease_factor=sr_data["ease_factor"],
                repetitions=sr_data["repetitions"],
            )
            forgetting_curves.append({"title": item["title"], "data": curve_data})

        # Get workload forecast
        all_items = self._get_all_user_items()
        workload = ForgettingCurve.predict_workload(all_items, 30)

        return {
            "metrics": metrics,
            "forgetting_curves": forgetting_curves,
            "workload_forecast": workload,
            "period_days": days,
        }

    def _get_user_review_history(self):
        """Get user's complete review history."""
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        review_history = []
        brains = catalog(Creator=user.getId())

        for brain in brains:
            try:
                obj = brain.getObject()
                if hasattr(obj, "review_history"):
                    for review in obj.review_history:
                        review_copy = dict(review)
                        review_copy["item_id"] = brain.UID
                        review_copy["item_title"] = brain.Title
                        review_history.append(review_copy)
            except:
                continue

        return review_history

    def _get_all_user_items(self):
        """Get all user items with SR data."""
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        items = []
        brains = catalog(Creator=user.getId())

        for brain in brains:
            try:
                obj = brain.getObject()
                if hasattr(obj, "sr_enabled") and obj.sr_enabled:
                    items.append({
                        "uid": brain.UID,
                        "title": brain.Title,
                        "type": brain.portal_type,
                        "sr_data": {
                            "ease_factor": obj.ease_factor,
                            "interval": obj.interval,
                            "repetitions": obj.repetitions,
                            "last_review": obj.last_review,
                            "next_review": obj.next_review,
                        },
                    })
            except:
                continue

        return items

    def get_performance_summary(self):
        """Get performance summary for display."""
        review_history = self._get_user_review_history()

        if not review_history:
            return {
                "has_data": False,
                "message": "No review data available yet. Start reviewing to see your performance!",
            }

        # Recent performance (last 7 days)
        recent_history = [
            r
            for r in review_history
            if (datetime.now() - datetime.fromisoformat(r["date"])).days <= 7
        ]

        recent_metrics = (
            PerformanceTracker.calculate_performance_metrics(recent_history, 7)
            if recent_history
            else None
        )

        # All-time performance
        all_time_metrics = PerformanceTracker.calculate_performance_metrics(
            review_history
        )

        return {
            "has_data": True,
            "recent": recent_metrics,
            "all_time": all_time_metrics,
        }


class ReviewStatisticsView(BrowserView):
    """Detailed statistics dashboard."""

    template = ViewPageTemplateFile("templates/review_statistics.pt")

    def __call__(self):
        return self.template()

    def get_statistics(self):
        """Get comprehensive statistics."""
        # Get adaptive schedule
        schedule_data = ReviewUtilities.get_adaptive_schedule()

        # Get items at risk
        at_risk = ReviewUtilities.get_items_at_risk()

        # Get learning velocity
        review_history = self._get_user_review_history()
        metrics = PerformanceTracker.calculate_performance_metrics(review_history)

        return {
            "schedule": schedule_data,
            "at_risk_items": at_risk[:10],  # Top 10 at risk
            "learning_velocity": metrics.get("learning_velocity", {}),
            "difficulty_distribution": metrics.get("difficulty_analysis", {}),
            "time_patterns": metrics.get("time_patterns", {}),
        }

    def _get_user_review_history(self):
        """Get user's review history."""
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        review_history = []
        brains = catalog(Creator=user.getId())

        for brain in brains:
            try:
                obj = brain.getObject()
                if hasattr(obj, "review_history"):
                    for review in obj.review_history:
                        review_copy = dict(review)
                        review_copy["item_id"] = brain.UID
                        review_history.append(review_copy)
            except:
                continue

        return review_history

    def export_statistics(self):
        """Export statistics as JSON."""
        stats = self.get_statistics()

        self.request.response.setHeader("Content-Type", "application/json")
        self.request.response.setHeader(
            "Content-Disposition",
            f'attachment; filename="sr_statistics_{datetime.now().strftime("%Y%m%d")}.json"',
        )

        return json.dumps(stats, indent=2, default=str)
