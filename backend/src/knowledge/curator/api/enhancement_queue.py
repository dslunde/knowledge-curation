"""Enhancement Queue API endpoints."""

from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from knowledge.curator.workflow_scripts import (
    queue_for_enhancement,
    get_enhancement_queue,
    process_enhancement_queue,
    get_queue_statistics,
    calculate_enhancement_priority
)
import json


@implementer(IPublishTraverse)
class EnhancementQueueService(Service):
    """Service for enhancement queue operations."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if len(self.params) == 0:
            # List queue items
            if self.request.method == "GET":
                return self.get_queue()
            elif self.request.method == "POST":
                return self.add_to_queue()
            else:
                self.request.response.setStatus(405)
                return {"error": "Method not allowed"}
        
        action = self.params[0]
        
        if action == "process":
            return self.process_queue()
        elif action == "stats":
            return self.get_stats()
        elif action == "priority":
            return self.get_priority_info()
        elif action == "clear":
            return self.clear_queue()
        else:
            self.request.response.setStatus(404)
            return {"error": f"Unknown action: {action}"}

    def get_queue(self):
        """Get enhancement queue items."""
        limit = int(self.request.get("limit", 50))
        content_type = self.request.get("content_type", None)
        min_priority = self.request.get("min_priority", None)
        
        if min_priority:
            min_priority = float(min_priority)
        
        items = get_enhancement_queue(limit=limit, min_priority=min_priority)
        
        # Filter by content type if specified
        if content_type:
            items = [item for item in items if item.get("portal_type") == content_type]
        
        # Separate Knowledge Items for visibility
        knowledge_items = [item for item in items if item.get("portal_type") == "KnowledgeItem"]
        other_items = [item for item in items if item.get("portal_type") != "KnowledgeItem"]
        
        return {
            "total": len(items),
            "knowledge_items": {
                "count": len(knowledge_items),
                "items": knowledge_items
            },
            "other_items": {
                "count": len(other_items),
                "items": other_items
            },
            "limit": limit,
            "filters": {
                "content_type": content_type,
                "min_priority": min_priority
            }
        }

    def add_to_queue(self):
        """Add items to enhancement queue."""
        data = json.loads(self.request.get("BODY", "{}"))
        uids = data.get("uids", [])
        operation = data.get("operation", "full")
        priority_boost = data.get("priority_boost", 1.0)
        
        if not uids:
            self.request.response.setStatus(400)
            return {"error": "No UIDs provided"}
        
        results = {"queued": [], "errors": []}
        
        # Process Knowledge Items first with priority
        for uid in uids:
            try:
                obj = api.content.get(UID=uid)
                if not obj:
                    results["errors"].append({
                        "uid": uid,
                        "error": "Object not found"
                    })
                    continue
                
                # Check permissions
                if not api.user.has_permission("Modify portal content", obj=obj):
                    results["errors"].append({
                        "uid": uid,
                        "error": "Insufficient permissions"
                    })
                    continue
                
                # Calculate priority with boost for Knowledge Items
                base_priority = calculate_enhancement_priority(obj)
                if obj.portal_type == "KnowledgeItem":
                    priority = base_priority * priority_boost * 1.5  # Extra boost
                else:
                    priority = base_priority * priority_boost
                
                entry = queue_for_enhancement(
                    obj,
                    operation=operation,
                    priority_override=priority
                )
                
                results["queued"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "portal_type": obj.portal_type,
                    "priority": entry["priority"],
                    "operation": operation
                })
                
            except Exception as e:
                results["errors"].append({
                    "uid": uid,
                    "error": str(e)
                })
        
        return {
            "success": len(results["queued"]),
            "failed": len(results["errors"]),
            "results": results
        }

    def process_queue(self):
        """Process items from the queue."""
        if self.request.method != "POST":
            self.request.response.setStatus(405)
            return {"error": "Method not allowed"}
        
        data = json.loads(self.request.get("BODY", "{}"))
        batch_size = data.get("batch_size", 10)
        content_type = data.get("content_type", None)
        
        # Ensure Knowledge Items are processed with priority
        if content_type != "KnowledgeItem":
            # Process some Knowledge Items first
            ki_batch = max(1, batch_size // 3)  # At least 1/3 for Knowledge Items
            ki_processed = process_enhancement_queue(
                batch_size=ki_batch,
                content_type_filter="KnowledgeItem"
            )
            
            # Process remaining batch with specified type
            remaining_batch = batch_size - len(ki_processed)
            other_processed = process_enhancement_queue(
                batch_size=remaining_batch,
                content_type_filter=content_type
            )
            
            processed = ki_processed + other_processed
        else:
            # Process only Knowledge Items
            processed = process_enhancement_queue(
                batch_size=batch_size,
                content_type_filter="KnowledgeItem"
            )
        
        return {
            "processed": len(processed),
            "items": [
                {
                    "uid": item["uid"],
                    "title": item["title"],
                    "portal_type": item["portal_type"],
                    "priority": item["priority"]
                }
                for item in processed
            ]
        }

    def get_stats(self):
        """Get enhancement queue statistics."""
        stats = get_queue_statistics()
        
        # Add processing recommendations
        recommendations = []
        
        if stats["knowledge_items"] > 10:
            recommendations.append({
                "type": "warning",
                "message": f"{stats['knowledge_items']} Knowledge Items pending enhancement",
                "action": "Process Knowledge Items with priority"
            })
        
        if stats["average_priority"] > 75:
            recommendations.append({
                "type": "alert",
                "message": "High average priority indicates urgent processing needed",
                "action": "Increase batch processing frequency"
            })
        
        if stats.get("oldest_item"):
            recommendations.append({
                "type": "info",
                "message": f"Oldest item queued at {stats['oldest_item']['queued_at']}",
                "action": "Consider processing or removing stale items"
            })
        
        stats["recommendations"] = recommendations
        
        return stats

    def get_priority_info(self):
        """Get priority calculation information."""
        uid = self.request.get("uid")
        
        if not uid:
            # Return general priority configuration
            from knowledge.curator.workflow_scripts import ENHANCEMENT_PRIORITY_CONFIG
            return {
                "configuration": ENHANCEMENT_PRIORITY_CONFIG,
                "description": "Priority calculation based on content type, workflow state, age, and AI confidence"
            }
        
        # Calculate priority for specific object
        try:
            obj = api.content.get(UID=uid)
            if not obj:
                self.request.response.setStatus(404)
                return {"error": "Object not found"}
            
            priority = calculate_enhancement_priority(obj)
            
            # Get detailed breakdown
            from knowledge.curator.workflow_scripts import ENHANCEMENT_PRIORITY_CONFIG
            portal_type = obj.portal_type
            config = ENHANCEMENT_PRIORITY_CONFIG.get(
                portal_type,
                ENHANCEMENT_PRIORITY_CONFIG["default"]
            )
            
            state = api.content.get_state(obj)
            
            return {
                "uid": uid,
                "title": obj.Title(),
                "portal_type": portal_type,
                "state": state,
                "calculated_priority": priority,
                "breakdown": {
                    "base_priority": config["base_priority"],
                    "workflow_multiplier": config["workflow_multipliers"].get(state, 1.0),
                    "is_knowledge_item": portal_type == "KnowledgeItem",
                    "special_boost": "1.5x for Knowledge Items" if portal_type == "KnowledgeItem" else "None"
                }
            }
            
        except Exception as e:
            self.request.response.setStatus(500)
            return {"error": str(e)}

    def clear_queue(self):
        """Clear the enhancement queue."""
        if self.request.method != "DELETE":
            self.request.response.setStatus(405)
            return {"error": "Method not allowed"}
        
        # Check permissions
        if not api.user.has_permission("Manage portal", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Insufficient permissions"}
        
        from zope.annotation.interfaces import IAnnotations
        portal = api.portal.get()
        annotations = IAnnotations(portal)
        
        if "knowledge.curator.enhancement_queue" in annotations:
            queue_size = len(annotations["knowledge.curator.enhancement_queue"])
            del annotations["knowledge.curator.enhancement_queue"]
            
            return {
                "status": "Queue cleared",
                "items_removed": queue_size
            }
        
        return {
            "status": "Queue was already empty",
            "items_removed": 0
        }