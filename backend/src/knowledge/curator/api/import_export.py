"""Import/Export API endpoints."""

from datetime import datetime
from lxml import etree
from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
import json
import csv
import io
import transaction


@implementer(IPublishTraverse)
class ImportExportService(Service):
    """Service for importing and exporting knowledge content."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if len(self.params) == 0:
            self.request.response.setStatus(400)
            return {"error": "Operation required"}

        operation = self.params[0]

        if operation == "export":
            return self.export_content()
        elif operation == "import":
            return self.import_content()
        elif operation == "formats":
            return self.get_supported_formats()
        elif operation == "validate":
            return self.validate_import()
        else:
            self.request.response.setStatus(404)
            return {"error": "Unknown operation"}

    def export_content(self):
        """Export knowledge content in various formats."""
        if not api.user.has_permission("View", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        # Get parameters
        file_format = self.request.get("format", "json")
        portal_types = (
            self.request.get("types", "").split(",")
            if self.request.get("types")
            else None
        )
        include_embeddings = (
            self.request.get("include_embeddings", "false").lower() == "true"
        )
        include_connections = (
            self.request.get("include_connections", "true").lower() == "true"
        )

        if not portal_types:
            portal_types = [
                "ResearchNote",
                "LearningGoal",
                "ProjectLog",
                "BookmarkPlus",
            ]

        # Get content
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        brains = catalog(
            Creator=user.getId(),
            portal_type=portal_types,
            path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
        )

        if file_format == "json":
            return self._export_json(brains, include_embeddings, include_connections)
        elif file_format == "csv":
            return self._export_csv(brains)
        elif file_format == "opml":
            return self._export_opml(brains)
        elif file_format == "markdown":
            return self._export_markdown(brains)
        elif file_format == "roam":
            return self._export_roam_json(brains)
        else:
            self.request.response.setStatus(400)
            return {"error": f"Unsupported format: {file_format}"}

    def _export_json(self, brains, include_embeddings, include_connections):
        """Export as JSON format."""
        items = []

        for brain in brains:
            obj = brain.getObject()

            item = {
                "uid": brain.UID,
                "portal_type": brain.portal_type,
                "title": brain.Title,
                "description": brain.Description,
                "created": brain.created.ISO8601(),
                "modified": brain.modified.ISO8601(),
                "review_state": brain.review_state,
                "tags": list(brain.Subject),
                "path": "/".join(obj.getPhysicalPath()),
            }

            # Type-specific fields
            if brain.portal_type == "ResearchNote":
                item["content"] = obj.content.raw if hasattr(obj, "content") else ""
                item["source_url"] = getattr(obj, "source_url", "")
                item["key_insights"] = getattr(obj, "key_insights", [])
                if include_connections:
                    item["connections"] = getattr(obj, "connections", [])
                if include_embeddings and hasattr(obj, "embedding_vector"):
                    item["embedding_vector"] = getattr(obj, "embedding_vector", [])
                item["ai_summary"] = getattr(obj, "ai_summary", "")

            elif brain.portal_type == "LearningGoal":
                item["target_date"] = getattr(obj, "target_date", None)
                item["target_date"] = (
                    item["target_date"].isoformat() if item["target_date"] else None
                )
                item["milestones"] = getattr(obj, "milestones", [])
                item["progress"] = getattr(obj, "progress", 0)
                item["priority"] = getattr(obj, "priority", "medium")
                item["reflection"] = getattr(obj, "reflection", "")
                if include_connections:
                    item["related_notes"] = getattr(obj, "related_notes", [])

            elif brain.portal_type == "ProjectLog":
                item["start_date"] = getattr(obj, "start_date", None)
                item["start_date"] = (
                    item["start_date"].isoformat() if item["start_date"] else None
                )
                item["entries"] = getattr(obj, "entries", [])
                item["deliverables"] = getattr(obj, "deliverables", [])
                item["learnings"] = getattr(obj, "learnings", [])
                item["status"] = getattr(obj, "status", "planning")

            elif brain.portal_type == "BookmarkPlus":
                item["url"] = getattr(obj, "url", "")
                item["notes"] = obj.notes.raw if hasattr(obj, "notes") else ""
                item["read_status"] = getattr(obj, "read_status", "unread")
                item["importance"] = getattr(obj, "importance", "medium")
                if include_embeddings and hasattr(obj, "embedding_vector"):
                    item["embedding_vector"] = getattr(obj, "embedding_vector", [])
                item["ai_summary"] = getattr(obj, "ai_summary", "")

            items.append(item)

        # Create export package
        export_data = {
            "version": "1.0",
            "export_date": datetime.now().isoformat(),
            "exporter": "knowledge.curator",
            "item_count": len(items),
            "items": items,
        }

        # Set response headers for download
        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.request.response.setHeader("Content-Type", "application/json")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )

        return export_data

    def _export_csv(self, brains):
        """Export as CSV format."""
        output = io.StringIO()

        # Define fields based on content types
        fieldnames = [
            "uid",
            "portal_type",
            "title",
            "description",
            "created",
            "modified",
            "review_state",
            "tags",
            "url",
            "content",
            "source_url",
            "priority",
            "progress",
            "status",
            "importance",
            "read_status",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for brain in brains:
            obj = brain.getObject()

            row = {
                "uid": brain.UID,
                "portal_type": brain.portal_type,
                "title": brain.Title,
                "description": brain.Description,
                "created": brain.created.ISO8601(),
                "modified": brain.modified.ISO8601(),
                "review_state": brain.review_state,
                "tags": ", ".join(brain.Subject),
            }

            # Add type-specific fields
            if brain.portal_type == "ResearchNote":
                row["content"] = obj.content.raw if hasattr(obj, "content") else ""
                row["source_url"] = getattr(obj, "source_url", "")
            elif brain.portal_type == "LearningGoal":
                row["priority"] = getattr(obj, "priority", "")
                row["progress"] = getattr(obj, "progress", 0)
            elif brain.portal_type == "ProjectLog":
                row["status"] = getattr(obj, "status", "")
            elif brain.portal_type == "BookmarkPlus":
                row["url"] = getattr(obj, "url", "")
                row["importance"] = getattr(obj, "importance", "")
                row["read_status"] = getattr(obj, "read_status", "")

            writer.writerow(row)

        # Set response headers
        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.request.response.setHeader("Content-Type", "text/csv")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )

        return output.getvalue()

    def _export_opml(self, brains):
        """Export as OPML (Outline Processor Markup Language) format."""
        root = etree.Element("opml", version="2.0")

        # Head
        head = etree.SubElement(root, "head")
        etree.SubElement(head, "title").text = "Knowledge Export"
        etree.SubElement(head, "dateCreated").text = datetime.now().isoformat()
        etree.SubElement(head, "ownerName").text = api.user.get_current().getProperty(
            "fullname", ""
        )

        # Body
        body = etree.SubElement(root, "body")

        # Group by type
        type_outlines = {}

        for brain in brains:
            portal_type = brain.portal_type

            if portal_type not in type_outlines:
                outline = etree.SubElement(body, "outline", text=portal_type)
                type_outlines[portal_type] = outline

            # Create item outline
            item_attrs = {
                "text": brain.Title,
                "type": "link" if brain.portal_type == "BookmarkPlus" else "text",
                "created": brain.created.ISO8601(),
                "category": ", ".join(brain.Subject),
            }

            if brain.portal_type == "BookmarkPlus":
                obj = brain.getObject()
                item_attrs["url"] = getattr(obj, "url", "")

            etree.SubElement(type_outlines[portal_type], "outline", **item_attrs)

        # Convert to string
        xml_string = etree.tostring(root, pretty_print=True, encoding="unicode")

        # Set response headers
        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.opml"
        self.request.response.setHeader("Content-Type", "text/x-opml")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )

        return xml_string

    def _format_markdown_item(self, brain):
        """Format a single item as a Markdown string."""
        obj = brain.getObject()
        item_output = io.StringIO()

        item_output.write(f"### {brain.Title}\n\n")

        if brain.Description:
            item_output.write(f"*{brain.Description}*\n\n")

        item_output.write(f"- **Created:** {brain.created.strftime('%Y-%m-%d')}\n")
        item_output.write(f"- **Modified:** {brain.modified.strftime('%Y-%m-%d')}\n")
        item_output.write(f"- **State:** {brain.review_state}\n")

        if brain.Subject:
            item_output.write(f"- **Tags:** {', '.join(brain.Subject)}\n")

        item_output.write("\n")

        if brain.portal_type == "ResearchNote":
            self._format_research_note(item_output, obj)
        elif brain.portal_type == "BookmarkPlus":
            self._format_bookmark_plus(item_output, obj)

        item_output.write("---\n\n")
        return item_output.getvalue()

    def _format_research_note(self, output, obj):
        """Format a ResearchNote item for Markdown export."""
        if hasattr(obj, "content"):
            output.write(f"{obj.content.raw}\n\n")

        if getattr(obj, "key_insights", []):
            output.write("#### Key Insights\n\n")
            for insight in obj.key_insights:
                output.write(f"- {insight}\n")
            output.write("\n")

        if getattr(obj, "source_url", ""):
            output.write(f"**Source:** [{obj.source_url}]({obj.source_url})\n\n")

    def _format_bookmark_plus(self, output, obj):
        """Format a BookmarkPlus item for Markdown export."""
        if getattr(obj, "url", ""):
            output.write(f"**URL:** [{obj.url}]({obj.url})\n\n")

        if hasattr(obj, "notes") and obj.notes:
            output.write(f"{obj.notes.raw}\n\n")

    def _export_markdown(self, brains):
        """Export as Markdown format."""
        output = io.StringIO()
        by_type = {}
        for brain in brains:
            if brain.portal_type not in by_type:
                by_type[brain.portal_type] = []
            by_type[brain.portal_type].append(brain)

        output.write("# Knowledge Export\n\n")
        output.write(
            f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        )

        for portal_type, items in by_type.items():
            output.write(f"## {portal_type}\n\n")
            for brain in items:
                output.write(self._format_markdown_item(brain))

        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.request.response.setHeader("Content-Type", "text/markdown")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
        return output.getvalue()

    def _create_roam_page(self, brain):
        """Create a Roam Research page structure for a single item."""
        return {
            "title": brain.Title,
            "uid": brain.UID[:9],
            "created-time": int(brain.created.millis()),
            "edited-time": int(brain.modified.millis()),
            "children": [],
        }

    def _add_roam_metadata(self, page, brain):
        """Add metadata block to a Roam page."""
        metadata = {
            "string": "Metadata",
            "uid": f"{brain.UID[:9]}-meta",
            "children": [
                {
                    "string": f"Type:: {brain.portal_type}",
                    "uid": f"{brain.UID[:9]}-type",
                },
                {
                    "string": f"Created:: {brain.created.strftime('%B %d, %Y')}",
                    "uid": f"{brain.UID[:9]}-created",
                },
                {
                    "string": f"Tags:: {', '.join(brain.Subject)}",
                    "uid": f"{brain.UID[:9]}-tags",
                },
            ],
        }
        page["children"].append(metadata)

    def _add_research_note_content(self, page, brain, obj):
        """Add ResearchNote-specific content to a Roam page."""
        if hasattr(obj, "content") and obj.content:
            for i, line in enumerate(obj.content.raw.split("\n")):
                if line.strip():
                    page["children"].append({
                        "string": line,
                        "uid": f"{brain.UID[:9]}-c{i}",
                    })
        if getattr(obj, "key_insights", []):
            insights_block = {
                "string": "Key Insights",
                "uid": f"{brain.UID[:9]}-insights",
                "children": [],
            }
            for i, insight in enumerate(obj.key_insights):
                insights_block["children"].append({
                    "string": insight,
                    "uid": f"{brain.UID[:9]}-i{i}",
                })
            page["children"].append(insights_block)
        if getattr(obj, "connections", []):
            connections_block = {
                "string": "Connections",
                "uid": f"{brain.UID[:9]}-conn",
                "children": [],
            }
            for i, conn_uid in enumerate(obj.connections):
                conn_brains = api.content.find(UID=conn_uid)
                if conn_brains:
                    connections_block["children"].append({
                        "string": f"[[{conn_brains[0].Title}]]",
                        "uid": f"{brain.UID[:9]}-conn{i}",
                    })
            if connections_block["children"]:
                page["children"].append(connections_block)

    def _add_roam_content(self, page, brain, obj):
        """Add content-specific fields to a Roam page."""
        if brain.Description:
            page["children"].append({
                "string": brain.Description,
                "uid": f"{brain.UID[:9]}-desc",
            })

        if brain.portal_type == "ResearchNote":
            self._add_research_note_content(page, brain, obj)

    def _export_roam_json(self, brains):
        """Export in Roam Research JSON format."""
        pages = []
        for brain in brains:
            obj = brain.getObject()
            page = self._create_roam_page(brain)
            self._add_roam_metadata(page, brain)
            self._add_roam_content(page, brain, obj)
            pages.append(page)

        filename = (
            f"knowledge_roam_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.request.response.setHeader("Content-Type", "application/json")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
        return pages

    def import_content(self):
        """Import knowledge content from various formats."""
        if not api.user.has_permission("Add portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        # Get file from request
        file_data = self.request.get("file")
        file_format = self.request.get("format", "json")
        merge_strategy = self.request.get(
            "merge_strategy", "skip"
        )  # skip, update, duplicate

        if not file_data:
            self.request.response.setStatus(400)
            return {"error": "No file provided"}

        try:
            if file_format == "json":
                return self._import_json(file_data, merge_strategy)
            elif file_format == "csv":
                return self._import_csv(file_data, merge_strategy)
            elif file_format == "opml":
                return self._import_opml(file_data, merge_strategy)
            else:
                self.request.response.setStatus(400)
                return {"error": f"Unsupported format: {file_format}"}
        except Exception as e:
            self.request.response.setStatus(400)
            return {"error": f"Import failed: {e!s}"}

    def _import_json(self, file_data, merge_strategy):
        """Import from JSON format."""
        # Parse JSON
        content = file_data.read() if hasattr(file_data, "read") else file_data

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        data = json.loads(content)

        # Validate structure
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError("Invalid JSON structure")

        results = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}

        # Import items
        for item_data in data["items"]:
            try:
                result = self._import_item(item_data, merge_strategy)
                if result == "imported":
                    results["imported"] += 1
                elif result == "updated":
                    results["updated"] += 1
                elif result == "skipped":
                    results["skipped"] += 1
            except Exception as e:
                results["errors"].append({
                    "title": item_data.get("title", "Unknown"),
                    "error": str(e),
                })

        transaction.commit()

        return {"success": True, "results": results}

    def _import_item(self, item_data, merge_strategy):
        """Import a single item."""
        portal_type = item_data.get("portal_type")
        title = item_data.get("title", "Untitled")

        # Check if item exists (by title and type)
        catalog = api.portal.get_tool("portal_catalog")
        existing = catalog(
            portal_type=portal_type,
            Title=title,
            path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
        )

        if existing and merge_strategy == "skip":
            return "skipped"
        elif existing and merge_strategy == "update":
            obj = existing[0].getObject()
            self._update_object(obj, item_data)
            return "updated"
        else:
            # Create new item
            obj = api.content.create(
                container=self.context, type=portal_type, title=title
            )
            self._update_object(obj, item_data)
            return "imported"

    def _update_research_note(self, obj, data):
        """Update a ResearchNote object."""
        if "content" in data:
            obj.content = data["content"]
        if "source_url" in data:
            obj.source_url = data["source_url"]
        if "key_insights" in data:
            obj.key_insights = data["key_insights"]
        if "connections" in data:
            obj.connections = data["connections"]
        if "ai_summary" in data:
            obj.ai_summary = data["ai_summary"]

    def _update_learning_goal(self, obj, data):
        """Update a LearningGoal object."""
        if data.get("target_date"):
            obj.target_date = datetime.fromisoformat(data["target_date"]).date()
        if "milestones" in data:
            obj.milestones = data["milestones"]
        if "progress" in data:
            obj.progress = data["progress"]
        if "priority" in data:
            obj.priority = data["priority"]
        if "reflection" in data:
            obj.reflection = data["reflection"]
        if "related_notes" in data:
            obj.related_notes = data["related_notes"]

    def _update_project_log(self, obj, data):
        """Update a ProjectLog object."""
        if data.get("start_date"):
            obj.start_date = datetime.fromisoformat(data["start_date"]).date()
        if "entries" in data:
            obj.entries = data["entries"]
        if "deliverables" in data:
            obj.deliverables = data["deliverables"]
        if "learnings" in data:
            obj.learnings = data["learnings"]
        if "status" in data:
            obj.status = data["status"]

    def _update_bookmark_plus(self, obj, data):
        """Update a BookmarkPlus object."""
        if "url" in data:
            obj.url = data["url"]
        if "notes" in data:
            obj.notes = data["notes"]
        if "read_status" in data:
            obj.read_status = data["read_status"]
        if "importance" in data:
            obj.importance = data["importance"]
        if "ai_summary" in data:
            obj.ai_summary = data["ai_summary"]

    def _update_object(self, obj, data):
        """Update object with imported data."""
        if "description" in data:
            obj.description = data["description"]
        if "tags" in data:
            obj.setSubject(data["tags"])

        portal_type = data.get("portal_type")

        update_handlers = {
            "ResearchNote": self._update_research_note,
            "LearningGoal": self._update_learning_goal,
            "ProjectLog": self._update_project_log,
            "BookmarkPlus": self._update_bookmark_plus,
        }

        handler = update_handlers.get(portal_type)
        if handler:
            handler(obj, data)

        obj.reindexObject()

    def _import_csv(self, file_data, merge_strategy):
        """Import from CSV format."""
        content = file_data.read() if hasattr(file_data, "read") else file_data

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        reader = csv.DictReader(io.StringIO(content))

        results = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}

        for row in reader:
            try:
                # Convert CSV row to item data format
                item_data = {
                    "portal_type": row.get("portal_type", "ResearchNote"),
                    "title": row.get("title", "Untitled"),
                    "description": row.get("description", ""),
                    "tags": [
                        t.strip() for t in row.get("tags", "").split(",") if t.strip()
                    ],
                }

                # Add type-specific fields
                for field in [
                    "content",
                    "source_url",
                    "url",
                    "priority",
                    "progress",
                    "status",
                    "importance",
                    "read_status",
                ]:
                    if row.get(field):
                        item_data[field] = row[field]

                result = self._import_item(item_data, merge_strategy)
                if result == "imported":
                    results["imported"] += 1
                elif result == "updated":
                    results["updated"] += 1
                elif result == "skipped":
                    results["skipped"] += 1

            except Exception as e:
                results["errors"].append({
                    "title": row.get("title", "Unknown"),
                    "error": str(e),
                })

        transaction.commit()

        return {"success": True, "results": results}

    def _import_opml(self, file_data, merge_strategy):
        """Import from OPML format."""
        content = file_data.read() if hasattr(file_data, "read") else file_data

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        # Parse OPML
        root = etree.fromstring(content)
        body = root.find(".//body")

        if body is None:
            raise ValueError("Invalid OPML structure")

        results = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}

        # Process outlines
        for type_outline in body.findall("./outline"):
            portal_type = type_outline.get("text", "ResearchNote")

            for item_outline in type_outline.findall("./outline"):
                try:
                    item_data = {
                        "portal_type": portal_type,
                        "title": item_outline.get("text", "Untitled"),
                        "tags": [
                            t.strip()
                            for t in item_outline.get("category", "").split(",")
                            if t.strip()
                        ],
                    }

                    # Add URL for bookmarks
                    if item_outline.get("url"):
                        item_data["url"] = item_outline.get("url")

                    result = self._import_item(item_data, merge_strategy)
                    if result == "imported":
                        results["imported"] += 1
                    elif result == "updated":
                        results["updated"] += 1
                    elif result == "skipped":
                        results["skipped"] += 1

                except Exception as e:
                    results["errors"].append({
                        "title": item_outline.get("text", "Unknown"),
                        "error": str(e),
                    })

        transaction.commit()

        return {"success": True, "results": results}

    def validate_import(self):
        """Validate import file before importing."""
        if self.request.method != "POST":
            self.request.response.setStatus(405)
            return {"error": "Method not allowed"}

        file_data = self.request.get("file")
        file_format = self.request.get("format", "json")

        if not file_data:
            self.request.response.setStatus(400)
            return {"error": "No file provided"}

        try:
            if hasattr(file_data, "read"):
                content = file_data.read()
                file_data.seek(0)  # Reset for actual import
            else:
                content = file_data

            if isinstance(content, bytes):
                content = content.decode("utf-8")

            validation = {"valid": True, "errors": [], "warnings": [], "summary": {}}

            if file_format == "json":
                self._validate_json(content, validation)
            elif file_format == "csv":
                self._validate_csv(content, validation)
            elif file_format == "opml":
                self._validate_opml(content, validation)
            else:
                validation["valid"] = False
                validation["errors"].append(f"Unsupported format: {file_format}")

            return validation

        except Exception as e:
            return {"valid": False, "errors": [str(e)], "warnings": [], "summary": {}}

    def _validate_json_structure(self, data, validation):
        """Validate the basic structure of the JSON import file."""
        if not isinstance(data, dict):
            validation["valid"] = False
            validation["errors"].append("Root must be an object")
            return False
        if "items" not in data:
            validation["valid"] = False
            validation["errors"].append('Missing "items" array')
            return False
        if not isinstance(data["items"], list):
            validation["valid"] = False
            validation["errors"].append('"items" must be an array')
            return False
        return True

    def _validate_json_item(self, item, i, type_counts, validation):
        """Validate a single item in the JSON import file."""
        required_fields = {
            "ResearchNote": ["title", "content"],
            "LearningGoal": ["title", "description"],
            "ProjectLog": ["title", "description", "start_date"],
            "BookmarkPlus": ["title", "url"],
        }
        if not isinstance(item, dict):
            validation["errors"].append(f"Item {i} must be an object")
            return

        portal_type = item.get("portal_type", "ResearchNote")
        if not item.get("portal_type"):
            validation["warnings"].append(
                f"Item {i} missing portal_type, will default to ResearchNote"
            )

        type_counts[portal_type] = type_counts.get(portal_type, 0) + 1

        if portal_type in required_fields:
            for field in required_fields[portal_type]:
                if field not in item or not item[field]:
                    validation["warnings"].append(
                        f"Item {i} ({portal_type}) missing required field: {field}"
                    )

    def _validate_json(self, content, validation):
        """Validate JSON import file."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            validation["valid"] = False
            validation["errors"].append(f"Invalid JSON: {e!s}")
            return

        if not self._validate_json_structure(data, validation):
            return

        type_counts = {}
        for i, item in enumerate(data["items"]):
            self._validate_json_item(item, i, type_counts, validation)

        validation["summary"] = {
            "total_items": len(data["items"]),
            "by_type": type_counts,
            "version": data.get("version", "unknown"),
        }

    def _validate_csv(self, content, validation):
        """Validate CSV import file."""
        try:
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Invalid CSV: {e!s}")
            return

        if not rows:
            validation["valid"] = False
            validation["errors"].append("CSV file is empty")
            return

        # Check headers
        required_headers = ["title", "portal_type"]
        headers = reader.fieldnames or []

        for header in required_headers:
            if header not in headers:
                validation["errors"].append(f"Missing required column: {header}")

        # Count items
        type_counts = {}
        for i, row in enumerate(rows):
            portal_type = row.get("portal_type", "ResearchNote")
            type_counts[portal_type] = type_counts.get(portal_type, 0) + 1

            if not row.get("title"):
                validation["warnings"].append(f"Row {i + 2} missing title")

        validation["summary"] = {
            "total_items": len(rows),
            "by_type": type_counts,
            "columns": headers,
        }

    def _validate_opml(self, content, validation):
        """Validate OPML import file."""
        try:
            root = etree.fromstring(content)
        except etree.XMLSyntaxError as e:
            validation["valid"] = False
            validation["errors"].append(f"Invalid XML: {e!s}")
            return

        if root.tag != "opml":
            validation["valid"] = False
            validation["errors"].append("Root element must be <opml>")
            return

        body = root.find(".//body")
        if body is None:
            validation["valid"] = False
            validation["errors"].append("Missing <body> element")
            return

        # Count items
        total_items = 0
        type_counts = {}

        for type_outline in body.findall("./outline"):
            portal_type = type_outline.get("text", "ResearchNote")
            items = type_outline.findall("./outline")
            count = len(items)
            total_items += count
            type_counts[portal_type] = count

        validation["summary"] = {"total_items": total_items, "by_type": type_counts}

    def get_supported_formats(self):
        """Get list of supported import/export formats."""
        return {
            "export": [
                {
                    "format": "json",
                    "name": "JSON",
                    "description": (
                        "Complete export with all metadata and relationships"
                    ),
                    "mime_type": "application/json",
                    "extension": ".json",
                },
                {
                    "format": "csv",
                    "name": "CSV",
                    "description": "Tabular format for spreadsheet applications",
                    "mime_type": "text/csv",
                    "extension": ".csv",
                },
                {
                    "format": "opml",
                    "name": "OPML",
                    "description": "Outline format for mind mapping tools",
                    "mime_type": "text/x-opml",
                    "extension": ".opml",
                },
                {
                    "format": "markdown",
                    "name": "Markdown",
                    "description": "Human-readable text format",
                    "mime_type": "text/markdown",
                    "extension": ".md",
                },
                {
                    "format": "roam",
                    "name": "Roam JSON",
                    "description": "Roam Research compatible format",
                    "mime_type": "application/json",
                    "extension": ".json",
                },
            ],
            "import": [
                {
                    "format": "json",
                    "name": "JSON",
                    "description": "Import from JSON export",
                    "mime_type": "application/json",
                },
                {
                    "format": "csv",
                    "name": "CSV",
                    "description": "Import from CSV file",
                    "mime_type": "text/csv",
                },
                {
                    "format": "opml",
                    "name": "OPML",
                    "description": "Import from OPML outline",
                    "mime_type": "text/x-opml",
                },
            ],
        }
