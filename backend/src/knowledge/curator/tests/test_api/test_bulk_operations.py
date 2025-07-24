"""Tests for Bulk Operations API."""

<<<<<<< HEAD
=======
import unittest
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from plone.restapi.testing import RelativeSession
>>>>>>> fixing_linting_and_tests
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession

import unittest


class TestBulkOperationsAPI(unittest.TestCase):
    """Test Bulk Operations API endpoints."""

    layer = PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (TEST_USER_ID, "secret")

        # Create test content
        self.folder = api.content.create(
            container=self.portal,
            type="Folder",
            id="knowledge-base",
            title="Knowledge Base",
        )

        # Create multiple research notes
        self.notes = []
        for i in range(5):
            note = api.content.create(
                container=self.folder,
                type="ResearchNote",
                title=f"Research Note {i + 1}",
                description=f"Description for note {i + 1}",
                tags=["test", f"note-{i + 1}"],
            )
            self.notes.append(note)

        # Create a target folder for move operations
        self.target_folder = api.content.create(
            container=self.portal, type="Folder", id="archive", title="Archive"
        )

        import transaction

        transaction.commit()

    def test_bulk_workflow_transition(self):
        """Test bulk workflow transitions."""
        # Get UIDs
        uids = [note.UID() for note in self.notes[:3]]

        response = self.api_session.post(
            "/@knowledge-bulk/workflow",
            json={
                "uids": uids,
                "transition": "publish",
                "comment": "Publishing reviewed content",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

<<<<<<< HEAD
        self.assertEqual(data["operation"], "workflow_transition")
        self.assertEqual(data["transition"], "publish")
        self.assertIn("results", data)
        self.assertIn("summary", data)
=======
        self.assertEqual(data['operation'], 'workflow_transition')
        self.assertEqual(data['transition'], 'publish')
        self.assertIn('results', data)
        self.assertIn('summary', data)
>>>>>>> fixing_linting_and_tests

        # Check summary
        summary = data["summary"]
        self.assertEqual(summary["total"], 3)
        self.assertGreaterEqual(summary["successful"], 0)

    def test_bulk_tag_add(self):
        """Test bulk tag addition."""
        uids = [note.UID() for note in self.notes[:3]]

        response = self.api_session.post(
            "/@knowledge-bulk/tag",
            json={
                "uids": uids,
                "mode": "add",
                "add_tags": ["important", "reviewed"],
                "remove_tags": [],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

<<<<<<< HEAD
        self.assertEqual(data["operation"], "bulk_tag")
        self.assertEqual(data["mode"], "add")
=======
        self.assertEqual(data['operation'], 'bulk_tag')
        self.assertEqual(data['mode'], 'add')
>>>>>>> fixing_linting_and_tests

        # Verify tags were added
        for result in data["results"]["successful"]:
            self.assertIn("important", result["tags"])
            self.assertIn("reviewed", result["tags"])

    def test_bulk_tag_remove(self):
        """Test bulk tag removal."""
        uids = [note.UID() for note in self.notes[:2]]

        response = self.api_session.post(
            "/@knowledge-bulk/tag",
            json={
                "uids": uids,
                "mode": "remove",
                "add_tags": [],
                "remove_tags": ["test"],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify tag was removed
        for result in data["results"]["successful"]:
            self.assertNotIn("test", result["tags"])

    def test_bulk_tag_replace(self):
        """Test bulk tag replacement."""
        uids = [note.UID() for note in self.notes[:2]]

        response = self.api_session.post(
            "/@knowledge-bulk/tag",
            json={
                "uids": uids,
                "mode": "replace",
                "add_tags": ["new-tag-1", "new-tag-2"],
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify tags were replaced
        for result in data["results"]["successful"]:
            self.assertEqual(set(result["tags"]), {"new-tag-1", "new-tag-2"})

    def test_bulk_delete(self):
        """Test bulk delete operation."""
        # Create items to delete
        to_delete = []
        for i in range(3):
            note = api.content.create(
                container=self.folder, type="ResearchNote", title=f"To Delete {i + 1}"
            )
            to_delete.append(note.UID())

        import transaction

        transaction.commit()

        response = self.api_session.post(
            "/@knowledge-bulk/delete", json={"uids": to_delete}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

<<<<<<< HEAD
        self.assertEqual(data["operation"], "bulk_delete")
        self.assertEqual(data["summary"]["successful"], 3)
=======
        self.assertEqual(data['operation'], 'bulk_delete')
        self.assertEqual(data['summary']['successful'], 3)
>>>>>>> fixing_linting_and_tests

        # Verify items were deleted
        catalog = api.portal.get_tool("portal_catalog")
        for uid in to_delete:
            brains = catalog(UID=uid)
            self.assertEqual(len(brains), 0)

    def test_bulk_move(self):
        """Test bulk move operation."""
        uids = [note.UID() for note in self.notes[:2]]
<<<<<<< HEAD
        target_path = "/".join(self.target_folder.getPhysicalPath())
=======
        target_path = '/'.join(self.target_folder.getPhysicalPath())
>>>>>>> fixing_linting_and_tests

        response = self.api_session.post(
            "/@knowledge-bulk/move", json={"uids": uids, "target_path": target_path}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

<<<<<<< HEAD
        self.assertEqual(data["operation"], "bulk_move")
        self.assertEqual(data["summary"]["successful"], 2)
=======
        self.assertEqual(data['operation'], 'bulk_move')
        self.assertEqual(data['summary']['successful'], 2)
>>>>>>> fixing_linting_and_tests

        # Verify items were moved
        for result in data["results"]["successful"]:
            self.assertIn("/archive/", result["new_path"])

    def test_bulk_update(self):
        """Test bulk update operation."""
        # Create learning goals for update testing
        goals = []
        for i in range(3):
            goal = api.content.create(
                container=self.folder,
                type="LearningGoal",
                title=f"Goal {i + 1}",
                priority="low",
                progress=0,
            )
            goals.append(goal.UID())

        import transaction

        transaction.commit()

        response = self.api_session.post(
            "/@knowledge-bulk/update",
            json={"uids": goals, "updates": {"priority": "high", "progress": 50}},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

<<<<<<< HEAD
        self.assertEqual(data["operation"], "bulk_update")
        self.assertEqual(data["summary"]["successful"], 3)
=======
        self.assertEqual(data['operation'], 'bulk_update')
        self.assertEqual(data['summary']['successful'], 3)
>>>>>>> fixing_linting_and_tests

        # Verify updates
        catalog = api.portal.get_tool("portal_catalog")
        for uid in goals:
            obj = catalog(UID=uid)[0].getObject()
            self.assertEqual(obj.priority, "high")
            self.assertEqual(obj.progress, 50)

    def test_bulk_connect(self):
        """Test bulk connection creation."""
        source_uids = [self.notes[0].UID(), self.notes[1].UID()]
        target_uids = [self.notes[2].UID(), self.notes[3].UID()]

        response = self.api_session.post(
            "/@knowledge-bulk/connect",
            json={
                "source_uids": source_uids,
                "target_uids": target_uids,
                "connection_type": "bidirectional",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

<<<<<<< HEAD
        self.assertEqual(data["operation"], "bulk_connect")
        self.assertEqual(data["connection_type"], "bidirectional")
=======
        self.assertEqual(data['operation'], 'bulk_connect')
        self.assertEqual(data['connection_type'], 'bidirectional')
>>>>>>> fixing_linting_and_tests

        # Verify connections were created
        self.assertGreater(data["summary"]["successful"], 0)

    def test_bulk_operation_invalid_type(self):
        """Test invalid bulk operation type."""
        response = self.api_session.post(
            "/@knowledge-bulk/invalid", json={"uids": ["uid-1"]}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_bulk_operation_no_uids(self):
        """Test bulk operation without UIDs."""
        response = self.api_session.post(
            "/@knowledge-bulk/workflow", json={"transition": "publish"}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_bulk_operation_invalid_uids(self):
        """Test bulk operation with invalid UIDs."""
        response = self.api_session.post(
            "/@knowledge-bulk/workflow",
            json={"uids": ["invalid-uid-1", "invalid-uid-2"], "transition": "publish"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # All should fail
        self.assertEqual(data["summary"]["failed"], 2)
        self.assertEqual(data["summary"]["successful"], 0)

    def test_bulk_operation_permissions(self):
        """Test bulk operations with insufficient permissions."""
        # Create a new user with limited permissions
        api.user.create(
            email="limited@example.com", username="limited", password="test_password"
        )

        # Create new session with limited user
        limited_session = RelativeSession(self.portal_url)
<<<<<<< HEAD
        limited_session.headers.update({"Accept": "application/json"})
        limited_session.auth = ("limited", "secret")
=======
        limited_session.headers.update({'Accept': 'application/json'})
        limited_session.auth = ('limited', 'secret')
>>>>>>> fixing_linting_and_tests

        uids = [self.notes[0].UID()]

        response = limited_session.post(
            "/@knowledge-bulk/workflow", json={"uids": uids, "transition": "publish"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should be unauthorized
        self.assertEqual(data["summary"]["unauthorized"], 1)
        self.assertEqual(data["summary"]["successful"], 0)

    def test_bulk_update_invalid_fields(self):
        """Test bulk update with invalid fields."""
        uids = [self.notes[0].UID()]

        response = self.api_session.post(
            "/@knowledge-bulk/update",
            json={
                "uids": uids,
                "updates": {"invalid_field": "value", "another_invalid": 123},
            },
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
<<<<<<< HEAD
        self.assertIn("error", data)
=======
        self.assertIn('error', data)
>>>>>>> fixing_linting_and_tests
