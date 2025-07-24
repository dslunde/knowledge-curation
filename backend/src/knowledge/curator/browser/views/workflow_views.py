"""Workflow-related views and forms."""

from knowledge.curator import _
from plone import api
from plone.z3cform import layout
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope import schema
from zope.interface import Interface

import json
import logging

logger = logging.getLogger(__name__)


class IWorkflowTransitionForm(Interface):
    """Schema for workflow transition form."""

    comment = schema.Text(
        title=_("Comment"),
        description=_("Add a comment about this transition"),
        required=False,
    )


class IPublishForm(IWorkflowTransitionForm):
    """Schema for publish transition with additional validation."""

    confirm_quality = schema.Bool(
        title=_("Content Quality"),
        description=_("I confirm this content meets quality standards"),
        required=True,
    )

    confirm_connections = schema.Bool(
        title=_("Connections Reviewed"),
        description=_("I have reviewed and established relevant connections"),
        required=True,
    )


class WorkflowTransitionForm(form.Form):
    """Base form for workflow transitions."""

    fields = field.Fields(IWorkflowTransitionForm)
    ignoreContext = True

    def __init__(self, context, request):
        super().__init__(context, request)
        self.transition_id = request.get("transition", "")

    @button.buttonAndHandler(_("Confirm Transition"), name="transition")
    def handle_transition(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        try:
            api.content.transition(
                obj=self.context,
                transition=self.transition_id,
                comment=data.get("comment", ""),
            )

            IStatusMessage(self.request).addStatusMessage(
                _("Workflow transition completed successfully."), type="info"
            )

            self.request.response.redirect(self.context.absolute_url())

        except Exception as e:
            IStatusMessage(self.request).addStatusMessage(
                _("Transition failed: ${error}", mapping={"error": str(e)}),
                type="error",
            )

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handle_cancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _("Transition cancelled."), type="info"
        )
        self.request.response.redirect(self.context.absolute_url())


class PublishTransitionForm(WorkflowTransitionForm):
    """Special form for publish transition with extra validation."""

    fields = field.Fields(IPublishForm)

    @button.buttonAndHandler(_("Publish Content"), name="publish")
    def handle_publish(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        if not (data.get("confirm_quality") and data.get("confirm_connections")):
            IStatusMessage(self.request).addStatusMessage(
                _("Please confirm all requirements before publishing."), type="error"
            )
            return

        # Call parent handler
        self.handle_transition(action)


class WorkflowHistoryView(BrowserView):
    """View to display workflow history."""

    def __call__(self):
        self.update()
        return self.index()

    def update(self):
        """Prepare workflow history data."""
        self.history = []

        try:
            # Get workflow history
            workflow_tool = api.portal.get_tool("portal_workflow")
            history = workflow_tool.getInfoFor(self.context, "review_history", [])

            for item in reversed(history):
                self.history.append({
                    "action": item.get("action", "Unknown"),
                    "actor": item.get("actor", "Unknown"),
                    "time": item.get("time", ""),
                    "comments": item.get("comments", ""),
                    "review_state": item.get("review_state", ""),
                })

        except Exception as e:
            logger.error(f"Error getting workflow history: {e!s}")

    def format_date(self, date):
        """Format date for display."""
        if not date:
            return "Unknown"
        return api.portal.get_localized_time(date, long_format=True)


class BulkWorkflowView(BrowserView):
    """View for bulk workflow operations."""

    def __call__(self):
        if self.request.method == "POST":
            return self.handle_bulk_transition()
        return self.index()

    def get_available_transitions(self):
        """Get transitions available for all selected items."""
        uids = self.request.get("uids", [])
        if not uids:
            return []

        # Find common transitions
        common_transitions = None
        workflow_tool = api.portal.get_tool("portal_workflow")

        for uid in uids:
            try:
                obj = api.content.get(UID=uid)
                if not obj:
                    continue

                transitions = workflow_tool.getTransitionsFor(obj)
                transition_ids = {t["id"] for t in transitions}

                if common_transitions is None:
                    common_transitions = transition_ids
                else:
                    common_transitions &= transition_ids

            except Exception:
                logger.exception("Error getting transitions for object with UID: %s", uid)
                continue

        if not common_transitions:
            return []

        # Get transition info
        result = []
        for uid in uids[:1]:  # Just need one object to get transition details
            obj = api.content.get(UID=uid)
            if obj:
                for t in workflow_tool.getTransitionsFor(obj):
                    if t["id"] in common_transitions:
                        result.append(t)
                break

        return result

    def handle_bulk_transition(self):
        """Handle bulk workflow transition."""
        uids = self.request.get("uids", [])
        transition = self.request.get("transition", "")
        comment = self.request.get("comment", "")

        if not (uids and transition):
            return json.dumps({
                "success": False,
                "message": "Missing required parameters",
            })

        success_count = 0
        errors = []

        for uid in uids:
            try:
                obj = api.content.get(UID=uid)
                if obj:
                    api.content.transition(
                        obj=obj, transition=transition, comment=comment
                    )
                    success_count += 1
            except Exception as e:
                errors.append(f"{uid}: {e!s}")

        response = {
            "success": success_count > 0,
            "message": f"Transitioned {success_count} items successfully.",
            "errors": errors,
        }

        self.request.response.setHeader("Content-Type", "application/json")
        return json.dumps(response)


# Form wrappers
WorkflowTransitionFormView = layout.wrap_form(
    WorkflowTransitionForm, label=_("Workflow Transition")
)

PublishTransitionFormView = layout.wrap_form(
    PublishTransitionForm, label=_("Publish Content")
)
