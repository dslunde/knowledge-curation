"""SM-2 Algorithm Implementation.

The SuperMemo 2 (SM-2) algorithm is a spaced repetition algorithm that determines
optimal intervals between repetitions based on the quality of recall.
"""

from datetime import datetime, timedelta
import math


class SM2Algorithm:
    """Implementation of the SuperMemo 2 algorithm for spaced repetition."""

    # Default parameters
    DEFAULT_EASE_FACTOR = 2.5
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 2.5

    # Quality responses (0-5 scale)
    QUALITY_BLACKOUT = 0  # Complete blackout
    QUALITY_INCORRECT = 1  # Incorrect response, but remembered upon seeing answer
    QUALITY_ERROR = 2  # Incorrect response, but close
    QUALITY_DIFFICULT = 3  # Correct response, but with difficulty
    QUALITY_GOOD = 4  # Correct response with some hesitation
    QUALITY_PERFECT = 5  # Perfect response

    # Initial intervals (in days)
    INITIAL_INTERVALS = [1, 6]

    @classmethod
    def calculate_next_review(
        cls,
        quality: int,
        repetitions: int = 0,
        ease_factor: float = DEFAULT_EASE_FACTOR,
        interval: int = 1,
        **kwargs
    ) -> dict[str, any]:
        """
        Calculate the next review parameters based on the SM-2 algorithm.
        
        Args:
            quality: Quality of recall (0-5)
            repetitions: Number of successful repetitions
            ease_factor: Current ease factor
            interval: Current interval in days
            **kwargs: Additional parameters for extensions
            
        Returns:
            Dictionary with updated parameters:
                - interval: Next interval in days
                - repetitions: Updated repetition count
                - ease_factor: Updated ease factor
                - next_review_date: Next review date
        """
        if quality < 0 or quality > 5:
            raise ValueError(f"Quality must be between 0 and 5, got {quality}")

        # Calculate new ease factor
        new_ease_factor = cls._calculate_ease_factor(ease_factor, quality)

        # Calculate interval and repetitions
        if quality >= 3:  # Successful recall
            new_repetitions = repetitions + 1
            new_interval = cls._calculate_interval(
                quality, new_repetitions, new_ease_factor, interval
            )
        else:  # Failed recall
            new_repetitions = 0
            new_interval = 1

        # Calculate next review date
        now = datetime.now()
        next_review_date = now + timedelta(days=new_interval)

        return {
            'interval': new_interval,
            'repetitions': new_repetitions,
            'ease_factor': round(new_ease_factor, 4),
            'next_review_date': next_review_date,
            'quality': quality
        }

    @classmethod
    def _calculate_ease_factor(cls, current_ease: float, quality: int) -> float:
        """
        Calculate new ease factor based on quality of response.
        
        Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        """
        if quality < 3:
            # Don't modify ease factor for failed recalls
            return current_ease

        # Calculate ease factor modification
        q = quality
        delta = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        new_ease = current_ease + delta

        # Clamp to min/max values
        return max(cls.MIN_EASE_FACTOR, min(cls.MAX_EASE_FACTOR, new_ease))

    @classmethod
    def _calculate_interval(
        cls,
        quality: int,
        repetitions: int,
        ease_factor: float,
        previous_interval: int
    ) -> int:
        """
        Calculate the next interval based on repetitions and ease factor.
        """
        if repetitions == 1:
            return cls.INITIAL_INTERVALS[0]
        elif repetitions == 2:
            return cls.INITIAL_INTERVALS[1]
        else:
            # I(n) = I(n-1) * EF
            new_interval = round(previous_interval * ease_factor)

            # Apply quality-based adjustment for edge cases
            if quality == 3:
                # Difficult recall - reduce interval slightly
                new_interval = round(new_interval * 0.9)
            elif quality == 5:
                # Perfect recall - can increase interval slightly
                new_interval = round(new_interval * 1.05)

            # Ensure minimum interval
            return max(1, new_interval)

    @classmethod
    def get_initial_parameters(cls) -> dict[str, any]:
        """Get initial parameters for a new item."""
        return {
            'ease_factor': cls.DEFAULT_EASE_FACTOR,
            'interval': 0,
            'repetitions': 0,
            'next_review_date': datetime.now()
        }

    @classmethod
    def estimate_success_probability(
        cls,
        days_since_review: int,
        interval: int,
        ease_factor: float
    ) -> float:
        """
        Estimate the probability of successful recall.
        
        Uses a modified forgetting curve based on the interval and ease factor.
        """
        if days_since_review <= 0:
            return 1.0

        # Stability factor based on ease factor
        stability = interval * (ease_factor / cls.DEFAULT_EASE_FACTOR)

        # Modified Ebbinghaus forgetting curve
        # P = e^(-t/S) where t is time and S is stability
        probability = math.exp(-days_since_review / stability)

        return max(0.0, min(1.0, probability))

    @classmethod
    def calculate_optimal_review_time(
        cls,
        interval: int,
        ease_factor: float,
        target_probability: float = 0.9
    ) -> int:
        """
        Calculate the optimal review time to maintain a target success probability.
        
        Args:
            interval: Current interval
            ease_factor: Current ease factor
            target_probability: Target success probability (default 0.9)
            
        Returns:
            Days until optimal review
        """
        if target_probability <= 0 or target_probability >= 1:
            raise ValueError("Target probability must be between 0 and 1")

        # Stability factor
        stability = interval * (ease_factor / cls.DEFAULT_EASE_FACTOR)

        # Solve for t: P = e^(-t/S) => t = -S * ln(P)
        optimal_days = -stability * math.log(target_probability)

        return max(1, round(optimal_days))

    @classmethod
    def adjust_for_time_constraint(
        cls,
        items: list,
        available_time: int,
        average_time_per_item: int = 60
    ) -> list:
        """
        Adjust review schedule based on time constraints.
        
        Args:
            items: List of items with review data
            available_time: Available time in seconds
            average_time_per_item: Average time per item in seconds
            
        Returns:
            Prioritized list of items within time constraint
        """
        # Calculate how many items can be reviewed
        max_items = available_time // average_time_per_item

        # Sort by urgency (lowest retention probability first)
        sorted_items = sorted(
            items,
            key=lambda x: x.get('retention_probability', 0)
        )

        return sorted_items[:max_items]

    @classmethod
    def get_quality_description(cls, quality: int) -> str:
        """Get human-readable description of quality rating."""
        descriptions = {
            0: "Complete blackout - no memory of the answer",
            1: "Incorrect, but remembered when seeing the answer",
            2: "Incorrect, but the answer was close",
            3: "Correct, but with significant difficulty",
            4: "Correct with some hesitation",
            5: "Perfect response - instant and confident"
        }
        return descriptions.get(quality, "Unknown quality")

    @classmethod
    def simulate_learning_curve(
        cls,
        days: int = 365,
        initial_quality: int = 3,
        quality_improvement_rate: float = 0.1
    ) -> list:
        """
        Simulate learning curve over time.
        
        Args:
            days: Number of days to simulate
            initial_quality: Starting quality level
            quality_improvement_rate: Rate of quality improvement
            
        Returns:
            List of review sessions with dates and parameters
        """
        sessions = []
        current_date = datetime.now()
        params = cls.get_initial_parameters()
        current_quality = initial_quality

        while (current_date - datetime.now()).days < days:
            # Simulate quality improvement over time
            if params['repetitions'] > 0:
                current_quality = min(5, current_quality + quality_improvement_rate)

            # Calculate next review
            quality = round(current_quality + (0.5 - math.random.random()))
            quality = max(0, min(5, quality))

            result = cls.calculate_next_review(
                quality=quality,
                repetitions=params['repetitions'],
                ease_factor=params['ease_factor'],
                interval=params['interval']
            )

            sessions.append({
                'date': current_date.isoformat(),
                'quality': quality,
                'interval': result['interval'],
                'ease_factor': result['ease_factor'],
                'repetitions': result['repetitions']
            })

            # Update for next iteration
            params = result
            current_date = result['next_review_date']

            # Stop if interval exceeds remaining days
            if result['interval'] > (days - (current_date - datetime.now()).days):
                break

        return sessions
