# -*- coding: utf-8 -*-
"""REST API endpoints for vector database operations."""

from plone import api
from knowledge.curator.vector.management import VectorCollectionManager
from knowledge.curator.vector.search import SimilaritySearch
from plone.restapi import deserializer
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
import json


@implementer(IPublishTraverse)
class VectorSearchService(Service):
    """Service for vector similarity search."""
    
    def reply(self):
        """Handle search requests."""
        data = json.loads(self.request.get("BODY", "{}"))
        
        query = data.get("query", "")
        if not query:
            self.request.response.setStatus(400)
            return {"error": "Query parameter is required"}
            
        # Get search parameters
        limit = data.get("limit", 10)
        score_threshold = data.get("score_threshold", 0.5)
        content_types = data.get("content_types")
        workflow_states = data.get("workflow_states")
        tags = data.get("tags")
        
        # Perform search
        search = SimilaritySearch()
        results = search.search_by_text(
            query,
            limit=limit,
            score_threshold=score_threshold,
            content_types=content_types,
            workflow_states=workflow_states,
            tags=tags
        )
        
        return {
            "items": results,
            "items_total": len(results),
            "query": query,
            "parameters": {
                "limit": limit,
                "score_threshold": score_threshold,
                "content_types": content_types,
                "workflow_states": workflow_states,
                "tags": tags
            }
        }


@implementer(IPublishTraverse)
class SimilarContentService(Service):
    """Service for finding similar content."""
    
    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []
        
    def publishTraverse(self, request, name):
        """Traverse to handle UID in URL."""
        self.params.append(name)
        return self
        
    def reply(self):
        """Find similar content."""
        if not self.params:
            self.request.response.setStatus(400)
            return {"error": "Content UID is required"}
            
        uid = self.params[0]
        
        # Get parameters from query string or body
        if self.request.method == "GET":
            limit = int(self.request.get("limit", 5))
            score_threshold = float(self.request.get("score_threshold", 0.6))
            same_type_only = self.request.get("same_type_only", "false") == "true"
        else:
            data = json.loads(self.request.get("BODY", "{}"))
            limit = data.get("limit", 5)
            score_threshold = data.get("score_threshold", 0.6)
            same_type_only = data.get("same_type_only", False)
            
        # Find similar content
        search = SimilaritySearch()
        results = search.find_similar_content(
            uid,
            limit=limit,
            score_threshold=score_threshold,
            same_type_only=same_type_only
        )
        
        return {
            "source_uid": uid,
            "similar_items": results,
            "items_total": len(results),
            "parameters": {
                "limit": limit,
                "score_threshold": score_threshold,
                "same_type_only": same_type_only
            }
        }


@implementer(IPublishTraverse)
class VectorManagementService(Service):
    """Service for vector database management operations."""
    
    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []
        
    def publishTraverse(self, request, name):
        """Traverse to handle operation names."""
        self.params.append(name)
        return self
        
    def reply(self):
        """Handle management operations."""
        # Check permissions
        if not api.user.has_permission("Manage portal", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Insufficient privileges"}
            
        if not self.params:
            # Return available operations
            return {
                "available_operations": [
                    "health",
                    "stats",
                    "initialize",
                    "rebuild",
                    "update"
                ]
            }
            
        operation = self.params[0]
        manager = VectorCollectionManager()
        
        if operation == "health":
            return manager.health_check()
            
        elif operation == "stats":
            return manager.get_database_stats()
            
        elif operation == "initialize":
            if self.request.method != "POST":
                self.request.response.setStatus(405)
                return {"error": "POST method required"}
                
            success = manager.initialize_database()
            return {"success": success}
            
        elif operation == "rebuild":
            if self.request.method != "POST":
                self.request.response.setStatus(405)
                return {"error": "POST method required"}
                
            data = json.loads(self.request.get("BODY", "{}"))
            result = manager.rebuild_index(
                content_types=data.get("content_types"),
                batch_size=data.get("batch_size", 100),
                clear_first=data.get("clear_first", True)
            )
            return result
            
        elif operation == "update":
            if self.request.method != "POST":
                self.request.response.setStatus(405)
                return {"error": "POST method required"}
                
            data = json.loads(self.request.get("BODY", "{}"))
            uid = data.get("uid")
            
            if not uid:
                self.request.response.setStatus(400)
                return {"error": "UID is required"}
                
            brain = api.content.find(UID=uid)
            if not brain:
                self.request.response.setStatus(404)
                return {"error": "Content not found"}
                
            obj = brain[0].getObject()
            success = manager.update_content_vector(obj)
            
            return {"success": success, "uid": uid}
            
        else:
            self.request.response.setStatus(404)
            return {"error": f"Unknown operation: {operation}"}


@implementer(IPublishTraverse)
class VectorRecommendationsService(Service):
    """Service for content recommendations based on vectors."""
    
    def reply(self):
        """Get personalized recommendations."""
        # Get current user
        user = api.user.get_current()
        if user.getId() == "Anonymous User":
            self.request.response.setStatus(401)
            return {"error": "Authentication required"}
            
        # Get parameters
        if self.request.method == "GET":
            limit = int(self.request.get("limit", 20))
            min_score = float(self.request.get("min_score", 0.5))
        else:
            data = json.loads(self.request.get("BODY", "{}"))
            limit = data.get("limit", 20)
            min_score = data.get("min_score", 0.5)
            
        # Get recommendations
        search = SimilaritySearch()
        recommendations = search.get_recommendation_candidates(
            user.getId(),
            limit=limit,
            min_score=min_score
        )
        
        return {
            "recommendations": recommendations,
            "items_total": len(recommendations),
            "user_id": user.getId(),
            "parameters": {
                "limit": limit,
                "min_score": min_score
            }
        }


@implementer(IPublishTraverse)
class VectorClusteringService(Service):
    """Service for semantic clustering of content."""
    
    def reply(self):
        """Perform semantic clustering."""
        # Check permissions
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Insufficient privileges"}
            
        # Get parameters
        if self.request.method == "GET":
            content_types = self.request.get("content_types", "").split(",")
            content_types = [ct.strip() for ct in content_types if ct.strip()] or None
            n_clusters = int(self.request.get("n_clusters", 5))
        else:
            data = json.loads(self.request.get("BODY", "{}"))
            content_types = data.get("content_types")
            n_clusters = data.get("n_clusters", 5)
            
        # Perform clustering
        search = SimilaritySearch()
        clusters = search.semantic_clustering(
            content_types=content_types,
            n_clusters=n_clusters
        )
        
        return {
            "clusters": clusters,
            "n_clusters": len(clusters),
            "parameters": {
                "content_types": content_types,
                "n_clusters": n_clusters
            }
        }