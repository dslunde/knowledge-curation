"""Base module for unittesting."""

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import knowledge.curator


class PloneAppKnowledgeLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=knowledge.curator)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'knowledge.curator:default')


PLONE_APP_KNOWLEDGE_FIXTURE = PloneAppKnowledgeLayer()


PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_APP_KNOWLEDGE_FIXTURE,),
    name='PloneAppKnowledgeLayer:IntegrationTesting',
)


PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_KNOWLEDGE_FIXTURE,),
    name='PloneAppKnowledgeLayer:FunctionalTesting',
)


PLONE_APP_KNOWLEDGE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONE_APP_KNOWLEDGE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='PloneAppKnowledgeLayer:AcceptanceTesting',
)
