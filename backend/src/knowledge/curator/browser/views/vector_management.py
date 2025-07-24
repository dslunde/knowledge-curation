"""Browser views for vector database management."""

from knowledge.curator.vector.management import VectorCollectionManager
from knowledge.curator.vector.search import SimilaritySearch
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

import json


class VectorManagementView(BrowserView):
    """View for managing vector database operations."""

    def __call__(self):
        """Handle form submissions."""
        if self.request.method == "POST":
            action = self.request.form.get("action")

            if action == "initialize":
                return self.initialize_database()
            elif action == "rebuild":
                return self.rebuild_index()
            elif action == "health_check":
                return self.health_check()
            elif action == "stats":
                return self.get_stats()

        return self.index()

    def initialize_database(self):
        """Initialize the vector database."""
        try:
            manager = VectorCollectionManager()
            success = manager.initialize_database()

            if success:
                IStatusMessage(self.request).addStatusMessage(
                    "Vector database initialized successfully", type="info"
                )
            else:
                IStatusMessage(self.request).addStatusMessage(
                    "Failed to initialize vector database", type="error"
                )

        except Exception as e:
<<<<<<< HEAD
            IStatusMessage(self.request).addStatusMessage(f"Error: {e!s}", type="error")

        return self.request.response.redirect(
            self.context.absolute_url() + "/@@vector-management"
        )
=======
            IStatusMessage(self.request).addStatusMessage(
                f"Error: {e!s}", type="error"
            )

        return self.request.response.redirect(self.context.absolute_url() + "/@@vector-management")
>>>>>>> fixing_linting_and_tests

    def rebuild_index(self):
        """Rebuild the vector index."""
        try:
            manager = VectorCollectionManager()

            # Get options from form
            clear_first = self.request.form.get("clear_first", "true") == "true"
            content_types = self.request.form.get("content_types", "").split(",")
            content_types = [ct.strip() for ct in content_types if ct.strip()]

            result = manager.rebuild_index(
                content_types=content_types or None, clear_first=clear_first
            )

            if result["success"]:
                msg = (
                    f"Index rebuilt successfully: {result['processed']} items "
                    f"in {result['duration_seconds']:.2f} seconds"
                )
                IStatusMessage(self.request).addStatusMessage(msg, type="info")
            else:
                IStatusMessage(self.request).addStatusMessage(
                    f"Index rebuild failed: {result.get('error', 'Unknown error')}",
<<<<<<< HEAD
                    type="error",
                )

        except Exception as e:
            IStatusMessage(self.request).addStatusMessage(f"Error: {e!s}", type="error")

        return self.request.response.redirect(
            self.context.absolute_url() + "/@@vector-management"
        )
=======
                    type="error"
                )

        except Exception as e:
            IStatusMessage(self.request).addStatusMessage(
                f"Error: {e!s}", type="error"
            )

        return self.request.response.redirect(self.context.absolute_url() + "/@@vector-management")
>>>>>>> fixing_linting_and_tests

    def health_check(self):
        """Perform health check."""
        try:
            manager = VectorCollectionManager()
            health = manager.health_check()

            self.request.response.setHeader("Content-Type", "application/json")
            return json.dumps(health, indent=2)

        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({"error": str(e)})

    def get_stats(self):
        """Get database statistics."""
        try:
            manager = VectorCollectionManager()
            stats = manager.get_database_stats()

            self.request.response.setHeader("Content-Type", "application/json")
            return json.dumps(stats, indent=2)

        except Exception as e:
            self.request.response.setStatus(500)
            return json.dumps({"error": str(e)})

    def get_health_status(self):
        """Get current health status for display."""
        try:
            manager = VectorCollectionManager()
            return manager.health_check()
        except Exception:
            return {"healthy": False, "error": "Could not connect to vector database"}

    def get_database_info(self):
        """Get database info for display."""
        try:
            manager = VectorCollectionManager()
            return manager.get_database_stats()
        except Exception:
            return {}


class VectorSearchView(BrowserView):
    """View for vector similarity search."""

    def __call__(self):
        """Handle search requests."""
        query = self.request.form.get("q", "")
        if not query:
            return self.index()

        # Perform search
        search = SimilaritySearch()

        # Get search parameters
        limit = int(self.request.form.get("limit", 10))
        score_threshold = float(self.request.form.get("threshold", 0.5))
        content_types = self.request.form.get("types", "").split(",")
        content_types = [ct.strip() for ct in content_types if ct.strip()] or None

        results = search.search_by_text(
            query,
            limit=limit,
            score_threshold=score_threshold,
            content_types=content_types,
        )

        # Return results
        if self.request.form.get("format") == "json":
            self.request.response.setHeader("Content-Type", "application/json")
            return json.dumps(results, indent=2)
        else:
            self.results = results
            self.query = query
            return self.index()

    def find_similar(self):
        """Find similar content to a given item."""
        uid = self.request.form.get("uid")
        if not uid:
            return json.dumps({"error": "No UID provided"})

        search = SimilaritySearch()
        results = search.find_similar_content(
            uid,
            limit=int(self.request.form.get("limit", 5)),
            score_threshold=float(self.request.form.get("threshold", 0.6)),
            same_type_only=self.request.form.get("same_type", "false") == "true",
        )

        self.request.response.setHeader("Content-Type", "application/json")
        return json.dumps(results, indent=2)
