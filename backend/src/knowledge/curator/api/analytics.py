"""Analytics API endpoints for learning statistics."""

from datetime import datetime, timedelta

from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
import math
from zope.security.interfaces import Unauthorized


@implementer(IPublishTraverse)
class AnalyticsService(Service):
    """Service for analytics and learning statistics."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if len(self.params) == 0:
            return self.get_overview()
        elif self.params[0] == "statistics":
            return self.get_statistics()
        elif self.params[0] == "forgetting-curve":
            return self.get_forgetting_curve()
        elif self.params[0] == "progress":
            return self.get_progress()
        elif self.params[0] == "activity":
            return self.get_activity()
        elif self.params[0] == "insights":
            return self.get_insights()
        elif self.params[0] == "learning-effectiveness":
            return self.get_learning_effectiveness()
        elif self.params[0] == "knowledge-gaps":
            return self.get_knowledge_gaps()
        elif self.params[0] == "learning-velocity":
            return self.get_learning_velocity()
        elif self.params[0] == "bloom-taxonomy":
            return self.get_bloom_taxonomy_analysis()
        elif self.params[0] == "cognitive-load":
            return self.get_cognitive_load_assessment()
        elif self.params[0] == "learning-goal-support":
            return self.get_learning_goal_support_analytics()
        elif self.params[0] == "goal-coverage-gaps":
            return self.get_goal_coverage_gaps()
        elif self.params[0] == "resource-recommendations":
            return self.get_resource_recommendations()
        else:
            self.request.response.setStatus(404)
            return {"error": "Not found"}

    def get_overview(self):
        """Get overview of knowledge base statistics."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        # Get user's content
        query = {
            "Creator": user.getId(),
            "portal_type": [
                "ResearchNote",
                "LearningGoal",
                "ProjectLog",
                "BookmarkPlus",
            ],
        }

        brains = catalog(**query)

        # Calculate statistics
        stats = {
            "total_items": len(brains),
            "by_type": {},
            "by_state": {},
            "recent_activity": [],
            "tags": {},
            "connections": 0,
        }

        # Process items
        for brain in brains:
            # Count by type
            portal_type = brain.portal_type
            stats["by_type"][portal_type] = stats["by_type"].get(portal_type, 0) + 1

            # Count by state
            state = brain.review_state
            stats["by_state"][state] = stats["by_state"].get(state, 0) + 1

            # Count tags
            for tag in brain.Subject:
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1

            # Count connections
            obj = brain.getObject()
            if hasattr(obj, "connections"):
                stats["connections"] += len(getattr(obj, "connections", []))
            if hasattr(obj, "related_notes"):
                stats["connections"] += len(getattr(obj, "related_notes", []))

        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_brains = catalog(
            Creator=user.getId(),
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
            modified={"query": thirty_days_ago, "range": "min"},
            sort_on="modified",
            sort_order="descending",
            sort_limit=10,
        )

        stats["recent_activity"] = [
            {
                "uid": brain.UID,
                "title": brain.Title,
                "type": brain.portal_type,
                "modified": brain.modified.ISO8601(),
                "url": brain.getURL(),
            }
            for brain in recent_brains[:10]
        ]

        # Top tags
        stats["top_tags"] = sorted(
            stats["tags"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        return stats

    def _calculate_goal_stats(self, goals):
        """Calculate goal statistics helper."""
        goal_stats = {
            "total": len(goals),
            "completed": 0,
            "in_progress": 0,
            "planned": 0,
            "average_progress": 0,
            "by_priority": {"low": 0, "medium": 0, "high": 0},
        }

        total_progress = 0
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                priority = getattr(obj, "priority", "medium")

                total_progress += progress
                goal_stats["by_priority"][priority] += 1

                if progress >= 100:
                    goal_stats["completed"] += 1
                elif progress > 0:
                    goal_stats["in_progress"] += 1
                else:
                    goal_stats["planned"] += 1
            except (AttributeError, Unauthorized):
                continue

        if goals:
            goal_stats["average_progress"] = total_progress / len(goals)

        return goal_stats

    def _calculate_content_stats(self, user_id, start_date):
        """Calculate content statistics helper."""
        catalog = api.portal.get_tool("portal_catalog")

        # Get all content created in timeframe
        content = catalog(
            Creator=user_id,
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
            created={"query": start_date, "range": "min"},
        )

        content_stats = {
            "total_items": len(content),
            "by_type": {
                "ResearchNote": 0,
                "LearningGoal": 0,
                "ProjectLog": 0,
                "BookmarkPlus": 0,
            },
        }

        for brain in content:
            content_stats["by_type"][brain.portal_type] += 1

        return content_stats

    def get_statistics(self):
        """Get detailed learning statistics."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        # Time range from query parameters
        days = int(self.request.get("days", 30))
        start_date = datetime.now() - timedelta(days=days)

        # Get learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal",
            created={"query": start_date, "range": "min"},
        )

        goal_stats = self._calculate_goal_stats(goals)
        content_stats = self._calculate_content_stats(user.getId(), start_date)

        # Get spaced repetition stats
        sr_stats = self.get_spaced_repetition_stats()

        return {
            "period_days": days,
            "goals": goal_stats,
            "content": content_stats,
            "spaced_repetition": sr_stats,
            "generated_at": datetime.now().isoformat(),
        }

    def get_forgetting_curve(self):
        """Get forgetting curve data for spaced repetition."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        # Get items with review data
        brains = catalog(
            Creator=user.getId(), portal_type=["ResearchNote", "BookmarkPlus"]
        )

        curve_data = []

        for brain in brains:
            obj = brain.getObject()

            # Calculate retention based on last review
            last_review = brain.modified
            days_since_review = (datetime.now() - last_review.asdatetime()).days

            # Ebbinghaus forgetting curve formula
            # R = e^(-t/S) where t is time and S is strength
            strength = 1.0  # Default strength

            # Adjust strength based on connections and importance
            if hasattr(obj, "connections"):
                strength += len(getattr(obj, "connections", [])) * 0.1

            if hasattr(obj, "importance"):
                importance_weights = {
                    "low": 0.5,
                    "medium": 1.0,
                    "high": 1.5,
                    "critical": 2.0,
                }
                strength *= importance_weights.get(
                    getattr(obj, "importance", "medium"), 1.0
                )

            retention = math.exp(-days_since_review / (strength * 5))  # 5 day half-life

            curve_data.append({
                "uid": brain.UID,
                "title": brain.Title,
                "type": brain.portal_type,
                "days_since_review": days_since_review,
                "retention_score": round(retention, 3),
                "review_recommended": retention < 0.8,
                "last_review": brain.modified.ISO8601(),
                "url": brain.getURL(),
            })

        # Sort by retention score (lowest first - needs review)
        curve_data.sort(key=lambda x: x["retention_score"])

        # Group by review urgency
        review_groups = {
            "urgent": [],  # < 0.5 retention
            "soon": [],  # 0.5 - 0.7 retention
            "later": [],  # 0.7 - 0.8 retention
            "good": [],  # > 0.8 retention
        }

        for item in curve_data:
            retention = item["retention_score"]
            if retention < 0.5:
                review_groups["urgent"].append(item)
            elif retention < 0.7:
                review_groups["soon"].append(item)
            elif retention < 0.8:
                review_groups["later"].append(item)
            else:
                review_groups["good"].append(item)

        return {
            "forgetting_curve": curve_data[:50],  # Top 50 items
            "review_groups": {
                "urgent": review_groups["urgent"][:10],
                "soon": review_groups["soon"][:10],
                "later": review_groups["later"][:10],
                "good": len(review_groups["good"]),
            },
            "total_items": len(curve_data),
        }

    def get_progress(self):
        """Get learning progress over time."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        # Time range
        days = int(self.request.get("days", 90))
        interval = self.request.get("interval", "week")  # day, week, month

        # Calculate intervals
        intervals = []
        end_date = datetime.now()

        if interval == "day":
            for i in range(days):
                date = end_date - timedelta(days=i)
                intervals.append({
                    "start": date.replace(hour=0, minute=0, second=0),
                    "end": date.replace(hour=23, minute=59, second=59),
                    "label": date.strftime("%Y-%m-%d"),
                })
        elif interval == "week":
            weeks = days // 7
            for i in range(weeks):
                week_end = end_date - timedelta(days=i * 7)
                week_start = week_end - timedelta(days=6)
                intervals.append({
                    "start": week_start.replace(hour=0, minute=0, second=0),
                    "end": week_end.replace(hour=23, minute=59, second=59),
                    "label": f"Week {weeks - i}",
                })
        elif interval == "month":
            months = days // 30
            for i in range(months):
                month_end = end_date - timedelta(days=i * 30)
                month_start = month_end - timedelta(days=29)
                intervals.append({
                    "start": month_start.replace(hour=0, minute=0, second=0),
                    "end": month_end.replace(hour=23, minute=59, second=59),
                    "label": month_end.strftime("%B %Y"),
                })

        intervals.reverse()

        # Get progress data for each interval
        progress_data = []

        for interval_data in intervals:
            # Count items created in this interval
            created = catalog(
                Creator=user.getId(),
                portal_type=[
                    "ResearchNote",
                    "LearningGoal",
                    "ProjectLog",
                    "BookmarkPlus",
                ],
                created={
                    "query": [interval_data["start"], interval_data["end"]],
                    "range": "min:max",
                },
            )

            # Count items modified in this interval
            modified = catalog(
                Creator=user.getId(),
                portal_type=[
                    "ResearchNote",
                    "LearningGoal",
                    "ProjectLog",
                    "BookmarkPlus",
                ],
                modified={
                    "query": [interval_data["start"], interval_data["end"]],
                    "range": "min:max",
                },
            )

            progress_data.append({
                "period": interval_data["label"],
                "created": len(created),
                "modified": len(modified),
                "by_type": {
                    "ResearchNote": len([
                        b for b in created if b.portal_type == "ResearchNote"
                    ]),
                    "LearningGoal": len([
                        b for b in created if b.portal_type == "LearningGoal"
                    ]),
                    "ProjectLog": len([
                        b for b in created if b.portal_type == "ProjectLog"
                    ]),
                    "BookmarkPlus": len([
                        b for b in created if b.portal_type == "BookmarkPlus"
                    ]),
                },
            })

        return {"progress": progress_data, "interval": interval, "days": days}

    def get_activity(self):
        """Get user activity heatmap data."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        # Get last 365 days of activity
        start_date = datetime.now() - timedelta(days=365)

        brains = catalog(
            Creator=user.getId(),
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
            modified={"query": start_date, "range": "min"},
        )

        # Group by date
        activity_map = {}

        for brain in brains:
            date = brain.modified.asdatetime().date()
            date_str = date.isoformat()

            if date_str not in activity_map:
                activity_map[date_str] = {"count": 0, "types": []}

            activity_map[date_str]["count"] += 1
            activity_map[date_str]["types"].append(brain.portal_type)

        # Convert to list format
        activity_data = []
        for date_str, data in activity_map.items():
            activity_data.append({
                "date": date_str,
                "count": data["count"],
                "level": min(4, data["count"] // 2),  # 0-4 activity level
                "types": list(set(data["types"])),
            })

        activity_data.sort(key=lambda x: x["date"])

        return {
            "activity": activity_data,
            "total_days": len(activity_data),
            "most_active_day": max(activity_data, key=lambda x: x["count"])
            if activity_data
            else None,
        }

    def _analyze_tag_patterns(self, brains):
        """Analyze tag co-occurrence and frequency."""
        tag_cooccurrence = {}
        patterns = []

        for brain in brains:
            tags = list(brain.Subject)
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i + 1 :]:
                    pair = tuple(sorted([tag1, tag2]))
                    tag_cooccurrence[pair] = tag_cooccurrence.get(pair, 0) + 1

        for pair, count in sorted(
            tag_cooccurrence.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            patterns.append({
                "type": "tag_correlation",
                "tags": list(pair),
                "strength": count,
                "message": (
                    f"Tags '{pair[0]}' and '{pair[1]}' frequently appear together "
                    f"({count} times)"
                ),
            })
        return patterns

    def _analyze_goal_completion(self, goals):
        """Analyze completion rates of learning goals."""
        completion_rates = {"low": [], "medium": [], "high": []}
        recommendations = []

        for brain in goals:
            obj = brain.getObject()
            priority = getattr(obj, "priority", "medium")
            progress = getattr(obj, "progress", 0)
            completion_rates[priority].append(progress)

        for priority, rates in completion_rates.items():
            if rates:
                avg_completion = sum(rates) / len(rates)
                recommendations.append({
                    "type": "goal_completion",
                    "priority": priority,
                    "average_completion": round(avg_completion, 1),
                    "message": (
                        f"{priority.capitalize()} priority goals have "
                        f"{avg_completion:.1f}% average completion"
                    ),
                })
        return recommendations

    def _find_isolated_content(self, brains):
        """Find content without connections."""
        isolated_items = []
        for brain in brains[:100]:  # Check first 100 items
            obj = brain.getObject()
            connections = len(getattr(obj, "connections", []))
            if connections == 0 and brain.portal_type == "ResearchNote":
                isolated_items.append({
                    "uid": brain.UID,
                    "title": brain.Title,
                    "url": brain.getURL(),
                })

        if isolated_items:
            return {
                "type": "isolated_content",
                "count": len(isolated_items),
                "items": isolated_items[:5],
                "message": (
                    f"Found {len(isolated_items)} research notes without connections"
                ),
            }
        return None

    def get_insights(self):
        """Get AI-generated insights from the knowledge base."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        brains = catalog(
            Creator=user.getId(),
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog", "BookmarkPlus"],
        )
        goals = catalog(Creator=user.getId(), portal_type="LearningGoal")

        patterns = self._analyze_tag_patterns(brains)
        recommendations = self._analyze_goal_completion(goals)
        isolated_content = self._find_isolated_content(brains)

        if isolated_content:
            patterns.append(isolated_content)

        return {
            "patterns": patterns,
            "recommendations": recommendations,
            "connections": [],
        }
    
    def get_learning_effectiveness(self):
        """Analyze learning effectiveness metrics."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Time range
        days = int(self.request.get("days", 90))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal",
            created={"query": start_date, "range": "min"}
        )
        
        effectiveness_metrics = {
            "completion_rate": 0,
            "average_time_to_complete": 0,
            "milestone_achievement_rate": 0,
            "objective_completion_rate": 0,
            "knowledge_retention": 0,
            "learning_paths": [],
            "by_difficulty": {
                "beginner": {"total": 0, "completed": 0, "avg_time": 0},
                "intermediate": {"total": 0, "completed": 0, "avg_time": 0},
                "advanced": {"total": 0, "completed": 0, "avg_time": 0}
            }
        }
        
        completed_goals = 0
        total_completion_time = 0
        completed_with_time = 0
        total_milestones = 0
        completed_milestones = 0
        total_objectives = 0
        completed_objectives = 0
        
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                difficulty = getattr(obj, "difficulty_level", "intermediate")
                
                # Track by difficulty
                if difficulty in effectiveness_metrics["by_difficulty"]:
                    effectiveness_metrics["by_difficulty"][difficulty]["total"] += 1
                
                if progress >= 100:
                    completed_goals += 1
                    
                    # Track by difficulty
                    if difficulty in effectiveness_metrics["by_difficulty"]:
                        effectiveness_metrics["by_difficulty"][difficulty]["completed"] += 1
                    
                    # Calculate time to complete
                    created = brain.created.asdatetime()
                    modified = brain.modified.asdatetime()
                    time_to_complete = (modified - created).days
                    
                    if time_to_complete > 0:
                        total_completion_time += time_to_complete
                        completed_with_time += 1
                        
                        if difficulty in effectiveness_metrics["by_difficulty"]:
                            diff_stats = effectiveness_metrics["by_difficulty"][difficulty]
                            current_total = diff_stats.get("avg_time", 0) * (diff_stats["completed"] - 1)
                            diff_stats["avg_time"] = (current_total + time_to_complete) / diff_stats["completed"]
                
                # Count milestones
                milestones = getattr(obj, "milestones", [])
                total_milestones += len(milestones)
                completed_milestones += sum(1 for m in milestones if m.get("status") == "completed")
                
                # Count objectives
                objectives = getattr(obj, "learning_objectives", [])
                total_objectives += len(objectives)
                # Consider objective complete if goal is >80% complete
                if progress >= 80:
                    completed_objectives += len(objectives)
                
            except:
                continue
        
        # Calculate metrics
        if len(goals) > 0:
            effectiveness_metrics["completion_rate"] = round((completed_goals / len(goals)) * 100, 1)
        
        if completed_with_time > 0:
            effectiveness_metrics["average_time_to_complete"] = round(total_completion_time / completed_with_time, 1)
        
        if total_milestones > 0:
            effectiveness_metrics["milestone_achievement_rate"] = round((completed_milestones / total_milestones) * 100, 1)
        
        if total_objectives > 0:
            effectiveness_metrics["objective_completion_rate"] = round((completed_objectives / total_objectives) * 100, 1)
        
        # Calculate knowledge retention (based on review frequency and confidence)
        notes = catalog(
            Creator=user.getId(),
            portal_type="ResearchNote",
            modified={"query": start_date, "range": "min"}
        )
        
        retention_scores = []
        for brain in notes:
            try:
                obj = brain.getObject()
                confidence = getattr(obj, "confidence_score", 0.5)
                days_since_review = (datetime.now() - brain.modified.asdatetime()).days
                
                # Retention score based on confidence and time
                retention = confidence * math.exp(-days_since_review / 30)  # 30-day half-life
                retention_scores.append(retention)
            except:
                continue
        
        if retention_scores:
            effectiveness_metrics["knowledge_retention"] = round(sum(retention_scores) / len(retention_scores) * 100, 1)
        
        # Analyze most effective learning paths
        effective_paths = []
        for brain in goals:
            try:
                obj = brain.getObject()
                if getattr(obj, "progress", 0) >= 100:
                    prerequisites = getattr(obj, "prerequisite_knowledge", [])
                    if prerequisites:
                        effective_paths.append({
                            "goal": brain.Title,
                            "prerequisites_count": len(prerequisites),
                            "difficulty": getattr(obj, "difficulty_level", "intermediate"),
                            "time_to_complete": (brain.modified.asdatetime() - brain.created.asdatetime()).days
                        })
            except:
                continue
        
        # Sort by time to complete
        effective_paths.sort(key=lambda x: x["time_to_complete"])
        effectiveness_metrics["learning_paths"] = effective_paths[:5]
        
        return effectiveness_metrics
    
    def get_knowledge_gaps(self):
        """Identify and analyze knowledge gaps."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        knowledge_gaps = {
            "identified_gaps": [],
            "prerequisite_gaps": [],
            "competency_gaps": [],
            "topic_coverage": {},
            "recommendations": []
        }
        
        # Get all content
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        notes = catalog(
            Creator=user.getId(),
            portal_type="ResearchNote"
        )
        
        # Build knowledge map
        covered_topics = set()
        topic_confidence = {}
        
        for brain in notes:
            try:
                obj = brain.getObject()
                tags = getattr(obj, "tags", [])
                confidence = getattr(obj, "confidence_score", 0.5)
                
                for tag in tags:
                    covered_topics.add(tag)
                    if tag not in topic_confidence:
                        topic_confidence[tag] = []
                    topic_confidence[tag].append(confidence)
                
                # Check for AI-identified gaps
                if hasattr(obj, "knowledge_gaps"):
                    for gap in getattr(obj, "knowledge_gaps", []):
                        knowledge_gaps["identified_gaps"].append({
                            "description": gap.get("gap_description", ""),
                            "importance": gap.get("importance", "medium"),
                            "source": brain.Title,
                            "source_url": brain.getURL(),
                            "suggested_topics": gap.get("suggested_topics", []),
                            "confidence": gap.get("confidence", 0.7)
                        })
            except:
                continue
        
        # Calculate average confidence per topic
        for topic, confidences in topic_confidence.items():
            avg_confidence = sum(confidences) / len(confidences)
            knowledge_gaps["topic_coverage"][topic] = {
                "count": len(confidences),
                "average_confidence": round(avg_confidence, 2),
                "needs_reinforcement": avg_confidence < 0.7
            }
        
        # Find prerequisite gaps
        unmet_prerequisites = set()
        completed_goal_uids = set()
        
        for brain in goals:
            try:
                obj = brain.getObject()
                if getattr(obj, "progress", 0) >= 100:
                    completed_goal_uids.add(brain.UID)
            except:
                continue
        
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                
                if progress < 100:
                    prerequisites = getattr(obj, "prerequisite_knowledge", [])
                    for prereq in prerequisites:
                        if prereq not in completed_goal_uids:
                            prereq_brain = catalog(UID=prereq)
                            if prereq_brain:
                                knowledge_gaps["prerequisite_gaps"].append({
                                    "blocking_goal": brain.Title,
                                    "blocking_goal_url": brain.getURL(),
                                    "prerequisite": prereq_brain[0].Title,
                                    "prerequisite_url": prereq_brain[0].getURL(),
                                    "prerequisite_type": prereq_brain[0].portal_type
                                })
            except:
                continue
        
        # Find competency gaps
        all_competencies = {}
        for brain in goals:
            try:
                obj = brain.getObject()
                competencies = getattr(obj, "competencies", [])
                
                for comp in competencies:
                    comp_name = comp.get("name")
                    if comp_name:
                        if comp_name not in all_competencies:
                            all_competencies[comp_name] = {
                                "occurrences": 0,
                                "average_progress": 0,
                                "levels": []
                            }
                        
                        all_competencies[comp_name]["occurrences"] += 1
                        progress = getattr(obj, "progress", 0)
                        current_avg = all_competencies[comp_name]["average_progress"]
                        all_competencies[comp_name]["average_progress"] = (
                            (current_avg * (all_competencies[comp_name]["occurrences"] - 1) + progress) /
                            all_competencies[comp_name]["occurrences"]
                        )
                        all_competencies[comp_name]["levels"].append(comp.get("level", "beginner"))
            except:
                continue
        
        # Identify weak competencies
        for comp_name, comp_data in all_competencies.items():
            if comp_data["average_progress"] < 50:
                knowledge_gaps["competency_gaps"].append({
                    "competency": comp_name,
                    "average_progress": round(comp_data["average_progress"], 1),
                    "occurrences": comp_data["occurrences"],
                    "current_levels": list(set(comp_data["levels"]))
                })
        
        # Generate recommendations
        if knowledge_gaps["identified_gaps"]:
            knowledge_gaps["recommendations"].append({
                "type": "content",
                "priority": "high",
                "action": "Review and strengthen understanding of identified knowledge gaps",
                "count": len(knowledge_gaps["identified_gaps"])
            })
        
        if knowledge_gaps["prerequisite_gaps"]:
            knowledge_gaps["recommendations"].append({
                "type": "prerequisites",
                "priority": "critical",
                "action": "Complete prerequisite knowledge before advancing",
                "count": len(set(gap["prerequisite"] for gap in knowledge_gaps["prerequisite_gaps"]))
            })
        
        weak_topics = [topic for topic, data in knowledge_gaps["topic_coverage"].items() 
                      if data["needs_reinforcement"]]
        if weak_topics:
            knowledge_gaps["recommendations"].append({
                "type": "reinforcement",
                "priority": "medium",
                "action": "Reinforce understanding of low-confidence topics",
                "topics": weak_topics[:5]
            })
        
        return knowledge_gaps
    
    def get_learning_velocity(self):
        """Track learning velocity and momentum."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Time windows
        windows = [
            {"name": "last_week", "days": 7},
            {"name": "last_month", "days": 30},
            {"name": "last_quarter", "days": 90},
            {"name": "last_year", "days": 365}
        ]
        
        velocity_data = {
            "current_velocity": 0,
            "trend": "stable",
            "by_window": {},
            "by_content_type": {},
            "momentum_indicators": {},
            "projections": {}
        }
        
        for window in windows:
            start_date = datetime.now() - timedelta(days=window["days"])
            
            # Get content created/modified in this window
            content = catalog(
                Creator=user.getId(),
                portal_type=["ResearchNote", "LearningGoal", "ProjectLog"],
                modified={"query": start_date, "range": "min"}
            )
            
            # Calculate metrics for this window
            window_data = {
                "items_created": 0,
                "items_modified": 0,
                "goals_completed": 0,
                "milestones_completed": 0,
                "knowledge_items_added": 0,
                "daily_average": 0
            }
            
            for brain in content:
                if brain.created.asdatetime() >= start_date:
                    window_data["items_created"] += 1
                else:
                    window_data["items_modified"] += 1
                
                if brain.portal_type == "ResearchNote":
                    window_data["knowledge_items_added"] += 1
                elif brain.portal_type == "LearningGoal":
                    try:
                        obj = brain.getObject()
                        if getattr(obj, "progress", 0) >= 100:
                            window_data["goals_completed"] += 1
                        
                        # Count completed milestones
                        milestones = getattr(obj, "milestones", [])
                        for m in milestones:
                            if m.get("status") == "completed":
                                completed_date = m.get("completed_date")
                                if completed_date:
                                    try:
                                        completed_dt = datetime.fromisoformat(completed_date)
                                        if completed_dt >= start_date:
                                            window_data["milestones_completed"] += 1
                                    except:
                                        pass
                    except:
                        continue
            
            # Calculate daily average
            window_data["daily_average"] = round(
                (window_data["items_created"] + window_data["items_modified"]) / window["days"],
                2
            )
            
            velocity_data["by_window"][window["name"]] = window_data
        
        # Calculate current velocity (last week's daily average)
        velocity_data["current_velocity"] = velocity_data["by_window"]["last_week"]["daily_average"]
        
        # Determine trend
        week_avg = velocity_data["by_window"]["last_week"]["daily_average"]
        month_avg = velocity_data["by_window"]["last_month"]["daily_average"]
        
        if week_avg > month_avg * 1.2:
            velocity_data["trend"] = "accelerating"
        elif week_avg < month_avg * 0.8:
            velocity_data["trend"] = "decelerating"
        else:
            velocity_data["trend"] = "stable"
        
        # Calculate momentum indicators
        velocity_data["momentum_indicators"] = {
            "consistency_score": 0,
            "diversity_score": 0,
            "completion_momentum": 0,
            "engagement_level": "medium"
        }
        
        # Consistency score (how many days with activity in last month)
        last_30_days = [datetime.now().date() - timedelta(days=i) for i in range(30)]
        active_days = set()
        
        month_content = catalog(
            Creator=user.getId(),
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog"],
            modified={"query": datetime.now() - timedelta(days=30), "range": "min"}
        )
        
        for brain in month_content:
            active_days.add(brain.modified.asdatetime().date())
        
        velocity_data["momentum_indicators"]["consistency_score"] = round(
            (len(active_days) / 30) * 100, 1
        )
        
        # Diversity score (variety of content types)
        content_type_counts = {"ResearchNote": 0, "LearningGoal": 0, "ProjectLog": 0}
        for brain in month_content:
            if brain.portal_type in content_type_counts:
                content_type_counts[brain.portal_type] += 1
        
        active_types = sum(1 for count in content_type_counts.values() if count > 0)
        velocity_data["momentum_indicators"]["diversity_score"] = round(
            (active_types / 3) * 100, 1
        )
        
        # Completion momentum
        week_completions = velocity_data["by_window"]["last_week"]["goals_completed"] + \
                          velocity_data["by_window"]["last_week"]["milestones_completed"]
        month_completions = velocity_data["by_window"]["last_month"]["goals_completed"] + \
                           velocity_data["by_window"]["last_month"]["milestones_completed"]
        
        if month_completions > 0:
            velocity_data["momentum_indicators"]["completion_momentum"] = round(
                (week_completions * 4 / month_completions) * 100, 1
            )
        
        # Engagement level
        if velocity_data["current_velocity"] >= 3:
            velocity_data["momentum_indicators"]["engagement_level"] = "high"
        elif velocity_data["current_velocity"] >= 1:
            velocity_data["momentum_indicators"]["engagement_level"] = "medium"
        else:
            velocity_data["momentum_indicators"]["engagement_level"] = "low"
        
        # Projections
        if velocity_data["current_velocity"] > 0:
            velocity_data["projections"] = {
                "items_next_week": round(velocity_data["current_velocity"] * 7),
                "items_next_month": round(velocity_data["current_velocity"] * 30),
                "goals_completion_rate": round(
                    velocity_data["by_window"]["last_month"]["goals_completed"] / 30 * 30, 1
                )
            }
        
        return velocity_data
    
    def get_bloom_taxonomy_analysis(self):
        """Analyze learning content according to Bloom's Taxonomy."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Bloom's Taxonomy levels
        bloom_levels = [
            "remember",
            "understand",
            "apply",
            "analyze",
            "evaluate",
            "create"
        ]
        
        # Keywords associated with each level
        bloom_keywords = {
            "remember": ["define", "list", "identify", "name", "recall", "recognize", "state"],
            "understand": ["explain", "describe", "interpret", "summarize", "classify", "compare"],
            "apply": ["implement", "use", "execute", "solve", "demonstrate", "operate"],
            "analyze": ["analyze", "differentiate", "organize", "attribute", "deconstruct", "integrate"],
            "evaluate": ["evaluate", "critique", "judge", "justify", "argue", "defend"],
            "create": ["create", "design", "construct", "develop", "formulate", "investigate"]
        }
        
        bloom_analysis = {
            "distribution": {level: 0 for level in bloom_levels},
            "by_content_type": {
                "ResearchNote": {level: 0 for level in bloom_levels},
                "LearningGoal": {level: 0 for level in bloom_levels},
                "ProjectLog": {level: 0 for level in bloom_levels}
            },
            "objectives_by_level": {level: [] for level in bloom_levels},
            "current_focus": "",
            "recommendations": [],
            "cognitive_progression": []
        }
        
        # Analyze learning objectives
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        for brain in goals:
            try:
                obj = brain.getObject()
                objectives = getattr(obj, "learning_objectives", [])
                
                for objective in objectives:
                    obj_text = objective.get("objective_text", "").lower()
                    
                    # Classify objective by Bloom's level
                    classified_level = None
                    for level, keywords in bloom_keywords.items():
                        if any(keyword in obj_text for keyword in keywords):
                            classified_level = level
                            break
                    
                    if not classified_level:
                        # Default to "understand" if no keywords match
                        classified_level = "understand"
                    
                    bloom_analysis["distribution"][classified_level] += 1
                    bloom_analysis["by_content_type"]["LearningGoal"][classified_level] += 1
                    
                    # Store example objectives
                    if len(bloom_analysis["objectives_by_level"][classified_level]) < 3:
                        bloom_analysis["objectives_by_level"][classified_level].append({
                            "text": objective.get("objective_text", ""),
                            "goal": brain.Title,
                            "goal_url": brain.getURL()
                        })
            except:
                continue
        
        # Analyze content for implicit taxonomy levels
        all_content = catalog(
            Creator=user.getId(),
            portal_type=["ResearchNote", "LearningGoal", "ProjectLog"]
        )
        
        for brain in all_content:
            try:
                obj = brain.getObject()
                
                # Analyze based on content type and characteristics
                if brain.portal_type == "ResearchNote":
                    # Research notes typically involve understanding and analyzing
                    key_insights = getattr(obj, "key_insights", [])
                    if key_insights:
                        bloom_analysis["by_content_type"]["ResearchNote"]["analyze"] += 1
                    else:
                        bloom_analysis["by_content_type"]["ResearchNote"]["understand"] += 1
                
                elif brain.portal_type == "ProjectLog":
                    # Project logs involve application and creation
                    status = getattr(obj, "status", "planning")
                    if status in ["completed", "deployed"]:
                        bloom_analysis["by_content_type"]["ProjectLog"]["create"] += 1
                    elif status in ["active", "testing"]:
                        bloom_analysis["by_content_type"]["ProjectLog"]["apply"] += 1
                    else:
                        bloom_analysis["by_content_type"]["ProjectLog"]["analyze"] += 1
                
            except:
                continue
        
        # Determine current focus
        total_activities = sum(bloom_analysis["distribution"].values())
        if total_activities > 0:
            # Find the level with most activities
            max_level = max(bloom_analysis["distribution"].items(), key=lambda x: x[1])
            bloom_analysis["current_focus"] = max_level[0]
            
            # Calculate percentage distribution
            for level in bloom_levels:
                percentage = (bloom_analysis["distribution"][level] / total_activities) * 100
                bloom_analysis["distribution"][level] = {
                    "count": bloom_analysis["distribution"][level],
                    "percentage": round(percentage, 1)
                }
        
        # Analyze cognitive progression
        recent_goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal",
            sort_on="created",
            sort_order="descending",
            sort_limit=10
        )[:10]
        
        for brain in recent_goals:
            try:
                obj = brain.getObject()
                objectives = getattr(obj, "learning_objectives", [])
                
                if objectives:
                    # Classify first objective
                    obj_text = objectives[0].get("objective_text", "").lower()
                    level = "understand"  # default
                    
                    for bloom_level, keywords in bloom_keywords.items():
                        if any(keyword in obj_text for keyword in keywords):
                            level = bloom_level
                            break
                    
                    bloom_analysis["cognitive_progression"].append({
                        "date": brain.created.ISO8601(),
                        "level": level,
                        "goal": brain.Title
                    })
            except:
                continue
        
        # Generate recommendations
        distribution = bloom_analysis["distribution"]
        
        # Check for imbalances
        lower_levels = sum(distribution[level]["count"] for level in ["remember", "understand"])
        higher_levels = sum(distribution[level]["count"] for level in ["evaluate", "create"])
        
        if total_activities > 0:
            if lower_levels / total_activities > 0.6:
                bloom_analysis["recommendations"].append({
                    "type": "progression",
                    "message": "Consider advancing to higher-order thinking tasks (Apply, Analyze, Evaluate, Create)",
                    "priority": "high"
                })
            
            if higher_levels / total_activities < 0.2:
                bloom_analysis["recommendations"].append({
                    "type": "challenge",
                    "message": "Add more creative and evaluative learning objectives to deepen understanding",
                    "priority": "medium"
                })
            
            if distribution["apply"]["count"] < total_activities * 0.15:
                bloom_analysis["recommendations"].append({
                    "type": "practice",
                    "message": "Include more practical application exercises to reinforce learning",
                    "priority": "medium"
                })
        
        return bloom_analysis
    
    def get_cognitive_load_assessment(self):
        """Assess cognitive load across learning materials."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        cognitive_load_data = {
            "overall_load": "medium",
            "by_content_type": {},
            "active_learning_load": 0,
            "concurrent_goals": 0,
            "complexity_distribution": {},
            "recommendations": [],
            "load_indicators": {},
            "optimal_schedule": []
        }
        
        # Get active learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        active_goals = []
        total_load_score = 0
        load_factors = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3
        }
        
        cognitive_load_levels = {
            "low": 0,
            "medium": 0,
            "high": 0
        }
        
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                
                if 0 < progress < 100:
                    difficulty = getattr(obj, "difficulty_level", "intermediate")
                    cognitive_load = getattr(obj, "cognitive_load", "medium")
                    estimated_effort = getattr(obj, "estimated_effort", 10)
                    
                    # Calculate load score
                    load_score = load_factors.get(difficulty, 2)
                    
                    # Adjust for cognitive load setting
                    if cognitive_load == "high":
                        load_score *= 1.5
                    elif cognitive_load == "low":
                        load_score *= 0.7
                    
                    # Adjust for effort
                    if estimated_effort > 40:
                        load_score *= 1.2
                    
                    active_goals.append({
                        "brain": brain,
                        "load_score": load_score,
                        "difficulty": difficulty,
                        "cognitive_load": cognitive_load,
                        "progress": progress,
                        "estimated_effort": estimated_effort
                    })
                    
                    total_load_score += load_score
                    
                    if cognitive_load in cognitive_load_levels:
                        cognitive_load_levels[cognitive_load] += 1
                
            except:
                continue
        
        cognitive_load_data["concurrent_goals"] = len(active_goals)
        cognitive_load_data["active_learning_load"] = round(total_load_score, 1)
        
        # Determine overall load
        if len(active_goals) == 0:
            cognitive_load_data["overall_load"] = "none"
        elif total_load_score < 5:
            cognitive_load_data["overall_load"] = "low"
        elif total_load_score < 10:
            cognitive_load_data["overall_load"] = "medium"
        elif total_load_score < 15:
            cognitive_load_data["overall_load"] = "high"
        else:
            cognitive_load_data["overall_load"] = "overload"
        
        # Analyze load distribution
        cognitive_load_data["complexity_distribution"] = cognitive_load_levels
        
        # Load indicators
        cognitive_load_data["load_indicators"] = {
            "variety_score": 0,
            "concurrency_risk": "low",
            "effort_concentration": 0,
            "difficulty_balance": "balanced"
        }
        
        if active_goals:
            # Variety score (different difficulty levels)
            difficulties = set(goal["difficulty"] for goal in active_goals)
            cognitive_load_data["load_indicators"]["variety_score"] = len(difficulties)
            
            # Concurrency risk
            if len(active_goals) > 5:
                cognitive_load_data["load_indicators"]["concurrency_risk"] = "high"
            elif len(active_goals) > 3:
                cognitive_load_data["load_indicators"]["concurrency_risk"] = "medium"
            
            # Effort concentration
            total_effort = sum(goal["estimated_effort"] for goal in active_goals)
            cognitive_load_data["load_indicators"]["effort_concentration"] = total_effort
            
            # Difficulty balance
            high_difficulty = sum(1 for goal in active_goals if goal["difficulty"] == "advanced")
            if high_difficulty > len(active_goals) * 0.5:
                cognitive_load_data["load_indicators"]["difficulty_balance"] = "too_difficult"
            elif high_difficulty == 0 and len(active_goals) > 3:
                cognitive_load_data["load_indicators"]["difficulty_balance"] = "too_easy"
        
        # Create optimal schedule
        if active_goals:
            # Sort by priority and load
            sorted_goals = sorted(active_goals, key=lambda x: (x["load_score"], -x["progress"]))
            
            daily_load_limit = 5
            current_day_load = 0
            day_number = 1
            
            for goal in sorted_goals[:10]:  # Limit to top 10
                if current_day_load + goal["load_score"] > daily_load_limit:
                    day_number += 1
                    current_day_load = 0
                
                cognitive_load_data["optimal_schedule"].append({
                    "day": day_number,
                    "goal": goal["brain"].Title,
                    "goal_url": goal["brain"].getURL(),
                    "load_score": round(goal["load_score"], 1),
                    "estimated_hours": round(goal["estimated_effort"] / 5, 1)  # Spread over 5 days
                })
                
                current_day_load += goal["load_score"]
        
        # Generate recommendations
        if cognitive_load_data["overall_load"] == "overload":
            cognitive_load_data["recommendations"].append({
                "type": "reduce_load",
                "priority": "critical",
                "message": "Cognitive overload detected. Consider pausing or deferring some learning goals.",
                "action": f"Reduce active goals from {len(active_goals)} to 3-4 maximum"
            })
        
        if cognitive_load_data["load_indicators"]["concurrency_risk"] == "high":
            cognitive_load_data["recommendations"].append({
                "type": "focus",
                "priority": "high",
                "message": "Too many concurrent learning goals may reduce effectiveness",
                "action": "Focus on completing 1-2 goals before starting new ones"
            })
        
        if cognitive_load_data["load_indicators"]["difficulty_balance"] == "too_difficult":
            cognitive_load_data["recommendations"].append({
                "type": "balance",
                "priority": "medium",
                "message": "High proportion of advanced content may cause fatigue",
                "action": "Mix in some intermediate or beginner level content"
            })
        
        if cognitive_load_data["load_indicators"]["effort_concentration"] > 100:
            cognitive_load_data["recommendations"].append({
                "type": "pacing",
                "priority": "medium",
                "message": "Total estimated effort is very high",
                "action": "Consider extending timelines or breaking down complex goals"
            })
        
        return cognitive_load_data
    
    def get_learning_goal_support_analytics(self):
        """Get comprehensive analytics on how BookmarkPlus resources support learning goals."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Get all BookmarkPlus resources
        bookmarks = catalog(
            Creator=user.getId(),
            portal_type="BookmarkPlus"
        )
        
        # Get all learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        analytics_data = {
            "summary": {
                "total_resources": len(bookmarks),
                "total_goals": len(goals),
                "resources_with_goal_support": 0,
                "goals_with_resource_support": 0,
                "average_resources_per_goal": 0.0,
                "average_goals_per_resource": 0.0,
                "overall_support_effectiveness": 0.0
            },
            "effectiveness_metrics": {
                "high_effectiveness_resources": [],
                "low_effectiveness_resources": [],
                "trending_resources": [],
                "completion_contributors": []
            },
            "goal_support_breakdown": {},
            "resource_performance": {},
            "satisfaction_metrics": {
                "average_satisfaction": 0.0,
                "satisfaction_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "highly_rated_resources": []
            },
            "usage_patterns": {
                "most_accessed_resources": [],
                "consistent_usage_resources": [],
                "engagement_trends": []
            }
        }
        
        # Process each bookmark
        total_effectiveness_scores = []
        total_satisfaction_scores = []
        resources_with_support = 0
        completion_contributions = 0
        
        for brain in bookmarks:
            try:
                obj = brain.getObject()
                supported_goals = getattr(obj, 'supports_learning_goals', [])
                
                if supported_goals:
                    resources_with_support += 1
                    
                    # Get summary metrics for this resource
                    summary = obj.get_learning_goal_support_summary()
                    
                    resource_data = {
                        "uid": brain.UID,
                        "title": brain.Title,
                        "url": brain.getURL(),
                        "supported_goals_count": summary['total_goals_supported'],
                        "goals_with_data": summary['goals_with_data'],
                        "average_effectiveness": summary['average_effectiveness'],
                        "average_satisfaction": summary['average_satisfaction'],
                        "support_rating": summary['overall_support_rating'],
                        "completion_contributions": summary['completion_contributions'],
                        "read_status": getattr(obj, 'read_status', 'unread'),
                        "resource_type": getattr(obj, 'resource_type', 'unknown'),
                        "content_quality": getattr(obj, 'content_quality', 'medium')
                    }
                    
                    analytics_data["resource_performance"][brain.UID] = resource_data
                    
                    # Track effectiveness scores
                    if summary['average_effectiveness'] > 0:
                        total_effectiveness_scores.append(summary['average_effectiveness'])
                        
                        # Categorize by effectiveness
                        if summary['average_effectiveness'] >= 0.8:
                            analytics_data["effectiveness_metrics"]["high_effectiveness_resources"].append(resource_data)
                        elif summary['average_effectiveness'] <= 0.4:
                            analytics_data["effectiveness_metrics"]["low_effectiveness_resources"].append(resource_data)
                    
                    # Track satisfaction scores
                    if summary['average_satisfaction'] > 0:
                        total_satisfaction_scores.append(summary['average_satisfaction'])
                        
                        # Update satisfaction distribution
                        satisfaction_rounded = str(round(summary['average_satisfaction']))
                        if satisfaction_rounded in analytics_data["satisfaction_metrics"]["satisfaction_distribution"]:
                            analytics_data["satisfaction_metrics"]["satisfaction_distribution"][satisfaction_rounded] += 1
                        
                        # Highly rated resources
                        if summary['average_satisfaction'] >= 4.0:
                            analytics_data["satisfaction_metrics"]["highly_rated_resources"].append(resource_data)
                    
                    # Track completion contributions
                    completion_contributions += summary['completion_contributions']
                    if summary['completion_contributions'] > 0:
                        analytics_data["effectiveness_metrics"]["completion_contributors"].append(resource_data)
                    
                    # Get detailed metrics for each goal
                    all_goal_metrics = obj.get_all_learning_goal_metrics()
                    for goal_uid, metrics in all_goal_metrics.items():
                        if goal_uid not in analytics_data["goal_support_breakdown"]:
                            # Get goal info
                            goal_brain = catalog(UID=goal_uid)
                            if goal_brain:
                                analytics_data["goal_support_breakdown"][goal_uid] = {
                                    "goal_title": goal_brain[0].Title,
                                    "goal_url": goal_brain[0].getURL(),
                                    "supporting_resources": [],
                                    "average_effectiveness": 0.0,
                                    "resource_count": 0,
                                    "completion_contributors": 0
                                }
                        
                        if goal_uid in analytics_data["goal_support_breakdown"]:
                            goal_data = analytics_data["goal_support_breakdown"][goal_uid]
                            goal_data["supporting_resources"].append({
                                "resource_uid": brain.UID,
                                "resource_title": brain.Title,
                                "effectiveness": metrics['average_effectiveness'],
                                "satisfaction": metrics['average_satisfaction'],
                                "sessions": metrics['total_sessions'],
                                "trend": metrics['recent_trend']
                            })
                            goal_data["resource_count"] += 1
                            
                            # Check for completion contribution
                            tracking_data = obj.get_learning_goal_support_data(goal_uid)
                            if tracking_data and tracking_data.get('completion_contributed', False):
                                goal_data["completion_contributors"] += 1
                
            except Exception as e:
                continue
        
        # Calculate summary statistics
        analytics_data["summary"]["resources_with_goal_support"] = resources_with_support
        
        if total_effectiveness_scores:
            from statistics import mean
            analytics_data["summary"]["overall_support_effectiveness"] = round(mean(total_effectiveness_scores), 3)
        
        if total_satisfaction_scores:
            from statistics import mean
            analytics_data["satisfaction_metrics"]["average_satisfaction"] = round(mean(total_satisfaction_scores), 1)
        
        # Calculate goal-level averages
        goals_with_support = 0
        total_resources_per_goal = 0
        
        for goal_uid, goal_data in analytics_data["goal_support_breakdown"].items():
            if goal_data["resource_count"] > 0:
                goals_with_support += 1
                total_resources_per_goal += goal_data["resource_count"]
                
                # Calculate average effectiveness for this goal
                effectiveness_scores = [r["effectiveness"] for r in goal_data["supporting_resources"] if r["effectiveness"] > 0]
                if effectiveness_scores:
                    from statistics import mean
                    goal_data["average_effectiveness"] = round(mean(effectiveness_scores), 3)
        
        analytics_data["summary"]["goals_with_resource_support"] = goals_with_support
        
        if goals_with_support > 0:
            analytics_data["summary"]["average_resources_per_goal"] = round(total_resources_per_goal / goals_with_support, 1)
        
        if resources_with_support > 0:
            analytics_data["summary"]["average_goals_per_resource"] = round(
                sum(len(getattr(catalog(UID=uid)[0].getObject(), 'supports_learning_goals', []))
                    for uid in analytics_data["resource_performance"].keys()) / resources_with_support, 1
            )
        
        # Identify trending resources (improving effectiveness)
        for resource_data in analytics_data["resource_performance"].values():
            try:
                obj = catalog(UID=resource_data["uid"])[0].getObject()
                all_metrics = obj.get_all_learning_goal_metrics()
                
                improving_count = sum(1 for metrics in all_metrics.values() 
                                    if metrics['recent_trend'] == 'improving')
                
                if improving_count > 0:
                    resource_data["improving_goals"] = improving_count
                    analytics_data["effectiveness_metrics"]["trending_resources"].append(resource_data)
                    
            except:
                continue
        
        # Sort lists by effectiveness/relevance
        analytics_data["effectiveness_metrics"]["high_effectiveness_resources"].sort(
            key=lambda x: x["average_effectiveness"], reverse=True
        )
        analytics_data["effectiveness_metrics"]["low_effectiveness_resources"].sort(
            key=lambda x: x["average_effectiveness"]
        )
        analytics_data["satisfaction_metrics"]["highly_rated_resources"].sort(
            key=lambda x: x["average_satisfaction"], reverse=True
        )
        analytics_data["effectiveness_metrics"]["trending_resources"].sort(
            key=lambda x: x.get("improving_goals", 0), reverse=True
        )
        
        return analytics_data
    
    def get_goal_coverage_gaps(self):
        """Analyze gaps in learning goal coverage and recommend additional resources."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Get all learning goals and bookmarks
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        bookmarks = catalog(
            Creator=user.getId(),
            portal_type="BookmarkPlus"
        )
        
        gap_analysis = {
            "unsupported_goals": [],
            "under_supported_goals": [],
            "well_supported_goals": [],
            "coverage_statistics": {
                "total_goals": len(goals),
                "unsupported_count": 0,
                "under_supported_count": 0,
                "well_supported_count": 0,
                "average_resources_per_goal": 0.0
            },
            "recommendations": [],
            "resource_distribution": {
                "goals_with_no_resources": 0,
                "goals_with_1_resource": 0,
                "goals_with_2_3_resources": 0,
                "goals_with_4_plus_resources": 0
            }
        }
        
        # Build resource-to-goal mapping
        goal_to_resources = {}
        resource_count_distribution = []
        
        for goal_brain in goals:
            goal_uid = goal_brain.UID
            goal_to_resources[goal_uid] = {
                "brain": goal_brain,
                "supporting_resources": [],
                "total_effectiveness": 0.0,
                "average_effectiveness": 0.0,
                "high_quality_resources": 0,
                "completion_contributors": 0
            }
        
        # Map resources to goals
        for bookmark_brain in bookmarks:
            try:
                obj = bookmark_brain.getObject()
                supported_goals = getattr(obj, 'supports_learning_goals', [])
                
                for goal_uid in supported_goals:
                    if goal_uid in goal_to_resources:
                        # Get effectiveness metrics
                        effectiveness_data = obj.calculate_learning_goal_effectiveness(goal_uid)
                        
                        resource_info = {
                            "uid": bookmark_brain.UID,
                            "title": bookmark_brain.Title,
                            "url": bookmark_brain.getURL(),
                            "resource_type": getattr(obj, 'resource_type', 'unknown'),
                            "content_quality": getattr(obj, 'content_quality', 'medium'),
                            "read_status": getattr(obj, 'read_status', 'unread'),
                            "effectiveness": effectiveness_data['average_effectiveness'] if effectiveness_data else 0.0,
                            "satisfaction": effectiveness_data['average_satisfaction'] if effectiveness_data else 0.0,
                            "recommendation_strength": effectiveness_data['recommendation_strength'] if effectiveness_data else 'low'
                        }
                        
                        goal_to_resources[goal_uid]["supporting_resources"].append(resource_info)
                        
                        if effectiveness_data:
                            goal_to_resources[goal_uid]["total_effectiveness"] += effectiveness_data['average_effectiveness']
                            
                            if effectiveness_data['recommendation_strength'] == 'high':
                                goal_to_resources[goal_uid]["high_quality_resources"] += 1
                            
                            # Check for completion contribution
                            tracking_data = obj.get_learning_goal_support_data(goal_uid)
                            if tracking_data and tracking_data.get('completion_contributed', False):
                                goal_to_resources[goal_uid]["completion_contributors"] += 1
                                
            except:
                continue
        
        # Analyze each goal's coverage
        total_resource_count = 0
        
        for goal_uid, goal_data in goal_to_resources.items():
            resource_count = len(goal_data["supporting_resources"])
            total_resource_count += resource_count
            resource_count_distribution.append(resource_count)
            
            # Calculate average effectiveness
            if goal_data["supporting_resources"]:
                effectiveness_scores = [r["effectiveness"] for r in goal_data["supporting_resources"] if r["effectiveness"] > 0]
                if effectiveness_scores:
                    from statistics import mean
                    goal_data["average_effectiveness"] = round(mean(effectiveness_scores), 3)
            
            goal_info = {
                "uid": goal_uid,
                "title": goal_data["brain"].Title,
                "url": goal_data["brain"].getURL(),
                "resource_count": resource_count,
                "average_effectiveness": goal_data["average_effectiveness"],
                "high_quality_resources": goal_data["high_quality_resources"],
                "completion_contributors": goal_data["completion_contributors"],
                "priority": getattr(goal_data["brain"].getObject(), 'priority', 'medium'),
                "progress": getattr(goal_data["brain"].getObject(), 'progress', 0),
                "difficulty": getattr(goal_data["brain"].getObject(), 'difficulty_level', 'intermediate')
            }
            
            # Categorize goals
            if resource_count == 0:
                gap_analysis["unsupported_goals"].append(goal_info)
                gap_analysis["coverage_statistics"]["unsupported_count"] += 1
                gap_analysis["resource_distribution"]["goals_with_no_resources"] += 1
            elif resource_count <= 2 or goal_data["average_effectiveness"] < 0.6:
                gap_analysis["under_supported_goals"].append(goal_info)
                gap_analysis["coverage_statistics"]["under_supported_count"] += 1
                
                if resource_count == 1:
                    gap_analysis["resource_distribution"]["goals_with_1_resource"] += 1
                elif resource_count <= 3:
                    gap_analysis["resource_distribution"]["goals_with_2_3_resources"] += 1
            else:
                gap_analysis["well_supported_goals"].append(goal_info)
                gap_analysis["coverage_statistics"]["well_supported_count"] += 1
                
                if resource_count >= 4:
                    gap_analysis["resource_distribution"]["goals_with_4_plus_resources"] += 1
                else:
                    gap_analysis["resource_distribution"]["goals_with_2_3_resources"] += 1
        
        # Calculate statistics
        if len(goals) > 0:
            gap_analysis["coverage_statistics"]["average_resources_per_goal"] = round(total_resource_count / len(goals), 1)
        
        # Generate recommendations
        # Priority 1: Unsupported high-priority goals
        high_priority_unsupported = [g for g in gap_analysis["unsupported_goals"] 
                                   if g["priority"] in ["high", "critical"]]
        if high_priority_unsupported:
            gap_analysis["recommendations"].append({
                "type": "critical_gap",
                "priority": "critical",
                "title": "High-Priority Goals Without Resources",
                "description": f"Found {len(high_priority_unsupported)} high-priority learning goals with no supporting resources",
                "action": "Add at least 2-3 quality resources for each of these goals",
                "affected_goals": [g["uid"] for g in high_priority_unsupported[:5]]
            })
        
        # Priority 2: Under-supported goals with low effectiveness
        low_effectiveness_goals = [g for g in gap_analysis["under_supported_goals"] 
                                 if g["average_effectiveness"] < 0.4 and g["resource_count"] > 0]
        if low_effectiveness_goals:
            gap_analysis["recommendations"].append({
                "type": "quality_gap",
                "priority": "high",
                "title": "Goals with Low-Effectiveness Resources",
                "description": f"Found {len(low_effectiveness_goals)} goals with resources that are not effective",
                "action": "Replace or supplement with higher-quality resources",
                "affected_goals": [g["uid"] for g in low_effectiveness_goals[:5]]
            })
        
        # Priority 3: Goals with only one resource
        single_resource_goals = [g for g in gap_analysis["under_supported_goals"] 
                               if g["resource_count"] == 1]
        if single_resource_goals:
            gap_analysis["recommendations"].append({
                "type": "diversity_gap",
                "priority": "medium",
                "title": "Goals with Single Resource",
                "description": f"Found {len(single_resource_goals)} goals with only one supporting resource",
                "action": "Add 1-2 additional resources with different perspectives or formats",
                "affected_goals": [g["uid"] for g in single_resource_goals[:5]]
            })
        
        # Priority 4: Advanced goals without completion contributors
        advanced_incomplete_goals = [g for g in gap_analysis["under_supported_goals"] + gap_analysis["well_supported_goals"]
                                   if g["difficulty"] == "advanced" and g["completion_contributors"] == 0 and g["progress"] < 80]
        if advanced_incomplete_goals:
            gap_analysis["recommendations"].append({
                "type": "completion_gap",
                "priority": "medium",
                "title": "Advanced Goals Without Completion-Oriented Resources",
                "description": f"Found {len(advanced_incomplete_goals)} advanced goals without resources that help with completion",
                "action": "Add practical, application-oriented resources (projects, exercises, assessments)",
                "affected_goals": [g["uid"] for g in advanced_incomplete_goals[:5]]
            })
        
        # Sort recommendations by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gap_analysis["recommendations"].sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        # Sort goal lists by priority and progress
        gap_analysis["unsupported_goals"].sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["progress"]))
        gap_analysis["under_supported_goals"].sort(key=lambda x: (priority_order.get(x["priority"], 3), x["average_effectiveness"]))
        gap_analysis["well_supported_goals"].sort(key=lambda x: -x["average_effectiveness"])
        
        return gap_analysis
    
    def get_resource_recommendations(self):
        """Generate personalized resource recommendations based on learning goals and gaps."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}
        
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Get gap analysis data
        gap_analysis = self.get_goal_coverage_gaps()
        
        recommendations = {
            "immediate_actions": [],
            "suggested_resource_types": {},
            "learning_path_suggestions": [],
            "quality_improvements": [],
            "content_format_recommendations": {},
            "priority_matrix": {
                "high_impact_low_effort": [],
                "high_impact_high_effort": [],
                "low_impact_low_effort": [],
                "low_impact_high_effort": []
            }
        }
        
        # Get existing bookmarks for pattern analysis
        bookmarks = catalog(
            Creator=user.getId(),
            portal_type="BookmarkPlus"
        )
        
        # Analyze existing resource patterns
        resource_type_effectiveness = {}
        content_quality_impact = {}
        
        for brain in bookmarks:
            try:
                obj = brain.getObject()
                resource_type = getattr(obj, 'resource_type', 'unknown')
                content_quality = getattr(obj, 'content_quality', 'medium')
                
                # Get average effectiveness across all goals
                all_metrics = obj.get_all_learning_goal_metrics()
                if all_metrics:
                    avg_effectiveness = sum(m['average_effectiveness'] for m in all_metrics.values()) / len(all_metrics)
                    
                    # Track by resource type
                    if resource_type not in resource_type_effectiveness:
                        resource_type_effectiveness[resource_type] = []
                    resource_type_effectiveness[resource_type].append(avg_effectiveness)
                    
                    # Track by content quality
                    if content_quality not in content_quality_impact:
                        content_quality_impact[content_quality] = []
                    content_quality_impact[content_quality].append(avg_effectiveness)
                    
            except:
                continue
        
        # Calculate average effectiveness by type and quality
        for resource_type, scores in resource_type_effectiveness.items():
            if scores:
                from statistics import mean
                avg_score = mean(scores)
                recommendations["suggested_resource_types"][resource_type] = {
                    "average_effectiveness": round(avg_score, 3),
                    "sample_count": len(scores),
                    "recommendation": "high" if avg_score >= 0.7 else "medium" if avg_score >= 0.5 else "low"
                }
        
        # Generate immediate action recommendations
        # 1. Address unsupported high-priority goals
        high_priority_unsupported = [g for g in gap_analysis["unsupported_goals"] 
                                   if g["priority"] in ["high", "critical"]][:3]
        
        for goal in high_priority_unsupported:
            # Suggest resource types based on difficulty and what works well
            best_resource_types = sorted(
                recommendations["suggested_resource_types"].items(),
                key=lambda x: x[1]["average_effectiveness"],
                reverse=True
            )[:2]
            
            recommended_types = [rt[0] for rt in best_resource_types] if best_resource_types else ["article", "course"]
            
            recommendations["immediate_actions"].append({
                "type": "add_resources",
                "priority": "critical",
                "goal_uid": goal["uid"],
                "goal_title": goal["title"],
                "action": f"Add 2-3 resources for '{goal['title']}'",
                "suggested_resource_types": recommended_types,
                "reasoning": f"High-priority goal ({goal['priority']}) with no supporting resources",
                "estimated_effort": "medium"
            })
        
        # 2. Improve low-effectiveness resources
        low_effectiveness_goals = [g for g in gap_analysis["under_supported_goals"] 
                                 if g["average_effectiveness"] < 0.4][:2]
        
        for goal in low_effectiveness_goals:
            recommendations["quality_improvements"].append({
                "type": "improve_quality",
                "priority": "high",
                "goal_uid": goal["uid"],
                "goal_title": goal["title"],
                "current_effectiveness": goal["average_effectiveness"],
                "action": f"Replace or supplement low-quality resources for '{goal['title']}'",
                "target_effectiveness": 0.7,
                "reasoning": "Current resources are not effectively supporting learning",
                "estimated_effort": "high"
            })
        
        # 3. Learning path suggestions for connected goals
        goals_by_difficulty = {}
        for goal_list in [gap_analysis["unsupported_goals"], gap_analysis["under_supported_goals"]]:
            for goal in goal_list:
                difficulty = goal["difficulty"]
                if difficulty not in goals_by_difficulty:
                    goals_by_difficulty[difficulty] = []
                goals_by_difficulty[difficulty].append(goal)
        
        # Suggest learning paths from beginner to advanced
        if "beginner" in goals_by_difficulty and "intermediate" in goals_by_difficulty:
            recommendations["learning_path_suggestions"].append({
                "path_name": "Foundation to Intermediate",
                "description": "Build foundational knowledge before tackling intermediate concepts",
                "beginner_goals": [g["uid"] for g in goals_by_difficulty["beginner"][:2]],
                "intermediate_goals": [g["uid"] for g in goals_by_difficulty["intermediate"][:2]],
                "suggested_sequence": "Complete beginner goals first, then progress to intermediate",
                "estimated_timeline": "2-3 months"
            })
        
        # 4. Content format recommendations based on learning styles and effectiveness
        format_preferences = {}
        
        # Analyze what formats work best for the user
        for brain in bookmarks:
            try:
                obj = brain.getObject()
                resource_type = getattr(obj, 'resource_type', 'unknown')
                read_status = getattr(obj, 'read_status', 'unread')
                
                if read_status == 'completed':
                    if resource_type not in format_preferences:
                        format_preferences[resource_type] = {"completed": 0, "total": 0}
                    format_preferences[resource_type]["completed"] += 1
                
                if resource_type not in format_preferences:
                    format_preferences[resource_type] = {"completed": 0, "total": 0}
                format_preferences[resource_type]["total"] += 1
                
            except:
                continue
        
        # Calculate completion rates by format
        for resource_type, data in format_preferences.items():
            if data["total"] > 0:
                completion_rate = data["completed"] / data["total"]
                recommendations["content_format_recommendations"][resource_type] = {
                    "completion_rate": round(completion_rate, 2),
                    "total_resources": data["total"],
                    "recommendation": "high" if completion_rate >= 0.7 else "medium" if completion_rate >= 0.4 else "low"
                }
        
        # 5. Priority matrix classification
        for goal in gap_analysis["unsupported_goals"] + gap_analysis["under_supported_goals"]:
            # Estimate impact based on priority and progress
            impact_score = 0
            if goal["priority"] == "critical":
                impact_score = 4
            elif goal["priority"] == "high":
                impact_score = 3
            elif goal["priority"] == "medium":
                impact_score = 2
            else:
                impact_score = 1
            
            # Adjust for progress (less progress = higher impact potential)
            impact_score += (100 - goal["progress"]) / 25
            
            # Estimate effort based on difficulty and current resource count
            effort_score = 0
            if goal["difficulty"] == "advanced":
                effort_score = 3
            elif goal["difficulty"] == "intermediate":
                effort_score = 2
            else:
                effort_score = 1
            
            # More effort needed if no resources exist
            if goal["resource_count"] == 0:
                effort_score += 2
            elif goal["resource_count"] == 1:
                effort_score += 1
            
            # Classify into matrix
            goal_recommendation = {
                "goal_uid": goal["uid"],
                "goal_title": goal["title"],
                "impact_score": round(impact_score, 1),
                "effort_score": effort_score,
                "current_resources": goal["resource_count"],
                "current_effectiveness": goal["average_effectiveness"]
            }
            
            if impact_score >= 4 and effort_score <= 2:
                recommendations["priority_matrix"]["high_impact_low_effort"].append(goal_recommendation)
            elif impact_score >= 4 and effort_score > 2:
                recommendations["priority_matrix"]["high_impact_high_effort"].append(goal_recommendation)
            elif impact_score < 4 and effort_score <= 2:
                recommendations["priority_matrix"]["low_impact_low_effort"].append(goal_recommendation)
            else:
                recommendations["priority_matrix"]["low_impact_high_effort"].append(goal_recommendation)
        
        # Sort each quadrant
        for quadrant in recommendations["priority_matrix"].values():
            quadrant.sort(key=lambda x: x["impact_score"], reverse=True)
        
        # Sort resource type recommendations
        recommendations["suggested_resource_types"] = dict(
            sorted(recommendations["suggested_resource_types"].items(),
                  key=lambda x: x[1]["average_effectiveness"],
                  reverse=True)
        )
        
        return recommendations
