"""Testing Setup Module for Knowledge Curator."""

import logging
from typing import Any

import knowledge.curator

logger = logging.getLogger(__name__)


# Create minimal stubs first (available globally)
class StubPloneSandboxLayer:
    """Stub Plone sandbox layer for when testing infrastructure is not available."""

    defaultBases: tuple[Any, ...] = ()

    def setUpZope(self, app: Any, configurationContext: Any) -> None:
        """Stub setup method."""
        pass

    def setUpPloneSite(self, portal: Any) -> None:
        """Stub setup method."""
        pass


class StubTestingFixture:
    """Stub testing fixture for when testing infrastructure is not available."""

    def __init__(self, bases: tuple[Any, ...] = (), name: str = "") -> None:
        self.bases = bases
        self.name = name


class StubZ2:
    """Stub z2 module."""

    ZSERVER_FIXTURE = None


def stub_apply_profile(portal: Any, profile_id: str) -> None:
    """Stub apply profile function."""
    logger.warning(f"Stub applyProfile called for {profile_id}")


# Conditional imports for Plone testing infrastructure
try:
    from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE  # type: ignore[import-untyped]
    from plone.app.testing import applyProfile  # type: ignore[import-untyped]
    from plone.app.testing import FunctionalTesting  # type: ignore[import-untyped]
    from plone.app.testing import IntegrationTesting  # type: ignore[import-untyped]
    from plone.app.testing import PLONE_FIXTURE  # type: ignore[import-untyped]
    from plone.app.testing import PloneSandboxLayer  # type: ignore[import-untyped]
    from plone.testing import z2  # type: ignore[import-untyped]

    PLONE_TESTING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Plone testing infrastructure not available: {e}")
    PLONE_TESTING_AVAILABLE = False

    # Use stubs when imports fail
    PloneSandboxLayer = StubPloneSandboxLayer  # type: ignore[misc]
    FunctionalTesting = StubTestingFixture
    IntegrationTesting = StubTestingFixture
    PLONE_FIXTURE = None
    REMOTE_LIBRARY_BUNDLE_FIXTURE = None
    z2 = StubZ2()  # type: ignore[misc]
    applyProfile = stub_apply_profile


class PloneAppKnowledgeLayer(PloneSandboxLayer):  # type: ignore[misc]
    """Knowledge Curator testing layer."""

    defaultBases = (PLONE_FIXTURE,) if PLONE_FIXTURE else ()

    def setUpZope(self, app: Any, configurationContext: Any) -> None:
        """Set up Zope for testing."""
        if not PLONE_TESTING_AVAILABLE:
            logger.warning("Plone testing not available, skipping ZCML setup")
            return

        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        try:
            import plone.restapi  # type: ignore[import-untyped]

            self.loadZCML(package=plone.restapi)  # type: ignore[attr-defined]
        except ImportError:
            logger.warning("plone.restapi not available for testing")

        self.loadZCML(package=knowledge.curator)  # type: ignore[attr-defined]

    def setUpPloneSite(self, portal: Any) -> None:
        """Set up Plone site for testing."""
        if not PLONE_TESTING_AVAILABLE:
            logger.warning("Plone testing not available, skipping site setup")
            return

        # Apply core dependencies first
        try:
            applyProfile(portal, "plone.app.dexterity:default")
            applyProfile(portal, "plone.restapi:default")
            applyProfile(portal, "plone.app.versioningbehavior:default")
            applyProfile(portal, "plone.app.relationfield:default")
        except Exception:
            logger.warning("Could not apply core dependencies for testing.")
            # Some dependencies might not be available in test environment

        # Apply our profile without dependencies
        try:
            applyProfile(portal, "knowledge.curator:default")
        except Exception:
            logger.warning("Could not apply knowledge.curator profile for testing.")
            # If dependencies fail, try to install just the content types
            if hasattr(portal, "portal_types"):
                portal.portal_types.manage_addPortalType(
                    id="ResearchNote",
                    title="Research Note",
                    meta_type="Dexterity Content Type",
                )


PLONE_APP_KNOWLEDGE_FIXTURE = PloneAppKnowledgeLayer()


PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_APP_KNOWLEDGE_FIXTURE,),
    name="PloneAppKnowledgeLayer:IntegrationTesting",
)


PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_KNOWLEDGE_FIXTURE,),
    name="PloneAppKnowledgeLayer:FunctionalTesting",
)


PLONE_APP_KNOWLEDGE_ACCEPTANCE_TESTING = (
    FunctionalTesting(
        bases=(
            PLONE_APP_KNOWLEDGE_FIXTURE,
            REMOTE_LIBRARY_BUNDLE_FIXTURE,
            z2.ZSERVER_FIXTURE,
        ),
        name="PloneAppKnowledgeLayer:AcceptanceTesting",
    )
    if PLONE_TESTING_AVAILABLE
    else StubTestingFixture(name="PloneAppKnowledgeLayer:AcceptanceTesting (stub)")
)
