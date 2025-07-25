"""Custom serializers for knowledge content types."""

from knowledge.curator.interfaces import IBookmarkPlus
from knowledge.curator.interfaces import IKnowledgeItem
from knowledge.curator.interfaces import ILearningGoal
from knowledge.curator.interfaces import IProjectLog
from knowledge.curator.interfaces import IResearchNote
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(IResearchNote, Interface)
class ResearchNoteSerializer(SerializeFolderToJson):
    """Serializer for Research Note content type."""

    def __call__(self, version=None, include_items=True):
        result = super().__call__(version, include_items)

        # Add custom fields
        obj = self.context

        # Include embedding vector if requested
        include_embeddings = (
            self.request.get("include_embeddings", "false").lower() == "true"
        )

        result["content"] = obj.content.raw if hasattr(obj, "content") else ""
        result["source_url"] = getattr(obj, "source_url", "")
        result["ai_summary"] = getattr(obj, "ai_summary", "")
        
        # Serialize structured key insights
        key_insights = getattr(obj, "key_insights", [])
        result["key_insights"] = [
            {
                "text": insight.get("text", ""),
                "importance": insight.get("importance", "medium"),
                "evidence": insight.get("evidence", ""),
                "timestamp": insight.get("timestamp").isoformat() if insight.get("timestamp") else None
            }
            for insight in key_insights
        ]
        
        # Serialize structured relationships
        relationships = getattr(obj, "relationships", [])
        result["relationships"] = [
            {
                "source_uid": rel.get("source_uid"),
                "target_uid": rel.get("target_uid"),
                "relationship_type": rel.get("relationship_type", "related"),
                "strength": rel.get("strength", 0.5),
                "metadata": rel.get("metadata", {}),
                "created": rel.get("created"),
                "confidence": rel.get("confidence", 1.0)
            }
            for rel in relationships
        ]
        
        # Serialize authors
        authors = getattr(obj, "authors", [])
        result["authors"] = [
            {
                "name": author.get("name", ""),
                "email": author.get("email", ""),
                "orcid": author.get("orcid", ""),
                "affiliation": author.get("affiliation", "")
            }
            for author in authors
        ]
        
        # Additional research fields
        result["research_method"] = getattr(obj, "research_method", "")
        result["citation_format"] = getattr(obj, "citation_format", "APA")
        result["builds_upon"] = getattr(obj, "builds_upon", [])
        result["contradicts"] = getattr(obj, "contradicts", [])
        result["peer_reviewed"] = getattr(obj, "peer_reviewed", False)
        result["replication_studies"] = getattr(obj, "replication_studies", [])
        
        # Bibliographic metadata
        result["publication_date"] = getattr(obj, "publication_date", None)
        if result["publication_date"]:
            result["publication_date"] = result["publication_date"].isoformat()
        result["doi"] = getattr(obj, "doi", "")
        result["isbn"] = getattr(obj, "isbn", "")
        result["journal_name"] = getattr(obj, "journal_name", "")
        result["volume_issue"] = getattr(obj, "volume_issue", "")
        result["page_numbers"] = getattr(obj, "page_numbers", "")
        result["publisher"] = getattr(obj, "publisher", "")
        result["citation_format"] = getattr(obj, "citation_format", "")
        
        # Learning metadata
        result["difficulty_level"] = getattr(obj, "difficulty_level", "intermediate")
        result["cognitive_load"] = getattr(obj, "cognitive_load", "medium")
        result["learning_style"] = getattr(obj, "learning_style", [])
        result["knowledge_status"] = getattr(obj, "knowledge_status", "draft")
        result["last_reviewed"] = getattr(obj, "last_reviewed", None)
        if result["last_reviewed"]:
            result["last_reviewed"] = result["last_reviewed"].isoformat()
        result["review_frequency"] = getattr(obj, "review_frequency", 30)
        result["confidence_score"] = getattr(obj, "confidence_score", 0.5)
        
        # Backwards compatibility - connections field
        result["connections"] = getattr(obj, "connections", [])

        if include_embeddings and hasattr(obj, "embedding_vector"):
            result["embedding_vector"] = getattr(obj, "embedding_vector", [])

        # Add connection details
        if result["connections"]:
            catalog = api.portal.get_tool("portal_catalog")
            connection_details = []

            for uid in result["connections"]:
                brains = catalog(UID=uid)
                if brains:
                    brain = brains[0]
                    connection_details.append({
                        "uid": uid,
                        "title": brain.Title,
                        "portal_type": brain.portal_type,
                        "url": brain.getURL(),
                    })

            result["connection_details"] = connection_details

        # Add spaced repetition data if available
        if hasattr(obj, "_sr_data"):
            sr_data = obj._sr_data
            result["spaced_repetition"] = {
                "interval": sr_data.get("interval"),
                "repetitions": sr_data.get("repetitions"),
                "ease_factor": sr_data.get("ease_factor"),
                "last_review": sr_data.get("last_review", "").isoformat()
                if sr_data.get("last_review")
                else None,
                "next_review": sr_data.get("next_review", "").isoformat()
                if sr_data.get("next_review")
                else None,
            }

        return result


@implementer(ISerializeToJson)
@adapter(ILearningGoal, Interface)
class LearningGoalSerializer(SerializeFolderToJson):
    """Serializer for Learning Goal content type."""

    def __call__(self, version=None, include_items=True):
        result = super().__call__(version, include_items)

        obj = self.context

        result["target_date"] = getattr(obj, "target_date", None)
        if result["target_date"]:
            result["target_date"] = result["target_date"].isoformat()

        result["progress"] = getattr(obj, "progress", 0)
        result["priority"] = getattr(obj, "priority", "medium")
        result["reflection"] = getattr(obj, "reflection", "")
        result["related_notes"] = getattr(obj, "related_notes", [])
        
        # Serialize structured milestones
        milestones = getattr(obj, "milestones", [])
        result["milestones"] = [
            {
                "id": milestone.get("id", ""),
                "title": milestone.get("title", ""),
                "description": milestone.get("description", ""),
                "target_date": milestone.get("target_date").isoformat() if milestone.get("target_date") and hasattr(milestone.get("target_date"), 'isoformat') else milestone.get("target_date"),
                "status": milestone.get("status", "not_started"),
                "progress_percentage": milestone.get("progress_percentage", 0),
                "completion_criteria": milestone.get("completion_criteria", "")
            }
            for milestone in milestones
        ]
        
        # Serialize learning objectives
        objectives = getattr(obj, "learning_objectives", [])
        result["learning_objectives"] = [
            {
                "objective_text": obj_data.get("objective_text", ""),
                "measurable": obj_data.get("measurable", False),
                "achievable": obj_data.get("achievable", False),
                "relevant": obj_data.get("relevant", False),
                "time_bound": obj_data.get("time_bound", False),
                "success_metrics": obj_data.get("success_metrics", [])
            }
            for obj_data in objectives
        ]
        
        # Serialize competencies
        competencies = getattr(obj, "competencies", [])
        result["competencies"] = [
            {
                "name": comp.get("name", ""),
                "description": comp.get("description", ""),
                "level": comp.get("level", "beginner"),
                "category": comp.get("category", "")
            }
            for comp in competencies
        ]
        
        # Serialize assessment criteria
        criteria = getattr(obj, "assessment_criteria", [])
        result["assessment_criteria"] = [
            {
                "criterion": crit.get("criterion", ""),
                "weight": crit.get("weight", 1.0),
                "description": crit.get("description", "")
            }
            for crit in criteria
        ]
        
        # Additional learning fields
        result["prerequisite_knowledge"] = getattr(obj, "prerequisite_knowledge", [])
        result["learning_approach"] = getattr(obj, "learning_approach", "")
        result["estimated_effort"] = getattr(obj, "estimated_effort", 0)

        # Add related note details
        if result["related_notes"]:
            catalog = api.portal.get_tool("portal_catalog")
            note_details = []

            for uid in result["related_notes"]:
                brains = catalog(UID=uid)
                if brains:
                    brain = brains[0]
                    note_details.append({
                        "uid": uid,
                        "title": brain.Title,
                        "portal_type": brain.portal_type,
                        "url": brain.getURL(),
                    })

            result["related_note_details"] = note_details

        # Calculate time to target
        if result["target_date"]:
            from datetime import date
            from datetime import datetime

            target = datetime.fromisoformat(result["target_date"]).date()
            today = date.today()
            days_remaining = (target - today).days
            result["days_remaining"] = days_remaining
            result["is_overdue"] = days_remaining < 0

        return result


@implementer(ISerializeToJson)
@adapter(IProjectLog, Interface)
class ProjectLogSerializer(SerializeFolderToJson):
    """Serializer for Project Log content type."""

    def __call__(self, version=None, include_items=True):
        result = super().__call__(version, include_items)

        obj = self.context

        result["start_date"] = getattr(obj, "start_date", None)
        if result["start_date"]:
            result["start_date"] = result["start_date"].isoformat()

        result["learnings"] = getattr(obj, "learnings", "")
        result["status"] = getattr(obj, "status", "planning")
        
        # Serialize structured entries
        entries = getattr(obj, "entries", [])
        result["entries"] = [
            {
                "id": entry.get("id", ""),
                "timestamp": entry.get("timestamp").isoformat() if entry.get("timestamp") and hasattr(entry.get("timestamp"), 'isoformat') else entry.get("timestamp"),
                "author": entry.get("author", ""),
                "entry_type": entry.get("entry_type", ""),
                "description": entry.get("description", ""),
                "related_items": entry.get("related_items", [])
            }
            for entry in entries
        ]
        
        # Serialize deliverables
        deliverables = getattr(obj, "deliverables", [])
        result["deliverables"] = [
            {
                "title": deliv.get("title", ""),
                "description": deliv.get("description", ""),
                "due_date": deliv.get("due_date").isoformat() if deliv.get("due_date") and hasattr(deliv.get("due_date"), 'isoformat') else deliv.get("due_date"),
                "status": deliv.get("status", ""),
                "assigned_to": deliv.get("assigned_to", ""),
                "completion_percentage": deliv.get("completion_percentage", 0)
            }
            for deliv in deliverables
        ]
        
        # Serialize stakeholders
        stakeholders = getattr(obj, "stakeholders", [])
        result["stakeholders"] = [
            {
                "name": stake.get("name", ""),
                "role": stake.get("role", ""),
                "interest_level": stake.get("interest_level", ""),
                "influence_level": stake.get("influence_level", ""),
                "contact_info": stake.get("contact_info", "")
            }
            for stake in stakeholders
        ]
        
        # Serialize resources
        resources = getattr(obj, "resources_used", [])
        result["resources_used"] = [
            {
                "resource_type": res.get("resource_type", ""),
                "name": res.get("name", ""),
                "quantity": res.get("quantity", 0),
                "availability": res.get("availability", ""),
                "cost": res.get("cost", 0)
            }
            for res in resources
        ]
        
        # Serialize success metrics
        metrics = getattr(obj, "success_metrics", [])
        result["success_metrics"] = [
            {
                "metric_name": metric.get("metric_name", ""),
                "target_value": metric.get("target_value", ""),
                "current_value": metric.get("current_value", ""),
                "unit": metric.get("unit", ""),
                "measurement_method": metric.get("measurement_method", "")
            }
            for metric in metrics
        ]
        
        # Serialize lessons learned
        lessons = getattr(obj, "lessons_learned", [])
        result["lessons_learned"] = [
            {
                "lesson": lesson.get("lesson", ""),
                "context": lesson.get("context", ""),
                "impact": lesson.get("impact", ""),
                "recommendations": lesson.get("recommendations", "")
            }
            for lesson in lessons
        ]
        
        # Additional project fields
        result["project_methodology"] = getattr(obj, "project_methodology", "")

        # Calculate project duration
        if result["start_date"]:
            from datetime import date
            from datetime import datetime

            start = datetime.fromisoformat(result["start_date"]).date()
            today = date.today()
            result["duration_days"] = (today - start).days

        # Add entry count and latest entry
        result["entry_count"] = len(result["entries"])
        if result["entries"]:
            # Sort entries by timestamp
            sorted_entries = sorted(
                result["entries"], key=lambda x: x.get("timestamp", ""), reverse=True
            )
            result["latest_entry"] = sorted_entries[0]

        return result


@implementer(ISerializeToJson)
@adapter(IBookmarkPlus, Interface)
class BookmarkPlusSerializer(SerializeFolderToJson):
    """Serializer for BookmarkPlus content type."""

    def __call__(self, version=None, include_items=True):
        result = super().__call__(version, include_items)

        obj = self.context

        # Include embedding vector if requested
        include_embeddings = (
            self.request.get("include_embeddings", "false").lower() == "true"
        )

        result["url"] = getattr(obj, "url", "")
        result["notes"] = obj.notes.raw if hasattr(obj, "notes") else ""
        result["read_status"] = getattr(obj, "read_status", "unread")
        result["importance"] = getattr(obj, "importance", "medium")
        result["ai_summary"] = getattr(obj, "ai_summary", "")

        if include_embeddings and hasattr(obj, "embedding_vector"):
            result["embedding_vector"] = getattr(obj, "embedding_vector", [])

        # Add spaced repetition data if available
        if hasattr(obj, "_sr_data"):
            sr_data = obj._sr_data
            result["spaced_repetition"] = {
                "interval": sr_data.get("interval"),
                "repetitions": sr_data.get("repetitions"),
                "ease_factor": sr_data.get("ease_factor"),
                "last_review": sr_data.get("last_review", "").isoformat()
                if sr_data.get("last_review")
                else None,
                "next_review": sr_data.get("next_review", "").isoformat()
                if sr_data.get("next_review")
                else None,
            }

        # Add domain info from URL
        if result["url"]:
            from urllib.parse import urlparse

            parsed = urlparse(result["url"])
            result["domain"] = parsed.netloc

        return result


@implementer(ISerializeToJson)
@adapter(IKnowledgeItem, Interface)
class KnowledgeItemSerializer(SerializeFolderToJson):
    """Serializer for Knowledge Item content type."""

    def __call__(self, version=None, include_items=True):
        result = super().__call__(version, include_items)

        obj = self.context

        # Include embedding vector if requested
        include_embeddings = (
            self.request.get("include_embeddings", "false").lower() == "true"
        )

        # Core fields
        result["content"] = obj.content.raw if hasattr(obj, "content") else ""
        result["knowledge_type"] = getattr(obj, "knowledge_type", "")
        result["atomic_concepts"] = getattr(obj, "atomic_concepts", [])
        result["source_url"] = getattr(obj, "source_url", "")
        result["ai_summary"] = getattr(obj, "ai_summary", "")
        result["relevance_score"] = getattr(obj, "relevance_score", 0.0)
        
        # Learning integration fields
        result["mastery_threshold"] = getattr(obj, "mastery_threshold", 0.8)
        result["learning_progress"] = getattr(obj, "learning_progress", 0.0)
        result["last_reviewed"] = getattr(obj, "last_reviewed", None)
        if result["last_reviewed"]:
            result["last_reviewed"] = result["last_reviewed"].isoformat()
        result["difficulty_level"] = getattr(obj, "difficulty_level", "intermediate")
        
        # Relationship fields
        result["prerequisite_items"] = getattr(obj, "prerequisite_items", [])
        result["enables_items"] = getattr(obj, "enables_items", [])
        
        # Include embedding vector if requested
        if include_embeddings and hasattr(obj, "embedding_vector"):
            result["embedding_vector"] = getattr(obj, "embedding_vector", [])

        # Add prerequisite details
        if result["prerequisite_items"]:
            catalog = api.portal.get_tool("portal_catalog")
            prerequisite_details = []

            for uid in result["prerequisite_items"]:
                brains = catalog(UID=uid)
                if brains:
                    brain = brains[0]
                    prerequisite_details.append({
                        "uid": uid,
                        "title": brain.Title,
                        "portal_type": brain.portal_type,
                        "url": brain.getURL(),
                    })

            result["prerequisite_details"] = prerequisite_details

        # Add enabled item details
        if result["enables_items"]:
            catalog = api.portal.get_tool("portal_catalog")
            enabled_details = []

            for uid in result["enables_items"]:
                brains = catalog(UID=uid)
                if brains:
                    brain = brains[0]
                    enabled_details.append({
                        "uid": uid,
                        "title": brain.Title,
                        "portal_type": brain.portal_type,
                        "url": brain.getURL(),
                    })

            result["enabled_details"] = enabled_details

        # Add attachment info if present
        if hasattr(obj, "attachment") and obj.attachment:
            result["has_attachment"] = True
            result["attachment_filename"] = obj.attachment.filename
            result["attachment_size"] = obj.attachment.size
            result["attachment_content_type"] = obj.attachment.contentType

        # Add spaced repetition data if available
        if hasattr(obj, "_sr_data"):
            sr_data = obj._sr_data
            result["spaced_repetition"] = {
                "interval": sr_data.get("interval"),
                "repetitions": sr_data.get("repetitions"),
                "ease_factor": sr_data.get("ease_factor"),
                "last_review": sr_data.get("last_review", "").isoformat()
                if sr_data.get("last_review")
                else None,
                "next_review": sr_data.get("next_review", "").isoformat()
                if sr_data.get("next_review")
                else None,
            }

        # Calculate mastery status
        progress = result["learning_progress"]
        threshold = result["mastery_threshold"]
        result["is_mastered"] = progress >= threshold

        return result
