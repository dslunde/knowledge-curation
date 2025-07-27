"""Post install import steps for knowledge.curator."""

from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
import logging

logger = logging.getLogger("knowledge.curator.setuphandlers")


@implementer(INonInstallable)
class HiddenProfiles:
    """Hidden GenericSetup profiles."""

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "knowledge.curator:uninstall",
        ]


def post_install(context):
    """Post install script."""
    logger.info("Running Knowledge Curator post-install setup...")
    
    # Initialize vector database
    try:
        from knowledge.curator.vector.management import VectorCollectionManager
        
        logger.info("Initializing vector database collection...")
        manager = VectorCollectionManager()
        success = manager.initialize_database()
        
        if success:
            logger.info("✅ Vector database collection initialized successfully")
        else:
            logger.warning("⚠️ Vector database initialization failed - collection may not be available")
            
    except Exception as e:
        logger.error(f"❌ Vector database initialization error: {e}")
        # Don't fail the entire installation if vector DB is unavailable
        logger.warning("Continuing installation without vector database")
    
    # Health check and statistics
    try:
        manager = VectorCollectionManager()
        health = manager.health_check()
        
        if health.get("healthy"):
            logger.info("✅ Vector database health check passed")
            stats = manager.get_database_stats()
            logger.info(f"Vector database ready - total vectors: {stats.get('total_vectors', 0)}")
        else:
            logger.warning(f"⚠️ Vector database health check failed: {health}")
            
    except Exception as e:
        logger.warning(f"Vector database health check error: {e}")
    
    logger.info("Knowledge Curator post-install setup completed")


def uninstall(context):
    """Uninstall script."""
    # Do something at the end of the uninstallation of this package.
