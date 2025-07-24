from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_ACCEPTANCE_TESTING as ACCEPTANCE_TESTING
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING as FUNCTIONAL_TESTING
from knowledge.curator.testing import PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING as INTEGRATION_TESTING
from pytest_plone import fixtures_factory


pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory((
        (ACCEPTANCE_TESTING, "acceptance"),
        (FUNCTIONAL_TESTING, "functional"),
        (INTEGRATION_TESTING, "integration"),
    ))
)
