#!/usr/bin/env python3
"""
Initialize Vector Database Script
Standalone script to initialize Qdrant vector database and index existing content
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from plone import api
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy, directlyProvides
import transaction
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up the Plone environment for script execution."""
    # Set up the request environment  
    app = makerequest(globals()["app"])
    request = app.REQUEST

    # Add the Knowledge Curator layer to the request
    ifaces = [IKnowledgeCuratorLayer]
    for iface in directlyProvidedBy(request):
        ifaces.append(iface)
    directlyProvides(request, *ifaces)

    # Set up admin user security context
    admin = app.acl_users.getUserById("admin")
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)
    
    return app

def initialize_vector_database():
    """Initialize the vector database and index existing content."""
    print("=== INITIALIZING VECTOR DATABASE ===")
    
    try:
        app = setup_environment()
        portal = app.Plone
        
        # Set site context
        from zope.component.hooks import setSite
        setSite(portal)
        
        # Initialize vector database
        from knowledge.curator.vector.management import VectorCollectionManager
        
        print("1. Initializing Qdrant collection...")
        manager = VectorCollectionManager()
        success = manager.initialize_database()
        
        if not success:
            print("❌ Failed to initialize vector database collection")
            return False
            
        print("✅ Vector database collection initialized")
        
        # Check for existing content to index
        print("2. Checking for existing content to index...")
        catalog = api.portal.get_tool('portal_catalog')
        
        supported_types = ["KnowledgeItem", "BookmarkPlus", "ResearchNote", "LearningGoal", "ProjectLog"]
        indexable_states = ["private", "process", "reviewed", "published"]
        
        query = {
            "portal_type": supported_types,
            "review_state": indexable_states
        }
        
        brains = catalog.searchResults(**query)
        print(f"Found {len(brains)} content items to index")
        
        if len(brains) > 0:
            # Rebuild the vector index
            print("3. Building vector index...")
            result = manager.rebuild_index(
                content_types=supported_types,
                clear_first=True
            )
            
            if result.get("success"):
                print(f"✅ Vector index built successfully!")
                print(f"   - Processed: {result['processed']} items")
                print(f"   - Errors: {result.get('errors', 0)}")
                print(f"   - Duration: {result['duration_seconds']:.2f} seconds")
            else:
                print(f"❌ Vector index build failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("📝 No content found to index")
            
        # Final health check
        print("4. Running health check...")
        health = manager.health_check()
        
        if health.get("healthy"):
            print("✅ Vector database is healthy and ready")
            stats = manager.get_database_stats()
            print(f"   - Total vectors: {stats.get('total_vectors', 0)}")
            
            distribution = stats.get('content_type_distribution', {})
            if distribution:
                print("   - Content distribution:")
                for content_type, count in distribution.items():
                    print(f"     * {content_type}: {count}")
        else:
            print(f"⚠️ Health check failed: {health}")
            return False
            
        # Commit changes
        transaction.commit()
        print("\n✅ Vector database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Vector database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = initialize_vector_database()
    if not success:
        exit(1) 