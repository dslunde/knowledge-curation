"""Bulk Operations API endpoints."""

from plone import api
from plone.restapi.services import Service
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

import json
import transaction


@implementer(IPublishTraverse)
class BulkOperationsService(Service):
    """Service for bulk operations on knowledge items."""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        self.params.append(name)
        return self

    def reply(self):
        if self.request.method != "POST":
            self.request.response.setStatus(405)
<<<<<<< HEAD
            return {"error": "Method not allowed"}

        if len(self.params) == 0:
            self.request.response.setStatus(400)
            return {"error": "Operation type required"}

        operation = self.params[0]

        if operation == "workflow":
=======
            return {'error': 'Method not allowed'}

        if len(self.params) == 0:
            self.request.response.setStatus(400)
            return {'error': 'Operation type required'}

        operation = self.params[0]

        if operation == 'workflow':
>>>>>>> fixing_linting_and_tests
            return self.bulk_workflow_transition()
        elif operation == "tag":
            return self.bulk_tag()
        elif operation == "delete":
            return self.bulk_delete()
        elif operation == "move":
            return self.bulk_move()
        elif operation == "update":
            return self.bulk_update()
        elif operation == "connect":
            return self.bulk_connect()
        else:
            self.request.response.setStatus(400)
            return {"error": f"Unknown operation: {operation}"}

    def bulk_workflow_transition(self):
        """Perform bulk workflow transitions."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        uids = data.get("uids", [])
        transition = data.get("transition")
        comment = data.get("comment", "")

        if not uids:
            self.request.response.setStatus(400)
            return {"error": "No items specified"}

        if not transition:
            self.request.response.setStatus(400)
            return {"error": "No transition specified"}

        catalog = api.portal.get_tool("portal_catalog")
        workflow = api.portal.get_tool("portal_workflow")

        results = {"successful": [], "failed": [], "unauthorized": []}
=======
        data = json.loads(self.request.get('BODY', '{}'))
        uids = data.get('uids', [])
        transition = data.get('transition')
        comment = data.get('comment', '')

        if not uids:
            self.request.response.setStatus(400)
            return {'error': 'No items specified'}

        if not transition:
            self.request.response.setStatus(400)
            return {'error': 'No transition specified'}

        catalog = api.portal.get_tool('portal_catalog')
        workflow = api.portal.get_tool('portal_workflow')

        results = {
            'successful': [],
            'failed': [],
            'unauthorized': []
        }
>>>>>>> fixing_linting_and_tests

        for uid in uids:
            brains = catalog(UID=uid)
            if not brains:
                results["failed"].append({"uid": uid, "error": "Item not found"})
                continue

            obj = brains[0].getObject()

            # Check permissions
            if not api.user.has_permission("Modify portal content", obj=obj):
                results["unauthorized"].append({"uid": uid, "title": obj.Title()})
                continue

            # Try transition
            try:
                workflow.doActionFor(obj, transition, comment=comment)
                obj.reindexObject()
                results["successful"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "new_state": api.content.get_state(obj),
                })
            except WorkflowException as e:
                results["failed"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "error": str(e),
                })

        transaction.commit()

        return {
            "operation": "workflow_transition",
            "transition": transition,
            "results": results,
            "summary": {
                "total": len(uids),
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "unauthorized": len(results["unauthorized"]),
            },
        }

    def bulk_tag(self):
        """Add or remove tags in bulk."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        uids = data.get("uids", [])
        add_tags = data.get("add_tags", [])
        remove_tags = data.get("remove_tags", [])
        operation_mode = data.get("mode", "add")  # add, remove, replace

        if not uids:
            self.request.response.setStatus(400)
            return {"error": "No items specified"}

        if not add_tags and not remove_tags and operation_mode != "replace":
            self.request.response.setStatus(400)
            return {"error": "No tags specified"}

        catalog = api.portal.get_tool("portal_catalog")

        results = {"successful": [], "failed": [], "unauthorized": []}
=======
        data = json.loads(self.request.get('BODY', '{}'))
        uids = data.get('uids', [])
        add_tags = data.get('add_tags', [])
        remove_tags = data.get('remove_tags', [])
        operation_mode = data.get('mode', 'add')  # add, remove, replace

        if not uids:
            self.request.response.setStatus(400)
            return {'error': 'No items specified'}

        if not add_tags and not remove_tags and operation_mode != 'replace':
            self.request.response.setStatus(400)
            return {'error': 'No tags specified'}

        catalog = api.portal.get_tool('portal_catalog')

        results = {
            'successful': [],
            'failed': [],
            'unauthorized': []
        }
>>>>>>> fixing_linting_and_tests

        for uid in uids:
            brains = catalog(UID=uid)
            if not brains:
                results["failed"].append({"uid": uid, "error": "Item not found"})
                continue

            obj = brains[0].getObject()

            # Check permissions
            if not api.user.has_permission("Modify portal content", obj=obj):
                results["unauthorized"].append({"uid": uid, "title": obj.Title()})
                continue

            try:
                current_tags = list(obj.Subject())

<<<<<<< HEAD
                if operation_mode == "replace":
=======
                if operation_mode == 'replace':
>>>>>>> fixing_linting_and_tests
                    new_tags = add_tags
                else:
                    # Add new tags
                    new_tags = current_tags.copy()
                    for tag in add_tags:
                        if tag not in new_tags:
                            new_tags.append(tag)

                    # Remove tags
                    for tag in remove_tags:
                        if tag in new_tags:
                            new_tags.remove(tag)

                obj.setSubject(tuple(new_tags))
<<<<<<< HEAD
                obj.reindexObject(idxs=["Subject"])

                results["successful"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "tags": new_tags,
=======
                obj.reindexObject(idxs=['Subject'])

                results['successful'].append({
                    'uid': uid,
                    'title': obj.Title(),
                    'tags': new_tags
>>>>>>> fixing_linting_and_tests
                })
            except Exception as e:
                results["failed"].append({
                    "uid": uid,
                    "title": obj.Title() if "obj" in locals() else "Unknown",
                    "error": str(e),
                })

        transaction.commit()

        return {
            "operation": "bulk_tag",
            "mode": operation_mode,
            "add_tags": add_tags,
            "remove_tags": remove_tags,
            "results": results,
            "summary": {
                "total": len(uids),
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "unauthorized": len(results["unauthorized"]),
            },
        }

    def bulk_delete(self):
        """Delete multiple items."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        uids = data.get("uids", [])

        if not uids:
            self.request.response.setStatus(400)
            return {"error": "No items specified"}

        catalog = api.portal.get_tool("portal_catalog")

        results = {"successful": [], "failed": [], "unauthorized": []}
=======
        data = json.loads(self.request.get('BODY', '{}'))
        uids = data.get('uids', [])

        if not uids:
            self.request.response.setStatus(400)
            return {'error': 'No items specified'}

        catalog = api.portal.get_tool('portal_catalog')

        results = {
            'successful': [],
            'failed': [],
            'unauthorized': []
        }
>>>>>>> fixing_linting_and_tests

        for uid in uids:
            brains = catalog(UID=uid)
            if not brains:
                results["failed"].append({"uid": uid, "error": "Item not found"})
                continue

            obj = brains[0].getObject()
            parent = obj.aq_parent

            # Check permissions
            if not api.user.has_permission("Delete objects", obj=parent):
                results["unauthorized"].append({"uid": uid, "title": obj.Title()})
                continue

            try:
                title = obj.Title()
                api.content.delete(obj)
                results["successful"].append({"uid": uid, "title": title})
            except Exception as e:
                results["failed"].append({
                    "uid": uid,
                    "title": obj.Title() if "obj" in locals() else "Unknown",
                    "error": str(e),
                })

        transaction.commit()

        return {
            "operation": "bulk_delete",
            "results": results,
            "summary": {
                "total": len(uids),
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "unauthorized": len(results["unauthorized"]),
            },
        }

    def bulk_move(self):
        """Move multiple items to a new location."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        uids = data.get("uids", [])
        target_path = data.get("target_path")

        if not uids:
            self.request.response.setStatus(400)
            return {"error": "No items specified"}

        if not target_path:
            self.request.response.setStatus(400)
            return {"error": "No target path specified"}
=======
        data = json.loads(self.request.get('BODY', '{}'))
        uids = data.get('uids', [])
        target_path = data.get('target_path')

        if not uids:
            self.request.response.setStatus(400)
            return {'error': 'No items specified'}

        if not target_path:
            self.request.response.setStatus(400)
            return {'error': 'No target path specified'}
>>>>>>> fixing_linting_and_tests

        # Get target container
        try:
            target = api.content.get(path=target_path)
            if not target:
                self.request.response.setStatus(400)
                return {"error": "Target container not found"}
        except Exception:
            self.request.response.setStatus(400)
<<<<<<< HEAD
            return {"error": "Invalid target path"}

        catalog = api.portal.get_tool("portal_catalog")

        results = {"successful": [], "failed": [], "unauthorized": []}
=======
            return {'error': 'Invalid target path'}

        catalog = api.portal.get_tool('portal_catalog')

        results = {
            'successful': [],
            'failed': [],
            'unauthorized': []
        }
>>>>>>> fixing_linting_and_tests

        for uid in uids:
            brains = catalog(UID=uid)
            if not brains:
                results["failed"].append({"uid": uid, "error": "Item not found"})
                continue

            obj = brains[0].getObject()

            # Check permissions
            if not api.user.has_permission("Copy or Move", obj=obj):
                results["unauthorized"].append({"uid": uid, "title": obj.Title()})
                continue

            if not api.user.has_permission("Add portal content", obj=target):
                results["unauthorized"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "error": "Cannot add to target",
                })
                continue

<<<<<<< HEAD
=======
            if not api.user.has_permission('Add portal content', obj=target):
                results['unauthorized'].append({
                    'uid': uid,
                    'title': obj.Title(),
                    'error': 'Cannot add to target'
                })
                continue

>>>>>>> fixing_linting_and_tests
            try:
                api.content.move(source=obj, target=target)
                results["successful"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "new_path": "/".join(obj.getPhysicalPath()),
                })
            except Exception as e:
                results["failed"].append({
                    "uid": uid,
                    "title": obj.Title() if "obj" in locals() else "Unknown",
                    "error": str(e),
                })

        transaction.commit()

        return {
            "operation": "bulk_move",
            "target_path": target_path,
            "results": results,
            "summary": {
                "total": len(uids),
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "unauthorized": len(results["unauthorized"]),
            },
        }

    def bulk_update(self):
        """Update multiple items with new field values."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        uids = data.get("uids", [])
        updates = data.get("updates", {})

        if not uids:
            self.request.response.setStatus(400)
            return {"error": "No items specified"}

        if not updates:
            self.request.response.setStatus(400)
            return {"error": "No updates specified"}

        catalog = api.portal.get_tool("portal_catalog")

        results = {"successful": [], "failed": [], "unauthorized": []}
=======
        data = json.loads(self.request.get('BODY', '{}'))
        uids = data.get('uids', [])
        updates = data.get('updates', {})

        if not uids:
            self.request.response.setStatus(400)
            return {'error': 'No items specified'}

        if not updates:
            self.request.response.setStatus(400)
            return {'error': 'No updates specified'}

        catalog = api.portal.get_tool('portal_catalog')

        results = {
            'successful': [],
            'failed': [],
            'unauthorized': []
        }
>>>>>>> fixing_linting_and_tests

        # Allowed fields for bulk update
        allowed_fields = {
            "priority",
            "status",
            "importance",
            "read_status",
            "progress",
            "description",
        }

        # Filter updates to allowed fields
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            self.request.response.setStatus(400)
<<<<<<< HEAD
            return {"error": "No valid fields to update"}
=======
            return {'error': 'No valid fields to update'}
>>>>>>> fixing_linting_and_tests

        for uid in uids:
            brains = catalog(UID=uid)
            if not brains:
                results["failed"].append({"uid": uid, "error": "Item not found"})
                continue

            obj = brains[0].getObject()

            # Check permissions
            if not api.user.has_permission("Modify portal content", obj=obj):
                results["unauthorized"].append({"uid": uid, "title": obj.Title()})
                continue

            try:
                # Apply updates
                for field, value in filtered_updates.items():
                    if hasattr(obj, field):
                        setattr(obj, field, value)

                obj.reindexObject()

<<<<<<< HEAD
                results["successful"].append({
                    "uid": uid,
                    "title": obj.Title(),
                    "updated_fields": list(filtered_updates.keys()),
=======
                results['successful'].append({
                    'uid': uid,
                    'title': obj.Title(),
                    'updated_fields': list(filtered_updates.keys())
>>>>>>> fixing_linting_and_tests
                })
            except Exception as e:
                results["failed"].append({
                    "uid": uid,
                    "title": obj.Title() if "obj" in locals() else "Unknown",
                    "error": str(e),
                })

        transaction.commit()

        return {
            "operation": "bulk_update",
            "updates": filtered_updates,
            "results": results,
            "summary": {
                "total": len(uids),
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "unauthorized": len(results["unauthorized"]),
            },
        }

    def bulk_connect(self):
        """Create connections between multiple items."""
<<<<<<< HEAD
        data = json.loads(self.request.get("BODY", "{}"))
        source_uids = data.get("source_uids", [])
        target_uids = data.get("target_uids", [])
        connection_type = data.get(
            "connection_type", "bidirectional"
        )  # unidirectional, bidirectional

        if not source_uids or not target_uids:
            self.request.response.setStatus(400)
            return {"error": "Source and target UIDs required"}

        catalog = api.portal.get_tool("portal_catalog")

        results = {"successful": [], "failed": [], "unauthorized": []}
=======
        data = json.loads(self.request.get('BODY', '{}'))
        source_uids = data.get('source_uids', [])
        target_uids = data.get('target_uids', [])
        connection_type = data.get('connection_type', 'bidirectional')  # unidirectional, bidirectional

        if not source_uids or not target_uids:
            self.request.response.setStatus(400)
            return {'error': 'Source and target UIDs required'}

        catalog = api.portal.get_tool('portal_catalog')

        results = {
            'successful': [],
            'failed': [],
            'unauthorized': []
        }
>>>>>>> fixing_linting_and_tests

        for source_uid in source_uids:
            source_brains = catalog(UID=source_uid)
            if not source_brains:
                results["failed"].append({
                    "source_uid": source_uid,
                    "error": "Source item not found",
                })
                continue

            source_obj = source_brains[0].getObject()

            # Check permissions
            if not api.user.has_permission("Modify portal content", obj=source_obj):
                results["unauthorized"].append({
                    "uid": source_uid,
                    "title": source_obj.Title(),
                })
                continue

            # Process each target
            for target_uid in target_uids:
                if source_uid == target_uid:
                    continue  # Skip self-connections

                target_brains = catalog(UID=target_uid)
                if not target_brains:
                    results["failed"].append({
                        "source_uid": source_uid,
                        "target_uid": target_uid,
                        "error": "Target item not found",
                    })
                    continue

                target_obj = target_brains[0].getObject()

                try:
                    # Add connection to source
                    if hasattr(source_obj, "connections"):
                        connections = list(getattr(source_obj, "connections", []))
                        if target_uid not in connections:
                            connections.append(target_uid)
                            source_obj.connections = connections
                            source_obj.reindexObject()

                    # Add reverse connection if bidirectional
                    if connection_type == "bidirectional":
                        if hasattr(target_obj, "connections"):
                            target_connections = list(
                                getattr(target_obj, "connections", [])
                            )
                            if source_uid not in target_connections:
                                target_connections.append(source_uid)
                                target_obj.connections = target_connections
                                target_obj.reindexObject()

<<<<<<< HEAD
                    results["successful"].append({
                        "source_uid": source_uid,
                        "source_title": source_obj.Title(),
                        "target_uid": target_uid,
                        "target_title": target_obj.Title(),
                        "type": connection_type,
=======
                    results['successful'].append({
                        'source_uid': source_uid,
                        'source_title': source_obj.Title(),
                        'target_uid': target_uid,
                        'target_title': target_obj.Title(),
                        'type': connection_type
>>>>>>> fixing_linting_and_tests
                    })

                except Exception as e:
                    results["failed"].append({
                        "source_uid": source_uid,
                        "target_uid": target_uid,
                        "error": str(e),
                    })

        transaction.commit()

        return {
<<<<<<< HEAD
            "operation": "bulk_connect",
            "connection_type": connection_type,
            "results": results,
            "summary": {
                "total_connections": len(source_uids) * len(target_uids),
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "unauthorized": len(results["unauthorized"]),
            },
=======
            'operation': 'bulk_connect',
            'connection_type': connection_type,
            'results': results,
            'summary': {
                'total_connections': len(source_uids) * len(target_uids),
                'successful': len(results['successful']),
                'failed': len(results['failed']),
                'unauthorized': len(results['unauthorized'])
            }
>>>>>>> fixing_linting_and_tests
        }
