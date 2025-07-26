#!/usr/bin/env python3
"""
Script to reinstall the Knowledge Curator add-on profile.
This is useful when FTI configurations have been updated and need to be reapplied.
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from Products.GenericSetup.tool import SetupTool
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides
import os
import transaction


def reinstall_addon():
    """Reinstall the Knowledge Curator add-on profile"""
    
    portal_id = os.environ.get("PLONE_SITE_ID", "Plone")
    
    print("=== REINSTALLING KNOWLEDGE CURATOR ADD-ON ===")
    print(f"Target site: {portal_id}")
    
    # Set up the request environment
    app = makerequest(globals()["app"])
    request = app.REQUEST
    
    # Add our layer to the request
    ifaces = [IKnowledgeCuratorLayer]
    for iface in directlyProvidedBy(request):
        ifaces.append(iface)
    directlyProvides(request, *ifaces)
    
    # Get the Plone site
    try:
        site = app[portal_id]
    except KeyError:
        print(f"ERROR: Site '{portal_id}' not found!")
        print("Available sites:", list(app.objectIds()))
        return False
    
    # Set up security context
    admin = app.acl_users.getUserById("admin")
    if admin is None:
        print("ERROR: Admin user not found!")
        return False
        
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)
    
    print(f"Reinstalling Knowledge Curator profile on site: {site.getId()}")
    
    try:
        # Get the portal_setup tool
        portal_setup: SetupTool = site.portal_setup
        
        # Run all import steps from the Knowledge Curator profile
        print("Running all import steps from Knowledge Curator profile...")
        portal_setup.runAllImportStepsFromProfile("profile-knowledge.curator:default")
        
        # Commit the transaction
        transaction.commit()
        
        print("✅ Knowledge Curator add-on reinstalled successfully!")
        print("FTI configurations have been updated.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR reinstalling Knowledge Curator profile: {e}")
        import traceback
        traceback.print_exc()
        transaction.abort()
        return False


if __name__ == "__main__":
    success = reinstall_addon()
    if success:
        print("\n✅ Reinstallation completed successfully!")
        print("The backend should now recognize the updated content type configurations.")
    else:
        print("\n❌ Reinstallation failed!")
        print("Please check the error messages above.") 