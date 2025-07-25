"""Learning Progression API endpoints."""

from datetime import datetime, timedelta
from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
import json
from zope.security.interfaces import Unauthorized


@implementer(IPublishTraverse)
class LearningProgressionService(Service):
    """Service for learning progression and milestone tracking."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if self.request.method == 'GET':
            if len(self.params) == 0:
                return self.get_overview()
            elif self.params[0] == "milestones":
                return self.get_milestones()
            elif self.params[0] == "path":
                return self.get_learning_path()
            elif self.params[0] == "competencies":
                return self.get_competencies()
            elif self.params[0] == "objectives":
                return self.get_objectives()
            elif self.params[0] == "prerequisites":
                return self.check_prerequisites()
            elif self.params[0] == "recommendations":
                return self.get_recommendations()
            else:
                self.request.response.setStatus(404)
                return {"error": "Not found"}
        elif self.request.method == 'POST':
            if len(self.params) > 0:
                if self.params[0] == "milestones":
                    return self.create_milestone()
                elif self.params[0] == "objectives":
                    return self.create_objective()
                elif self.params[0] == "competencies":
                    return self.assess_competency()
            self.request.response.setStatus(400)
            return {"error": "Invalid endpoint"}
        elif self.request.method == 'PUT':
            if len(self.params) > 0:
                if self.params[0] == "milestones":
                    return self.update_milestone()
                elif self.params[0] == "objectives":
                    return self.update_objective()
            self.request.response.setStatus(400)
            return {"error": "Invalid endpoint"}

    def get_overview(self):
        """Get learning progression overview."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        # Get user's learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )

        overview = {
            "total_goals": len(goals),
            "active_goals": 0,
            "completed_goals": 0,
            "total_milestones": 0,
            "completed_milestones": 0,
            "competencies": {},
            "learning_velocity": 0
        }

        # Process goals
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                
                if progress >= 100:
                    overview["completed_goals"] += 1
                elif progress > 0:
                    overview["active_goals"] += 1

                # Count milestones
                milestones = getattr(obj, "milestones", [])
                overview["total_milestones"] += len(milestones)
                overview["completed_milestones"] += sum(
                    1 for m in milestones if m.get("status") == "completed"
                )

                # Collect competencies
                competencies = getattr(obj, "competencies", [])
                for comp in competencies:
                    comp_name = comp.get("name")
                    if comp_name:
                        if comp_name not in overview["competencies"]:
                            overview["competencies"][comp_name] = {
                                "count": 0,
                                "levels": []
                            }
                        overview["competencies"][comp_name]["count"] += 1
                        level = comp.get("level")
                        if level:
                            overview["competencies"][comp_name]["levels"].append(level)

            except (AttributeError, Unauthorized):
                continue

        # Calculate learning velocity (milestones per month)
        if overview["total_milestones"] > 0:
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_completed = catalog(
                Creator=user.getId(),
                portal_type="LearningGoal",
                modified={"query": thirty_days_ago, "range": "min"}
            )
            
            recent_milestone_count = 0
            for brain in recent_completed:
                try:
                    obj = brain.getObject()
                    milestones = getattr(obj, "milestones", [])
                    for m in milestones:
                        if m.get("status") == "completed":
                            completed_date = m.get("completed_date")
                            if completed_date and isinstance(completed_date, str):
                                completed_dt = datetime.fromisoformat(completed_date)
                                if completed_dt > thirty_days_ago:
                                    recent_milestone_count += 1
                except:
                    continue
            
            overview["learning_velocity"] = round(recent_milestone_count / 30 * 30, 2)

        return overview

    def get_milestones(self):
        """Get milestones across all learning goals."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Filter parameters
        status_filter = self.request.get("status")
        goal_uid = self.request.get("goal_uid")
        
        # Get learning goals
        query = {
            "Creator": user.getId(),
            "portal_type": "LearningGoal"
        }
        
        if goal_uid:
            query["UID"] = goal_uid
            
        goals = catalog(**query)
        
        all_milestones = []
        
        for brain in goals:
            try:
                obj = brain.getObject()
                milestones = getattr(obj, "milestones", [])
                
                for milestone in milestones:
                    # Apply status filter if provided
                    if status_filter and milestone.get("status") != status_filter:
                        continue
                    
                    # Enrich milestone data
                    enriched_milestone = dict(milestone)
                    enriched_milestone["goal_uid"] = brain.UID
                    enriched_milestone["goal_title"] = brain.Title
                    enriched_milestone["goal_url"] = brain.getURL()
                    
                    # Calculate days until target
                    target_date = milestone.get("target_date")
                    if target_date:
                        if isinstance(target_date, str):
                            target_dt = datetime.fromisoformat(target_date).date()
                        else:
                            target_dt = target_date
                        
                        days_until = (target_dt - datetime.now().date()).days
                        enriched_milestone["days_until_target"] = days_until
                        enriched_milestone["is_overdue"] = days_until < 0
                    
                    all_milestones.append(enriched_milestone)
                    
            except (AttributeError, Unauthorized):
                continue
        
        # Sort milestones
        sort_by = self.request.get("sort_by", "target_date")
        reverse = self.request.get("sort_order", "asc") == "desc"
        
        if sort_by == "target_date":
            all_milestones.sort(
                key=lambda m: m.get("target_date", "9999-12-31"),
                reverse=reverse
            )
        elif sort_by == "progress":
            all_milestones.sort(
                key=lambda m: m.get("progress_percentage", 0),
                reverse=reverse
            )
        
        return {
            "milestones": all_milestones,
            "count": len(all_milestones),
            "filters": {
                "status": status_filter,
                "goal_uid": goal_uid
            }
        }

    def get_learning_path(self):
        """Get recommended learning path based on prerequisites and progress."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Get all learning goals and research notes
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        notes = catalog(
            Creator=user.getId(),
            portal_type="ResearchNote"
        )
        
        # Build dependency graph
        dependency_graph = {}
        goal_map = {}
        
        for brain in goals:
            try:
                obj = brain.getObject()
                uid = brain.UID
                goal_map[uid] = {
                    "uid": uid,
                    "title": brain.Title,
                    "url": brain.getURL(),
                    "progress": getattr(obj, "progress", 0),
                    "priority": getattr(obj, "priority", "medium"),
                    "prerequisites": getattr(obj, "prerequisite_knowledge", []),
                    "difficulty_level": getattr(obj, "difficulty_level", "intermediate"),
                    "estimated_effort": getattr(obj, "estimated_effort", 0)
                }
                dependency_graph[uid] = getattr(obj, "prerequisite_knowledge", [])
            except:
                continue
        
        # Topological sort to determine learning order
        def topological_sort(graph):
            in_degree = {node: 0 for node in graph}
            for node in graph:
                for dep in graph[node]:
                    if dep in in_degree:
                        in_degree[dep] += 1
            
            queue = [node for node in in_degree if in_degree[node] == 0]
            result = []
            
            while queue:
                node = queue.pop(0)
                result.append(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
            
            return result
        
        # Get recommended path
        path_order = topological_sort(dependency_graph)
        
        # Build learning path
        learning_path = []
        completed_knowledge = set()
        
        for uid in path_order:
            if uid in goal_map:
                goal = goal_map[uid]
                
                # Check if prerequisites are met
                prerequisites_met = all(
                    prereq in completed_knowledge 
                    for prereq in goal["prerequisites"]
                )
                
                path_item = {
                    "uid": goal["uid"],
                    "title": goal["title"],
                    "url": goal["url"],
                    "progress": goal["progress"],
                    "priority": goal["priority"],
                    "difficulty_level": goal["difficulty_level"],
                    "estimated_effort": goal["estimated_effort"],
                    "prerequisites_met": prerequisites_met,
                    "status": "completed" if goal["progress"] >= 100 else 
                             "in_progress" if goal["progress"] > 0 else 
                             "ready" if prerequisites_met else "blocked"
                }
                
                learning_path.append(path_item)
                
                if goal["progress"] >= 100:
                    completed_knowledge.add(uid)
        
        # Sort by status and priority
        status_order = {"in_progress": 0, "ready": 1, "blocked": 2, "completed": 3}
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        learning_path.sort(key=lambda x: (
            status_order.get(x["status"], 4),
            priority_order.get(x["priority"], 3)
        ))
        
        return {
            "learning_path": learning_path,
            "total_items": len(learning_path),
            "ready_to_learn": sum(1 for item in learning_path if item["status"] == "ready"),
            "in_progress": sum(1 for item in learning_path if item["status"] == "in_progress"),
            "blocked": sum(1 for item in learning_path if item["status"] == "blocked"),
            "completed": sum(1 for item in learning_path if item["status"] == "completed")
        }

    def get_competencies(self):
        """Get competency assessment across all learning."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Get all learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        competency_map = {}
        
        for brain in goals:
            try:
                obj = brain.getObject()
                competencies = getattr(obj, "competencies", [])
                goal_progress = getattr(obj, "progress", 0)
                
                for comp in competencies:
                    comp_name = comp.get("name")
                    if not comp_name:
                        continue
                    
                    if comp_name not in competency_map:
                        competency_map[comp_name] = {
                            "name": comp_name,
                            "description": comp.get("description", ""),
                            "category": comp.get("category", ""),
                            "occurrences": [],
                            "average_progress": 0,
                            "current_level": None,
                            "goals": []
                        }
                    
                    comp_data = competency_map[comp_name]
                    comp_data["occurrences"].append({
                        "level": comp.get("level"),
                        "progress": goal_progress,
                        "goal_uid": brain.UID,
                        "goal_title": brain.Title
                    })
                    
                    comp_data["goals"].append({
                        "uid": brain.UID,
                        "title": brain.Title,
                        "url": brain.getURL(),
                        "progress": goal_progress
                    })
                    
            except:
                continue
        
        # Calculate competency levels and progress
        competency_list = []
        
        for comp_name, comp_data in competency_map.items():
            occurrences = comp_data["occurrences"]
            
            if occurrences:
                # Calculate average progress
                total_progress = sum(occ["progress"] for occ in occurrences)
                comp_data["average_progress"] = round(total_progress / len(occurrences), 1)
                
                # Determine current level (from most progressed occurrence)
                best_occurrence = max(occurrences, key=lambda x: x["progress"])
                comp_data["current_level"] = best_occurrence["level"]
                
                # Remove occurrences from final output
                del comp_data["occurrences"]
                
                competency_list.append(comp_data)
        
        # Sort by average progress
        competency_list.sort(key=lambda x: x["average_progress"], reverse=True)
        
        # Group by category
        by_category = {}
        for comp in competency_list:
            category = comp["category"] or "Uncategorized"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(comp)
        
        return {
            "competencies": competency_list,
            "by_category": by_category,
            "total_competencies": len(competency_list),
            "mastered": sum(1 for c in competency_list if c["average_progress"] >= 80),
            "in_progress": sum(1 for c in competency_list if 20 <= c["average_progress"] < 80),
            "beginner": sum(1 for c in competency_list if c["average_progress"] < 20)
        }

    def get_objectives(self):
        """Get learning objectives and their progress."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        # Get all learning goals
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        all_objectives = []
        
        for brain in goals:
            try:
                obj = brain.getObject()
                objectives = getattr(obj, "learning_objectives", [])
                goal_progress = getattr(obj, "progress", 0)
                
                for obj_data in objectives:
                    enriched_obj = dict(obj_data)
                    enriched_obj["goal_uid"] = brain.UID
                    enriched_obj["goal_title"] = brain.Title
                    enriched_obj["goal_url"] = brain.getURL()
                    enriched_obj["goal_progress"] = goal_progress
                    
                    # Calculate SMART score
                    smart_score = 0
                    if obj_data.get("measurable"):
                        smart_score += 1
                    if obj_data.get("achievable"):
                        smart_score += 1
                    if obj_data.get("relevant"):
                        smart_score += 1
                    if obj_data.get("time_bound"):
                        smart_score += 1
                    
                    enriched_obj["smart_score"] = smart_score
                    enriched_obj["is_smart"] = smart_score == 4
                    
                    all_objectives.append(enriched_obj)
                    
            except:
                continue
        
        # Filter by SMART criteria if requested
        smart_only = self.request.get("smart_only", "false").lower() == "true"
        if smart_only:
            all_objectives = [obj for obj in all_objectives if obj["is_smart"]]
        
        # Sort by priority
        all_objectives.sort(key=lambda x: x.get("priority", 10))
        
        return {
            "objectives": all_objectives,
            "count": len(all_objectives),
            "smart_objectives": sum(1 for obj in all_objectives if obj["is_smart"]),
            "average_smart_score": round(
                sum(obj["smart_score"] for obj in all_objectives) / len(all_objectives), 2
            ) if all_objectives else 0
        }

    def check_prerequisites(self):
        """Check prerequisites for a specific learning goal."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        goal_uid = self.request.get("goal_uid")
        if not goal_uid:
            self.request.response.setStatus(400)
            return {"error": "goal_uid is required"}

        catalog = api.portal.get_tool("portal_catalog")
        
        # Get the goal
        goal_brain = catalog(UID=goal_uid)
        if not goal_brain:
            self.request.response.setStatus(404)
            return {"error": "Goal not found"}

        goal_obj = goal_brain[0].getObject()
        prerequisites = getattr(goal_obj, "prerequisite_knowledge", [])
        
        if not prerequisites:
            return {
                "goal_uid": goal_uid,
                "prerequisites": [],
                "all_met": True,
                "can_start": True
            }
        
        # Check each prerequisite
        prereq_status = []
        all_met = True
        
        for prereq_uid in prerequisites:
            prereq_brain = catalog(UID=prereq_uid)
            if prereq_brain:
                brain = prereq_brain[0]
                obj = brain.getObject()
                progress = 0
                
                if brain.portal_type == "LearningGoal":
                    progress = getattr(obj, "progress", 0)
                elif brain.portal_type == "ResearchNote":
                    # Consider research notes as complete if they exist
                    progress = 100
                
                is_met = progress >= 80  # 80% threshold for prerequisites
                if not is_met:
                    all_met = False
                
                prereq_status.append({
                    "uid": prereq_uid,
                    "title": brain.Title,
                    "type": brain.portal_type,
                    "url": brain.getURL(),
                    "progress": progress,
                    "is_met": is_met
                })
            else:
                # Prerequisite not found
                all_met = False
                prereq_status.append({
                    "uid": prereq_uid,
                    "title": "Unknown prerequisite",
                    "type": "unknown",
                    "url": None,
                    "progress": 0,
                    "is_met": False,
                    "error": "Prerequisite not found"
                })
        
        return {
            "goal_uid": goal_uid,
            "prerequisites": prereq_status,
            "all_met": all_met,
            "can_start": all_met,
            "met_count": sum(1 for p in prereq_status if p["is_met"]),
            "total_count": len(prereq_status)
        }

    def get_recommendations(self):
        """Get learning recommendations based on current progress and gaps."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()
        
        recommendations = {
            "next_goals": [],
            "skill_gaps": [],
            "review_needed": [],
            "milestone_suggestions": []
        }
        
        # Get current learning state
        goals = catalog(
            Creator=user.getId(),
            portal_type="LearningGoal"
        )
        
        notes = catalog(
            Creator=user.getId(),
            portal_type="ResearchNote"
        )
        
        # Analyze current progress
        active_goals = []
        completed_goals = []
        difficulty_levels = []
        
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                
                if progress >= 100:
                    completed_goals.append(brain)
                elif progress > 0:
                    active_goals.append({
                        "brain": brain,
                        "progress": progress,
                        "difficulty": getattr(obj, "difficulty_level", "intermediate")
                    })
                
                difficulty_levels.append(getattr(obj, "difficulty_level", "intermediate"))
                
            except:
                continue
        
        # Recommend next goals based on prerequisites met
        all_goal_uids = set(brain.UID for brain in goals)
        completed_uids = set(brain.UID for brain in completed_goals)
        
        for brain in goals:
            try:
                obj = brain.getObject()
                progress = getattr(obj, "progress", 0)
                
                if progress == 0:  # Not started
                    prerequisites = getattr(obj, "prerequisite_knowledge", [])
                    prereqs_met = all(
                        prereq in completed_uids or prereq not in all_goal_uids
                        for prereq in prerequisites
                    )
                    
                    if prereqs_met:
                        recommendations["next_goals"].append({
                            "uid": brain.UID,
                            "title": brain.Title,
                            "url": brain.getURL(),
                            "difficulty": getattr(obj, "difficulty_level", "intermediate"),
                            "estimated_effort": getattr(obj, "estimated_effort", 0),
                            "reason": "All prerequisites completed"
                        })
                
            except:
                continue
        
        # Sort next goals by difficulty and estimated effort
        recommendations["next_goals"].sort(
            key=lambda x: (
                {"beginner": 0, "intermediate": 1, "advanced": 2}.get(x["difficulty"], 1),
                x["estimated_effort"]
            )
        )
        
        # Identify skill gaps based on knowledge graph
        if hasattr(self.context, "suggested_relationships"):
            for sug in self.context.suggested_relationships:
                if not sug.get("is_accepted") and sug.get("suggestion_reason"):
                    recommendations["skill_gaps"].append({
                        "area": sug.get("suggestion_reason", ""),
                        "confidence": sug.get("confidence", 0.5),
                        "related_content": sug.get("target_uid")
                    })
        
        # Identify content needing review (based on last review date)
        review_threshold = datetime.now() - timedelta(days=30)
        
        for brain in notes:
            try:
                if brain.modified.asdatetime() < review_threshold:
                    obj = brain.getObject()
                    confidence = getattr(obj, "confidence_score", 0.5)
                    
                    if confidence < 0.8:
                        recommendations["review_needed"].append({
                            "uid": brain.UID,
                            "title": brain.Title,
                            "url": brain.getURL(),
                            "last_review": brain.modified.ISO8601(),
                            "confidence": confidence,
                            "days_since_review": (datetime.now() - brain.modified.asdatetime()).days
                        })
            except:
                continue
        
        # Sort review needed by confidence (lowest first)
        recommendations["review_needed"].sort(key=lambda x: x["confidence"])
        
        # Milestone suggestions for active goals
        for active in active_goals[:3]:  # Top 3 active goals
            brain = active["brain"]
            progress = active["progress"]
            
            if progress < 25:
                suggestion = "Set up initial learning resources and create first milestone"
            elif progress < 50:
                suggestion = "Complete foundational concepts and assess understanding"
            elif progress < 75:
                suggestion = "Apply knowledge in practical exercises"
            else:
                suggestion = "Finalize project and document learnings"
            
            recommendations["milestone_suggestions"].append({
                "goal_uid": brain.UID,
                "goal_title": brain.Title,
                "current_progress": progress,
                "suggestion": suggestion
            })
        
        return recommendations

    def create_milestone(self):
        """Create a new milestone for a learning goal."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        data = json.loads(self.request.body)
        goal_uid = data.get("goal_uid")
        
        if not goal_uid:
            self.request.response.setStatus(400)
            return {"error": "goal_uid is required"}

        # Get the goal
        catalog = api.portal.get_tool("portal_catalog")
        goal_brain = catalog(UID=goal_uid)
        
        if not goal_brain:
            self.request.response.setStatus(404)
            return {"error": "Goal not found"}

        goal_obj = goal_brain[0].getObject()
        
        # Create milestone
        import uuid
        new_milestone = {
            "id": str(uuid.uuid4()),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "target_date": data.get("target_date"),
            "status": data.get("status", "not_started"),
            "progress_percentage": data.get("progress_percentage", 0),
            "completion_criteria": data.get("completion_criteria", ""),
            "created": datetime.now().isoformat()
        }
        
        # Validate required fields
        if not new_milestone["title"]:
            self.request.response.setStatus(400)
            return {"error": "Milestone title is required"}
        
        # Add milestone to goal
        milestones = list(getattr(goal_obj, "milestones", []))
        milestones.append(new_milestone)
        goal_obj.milestones = milestones
        goal_obj.reindexObject()
        
        return {
            "status": "created",
            "milestone": new_milestone,
            "goal_uid": goal_uid
        }

    def update_milestone(self):
        """Update an existing milestone."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        data = json.loads(self.request.body)
        goal_uid = data.get("goal_uid")
        milestone_id = data.get("milestone_id")
        
        if not goal_uid or not milestone_id:
            self.request.response.setStatus(400)
            return {"error": "goal_uid and milestone_id are required"}

        # Get the goal
        catalog = api.portal.get_tool("portal_catalog")
        goal_brain = catalog(UID=goal_uid)
        
        if not goal_brain:
            self.request.response.setStatus(404)
            return {"error": "Goal not found"}

        goal_obj = goal_brain[0].getObject()
        
        # Find and update milestone
        milestones = list(getattr(goal_obj, "milestones", []))
        updated = False
        
        for milestone in milestones:
            if milestone.get("id") == milestone_id:
                # Update fields
                if "title" in data:
                    milestone["title"] = data["title"]
                if "description" in data:
                    milestone["description"] = data["description"]
                if "target_date" in data:
                    milestone["target_date"] = data["target_date"]
                if "status" in data:
                    milestone["status"] = data["status"]
                    # Set completed date if status is completed
                    if data["status"] == "completed" and not milestone.get("completed_date"):
                        milestone["completed_date"] = datetime.now().isoformat()
                if "progress_percentage" in data:
                    milestone["progress_percentage"] = data["progress_percentage"]
                if "completion_criteria" in data:
                    milestone["completion_criteria"] = data["completion_criteria"]
                
                milestone["modified"] = datetime.now().isoformat()
                updated = True
                break
        
        if not updated:
            self.request.response.setStatus(404)
            return {"error": "Milestone not found"}
        
        goal_obj.milestones = milestones
        goal_obj.reindexObject()
        
        return {"status": "updated"}

    def create_objective(self):
        """Create a new learning objective."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        data = json.loads(self.request.body)
        goal_uid = data.get("goal_uid")
        
        if not goal_uid:
            self.request.response.setStatus(400)
            return {"error": "goal_uid is required"}

        # Get the goal
        catalog = api.portal.get_tool("portal_catalog")
        goal_brain = catalog(UID=goal_uid)
        
        if not goal_brain:
            self.request.response.setStatus(404)
            return {"error": "Goal not found"}

        goal_obj = goal_brain[0].getObject()
        
        # Create objective
        import uuid
        new_objective = {
            "id": str(uuid.uuid4()),
            "objective_text": data.get("objective_text", ""),
            "measurable": data.get("measurable", False),
            "achievable": data.get("achievable", False),
            "relevant": data.get("relevant", False),
            "time_bound": data.get("time_bound", False),
            "success_metrics": data.get("success_metrics", []),
            "priority": data.get("priority", 5),
            "created": datetime.now().isoformat()
        }
        
        # Validate required fields
        if not new_objective["objective_text"]:
            self.request.response.setStatus(400)
            return {"error": "Objective text is required"}
        
        # Add objective to goal
        objectives = list(getattr(goal_obj, "learning_objectives", []))
        objectives.append(new_objective)
        goal_obj.learning_objectives = objectives
        goal_obj.reindexObject()
        
        return {
            "status": "created",
            "objective": new_objective,
            "goal_uid": goal_uid
        }

    def update_objective(self):
        """Update an existing learning objective."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        data = json.loads(self.request.body)
        goal_uid = data.get("goal_uid")
        objective_id = data.get("objective_id")
        
        if not goal_uid or not objective_id:
            self.request.response.setStatus(400)
            return {"error": "goal_uid and objective_id are required"}

        # Get the goal
        catalog = api.portal.get_tool("portal_catalog")
        goal_brain = catalog(UID=goal_uid)
        
        if not goal_brain:
            self.request.response.setStatus(404)
            return {"error": "Goal not found"}

        goal_obj = goal_brain[0].getObject()
        
        # Find and update objective
        objectives = list(getattr(goal_obj, "learning_objectives", []))
        updated = False
        
        for objective in objectives:
            if objective.get("id") == objective_id:
                # Update fields
                if "objective_text" in data:
                    objective["objective_text"] = data["objective_text"]
                if "measurable" in data:
                    objective["measurable"] = data["measurable"]
                if "achievable" in data:
                    objective["achievable"] = data["achievable"]
                if "relevant" in data:
                    objective["relevant"] = data["relevant"]
                if "time_bound" in data:
                    objective["time_bound"] = data["time_bound"]
                if "success_metrics" in data:
                    objective["success_metrics"] = data["success_metrics"]
                if "priority" in data:
                    objective["priority"] = data["priority"]
                
                objective["modified"] = datetime.now().isoformat()
                updated = True
                break
        
        if not updated:
            self.request.response.setStatus(404)
            return {"error": "Objective not found"}
        
        goal_obj.learning_objectives = objectives
        goal_obj.reindexObject()
        
        return {"status": "updated"}

    def assess_competency(self):
        """Assess or update a competency level."""
        if not api.user.has_permission("Modify portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        data = json.loads(self.request.body)
        goal_uid = data.get("goal_uid")
        competency_name = data.get("competency_name")
        
        if not goal_uid or not competency_name:
            self.request.response.setStatus(400)
            return {"error": "goal_uid and competency_name are required"}

        # Get the goal
        catalog = api.portal.get_tool("portal_catalog")
        goal_brain = catalog(UID=goal_uid)
        
        if not goal_brain:
            self.request.response.setStatus(404)
            return {"error": "Goal not found"}

        goal_obj = goal_brain[0].getObject()
        
        # Find or create competency
        competencies = list(getattr(goal_obj, "competencies", []))
        competency = None
        
        for comp in competencies:
            if comp.get("name") == competency_name:
                competency = comp
                break
        
        if not competency:
            # Create new competency
            competency = {
                "name": competency_name,
                "description": data.get("description", ""),
                "level": data.get("level", "beginner"),
                "category": data.get("category", ""),
                "assessed_date": datetime.now().isoformat()
            }
            competencies.append(competency)
        else:
            # Update existing competency
            if "level" in data:
                competency["level"] = data["level"]
            if "description" in data:
                competency["description"] = data["description"]
            if "category" in data:
                competency["category"] = data["category"]
            competency["assessed_date"] = datetime.now().isoformat()
        
        goal_obj.competencies = competencies
        goal_obj.reindexObject()
        
        return {
            "status": "assessed",
            "competency": competency,
            "goal_uid": goal_uid
        }