"""Review Scheduling Engine for Spaced Repetition."""

from datetime import datetime

import random


class ReviewScheduler:
    """Manages review scheduling and session planning."""

    # Review order strategies
    ORDER_URGENCY = "urgency"
    ORDER_RANDOM = "random"
    ORDER_OLDEST = "oldest"
    ORDER_DIFFICULTY = "difficulty"
    ORDER_INTERLEAVED = "interleaved"

    # Session defaults
    DEFAULT_SESSION_DURATION = 20  # minutes
    DEFAULT_BREAK_INTERVAL = 10  # reviews before break
    DEFAULT_BREAK_DURATION = 5  # minutes

    @classmethod
    def get_review_queue(
        cls, items: list[dict], settings: dict, current_time: datetime | None = None
    ) -> list[dict]:
        """
        Get prioritized review queue based on settings.

        Args:
            items: List of items with review data
            settings: User settings for review preferences
            current_time: Current time (for testing)

        Returns:
            Prioritized list of items for review
        """
        if current_time is None:
            current_time = datetime.now()

        # Filter items due for review
        due_items = cls._filter_due_items(items, current_time)

        # Apply review order strategy
        order_strategy = settings.get("review_order", cls.ORDER_URGENCY)
        ordered_items = cls._apply_order_strategy(due_items, order_strategy)

        # Apply daily limit
        daily_limit = settings.get("daily_review_limit", 20)
        limited_items = ordered_items[:daily_limit]

        # Add session metadata
        for i, item in enumerate(limited_items):
            item["review_metadata"] = {
                "position": i + 1,
                "total": len(limited_items),
                "estimated_time": cls._estimate_review_time(item),
                "break_after": cls._should_break_after(i, settings),
            }

        return limited_items

    @classmethod
    def _filter_due_items(cls, items: list[dict], current_time: datetime) -> list[dict]:
        """Filter items that are due for review."""
        due_items = []

        for item in items:
            sr_data = item.get("sr_data", {})
            next_review = sr_data.get("next_review")

            if next_review:
                if isinstance(next_review, str):
                    next_review = datetime.fromisoformat(next_review)

                if next_review <= current_time:
                    # Calculate urgency score
                    days_overdue = (current_time - next_review).days
                    item["urgency_score"] = days_overdue
                    due_items.append(item)
            else:
                # New items are always due
                item["urgency_score"] = 999
                due_items.append(item)

        return due_items

    @classmethod
    def _apply_order_strategy(cls, items: list[dict], strategy: str) -> list[dict]:
        """Apply ordering strategy to review items."""
        if strategy == cls.ORDER_URGENCY:
            # Sort by urgency score (highest first)
            return sorted(items, key=lambda x: x.get("urgency_score", 0), reverse=True)

        elif strategy == cls.ORDER_RANDOM:
            # Random shuffle
            shuffled = items.copy()
            random.shuffle(shuffled)
            return shuffled

        elif strategy == cls.ORDER_OLDEST:
            # Sort by last review date (oldest first)
            def get_last_review(item):
                sr_data = item.get("sr_data", {})
                last_review = sr_data.get("last_review")
                if last_review:
                    if isinstance(last_review, str):
                        return datetime.fromisoformat(last_review)
                    return last_review
                return datetime.min

            return sorted(items, key=get_last_review)

        elif strategy == cls.ORDER_DIFFICULTY:
            # Sort by ease factor (lowest first - most difficult)
            return sorted(
                items, key=lambda x: x.get("sr_data", {}).get("ease_factor", 2.5)
            )

        elif strategy == cls.ORDER_INTERLEAVED:
            # Interleave new and mature items
            new_items = [
                i for i in items if i.get("sr_data", {}).get("repetitions", 0) < 3
            ]
            mature_items = [
                i for i in items if i.get("sr_data", {}).get("repetitions", 0) >= 3
            ]

            # Shuffle both groups
            random.shuffle(new_items)
            random.shuffle(mature_items)

            # Interleave
            result = []
            while new_items or mature_items:
                if new_items and (not mature_items or len(result) % 3 != 2):
                    result.append(new_items.pop(0))
                elif mature_items:
                    result.append(mature_items.pop(0))

            return result

        else:
            # Default to urgency
            return cls._apply_order_strategy(items, cls.ORDER_URGENCY)

    @classmethod
    def _estimate_review_time(cls, item: dict) -> int:
        """Estimate review time in seconds based on item properties."""
        base_time = 60  # Base 60 seconds per item

        sr_data = item.get("sr_data", {})

        # Adjust based on ease factor (harder items take longer)
        ease_factor = sr_data.get("ease_factor", 2.5)
        if ease_factor < 2.0:
            base_time *= 1.5
        elif ease_factor > 2.3:
            base_time *= 0.8

        # Adjust based on content type
        content_type = item.get("type", "")
        if content_type == "ResearchNote":
            base_time *= 1.2  # Research notes typically take longer
        elif content_type == "BookmarkPlus":
            base_time *= 0.9  # Bookmarks are usually quicker

        # Adjust based on previous performance
        history = sr_data.get("history", [])
        if history:
            recent_times = [h.get("time_spent", 60) for h in history[-5:]]
            if recent_times:
                avg_time = sum(recent_times) / len(recent_times)
                base_time = (base_time + avg_time) / 2

        return int(base_time)

    @classmethod
    def _should_break_after(cls, position: int, settings: dict) -> bool:
        """Determine if a break should be taken after this item."""
        break_interval = settings.get("break_interval", cls.DEFAULT_BREAK_INTERVAL)
        return (position + 1) % break_interval == 0

    @classmethod
    def create_learning_session(
        cls, items: list[dict], settings: dict, session_type: str = "mixed"
    ) -> dict:
        """
        Create a structured learning session.

        Args:
            items: Available items for review
            settings: User settings
            session_type: Type of session (mixed, new_only, review_only)

        Returns:
            Session plan with items and metadata
        """
        session_duration = settings.get(
            "session_duration", cls.DEFAULT_SESSION_DURATION
        )

        # Filter items by session type
        if session_type == "new_only":
            filtered_items = [
                i for i in items if i.get("sr_data", {}).get("repetitions", 0) == 0
            ]
        elif session_type == "review_only":
            filtered_items = [
                i for i in items if i.get("sr_data", {}).get("repetitions", 0) > 0
            ]
        else:
            filtered_items = items

        # Get review queue
        queue = cls.get_review_queue(filtered_items, settings)

        # Calculate session items based on time
        session_items = []
        total_time = 0

        for item in queue:
            item_time = item["review_metadata"]["estimated_time"]
            if total_time + item_time <= session_duration * 60:
                session_items.append(item)
                total_time += item_time
            else:
                break

        # Create session plan
        session = {
            "id": datetime.now().isoformat(),
            "type": session_type,
            "items": session_items,
            "total_items": len(session_items),
            "estimated_duration": total_time,
            "breaks": cls._plan_breaks(session_items, settings),
            "metadata": {
                "created": datetime.now().isoformat(),
                "new_items": sum(
                    1
                    for i in session_items
                    if i.get("sr_data", {}).get("repetitions", 0) == 0
                ),
                "review_items": sum(
                    1
                    for i in session_items
                    if i.get("sr_data", {}).get("repetitions", 0) > 0
                ),
                "difficulty_distribution": cls._calculate_difficulty_distribution(
                    session_items
                ),
            },
        }

        return session

    @classmethod
    def _plan_breaks(cls, items: list[dict], settings: dict) -> list[dict]:
        """Plan break points in the session."""
        breaks = []
        break_duration = settings.get("break_duration", cls.DEFAULT_BREAK_DURATION)

        for i, item in enumerate(items):
            if item["review_metadata"]["break_after"]:
                breaks.append({
                    "after_item": i + 1,
                    "duration": break_duration,
                    "suggested_activity": cls._suggest_break_activity(),
                })

        return breaks

    @classmethod
    def _suggest_break_activity(cls) -> str:
        """Suggest a break activity."""
        activities = [
            "Stand up and stretch",
            "Take a short walk",
            "Do some eye exercises",
            "Get a glass of water",
            "Practice deep breathing",
            "Look at something 20 feet away for 20 seconds",
        ]
        return activities[0]  # Use deterministic selection for reproducibility

    @classmethod
    def _calculate_difficulty_distribution(cls, items: list[dict]) -> dict[str, int]:
        """Calculate distribution of item difficulties."""
        distribution = {"easy": 0, "medium": 0, "hard": 0}

        for item in items:
            ease_factor = item.get("sr_data", {}).get("ease_factor", 2.5)
            if ease_factor >= 2.3:
                distribution["easy"] += 1
            elif ease_factor >= 2.0:
                distribution["medium"] += 1
            else:
                distribution["hard"] += 1

        return distribution

    @classmethod
    def optimize_review_time(
        cls, user_preferences: dict, historical_performance: list[dict]
    ) -> dict[str, any]:
        """
        Optimize review times based on user performance patterns.

        Args:
            user_preferences: User's time preferences
            historical_performance: Historical review performance data

        Returns:
            Optimized review schedule recommendations
        """
        # Analyze performance by time of day
        performance_by_hour = {}

        for review in historical_performance:
            if "date" in review and "quality" in review:
                review_time = datetime.fromisoformat(review["date"])
                hour = review_time.hour

                if hour not in performance_by_hour:
                    performance_by_hour[hour] = {
                        "total": 0,
                        "sum_quality": 0,
                        "reviews": [],
                    }

                performance_by_hour[hour]["total"] += 1
                performance_by_hour[hour]["sum_quality"] += review["quality"]
                performance_by_hour[hour]["reviews"].append(review["quality"])

        # Calculate average quality by hour
        best_hours = []
        for hour, data in performance_by_hour.items():
            if data["total"] >= 5:  # Minimum sample size
                avg_quality = data["sum_quality"] / data["total"]
                best_hours.append({
                    "hour": hour,
                    "average_quality": avg_quality,
                    "sample_size": data["total"],
                })

        # Sort by average quality
        best_hours.sort(key=lambda x: x["average_quality"], reverse=True)

        # Generate recommendations
        recommendations = {
            "best_review_times": [],
            "avoid_times": [],
            "optimal_session_length": cls._calculate_optimal_session_length(
                historical_performance
            ),
            "suggested_schedule": [],
        }

        # Best times (top 3)
        for hour_data in best_hours[:3]:
            hour = hour_data["hour"]
            recommendations["best_review_times"].append({
                "time": f"{hour:02d}:00",
                "performance_score": round(hour_data["average_quality"], 2),
            })

        # Times to avoid (bottom 3)
        for hour_data in best_hours[-3:]:
            if hour_data["average_quality"] < 3.0:
                hour = hour_data["hour"]
                recommendations["avoid_times"].append({
                    "time": f"{hour:02d}:00",
                    "performance_score": round(hour_data["average_quality"], 2),
                })

        # Create suggested weekly schedule
        recommendations["suggested_schedule"] = cls._create_weekly_schedule(
            best_hours[:3] if best_hours else [], user_preferences
        )

        return recommendations

    @classmethod
    def _calculate_optimal_session_length(
        cls, historical_performance: list[dict]
    ) -> int:
        """Calculate optimal session length based on performance degradation."""
        # Group reviews by session (assuming sessions are within 2 hours)
        sessions = []
        current_session = []
        last_time = None

        for review in sorted(historical_performance, key=lambda x: x.get("date", "")):
            if "date" not in review:
                continue

            review_time = datetime.fromisoformat(review["date"])

            if (
                last_time and (review_time - last_time).total_seconds() > 7200
            ):  # 2 hours
                if current_session:
                    sessions.append(current_session)
                current_session = []

            current_session.append(review)
            last_time = review_time

        if current_session:
            sessions.append(current_session)

        # Analyze performance degradation in sessions
        optimal_lengths = []

        for session in sessions:
            if len(session) >= 5:
                # Find point where quality drops below 3.5
                for i, review in enumerate(session):
                    if review.get("quality", 5) < 3.5:
                        optimal_lengths.append(i * 2)  # Assume 2 minutes per review
                        break
                else:
                    optimal_lengths.append(len(session) * 2)

        if optimal_lengths:
            return min(60, max(10, sum(optimal_lengths) // len(optimal_lengths)))
        else:
            return cls.DEFAULT_SESSION_DURATION

    @classmethod
    def _create_weekly_schedule(
        cls, best_hours: list[dict], user_preferences: dict
    ) -> list[dict]:
        """Create a weekly review schedule."""
        schedule = []
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        # Get user's available days
        available_days = user_preferences.get("available_days", days)

        for day in days:
            if day in available_days and best_hours:
                # Rotate through best hours
                hour_data = best_hours[days.index(day) % len(best_hours)]
                schedule.append({
                    "day": day,
                    "time": f"{hour_data['hour']:02d}:00",
                    "duration": user_preferences.get(
                        "session_duration", cls.DEFAULT_SESSION_DURATION
                    ),
                })

        return schedule

    @classmethod
    def get_adaptive_intervals(
        cls, item: dict, user_performance: dict
    ) -> dict[str, int]:
        """
        Calculate adaptive intervals based on user's overall performance.

        Args:
            item: Item with review data
            user_performance: User's overall performance metrics

        Returns:
            Adjusted interval recommendations
        """
        sr_data = item.get("sr_data", {})
        base_interval = sr_data.get("interval", 1)

        # Get user's average success rate
        success_rate = user_performance.get("success_rate", 0.8)

        # Adjust interval based on success rate
        if success_rate < 0.7:
            # Struggling user - shorter intervals
            adjustment_factor = 0.8
        elif success_rate > 0.9:
            # High performing user - longer intervals
            adjustment_factor = 1.2
        else:
            adjustment_factor = 1.0

        # Consider item-specific performance
        item_history = sr_data.get("history", [])
        if len(item_history) >= 3:
            recent_qualities = [h.get("quality", 3) for h in item_history[-3:]]
            avg_recent_quality = sum(recent_qualities) / len(recent_qualities)

            if avg_recent_quality < 3.5:
                adjustment_factor *= 0.9
            elif avg_recent_quality > 4.5:
                adjustment_factor *= 1.1

        # Calculate adjusted intervals
        return {
            "minimum": max(1, int(base_interval * adjustment_factor * 0.8)),
            "recommended": max(1, int(base_interval * adjustment_factor)),
            "maximum": max(1, int(base_interval * adjustment_factor * 1.2)),
            "adjustment_reason": cls._get_adjustment_reason(
                success_rate, adjustment_factor
            ),
        }

    @classmethod
    def _get_adjustment_reason(cls, success_rate: float, factor: float) -> str:
        """Get human-readable reason for interval adjustment."""
        if factor < 0.9:
            return f"Shortened due to lower success rate ({success_rate * 100:.0f}%)"
        elif factor > 1.1:
            return f"Extended due to high success rate ({success_rate * 100:.0f}%)"
        else:
            return "Standard interval based on current performance"
