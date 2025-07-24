"""Performance Tracking for Spaced Repetition System."""

        cls,
        review_history: list[dict],
        time_period: int | None = None
    ) -> dict[str, any]:
        """
        Calculate comprehensive performance metrics.

        Args:
            review_history: List of review sessions
            time_period: Days to analyze (None for all time)

        Returns:
            Dictionary of performance metrics
        """
        if not review_history:
            return cls._empty_metrics()

        # Filter by time period if specified
        if time_period:
            cutoff_date = datetime.now() - timedelta(days=time_period)
            filtered_history = [
                r
                for r in review_history
                if datetime.fromisoformat(r["date"]) >= cutoff_date
            ]
        else:
            filtered_history = review_history

        if not filtered_history:
            return cls._empty_metrics()

        # Basic metrics
        total_reviews = len(filtered_history)
        qualities = [r["quality"] for r in filtered_history]
        successful_reviews = sum(1 for q in qualities if q >= 3)

        # Time-based metrics
        time_spent = sum(r.get('time_spent', 60) for r in filtered_history)

        # Calculate streaks
        current_streak, longest_streak = cls._calculate_streaks(filtered_history)

        # Learning velocity
        learning_velocity = cls._calculate_learning_velocity(filtered_history)

        # Difficulty analysis
        difficulty_metrics = cls._analyze_difficulty_patterns(filtered_history)

        # Time of day analysis
        time_patterns = cls._analyze_time_patterns(filtered_history)

        # Progress indicators
        progress = cls._calculate_progress_indicators(filtered_history)

        metrics = {
            "summary": {
                "total_reviews": total_reviews,
                "successful_reviews": successful_reviews,
                "failed_reviews": total_reviews - successful_reviews,
                "success_rate": round(successful_reviews / total_reviews * 100, 1),
                "average_quality": round(statistics.mean(qualities), 2),
                "total_time_hours": round(time_spent / 3600, 1),
                "average_time_per_review": round(time_spent / total_reviews, 0),
            },
            "streaks": {"current": current_streak, "longest": longest_streak},
            "learning_velocity": learning_velocity,
            "difficulty_analysis": difficulty_metrics,
            "time_patterns": time_patterns,
            "progress": progress,
            "quality_distribution": cls._calculate_quality_distribution(qualities),
        }

        return metrics

    @classmethod
    def _empty_metrics(cls) -> dict[str, any]:
        """Return empty metrics structure."""
        return {
            "summary": {
                "total_reviews": 0,
                "successful_reviews": 0,
                "failed_reviews": 0,
                "success_rate": 0,
                "average_quality": 0,
                "total_time_hours": 0,
                "average_time_per_review": 0,
            },
            "streaks": {"current": 0, "longest": 0},
            "learning_velocity": {"items_per_week": 0, "mastery_rate": 0},
            "difficulty_analysis": {},
            "time_patterns": {},
            "progress": {},
            "quality_distribution": {},
        }

    @classmethod
    def _calculate_streaks(cls, history: list[dict]) -> tuple[int, int]:
        """Calculate current and longest success streaks."""
        if not history:
            return 0, 0

        # Sort by date
        sorted_history = sorted(history, key=lambda x: x['date'])

        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        for review in sorted_history:
            if review["quality"] >= 3:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        # Current streak is the temp_streak if last reviews were successful
        if sorted_history and sorted_history[-1]["quality"] >= 3:
            current_streak = temp_streak

        return current_streak, longest_streak

    @classmethod
    def _calculate_learning_velocity(cls, history: list[dict]) -> dict[str, float]:
        """Calculate how fast the user is learning new material."""
        if not history:
            return {'items_per_week': 0, 'mastery_rate': 0, 'average_interval_growth': 0}

        # Group by item
        items_data = defaultdict(list)
        for review in history:
            item_id = review.get("item_id", review.get("uid", "unknown"))
            items_data[item_id].append(review)

        # Calculate metrics
        mastered_items = 0
        total_items = len(items_data)
        interval_growths = []

        for item_id, reviews in items_data.items():
            if reviews:
                # Check if mastered
                latest_interval = reviews[-1].get("interval", 0)
                if latest_interval >= cls.MASTERY_THRESHOLD:
                    mastered_items += 1

                # Calculate interval growth
                if len(reviews) >= 2:
                    first_interval = reviews[0].get("interval", 1)
                    growth = (
                        latest_interval / first_interval if first_interval > 0 else 0
                    )
                    interval_growths.append(growth)

        # Calculate time span
        date_range = [datetime.fromisoformat(r["date"]) for r in history]
        if date_range:
            time_span_days = (max(date_range) - min(date_range)).days or 1
            weeks = time_span_days / 7
            items_per_week = total_items / weeks if weeks > 0 else 0
        else:
            items_per_week = 0

        return {
            "items_per_week": round(items_per_week, 1),
            "mastery_rate": round(mastered_items / total_items * 100, 1)
            if total_items > 0
            else 0,
            "average_interval_growth": round(statistics.mean(interval_growths), 1)
            if interval_growths
            else 0,
        }

    @classmethod
    def _analyze_difficulty_patterns(cls, history: list[dict]) -> dict[str, any]:
        """Analyze patterns in difficult items."""
        # Group by ease factor ranges
        difficulty_groups = {
            "very_hard": [],  # EF < 1.5
            "hard": [],  # EF 1.5-2.0
            "medium": [],  # EF 2.0-2.3
            "easy": [],  # EF > 2.3
        }

        struggling_items = []

        # Group reviews by item
        items_data = defaultdict(list)
        for review in history:
            item_id = review.get("item_id", review.get("uid", "unknown"))
            items_data[item_id].append(review)

        for item_id, reviews in items_data.items():
            if reviews:
                latest_ef = reviews[-1].get('ease_factor', 2.5)
                qualities = [r['quality'] for r in reviews]

                # Categorize by difficulty
                if latest_ef < 1.5:
                    difficulty_groups["very_hard"].append(item_id)
                elif latest_ef < 2.0:
                    difficulty_groups["hard"].append(item_id)
                elif latest_ef < 2.3:
                    difficulty_groups["medium"].append(item_id)
                else:
                    difficulty_groups['easy'].append(item_id)

                # Check for struggling pattern
                if len(reviews) >= 3:
                    recent_failures = sum(1 for q in qualities[-3:] if q < 3)
                    if recent_failures >= 2:
                        struggling_items.append({
                            "item_id": item_id,
                            "recent_qualities": qualities[-3:],
                            "ease_factor": latest_ef,
                        })

        return {
            "distribution": {k: len(v) for k, v in difficulty_groups.items()},
            "struggling_items": struggling_items,
            "average_ease_factor": round(
                statistics.mean([r.get("ease_factor", 2.5) for r in history]), 2
            ),
        }

    @classmethod
    def _analyze_time_patterns(cls, history: list[dict]) -> dict[str, any]:
        """Analyze performance patterns by time of day and day of week."""
        hour_performance = defaultdict(list)
        day_performance = defaultdict(list)

        for review in history:
            review_time = datetime.fromisoformat(review["date"])
            hour = review_time.hour
            day = review_time.strftime('%A')

            hour_performance[hour].append(review['quality'])
            day_performance[day].append(review['quality'])

        # Calculate averages
        best_hours = []
        for hour, qualities in hour_performance.items():
            if len(qualities) >= 3:  # Minimum sample size
                best_hours.append({
                    "hour": hour,
                    "average_quality": round(statistics.mean(qualities), 2),
                    "reviews": len(qualities),
                })

        best_hours.sort(key=lambda x: x['average_quality'], reverse=True)

        best_days = []
        for day, qualities in day_performance.items():
            if qualities:
                best_days.append({
                    "day": day,
                    "average_quality": round(statistics.mean(qualities), 2),
                    "reviews": len(qualities),
                })

        best_days.sort(key=lambda x: x['average_quality'], reverse=True)

        return {
            "best_hours": best_hours[:3],
            "worst_hours": best_hours[-3:] if len(best_hours) > 3 else [],
            "best_days": best_days[:3],
            "consistency_score": cls._calculate_consistency_score(history),
        }

    @classmethod
    def _calculate_consistency_score(cls, history: list[dict]) -> float:
        """Calculate how consistent the user is with reviews."""
        if len(history) < 7:
            return 0.0

        # Group reviews by date
        reviews_by_date = defaultdict(int)
        for review in history:
            date = datetime.fromisoformat(review["date"]).date()
            reviews_by_date[date] += 1

        # Calculate days with reviews vs total days
        if reviews_by_date:
            date_range = sorted(reviews_by_date.keys())
            total_days = (date_range[-1] - date_range[0]).days + 1
            active_days = len(reviews_by_date)

            consistency = active_days / total_days if total_days > 0 else 0
            return round(consistency * 100, 1)

        return 0.0

    @classmethod
    def _calculate_progress_indicators(cls, history: list[dict]) -> dict[str, any]:
        """Calculate progress indicators."""
        if not history:
            return {}

        # Sort by date
        sorted_history = sorted(history, key=lambda x: x['date'])

        # Calculate moving averages
        window_size = 10
        quality_trend = []

        for i in range(len(sorted_history)):
            start = max(0, i - window_size + 1)
            window = sorted_history[start : i + 1]
            avg_quality = statistics.mean([r["quality"] for r in window])
            quality_trend.append(avg_quality)

        # Determine trend
        if len(quality_trend) >= 2:
            recent_avg = statistics.mean(quality_trend[-5:])
            older_avg = statistics.mean(quality_trend[:5])
            trend = "improving" if recent_avg > older_avg else "declining"
            trend_strength = abs(recent_avg - older_avg)
        else:
            trend = "stable"
            trend_strength = 0

        # Calculate milestone progress
        milestones = cls._calculate_milestones(sorted_history)

        return {
            "trend": trend,
            "trend_strength": round(trend_strength, 2),
            "current_performance": round(quality_trend[-1], 2) if quality_trend else 0,
            "milestones": milestones,
        }

    @classmethod
    def _calculate_milestones(cls, history: list[dict]) -> list[dict]:
        """Calculate learning milestones."""
        milestones = []

        # First successful review
        for _i, review in enumerate(history):
            if review["quality"] >= 3:
                milestones.append({
                    "type": "first_success",
                    "date": review["date"],
                    "description": "First successful review",
                })
                break

        # First perfect score
        for review in history:
            if review["quality"] == 5:
                milestones.append({
                    "type": "first_perfect",
                    "date": review["date"],
                    "description": "First perfect recall",
                })
                break

        # Milestones for total reviews
        review_milestones = [10, 50, 100, 500, 1000]
        for milestone in review_milestones:
            if len(history) >= milestone:
                milestones.append({
                    "type": f"reviews_{milestone}",
                    "date": history[milestone - 1]["date"],
                    "description": f"Completed {milestone} reviews",
                })

        return sorted(milestones, key=lambda x: x['date'])

    @classmethod
    def _calculate_quality_distribution(cls, qualities: list[int]) -> dict[int, float]:
        """Calculate distribution of quality scores."""
        if not qualities:
            return dict.fromkeys(range(6), 0)

        distribution = defaultdict(int)
        for q in qualities:
            distribution[q] += 1

        total = len(qualities)
        return {
            i: round(distribution[i] / total * 100, 1)
            for i in range(6)
        }

    @classmethod
    def generate_performance_report(
        cls,
        user_data: dict,
        time_period: int = 30
    ) -> dict[str, any]:
        """
        Generate a comprehensive performance report.

        Args:
            user_data: User's complete review data
            time_period: Days to include in report

        Returns:
            Formatted performance report
        """
        # Extract review history
        review_history = []
        for item in user_data.get("items", []):
            sr_data = item.get("sr_data", {})
            for review in sr_data.get("history", []):
                review_copy = review.copy()
                review_copy["item_id"] = item.get("uid", "unknown")
                review_copy["ease_factor"] = sr_data.get("ease_factor", 2.5)
                review_copy["interval"] = sr_data.get("interval", 1)
                review_history.append(review_copy)

        # Calculate metrics
        metrics = cls.calculate_performance_metrics(review_history, time_period)

        # Generate insights
        insights = cls._generate_insights(metrics)

        # Create recommendations
        recommendations = cls._generate_recommendations(metrics)

        return {
            "period": f"Last {time_period} days",
            "generated_date": datetime.now().isoformat(),
            "metrics": metrics,
            "insights": insights,
            "recommendations": recommendations,
            "performance_grade": cls._calculate_performance_grade(metrics),
        }

    @classmethod
    def _generate_insights(cls, metrics: dict) -> list[str]:
        """Generate insights from metrics."""
        insights = []

        summary = metrics['summary']
        if summary['success_rate'] > 90:
            insights.append("Excellent performance! Your success rate is above 90%.")
        elif summary['success_rate'] < 70:
            insights.append("Your success rate is below 70%. Consider reviewing items more frequently.")

        # Streak insights
        streaks = metrics['streaks']
        if streaks['current'] >= 7:
            insights.append(f"Great job! You're on a {streaks['current']}-day success streak.")

        # Time pattern insights
        time_patterns = metrics.get("time_patterns", {})
        if time_patterns.get("best_hours"):
            best_hour = time_patterns["best_hours"][0]
            insights.append(
                f"You perform best at {best_hour['hour']:02d}:00 "
                f"(avg quality: {best_hour['average_quality']})"
            )

        # Progress insights
        progress = metrics.get("progress", {})
        if progress.get("trend") == "improving":
            insights.append("Your performance is improving over time!")
        elif progress.get('trend') == 'declining':
            insights.append("Your performance has been declining. Consider adjusting your review schedule.")

        return insights

    @classmethod
    def _generate_recommendations(cls, metrics: dict) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        summary = metrics['summary']

        # Time-based recommendations
        if summary["average_time_per_review"] > 120:
            recommendations.append(
                "Your reviews are taking over 2 minutes on average. "
                "Consider breaking down complex items into smaller pieces."
            )

        # Difficulty recommendations
        difficulty = metrics.get("difficulty_analysis", {})
        if difficulty.get("struggling_items"):
            recommendations.append(
                f"You have {len(difficulty['struggling_items'])} items you're struggling with. "
                "Consider creating additional notes or examples for these."
            )

        # Consistency recommendations
        time_patterns = metrics.get("time_patterns", {})
        consistency = time_patterns.get("consistency_score", 0)
        if consistency < 50:
            recommendations.append(
                "Your review consistency is below 50%. "
                "Try to establish a daily review routine."
            )

        # Learning velocity recommendations
        velocity = metrics.get("learning_velocity", {})
        if velocity.get("mastery_rate", 0) < 20:
            recommendations.append(
                "Less than 20% of your items have reached mastery level. "
                "Focus on quality over quantity when learning new material."
            )

        return recommendations

    @classmethod
    def _calculate_performance_grade(cls, metrics: dict) -> str:
        """Calculate overall performance grade."""
        summary = metrics['summary']

        # Weighted scoring
        success_weight = 0.4
        consistency_weight = 0.3
        mastery_weight = 0.3

        success_score = summary['success_rate'] / 100
        consistency_score = metrics.get('time_patterns', {}).get('consistency_score', 0) / 100
        mastery_score = metrics.get('learning_velocity', {}).get('mastery_rate', 0) / 100

        total_score = (
            success_score * success_weight +
            consistency_score * consistency_weight +
            mastery_score * mastery_weight
        )

        if total_score >= 0.9:
            return "A+"
        elif total_score >= 0.8:
            return "A"
        elif total_score >= 0.7:
            return "B"
        elif total_score >= 0.6:
            return "C"
        else:
            return 'D'
