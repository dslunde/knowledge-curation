import logging

from knowledge.curator.testing import (
    PLONE_APP_KNOWLEDGE_ACCEPTANCE_TESTING as ACCEPTANCE_TESTING,
)
from knowledge.curator.testing import (
    PLONE_APP_KNOWLEDGE_FUNCTIONAL_TESTING as FUNCTIONAL_TESTING,
)
from knowledge.curator.testing import (
    PLONE_APP_KNOWLEDGE_INTEGRATION_TESTING as INTEGRATION_TESTING,
)

logger = logging.getLogger(__name__)

# Conditional import for pytest_plone
try:
    from pytest_plone import fixtures_factory

    pytest_plugins = ["pytest_plone"]

    globals().update(
        fixtures_factory((
            (ACCEPTANCE_TESTING, "acceptance"),
            (FUNCTIONAL_TESTING, "functional"),
            (INTEGRATION_TESTING, "integration"),
        ))
    )
    logger.info("pytest_plone available - full testing fixtures loaded")
except ImportError as e:
    logger.warning(f"pytest_plone not available: {e}")
    logger.warning("Running with limited testing capabilities")
    # When pytest_plone is not available, we can still run basic tests
    # but without the full Plone testing fixtures
