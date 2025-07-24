"""Tests for Spaced Repetition System."""

from datetime import datetime
from datetime import timedelta
from knowledge.curator.repetition import ForgettingCurve
from knowledge.curator.repetition import PerformanceTracker
from knowledge.curator.repetition import ReviewScheduler
from knowledge.curator.repetition import SM2Algorithm
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestSM2Algorithm(unittest.TestCase):
    """Test SM-2 Algorithm implementation."""

    def test_calculate_next_review_perfect_response(self):
        """Test calculation for perfect response."""
        result = SM2Algorithm.calculate_next_review(
            quality=5, repetitions=0, ease_factor=2.5, interval=1
        )

        self.assertEqual(result["quality"], 5)
        self.assertEqual(result["repetitions"], 1)
        self.assertEqual(result["interval"], 1)  # First interval
        self.assertGreater(result["ease_factor"], 2.5)  # Should increase
        self.assertIsInstance(result["next_review_date"], datetime)

    def test_calculate_next_review_failed_response(self):
        """Test calculation for failed response."""
        result = SM2Algorithm.calculate_next_review(
            quality=2, repetitions=5, ease_factor=2.3, interval=10
        )

        self.assertEqual(result["quality"], 2)
        self.assertEqual(result["repetitions"], 0)  # Reset to 0
        self.assertEqual(result["interval"], 1)  # Reset to 1
        self.assertEqual(result["ease_factor"], 2.3)  # Unchanged for failures

    def test_calculate_next_review_progression(self):
        """Test interval progression."""
        # First review
        result1 = SM2Algorithm.calculate_next_review(quality=4, repetitions=0)
        self.assertEqual(result1["interval"], 1)

        # Second review
        result2 = SM2Algorithm.calculate_next_review(
            quality=4,
            repetitions=result1["repetitions"],
            ease_factor=result1["ease_factor"],
            interval=result1["interval"],
        )
        self.assertEqual(result2["interval"], 6)  # Second interval

        # Third review
        result3 = SM2Algorithm.calculate_next_review(
            quality=4,
            repetitions=result2["repetitions"],
            ease_factor=result2["ease_factor"],
            interval=result2["interval"],
        )
        self.assertGreater(result3["interval"], 6)  # Should be ~15 days

    def test_ease_factor_bounds(self):
        """Test ease factor stays within bounds."""
        # Very poor performance
        result_poor = SM2Algorithm.calculate_next_review(quality=3, ease_factor=1.5)
        self.assertGreaterEqual(result_poor["ease_factor"], 1.3)

        # Perfect performance
        result_perfect = SM2Algorithm.calculate_next_review(quality=5, ease_factor=2.4)
        self.assertLessEqual(result_perfect["ease_factor"], 2.5)

    def test_quality_validation(self):
        """Test quality parameter validation."""
        with self.assertRaises(ValueError):
            SM2Algorithm.calculate_next_review(quality=-1)

        with self.assertRaises(ValueError):
            SM2Algorithm.calculate_next_review(quality=6)

    def test_estimate_success_probability(self):
        """Test success probability estimation."""
        # Just reviewed
        prob = SM2Algorithm.estimate_success_probability(0, 10, 2.5)
        self.assertEqual(prob, 1.0)

        # At interval
        prob = SM2Algorithm.estimate_success_probability(10, 10, 2.5)
        self.assertLess(prob, 1.0)
        self.assertGreater(prob, 0.3)

        # Way overdue
        prob = SM2Algorithm.estimate_success_probability(30, 10, 2.5)
        self.assertLess(prob, 0.3)


class TestForgettingCurve(unittest.TestCase):
    """Test Forgetting Curve calculations."""

    def test_calculate_retention(self):
        """Test retention calculation."""
        # Just reviewed
        retention = ForgettingCurve.calculate_retention(0, 10, 2.5, 3)
        self.assertEqual(retention, 1.0)

        # Half interval
        retention = ForgettingCurve.calculate_retention(5, 10, 2.5, 3)
        self.assertGreater(retention, 0.5)
        self.assertLess(retention, 1.0)

        # At interval
        retention = ForgettingCurve.calculate_retention(10, 10, 2.5, 3)
        self.assertGreater(retention, 0.3)
        self.assertLess(retention, 0.7)

    def test_get_forgetting_curve_data(self):
        """Test forgetting curve data generation."""
        data = ForgettingCurve.get_forgetting_curve_data(10, 2.5, 3, 20)

        self.assertEqual(len(data), 21)  # 0-20 days
        self.assertEqual(data[0]["day"], 0)
        self.assertEqual(data[0]["retention"], 1.0)
        self.assertEqual(data[0]["percentage"], 100.0)

        # Check decreasing retention
        for i in range(1, len(data)):
            self.assertLess(data[i]["retention"], data[i - 1]["retention"])

    def test_find_optimal_review_day(self):
        """Test optimal review day calculation."""
        # 90% retention target
        optimal = ForgettingCurve.find_optimal_review_day(10, 2.5, 3, 0.9)
        self.assertGreater(optimal, 0)
        self.assertLess(optimal, 10)

        # 50% retention target
        optimal_low = ForgettingCurve.find_optimal_review_day(10, 2.5, 3, 0.5)
        self.assertGreater(optimal_low, optimal)

    def test_get_retention_alerts(self):
        """Test retention alerts."""
        items = [
            {
                "uid": "1",
                "sr_data": {
                    "last_review": (datetime.now() - timedelta(days=15)),
                    "interval": 10,
                    "ease_factor": 2.5,
                    "repetitions": 3,
                },
            },
            {
                "uid": "2",
                "sr_data": {
                    "last_review": (datetime.now() - timedelta(days=2)),
                    "interval": 10,
                    "ease_factor": 2.5,
                    "repetitions": 3,
                },
            },
        ]

        alerts = ForgettingCurve.get_retention_alerts(items, 0.8)

        self.assertEqual(len(alerts), 1)  # Only first item
        self.assertEqual(alerts[0]["item"]["uid"], "1")
        self.assertIn(alerts[0]["risk_level"], ["high", "critical"])

    def test_analyze_learning_efficiency(self):
        """Test learning efficiency analysis."""
        history = [
            {
                "date": (datetime.now() - timedelta(days=10)).isoformat(),
                "quality": 4,
                "interval": 1,
            },
            {
                "date": (datetime.now() - timedelta(days=9)).isoformat(),
                "quality": 3,
                "interval": 6,
            },
            {
                "date": (datetime.now() - timedelta(days=3)).isoformat(),
                "quality": 5,
                "interval": 15,
            },
        ]

        analysis = ForgettingCurve.analyze_learning_efficiency(history)

        self.assertIn("efficiency_score", analysis)
        self.assertIn("average_retention", analysis)
        self.assertIn("success_rate", analysis)
        self.assertIn("recommendations", analysis)
        self.assertGreater(analysis["efficiency_score"], 0)


class TestReviewScheduler(unittest.TestCase):
    """Test Review Scheduler."""

    def test_get_review_queue(self):
        """Test review queue generation."""
        items = [
            {
                "uid": "1",
                "sr_data": {"next_review": datetime.now() - timedelta(days=2)},
            },
            {
                "uid": "2",
                "sr_data": {"next_review": datetime.now() + timedelta(days=2)},
            },
            {
                "uid": "3",
                "sr_data": {"next_review": datetime.now() - timedelta(days=1)},
            },
        ]

        settings = {"daily_review_limit": 10, "review_order": "urgency"}
        queue = ReviewScheduler.get_review_queue(items, settings)

        self.assertEqual(len(queue), 2)  # Only due items
        self.assertEqual(queue[0]["uid"], "1")  # Most overdue first
        self.assertEqual(queue[1]["uid"], "3")

    def test_review_order_strategies(self):
        """Test different ordering strategies."""
        items = [
            {
                "uid": "1",
                "sr_data": {
                    "next_review": datetime.now() - timedelta(days=1),
                    "ease_factor": 2.0,
                    "repetitions": 1,
                    "last_review": datetime.now() - timedelta(days=10),
                },
            },
            {
                "uid": "2",
                "sr_data": {
                    "next_review": datetime.now() - timedelta(days=2),
                    "ease_factor": 2.5,
                    "repetitions": 5,
                    "last_review": datetime.now() - timedelta(days=5),
                },
            },
        ]

        # Test urgency order
        settings = {"daily_review_limit": 10, "review_order": "urgency"}
        queue = ReviewScheduler.get_review_queue(items, settings)
        self.assertEqual(queue[0]["uid"], "2")  # More overdue

        # Test difficulty order
        settings["review_order"] = "difficulty"
        queue = ReviewScheduler.get_review_queue(items, settings)
        self.assertEqual(queue[0]["uid"], "1")  # Lower ease factor

    def test_create_learning_session(self):
        """Test learning session creation."""
        items = [{"uid": str(i), "sr_data": {"repetitions": i % 3}} for i in range(10)]

        settings = {
            "session_duration": 20,
            "daily_review_limit": 20,
            "review_order": "urgency",
            "break_interval": 5,
        }

        session = ReviewScheduler.create_learning_session(items, settings, "mixed")

        self.assertIn("id", session)
        self.assertIn("items", session)
        self.assertIn("breaks", session)
        self.assertIn("metadata", session)
        self.assertEqual(session["type"], "mixed")

    def test_optimize_review_time(self):
        """Test review time optimization."""
        preferences = {"available_days": ["Monday", "Tuesday", "Wednesday"]}
        history = [
            {
                "date": (
                    datetime.now().replace(hour=9) - timedelta(days=i)
                ).isoformat(),
                "quality": 4 if i % 2 == 0 else 3,
            }
            for i in range(20)
        ]

        result = ReviewScheduler.optimize_review_time(preferences, history)

        self.assertIn("best_review_times", result)
        self.assertIn("optimal_session_length", result)
        self.assertIn("suggested_schedule", result)


class TestPerformanceTracker(unittest.TestCase):
    """Test Performance Tracker."""

    def test_calculate_performance_metrics(self):
        """Test performance metrics calculation."""
        history = [
            {
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "quality": 4 if i % 3 != 0 else 2,
                "time_spent": 60 + i * 5,
                "ease_factor": 2.3,
                "interval": i + 1,
            }
            for i in range(10)
        ]

        metrics = PerformanceTracker.calculate_performance_metrics(history)

        self.assertIn("summary", metrics)
        self.assertIn("streaks", metrics)
        self.assertIn("learning_velocity", metrics)
        self.assertIn("difficulty_analysis", metrics)
        self.assertIn("time_patterns", metrics)
        self.assertIn("progress", metrics)

        # Check summary calculations
        self.assertEqual(metrics["summary"]["total_reviews"], 10)
        self.assertGreater(metrics["summary"]["success_rate"], 0)
        self.assertGreater(metrics["summary"]["average_quality"], 0)

    def test_calculate_streaks(self):
        """Test streak calculation."""
        history = [
            {"date": (datetime.now() - timedelta(days=5)).isoformat(), "quality": 4},
            {"date": (datetime.now() - timedelta(days=4)).isoformat(), "quality": 5},
            {
                "date": (datetime.now() - timedelta(days=3)).isoformat(),
                "quality": 2,
            },  # Fail
            {"date": (datetime.now() - timedelta(days=2)).isoformat(), "quality": 3},
            {"date": (datetime.now() - timedelta(days=1)).isoformat(), "quality": 4},
        ]

        metrics = PerformanceTracker.calculate_performance_metrics(history)

        self.assertEqual(metrics["streaks"]["current"], 2)
        self.assertEqual(metrics["streaks"]["longest"], 2)

    def test_generate_performance_report(self):
        """Test performance report generation."""
        user_data = {
            "items": [
                {
                    "uid": "1",
                    "sr_data": {
                        "ease_factor": 2.3,
                        "history": [
                            {
                                "date": (
                                    datetime.now() - timedelta(days=i)
                                ).isoformat(),
                                "quality": 4,
                                "interval": i + 1,
                            }
                            for i in range(5)
                        ],
                    },
                }
            ]
        }

        report = PerformanceTracker.generate_performance_report(user_data, 30)

        self.assertIn("metrics", report)
        self.assertIn("insights", report)
        self.assertIn("recommendations", report)
        self.assertIn("performance_grade", report)
        self.assertIsInstance(report["insights"], list)
        self.assertIsInstance(report["recommendations"], list)


class TestSpacedRepetitionIntegration(unittest.TestCase):
    """Test Spaced Repetition integration with Plone."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        # Create test content
        self.research_note = api.content.create(
            container=self.portal,
            type="ResearchNote",
            title="Test Research Note",
            description="Test description",
            key_findings="Important findings",
        )

    def test_spaced_repetition_behavior(self):
        """Test spaced repetition behavior on content."""
        # Check behavior is available
        self.assertTrue(hasattr(self.research_note, "sr_enabled"))
        self.assertTrue(hasattr(self.research_note, "ease_factor"))
        self.assertTrue(hasattr(self.research_note, "update_review"))

        # Test initial values
        self.assertTrue(self.research_note.sr_enabled)
        self.assertEqual(self.research_note.ease_factor, 2.5)
        self.assertEqual(self.research_note.interval, 0)
        self.assertEqual(self.research_note.repetitions, 0)

    def test_update_review(self):
        """Test updating review on content."""
        # Perform review
        result = self.research_note.update_review(quality=4, time_spent=60)

        self.assertIsNotNone(result)
        self.assertEqual(self.research_note.repetitions, 1)
        self.assertEqual(self.research_note.interval, 1)
        self.assertIsNotNone(self.research_note.last_review)
        self.assertIsNotNone(self.research_note.next_review)
        self.assertEqual(self.research_note.total_reviews, 1)

        # Check review history
        self.assertEqual(len(self.research_note.review_history), 1)
        self.assertEqual(self.research_note.review_history[0]["quality"], 4)

    def test_review_stats(self):
        """Test review statistics."""
        # Add some reviews
        self.research_note.update_review(quality=3, time_spent=60)
        self.research_note.update_review(quality=4, time_spent=50)
        self.research_note.update_review(quality=5, time_spent=40)

        stats = self.research_note.get_review_stats()

        self.assertEqual(stats["total_reviews"], 3)
        self.assertEqual(stats["current_streak"], 3)
        self.assertEqual(stats["success_rate"], 100.0)
        self.assertGreater(stats["average_quality"], 3)

    def test_mastery_levels(self):
        """Test mastery level calculation."""
        self.assertEqual(self.research_note.get_mastery_level(), "not_started")

        self.research_note.interval = 5
        self.assertEqual(self.research_note.get_mastery_level(), "learning")

        self.research_note.interval = 15
        self.assertEqual(self.research_note.get_mastery_level(), "young")

        self.research_note.interval = 30
        self.assertEqual(self.research_note.get_mastery_level(), "mature")

        self.research_note.interval = 100
        self.assertEqual(self.research_note.get_mastery_level(), "mastered")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSM2Algorithm))
    suite.addTest(unittest.makeSuite(TestForgettingCurve))
    suite.addTest(unittest.makeSuite(TestReviewScheduler))
    suite.addTest(unittest.makeSuite(TestPerformanceTracker))
    suite.addTest(unittest.makeSuite(TestSpacedRepetitionIntegration))
    return suite
