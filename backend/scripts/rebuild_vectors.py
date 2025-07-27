#!/usr/bin/env python3
"""
Script to rebuild vector index for testing vectorization.
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from knowledge.curator.vector.management import VectorCollectionManager
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy, directlyProvides
import transaction


def setup_environment():
    """Set up the request environment"""
    # Set up the request environment - app is provided by Zope context
    app = makerequest(globals()["app"])
    request = app.REQUEST

    # Add Knowledge Curator layer
    ifaces = [IKnowledgeCuratorLayer]
    for iface in directlyProvidedBy(request):
        ifaces.append(iface)
    directlyProvides(request, *ifaces)

    # Set up admin user
    admin = app.acl_users.getUserById("admin")
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)

    return app


def main():
    """Main function to rebuild vector index"""
    print("=== VECTOR INDEX REBUILD TEST ===")
    
    # Set up environment
    app = setup_environment()
    
    print("Rebuilding vector index for test content...")
    
    try:
        manager = VectorCollectionManager()
        
        # Rebuild index for our test content types
        result = manager.rebuild_index(
            content_types=["KnowledgeItem", "BookmarkPlus"],
            clear_first=False,
            batch_size=100
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Processed: {result.get('processed', 0)} items")
        print(f"Errors: {result.get('errors', 0)}")
        
        if result.get('duration_seconds'):
            print(f"Duration: {result['duration_seconds']:.2f} seconds")
        
        if result.get('success'):
            transaction.commit()
            print("✓ Transaction committed")
            print("✓ Vector index rebuild completed successfully")
        else:
            print(f"✗ Failed to rebuild vector index: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"✗ Error during vector rebuild: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 