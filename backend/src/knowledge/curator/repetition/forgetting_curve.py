"""Forgetting Curve calculations and visualizations.

Based on Ebbinghaus's forgetting curve and modified for spaced repetition.
"""

from datetime import datetime
from datetime import timedelta

import math

# Default retention threshold (90%)
DEFAULT_RETENTION_THRESHOLD = 0.9


class ForgettingCurve:
    """Forgetting curve calculations and analysis."""

    @classmethod
    def calculate_retention(
        cls,
        days_elapsed: int,
        interval: int = 1,
        ease_factor: float = 2.5,
        repetitions: int = 0,
    ) -> float:
        """Calculate retention based on forgetting curve."""
        if days_elapsed <= 0:
            return 1.0

        # Calculate stability factor based on spaced repetition algorithm
        stability = cls._calculate_stability(interval, ease_factor, repetitions)

        # Exponential decay: R(t) = e^(-t/S)
        retention = math.exp(-days_elapsed / stability)

        return max(0.0, min(1.0, retention))

    @classmethod
    def _calculate_stability(
        cls, interval: int, ease_factor: float, repetitions: int
    ) -> float:
        """Calculate memory stability based on spaced repetition factors."""
        # Base stability increases with repetitions and ease factor
        base_stability = max(1.0, interval * ease_factor)

        # Additional stability from repetitions
        repetition_factor = 1 + (repetitions * 0.1)

        return base_stability * repetition_factor

    @classmethod
    def generate_curve_data(
        cls,
        interval: int = 1,
        ease_factor: float = 2.5,
        repetitions: int = 0,
        days_ahead: int | None = None,
    ) -> list[dict[str, float]]:
        """
        Generate forgetting curve data points for visualization.

        Args:
            interval: Current interval
            ease_factor: Ease factor
            repetitions: Number of repetitions
            days_ahead: Number of days to project (default: 2x interval)

        Returns:
            List of data points with day and retention values
        """
        if days_ahead is None:
            days_ahead = max(interval * 2, 30)

        data_points = []

        for day in range(days_ahead + 1):
            retention = cls.calculate_retention(day, interval, ease_factor, repetitions)
            data_points.append({
                "day": day,
                "retention": round(retention, 3),
                "percentage": round(retention * 100, 1),
            })

        return data_points

    @classmethod
    def find_optimal_review_day(
        cls,
        interval: int,
        ease_factor: float = 2.5,
        repetitions: int = 0,
        target_retention: float = 0.9,
    ) -> int:
        """
        Find the optimal day for review to maintain target retention.

        Args:
            interval: Current interval
            ease_factor: Ease factor
            repetitions: Number of repetitions
            target_retention: Desired retention level (0-1)

        Returns:
            Optimal day for review
        """
        stability = cls._calculate_stability(interval, ease_factor, repetitions)

        # Solve for t: R = e^(-t/S) => t = -S * ln(R)
        if target_retention <= 0 or target_retention >= 1:
            target_retention = 0.9

        optimal_day = -stability * math.log(target_retention)

        return max(1, round(optimal_day))

    @classmethod
    def get_retention_alerts(
        cls, items: list[dict], threshold: float = DEFAULT_RETENTION_THRESHOLD
    ) -> list[dict]:
        """
        Get alerts for items at risk of being forgotten.

        Args:
            items: List of items with review data
            threshold: Retention threshold for alerts

        Returns:
            List of items below retention threshold
        """
        alerts = []
        now = datetime.now()

        for item in items:
            sr_data = item.get("sr_data", {})

            if sr_data.get("last_review"):
                last_review = sr_data["last_review"]
                if isinstance(last_review, str):
                    last_review = datetime.fromisoformat(last_review)

                days_elapsed = (now - last_review).days

                retention = cls.calculate_retention(
                    days_elapsed,
                    sr_data.get("interval", 1),
                    sr_data.get("ease_factor", 2.5),
                    sr_data.get("repetitions", 0),
                )

                if retention < threshold:
                    alerts.append({
                        "item": item,
                        "retention": retention,
                        "days_overdue": days_elapsed - sr_data.get("interval", 1),
                        "risk_level": cls._calculate_risk_level(retention),
                    })

        # Sort by retention (lowest first)
        alerts.sort(key=lambda x: x["retention"])

        return alerts

    @classmethod
    def _calculate_risk_level(cls, retention: float) -> str:
        """Calculate risk level based on retention."""
        if retention >= 0.8:
            return "low"
        elif retention >= 0.5:
            return "medium"
        elif retention >= 0.2:
            return "high"
        else:
            return "critical"

    @classmethod
    def analyze_learning_efficiency(cls, review_history: list[dict]) -> dict[str, any]:
        """
        Analyze learning efficiency based on review history.

        Args:
            review_history: List of review sessions with quality and intervals

        Returns:
            Analysis results including efficiency metrics
        """
        if not review_history:
            return {
                "efficiency_score": 0,
                "average_retention": 0,
                "optimal_interval_adherence": 0,
                "recommendations": ["No review history available"],
            }

        total_reviews = len(review_history)
        successful_reviews = sum(1 for r in review_history if r.get("quality", 0) >= 3)

        # Calculate average retention at review time
        retention_values = []
        for i, review in enumerate(review_history):
            if i > 0:
                prev_review = review_history[i - 1]
                days_between = (
                    datetime.fromisoformat(review["date"])
                    - datetime.fromisoformat(prev_review["date"])
                ).days

                retention = cls.calculate_retention(
                    days_between,
                    prev_review.get("interval", 1),
                    prev_review.get("ease_factor", 2.5),
                    prev_review.get("repetitions", 0),
                )
                retention_values.append(retention)

        avg_retention = (
            sum(retention_values) / len(retention_values) if retention_values else 0
        )

        # Calculate efficiency score
        success_rate = successful_reviews / total_reviews if total_reviews > 0 else 0
        efficiency_score = (success_rate * 0.6 + avg_retention * 0.4) * 100

        # Generate recommendations
        recommendations = []

        if avg_retention < 0.8:
            recommendations.append(
                "Review items more frequently to maintain better retention"
            )
        elif avg_retention > 0.95:
            recommendations.append(
                "You might be reviewing too frequently - consider longer intervals"
            )

        if success_rate < 0.8:
            recommendations.append(
                "Focus on understanding before moving to longer intervals"
            )

        # Check interval progression
        intervals = [r.get("interval", 1) for r in review_history]
        if len(intervals) > 3 and all(i <= 7 for i in intervals[-3:]):
            recommendations.append(
                "Your intervals aren't increasing - ensure quality responses"
            )

        return {
            "efficiency_score": round(efficiency_score, 1),
            "average_retention": round(avg_retention, 3),
            "success_rate": round(success_rate, 3),
            "total_reviews": total_reviews,
            "successful_reviews": successful_reviews,
            "recommendations": recommendations,
        }

    @classmethod
    def predict_workload(
        cls, items: list[dict], days_ahead: int = 30
    ) -> list[dict[str, any]]:
        """
        Predict review workload for upcoming days.

        Args:
            items: List of items with review data
            days_ahead: Number of days to predict

        Returns:
            Daily workload predictions
        """
        workload = {}
        today = datetime.now().date()

        for item in items:
            sr_data = item.get("sr_data", {})

            if sr_data.get("next_review"):
                next_review = sr_data["next_review"]
                if isinstance(next_review, str):
                    next_review = datetime.fromisoformat(next_review).date()
                elif isinstance(next_review, datetime):
                    next_review = next_review.date()

                # Only include if within prediction range
                days_until = (next_review - today).days
                if 0 <= days_until <= days_ahead:
                    date_str = next_review.isoformat()
                    if date_str not in workload:
                        workload[date_str] = {"date": date_str, "count": 0, "items": []}

                    workload[date_str]["count"] += 1
                    workload[date_str]["items"].append({
                        "title": item.get("title", "Unknown"),
                        "type": item.get("type", "Unknown"),
                        "interval": sr_data.get("interval", 1),
                    })

        # Fill in missing days
        for day in range(days_ahead + 1):
            date = today + timedelta(days=day)
            date_str = date.isoformat()
            if date_str not in workload:
                workload[date_str] = {"date": date_str, "count": 0, "items": []}

        # Convert to sorted list
        workload_list = sorted(workload.values(), key=lambda x: x["date"])

        # Add cumulative and average metrics
        total_items = sum(day["count"] for day in workload_list)
        avg_per_day = total_items / len(workload_list) if workload_list else 0

        for i, day in enumerate(workload_list):
            day["cumulative"] = sum(d["count"] for d in workload_list[: i + 1])
            day["is_above_average"] = day["count"] > avg_per_day

        return workload_list

    @classmethod
    def generate_retention_heatmap(
        cls, items: list[dict], days: int = 30
    ) -> dict[str, list[float]]:
        """
        Generate retention heatmap data for visualization.

        Args:
            items: List of items with review data
            days: Number of days for heatmap

        Returns:
            Heatmap data organized by item and day
        """
        heatmap_data = {}

        for item in items:
            sr_data = item.get("sr_data", {})
            item_id = item.get("uid", item.get("title", "Unknown"))

            retention_values = []
            for day in range(days):
                retention = cls.calculate_retention(
                    day,
                    sr_data.get("interval", 1),
                    sr_data.get("ease_factor", 2.5),
                    sr_data.get("repetitions", 0),
                )
                retention_values.append(round(retention, 2))

            heatmap_data[item_id] = retention_values

        return heatmap_data
