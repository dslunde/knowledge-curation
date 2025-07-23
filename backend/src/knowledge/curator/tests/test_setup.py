"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from knowledge.curator.testing import (
    PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING,
    PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING,
)

import unittest


class TestSetup(unittest.TestCase):
    """Test that plone.app.knowledge is properly installed."""

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if plone.app.knowledge is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'plone.app.knowledge'))

    def test_browserlayer(self):
        """Test that IPloneAppKnowledgeLayer is registered."""
        from knowledge.curator.interfaces import (
            IPloneAppKnowledgeLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IPloneAppKnowledgeLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['plone.app.knowledge'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if plone.app.knowledge is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'plone.app.knowledge'))

    def test_browserlayer_removed(self):
        """Test that IPloneAppKnowledgeLayer is removed."""
        from knowledge.curator.interfaces import \
            IPloneAppKnowledgeLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IPloneAppKnowledgeLayer,
            utils.registered_layers())