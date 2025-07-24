"""Import/Export API endpoints."""

from datetime import datetime
from lxml import etree
from plone import api
from plone.restapi.services import Service
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
<<<<<<< HEAD

import csv
import io
import json
=======
from datetime import datetime
import json
import csv
import io
from lxml import etree
>>>>>>> fixing_linting_and_tests
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
<<<<<<< HEAD
            return {"error": "Operation required"}

        operation = self.params[0]

        if operation == "export":
=======
            return {'error': 'Operation required'}

        operation = self.params[0]

        if operation == 'export':
>>>>>>> fixing_linting_and_tests
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
<<<<<<< HEAD
        format = self.request.get("format", "json")
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
=======
        format = self.request.get('format', 'json')
        portal_types = self.request.get('types', '').split(',') if self.request.get('types') else None
        include_embeddings = self.request.get('include_embeddings', 'false').lower() == 'true'
        include_connections = self.request.get('include_connections', 'true').lower() == 'true'

        if not portal_types:
            portal_types = ['ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
>>>>>>> fixing_linting_and_tests

        # Get content
        catalog = api.portal.get_tool("portal_catalog")
        user = api.user.get_current()

        brains = catalog(
            Creator=user.getId(),
            portal_type=portal_types,
            path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
        )

<<<<<<< HEAD
        if format == "json":
=======
        if format == 'json':
>>>>>>> fixing_linting_and_tests
            return self._export_json(brains, include_embeddings, include_connections)
        elif format == "csv":
            return self._export_csv(brains)
        elif format == "opml":
            return self._export_opml(brains)
        elif format == "markdown":
            return self._export_markdown(brains)
        elif format == "roam":
            return self._export_roam_json(brains)
        else:
            self.request.response.setStatus(400)
            return {"error": f"Unsupported format: {format}"}

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
<<<<<<< HEAD
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
=======
                    item['connections'] = getattr(obj, 'connections', [])
                if include_embeddings and hasattr(obj, 'embedding_vector'):
                    item['embedding_vector'] = getattr(obj, 'embedding_vector', [])
                item['ai_summary'] = getattr(obj, 'ai_summary', '')

            elif brain.portal_type == 'LearningGoal':
                item['target_date'] = getattr(obj, 'target_date', None)
                item['target_date'] = item['target_date'].isoformat() if item['target_date'] else None
                item['milestones'] = getattr(obj, 'milestones', [])
                item['progress'] = getattr(obj, 'progress', 0)
                item['priority'] = getattr(obj, 'priority', 'medium')
                item['reflection'] = getattr(obj, 'reflection', '')
                if include_connections:
                    item['related_notes'] = getattr(obj, 'related_notes', [])

            elif brain.portal_type == 'ProjectLog':
                item['start_date'] = getattr(obj, 'start_date', None)
                item['start_date'] = item['start_date'].isoformat() if item['start_date'] else None
                item['entries'] = getattr(obj, 'entries', [])
                item['deliverables'] = getattr(obj, 'deliverables', [])
                item['learnings'] = getattr(obj, 'learnings', [])
                item['status'] = getattr(obj, 'status', 'planning')

            elif brain.portal_type == 'BookmarkPlus':
                item['url'] = getattr(obj, 'url', '')
                item['notes'] = obj.notes.raw if hasattr(obj, 'notes') else ''
                item['read_status'] = getattr(obj, 'read_status', 'unread')
                item['importance'] = getattr(obj, 'importance', 'medium')
                if include_embeddings and hasattr(obj, 'embedding_vector'):
                    item['embedding_vector'] = getattr(obj, 'embedding_vector', [])
                item['ai_summary'] = getattr(obj, 'ai_summary', '')
>>>>>>> fixing_linting_and_tests

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
<<<<<<< HEAD
        self.request.response.setHeader("Content-Type", "application/json")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
=======
        self.request.response.setHeader('Content-Type', 'application/json')
        self.request.response.setHeader('Content-Disposition', f'attachment; filename="{filename}"')
>>>>>>> fixing_linting_and_tests

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
<<<<<<< HEAD
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
=======
            if brain.portal_type == 'ResearchNote':
                row['content'] = obj.content.raw if hasattr(obj, 'content') else ''
                row['source_url'] = getattr(obj, 'source_url', '')
            elif brain.portal_type == 'LearningGoal':
                row['priority'] = getattr(obj, 'priority', '')
                row['progress'] = getattr(obj, 'progress', 0)
            elif brain.portal_type == 'ProjectLog':
                row['status'] = getattr(obj, 'status', '')
            elif brain.portal_type == 'BookmarkPlus':
                row['url'] = getattr(obj, 'url', '')
                row['importance'] = getattr(obj, 'importance', '')
                row['read_status'] = getattr(obj, 'read_status', '')
>>>>>>> fixing_linting_and_tests

            writer.writerow(row)

        # Set response headers
        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
<<<<<<< HEAD
        self.request.response.setHeader("Content-Type", "text/csv")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
=======
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader('Content-Disposition', f'attachment; filename="{filename}"')
>>>>>>> fixing_linting_and_tests

        return output.getvalue()

    def _export_opml(self, brains):
        """Export as OPML (Outline Processor Markup Language) format."""
<<<<<<< HEAD
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
=======
        root = etree.Element('opml', version='2.0')

        # Head
        head = etree.SubElement(root, 'head')
        etree.SubElement(head, 'title').text = 'Knowledge Export'
        etree.SubElement(head, 'dateCreated').text = datetime.now().isoformat()
        etree.SubElement(head, 'ownerName').text = api.user.get_current().getProperty('fullname', '')

        # Body
        body = etree.SubElement(root, 'body')
>>>>>>> fixing_linting_and_tests

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

<<<<<<< HEAD
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
=======
            if brain.portal_type == 'BookmarkPlus':
                obj = brain.getObject()
                item_attrs['url'] = getattr(obj, 'url', '')

            etree.SubElement(type_outlines[portal_type], 'outline', **item_attrs)

        # Convert to string
        xml_string = etree.tostring(root, pretty_print=True, encoding='unicode')

        # Set response headers
        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.opml"
        self.request.response.setHeader('Content-Type', 'text/x-opml')
        self.request.response.setHeader('Content-Disposition', f'attachment; filename="{filename}"')
>>>>>>> fixing_linting_and_tests

        return xml_string

    def _export_markdown(self, brains):
        """Export as Markdown format."""
        output = io.StringIO()

        # Group by type
        by_type = {}
        for brain in brains:
            if brain.portal_type not in by_type:
                by_type[brain.portal_type] = []
            by_type[brain.portal_type].append(brain)

        # Write header
        output.write("# Knowledge Export\n\n")
<<<<<<< HEAD
        output.write(
            f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        )
=======
        output.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
>>>>>>> fixing_linting_and_tests

        # Write sections by type
        for portal_type, items in by_type.items():
            output.write(f"## {portal_type}\n\n")

            for brain in items:
                obj = brain.getObject()

                output.write(f"### {brain.Title}\n\n")

                if brain.Description:
                    output.write(f"*{brain.Description}*\n\n")

                # Metadata
                output.write(f"- **Created:** {brain.created.strftime('%Y-%m-%d')}\n")
                output.write(f"- **Modified:** {brain.modified.strftime('%Y-%m-%d')}\n")
                output.write(f"- **State:** {brain.review_state}\n")

                if brain.Subject:
                    output.write(f"- **Tags:** {', '.join(brain.Subject)}\n")

                output.write("\n")

                # Type-specific content
                if brain.portal_type == "ResearchNote" and hasattr(obj, "content"):
                    output.write(f"{obj.content.raw}\n\n")

<<<<<<< HEAD
                    if getattr(obj, "key_insights", []):
=======
                    if getattr(obj, 'key_insights', []):
>>>>>>> fixing_linting_and_tests
                        output.write("#### Key Insights\n\n")
                        for insight in obj.key_insights:
                            output.write(f"- {insight}\n")
                        output.write("\n")

<<<<<<< HEAD
                    if getattr(obj, "source_url", ""):
                        output.write(
                            f"**Source:** [{obj.source_url}]({obj.source_url})\n\n"
                        )

                elif brain.portal_type == "BookmarkPlus":
                    if getattr(obj, "url", ""):
                        output.write(f"**URL:** [{obj.url}]({obj.url})\n\n")

                    if hasattr(obj, "notes") and obj.notes:
=======
                    if getattr(obj, 'source_url', ''):
                        output.write(f"**Source:** [{obj.source_url}]({obj.source_url})\n\n")

                elif brain.portal_type == 'BookmarkPlus':
                    if getattr(obj, 'url', ''):
                        output.write(f"**URL:** [{obj.url}]({obj.url})\n\n")

                    if hasattr(obj, 'notes') and obj.notes:
>>>>>>> fixing_linting_and_tests
                        output.write(f"{obj.notes.raw}\n\n")

                output.write("---\n\n")

        # Set response headers
        filename = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
<<<<<<< HEAD
        self.request.response.setHeader("Content-Type", "text/markdown")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
=======
        self.request.response.setHeader('Content-Type', 'text/markdown')
        self.request.response.setHeader('Content-Disposition', f'attachment; filename="{filename}"')
>>>>>>> fixing_linting_and_tests

        return output.getvalue()

    def _export_roam_json(self, brains):
        """Export in Roam Research JSON format."""
        pages = []

        for brain in brains:
            obj = brain.getObject()

            # Create page
            page = {
                "title": brain.Title,
                "uid": brain.UID[:9],  # Roam uses 9-character UIDs
                "created-time": int(brain.created.millis()),
                "edited-time": int(brain.modified.millis()),
                "children": [],
            }

            # Add metadata block
            metadata = {
<<<<<<< HEAD
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
=======
                'string': "Metadata",
                'uid': f"{brain.UID[:9]}-meta",
                'children': [
                    {'string': f"Type:: {brain.portal_type}", 'uid': f"{brain.UID[:9]}-type"},
                    {'string': f"Created:: {brain.created.strftime('%B %d, %Y')}", 'uid': f"{brain.UID[:9]}-created"},
                    {'string': f"Tags:: {', '.join(brain.Subject)}", 'uid': f"{brain.UID[:9]}-tags"}
                ]
            }
            page['children'].append(metadata)
>>>>>>> fixing_linting_and_tests

            # Add content
            if brain.Description:
                page["children"].append({
                    "string": brain.Description,
                    "uid": f"{brain.UID[:9]}-desc",
                })

            # Type-specific content
            if brain.portal_type == "ResearchNote":
                if hasattr(obj, "content") and obj.content:
                    # Split content into blocks
                    content_lines = obj.content.raw.split("\n")
                    for i, line in enumerate(content_lines):
                        if line.strip():
                            page["children"].append({
                                "string": line,
                                "uid": f"{brain.UID[:9]}-c{i}",
                            })

                # Add key insights
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
<<<<<<< HEAD
                    page["children"].append(insights_block)
=======
                    page['children'].append(insights_block)
>>>>>>> fixing_linting_and_tests

                # Add connections as page references
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
<<<<<<< HEAD
                    if connections_block["children"]:
                        page["children"].append(connections_block)
=======
                    if connections_block['children']:
                        page['children'].append(connections_block)
>>>>>>> fixing_linting_and_tests

            pages.append(page)

        # Set response headers
<<<<<<< HEAD
        filename = (
            f"knowledge_roam_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.request.response.setHeader("Content-Type", "application/json")
        self.request.response.setHeader(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
=======
        filename = f"knowledge_roam_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.request.response.setHeader('Content-Type', 'application/json')
        self.request.response.setHeader('Content-Disposition', f'attachment; filename="{filename}"')
>>>>>>> fixing_linting_and_tests

        return pages

    def import_content(self):
        """Import knowledge content from various formats."""
        if not api.user.has_permission("Add portal content", obj=self.context):
            self.request.response.setStatus(403)
            return {"error": "Unauthorized"}

        # Get file from request
<<<<<<< HEAD
        file_data = self.request.get("file")
        format = self.request.get("format", "json")
        merge_strategy = self.request.get(
            "merge_strategy", "skip"
        )  # skip, update, duplicate

        if not file_data:
            self.request.response.setStatus(400)
            return {"error": "No file provided"}
=======
        file_data = self.request.get('file')
        format = self.request.get('format', 'json')
        merge_strategy = self.request.get('merge_strategy', 'skip')  # skip, update, duplicate

        if not file_data:
            self.request.response.setStatus(400)
            return {'error': 'No file provided'}
>>>>>>> fixing_linting_and_tests

        try:
            if format == "json":
                return self._import_json(file_data, merge_strategy)
            elif format == "csv":
                return self._import_csv(file_data, merge_strategy)
            elif format == "opml":
                return self._import_opml(file_data, merge_strategy)
            else:
                self.request.response.setStatus(400)
                return {"error": f"Unsupported format: {format}"}
        except Exception as e:
            self.request.response.setStatus(400)
<<<<<<< HEAD
            return {"error": f"Import failed: {e!s}"}
=======
            return {'error': f'Import failed: {e!s}'}
>>>>>>> fixing_linting_and_tests

    def _import_json(self, file_data, merge_strategy):
        """Import from JSON format."""
        # Parse JSON
        if hasattr(file_data, "read"):
            content = file_data.read()
        else:
            content = file_data

        if isinstance(content, bytes):
<<<<<<< HEAD
            content = content.decode("utf-8")
=======
            content = content.decode('utf-8')
>>>>>>> fixing_linting_and_tests

        data = json.loads(content)

        # Validate structure
<<<<<<< HEAD
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError("Invalid JSON structure")

        results = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}
=======
        if not isinstance(data, dict) or 'items' not in data:
            raise ValueError('Invalid JSON structure')

        results = {
            'imported': 0,
            'skipped': 0,
            'updated': 0,
            'errors': []
        }
>>>>>>> fixing_linting_and_tests

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

<<<<<<< HEAD
        return {"success": True, "results": results}

    def _import_item(self, item_data, merge_strategy):
        """Import a single item."""
        portal_type = item_data.get("portal_type")
        title = item_data.get("title", "Untitled")
=======
        return {
            'success': True,
            'results': results
        }

    def _import_item(self, item_data, merge_strategy):
        """Import a single item."""
        portal_type = item_data.get('portal_type')
        title = item_data.get('title', 'Untitled')
>>>>>>> fixing_linting_and_tests

        # Check if item exists (by title and type)
        catalog = api.portal.get_tool("portal_catalog")
        existing = catalog(
            portal_type=portal_type,
            Title=title,
            path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
        )

<<<<<<< HEAD
        if existing and merge_strategy == "skip":
            return "skipped"
        elif existing and merge_strategy == "update":
=======
        if existing and merge_strategy == 'skip':
            return 'skipped'
        elif existing and merge_strategy == 'update':
>>>>>>> fixing_linting_and_tests
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

    def _update_object(self, obj, data):
        """Update object with imported data."""
        # Common fields
<<<<<<< HEAD
        if "description" in data:
            obj.description = data["description"]

        if "tags" in data:
            obj.setSubject(data["tags"])

        # Type-specific fields
        portal_type = data.get("portal_type")

        if portal_type == "ResearchNote":
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

        elif portal_type == "LearningGoal":
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

        elif portal_type == "ProjectLog":
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

        elif portal_type == "BookmarkPlus":
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
=======
        if 'description' in data:
            obj.description = data['description']

        if 'tags' in data:
            obj.setSubject(data['tags'])

        # Type-specific fields
        portal_type = data.get('portal_type')

        if portal_type == 'ResearchNote':
            if 'content' in data:
                obj.content = data['content']
            if 'source_url' in data:
                obj.source_url = data['source_url']
            if 'key_insights' in data:
                obj.key_insights = data['key_insights']
            if 'connections' in data:
                obj.connections = data['connections']
            if 'ai_summary' in data:
                obj.ai_summary = data['ai_summary']

        elif portal_type == 'LearningGoal':
            if data.get('target_date'):
                obj.target_date = datetime.fromisoformat(data['target_date']).date()
            if 'milestones' in data:
                obj.milestones = data['milestones']
            if 'progress' in data:
                obj.progress = data['progress']
            if 'priority' in data:
                obj.priority = data['priority']
            if 'reflection' in data:
                obj.reflection = data['reflection']
            if 'related_notes' in data:
                obj.related_notes = data['related_notes']

        elif portal_type == 'ProjectLog':
            if data.get('start_date'):
                obj.start_date = datetime.fromisoformat(data['start_date']).date()
            if 'entries' in data:
                obj.entries = data['entries']
            if 'deliverables' in data:
                obj.deliverables = data['deliverables']
            if 'learnings' in data:
                obj.learnings = data['learnings']
            if 'status' in data:
                obj.status = data['status']

        elif portal_type == 'BookmarkPlus':
            if 'url' in data:
                obj.url = data['url']
            if 'notes' in data:
                obj.notes = data['notes']
            if 'read_status' in data:
                obj.read_status = data['read_status']
            if 'importance' in data:
                obj.importance = data['importance']
            if 'ai_summary' in data:
                obj.ai_summary = data['ai_summary']
>>>>>>> fixing_linting_and_tests

        obj.reindexObject()

    def _import_csv(self, file_data, merge_strategy):
        """Import from CSV format."""
        if hasattr(file_data, "read"):
            content = file_data.read()
        else:
            content = file_data

        if isinstance(content, bytes):
<<<<<<< HEAD
            content = content.decode("utf-8")

        reader = csv.DictReader(io.StringIO(content))

        results = {"imported": 0, "skipped": 0, "updated": 0, "errors": []}
=======
            content = content.decode('utf-8')

        reader = csv.DictReader(io.StringIO(content))

        results = {
            'imported': 0,
            'skipped': 0,
            'updated': 0,
            'errors': []
        }
>>>>>>> fixing_linting_and_tests

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
<<<<<<< HEAD
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
=======
                for field in ['content', 'source_url', 'url', 'priority', 'progress', 'status', 'importance', 'read_status']:
>>>>>>> fixing_linting_and_tests
                    if row.get(field):
                        item_data[field] = row[field]

                result = self._import_item(item_data, merge_strategy)
<<<<<<< HEAD
                if result == "imported":
                    results["imported"] += 1
                elif result == "updated":
                    results["updated"] += 1
                elif result == "skipped":
                    results["skipped"] += 1
=======
                if result == 'imported':
                    results['imported'] += 1
                elif result == 'updated':
                    results['updated'] += 1
                elif result == 'skipped':
                    results['skipped'] += 1
>>>>>>> fixing_linting_and_tests

            except Exception as e:
                results["errors"].append({
                    "title": row.get("title", "Unknown"),
                    "error": str(e),
                })

        transaction.commit()

<<<<<<< HEAD
        return {"success": True, "results": results}
=======
        return {
            'success': True,
            'results': results
        }
>>>>>>> fixing_linting_and_tests

    def _import_opml(self, file_data, merge_strategy):
        """Import from OPML format."""
        if hasattr(file_data, "read"):
            content = file_data.read()
        else:
            content = file_data

        if isinstance(content, bytes):
<<<<<<< HEAD
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
=======
            content = content.decode('utf-8')

        # Parse OPML
        root = etree.fromstring(content)
        body = root.find('.//body')

        if body is None:
            raise ValueError('Invalid OPML structure')

        results = {
            'imported': 0,
            'skipped': 0,
            'updated': 0,
            'errors': []
        }

        # Process outlines
        for type_outline in body.findall('./outline'):
            portal_type = type_outline.get('text', 'ResearchNote')

            for item_outline in type_outline.findall('./outline'):
>>>>>>> fixing_linting_and_tests
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
<<<<<<< HEAD
                    if item_outline.get("url"):
                        item_data["url"] = item_outline.get("url")

                    result = self._import_item(item_data, merge_strategy)
                    if result == "imported":
                        results["imported"] += 1
                    elif result == "updated":
                        results["updated"] += 1
                    elif result == "skipped":
                        results["skipped"] += 1
=======
                    if item_outline.get('url'):
                        item_data['url'] = item_outline.get('url')

                    result = self._import_item(item_data, merge_strategy)
                    if result == 'imported':
                        results['imported'] += 1
                    elif result == 'updated':
                        results['updated'] += 1
                    elif result == 'skipped':
                        results['skipped'] += 1
>>>>>>> fixing_linting_and_tests

                except Exception as e:
                    results["errors"].append({
                        "title": item_outline.get("text", "Unknown"),
                        "error": str(e),
                    })

        transaction.commit()

<<<<<<< HEAD
        return {"success": True, "results": results}
=======
        return {
            'success': True,
            'results': results
        }
>>>>>>> fixing_linting_and_tests

    def validate_import(self):
        """Validate import file before importing."""
        if self.request.method != "POST":
            self.request.response.setStatus(405)
            return {"error": "Method not allowed"}

        file_data = self.request.get("file")
        format = self.request.get("format", "json")

<<<<<<< HEAD
        if not file_data:
            self.request.response.setStatus(400)
            return {"error": "No file provided"}
=======
        file_data = self.request.get('file')
        format = self.request.get('format', 'json')

        if not file_data:
            self.request.response.setStatus(400)
            return {'error': 'No file provided'}
>>>>>>> fixing_linting_and_tests

        try:
            if hasattr(file_data, "read"):
                content = file_data.read()
                file_data.seek(0)  # Reset for actual import
            else:
                content = file_data

            if isinstance(content, bytes):
<<<<<<< HEAD
                content = content.decode("utf-8")

            validation = {"valid": True, "errors": [], "warnings": [], "summary": {}}

            if format == "json":
=======
                content = content.decode('utf-8')

            validation = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'summary': {}
            }

            if format == 'json':
>>>>>>> fixing_linting_and_tests
                self._validate_json(content, validation)
            elif format == "csv":
                self._validate_csv(content, validation)
            elif format == "opml":
                self._validate_opml(content, validation)
            else:
<<<<<<< HEAD
                validation["valid"] = False
                validation["errors"].append(f"Unsupported format: {format}")
=======
                validation['valid'] = False
                validation['errors'].append(f'Unsupported format: {format}')
>>>>>>> fixing_linting_and_tests

            return validation

        except Exception as e:
            return {"valid": False, "errors": [str(e)], "warnings": [], "summary": {}}

    def _validate_json(self, content, validation):
        """Validate JSON import file."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
<<<<<<< HEAD
            validation["valid"] = False
            validation["errors"].append(f"Invalid JSON: {e!s}")
=======
            validation['valid'] = False
            validation['errors'].append(f'Invalid JSON: {e!s}')
>>>>>>> fixing_linting_and_tests
            return

        if not isinstance(data, dict):
            validation["valid"] = False
            validation["errors"].append("Root must be an object")
            return

<<<<<<< HEAD
        if "items" not in data:
            validation["valid"] = False
            validation["errors"].append('Missing "items" array')
            return

        if not isinstance(data["items"], list):
            validation["valid"] = False
            validation["errors"].append('"items" must be an array')
=======
        if 'items' not in data:
            validation['valid'] = False
            validation['errors'].append('Missing "items" array')
            return

        if not isinstance(data['items'], list):
            validation['valid'] = False
            validation['errors'].append('"items" must be an array')
>>>>>>> fixing_linting_and_tests
            return

        # Count items by type
        type_counts = {}
        required_fields = {
            "ResearchNote": ["title", "content"],
            "LearningGoal": ["title", "description"],
            "ProjectLog": ["title", "description", "start_date"],
            "BookmarkPlus": ["title", "url"],
        }

<<<<<<< HEAD
        for i, item in enumerate(data["items"]):
=======
        for i, item in enumerate(data['items']):
>>>>>>> fixing_linting_and_tests
            if not isinstance(item, dict):
                validation["errors"].append(f"Item {i} must be an object")
                continue

<<<<<<< HEAD
            portal_type = item.get("portal_type")
            if not portal_type:
                validation["warnings"].append(
                    f"Item {i} missing portal_type, will default to ResearchNote"
                )
                portal_type = "ResearchNote"
=======
            portal_type = item.get('portal_type')
            if not portal_type:
                validation['warnings'].append(f'Item {i} missing portal_type, will default to ResearchNote')
                portal_type = 'ResearchNote'
>>>>>>> fixing_linting_and_tests

            type_counts[portal_type] = type_counts.get(portal_type, 0) + 1

            # Check required fields
            if portal_type in required_fields:
                for field in required_fields[portal_type]:
                    if field not in item or not item[field]:
<<<<<<< HEAD
                        validation["warnings"].append(
                            f"Item {i} ({portal_type}) missing required field: {field}"
                        )

        validation["summary"] = {
            "total_items": len(data["items"]),
            "by_type": type_counts,
            "version": data.get("version", "unknown"),
=======
                        validation['warnings'].append(f'Item {i} ({portal_type}) missing required field: {field}')

        validation['summary'] = {
            'total_items': len(data['items']),
            'by_type': type_counts,
            'version': data.get('version', 'unknown')
>>>>>>> fixing_linting_and_tests
        }

    def _validate_csv(self, content, validation):
        """Validate CSV import file."""
        try:
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
        except Exception as e:
<<<<<<< HEAD
            validation["valid"] = False
            validation["errors"].append(f"Invalid CSV: {e!s}")
=======
            validation['valid'] = False
            validation['errors'].append(f'Invalid CSV: {e!s}')
>>>>>>> fixing_linting_and_tests
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
<<<<<<< HEAD
                validation["errors"].append(f"Missing required column: {header}")
=======
                validation['errors'].append(f'Missing required column: {header}')
>>>>>>> fixing_linting_and_tests

        # Count items
        type_counts = {}
        for i, row in enumerate(rows):
            portal_type = row.get("portal_type", "ResearchNote")
            type_counts[portal_type] = type_counts.get(portal_type, 0) + 1

<<<<<<< HEAD
            if not row.get("title"):
                validation["warnings"].append(f"Row {i + 2} missing title")

        validation["summary"] = {
            "total_items": len(rows),
            "by_type": type_counts,
            "columns": headers,
=======
            if not row.get('title'):
                validation['warnings'].append(f'Row {i+2} missing title')

        validation['summary'] = {
            'total_items': len(rows),
            'by_type': type_counts,
            'columns': headers
>>>>>>> fixing_linting_and_tests
        }

    def _validate_opml(self, content, validation):
        """Validate OPML import file."""
        try:
            root = etree.fromstring(content)
        except etree.XMLSyntaxError as e:
<<<<<<< HEAD
            validation["valid"] = False
            validation["errors"].append(f"Invalid XML: {e!s}")
            return

        if root.tag != "opml":
            validation["valid"] = False
            validation["errors"].append("Root element must be <opml>")
            return

        body = root.find(".//body")
=======
            validation['valid'] = False
            validation['errors'].append(f'Invalid XML: {e!s}')
            return

        if root.tag != 'opml':
            validation['valid'] = False
            validation['errors'].append('Root element must be <opml>')
            return

        body = root.find('.//body')
>>>>>>> fixing_linting_and_tests
        if body is None:
            validation["valid"] = False
            validation["errors"].append("Missing <body> element")
            return

        # Count items
        total_items = 0
        type_counts = {}

<<<<<<< HEAD
        for type_outline in body.findall("./outline"):
            portal_type = type_outline.get("text", "ResearchNote")
            items = type_outline.findall("./outline")
=======
        for type_outline in body.findall('./outline'):
            portal_type = type_outline.get('text', 'ResearchNote')
            items = type_outline.findall('./outline')
>>>>>>> fixing_linting_and_tests
            count = len(items)
            total_items += count
            type_counts[portal_type] = count

<<<<<<< HEAD
        validation["summary"] = {"total_items": total_items, "by_type": type_counts}
=======
        validation['summary'] = {
            'total_items': total_items,
            'by_type': type_counts
        }
>>>>>>> fixing_linting_and_tests

    def get_supported_formats(self):
        """Get list of supported import/export formats."""
        return {
            "export": [
                {
                    "format": "json",
                    "name": "JSON",
                    "description": "Complete export with all metadata and relationships",
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
<<<<<<< HEAD
                    "format": "opml",
                    "name": "OPML",
                    "description": "Import from OPML outline",
                    "mime_type": "text/x-opml",
                },
            ],
=======
                    'format': 'opml',
                    'name': 'OPML',
                    'description': 'Import from OPML outline',
                    'mime_type': 'text/x-opml'
                }
            ]
>>>>>>> fixing_linting_and_tests
        }
