from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.factory import addPloneSite
from Products.GenericSetup.tool import SetupTool
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides

import os
import transaction


truthy = frozenset(("t", "true", "y", "yes", "on", "1"))


def asbool(s):
    """Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is a :term:`truthy string`. If ``s`` is already one of the
    boolean values ``True`` or ``False``, return it."""
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    s = str(s).strip()
    return s.lower() in truthy


DELETE_EXISTING = asbool(os.getenv("DELETE_EXISTING"))
EXAMPLE_CONTENT = asbool(os.getenv("EXAMPLE_CONTENT", "1"))
CREATE_DEMO_DATA = asbool(os.getenv("CREATE_DEMO_DATA", "1"))  # Default to True for demo

admin_user = os.environ.get("PLONE_SITE_ID", "admin")
admin_pass = os.environ.get("PLONE_SITE_PASSWORD", "admin")
portal_id = os.environ.get("PLONE_SITE_ID", "Plone")
site_title = os.environ.get("PLONE_SITE_TITLE", "Personal Knowledge Curation")

print("=== CREATE SITE SCRIPT STARTING ===")
print(f"DELETE_EXISTING: {DELETE_EXISTING}")
print(f"EXAMPLE_CONTENT: {EXAMPLE_CONTENT}")
print(f"CREATE_DEMO_DATA: {CREATE_DEMO_DATA}")
print(f"portal_id: {portal_id}")

# Set up the request environment
app = makerequest(globals()["app"])
request = app.REQUEST

ifaces = [IKnowledgeCuratorLayer]
for iface in directlyProvidedBy(request):
    ifaces.append(iface)

directlyProvides(request, *ifaces)

admin = app.acl_users.getUserById("admin")
admin = admin.__of__(app.acl_users)
newSecurityManager(None, admin)

site_id = "Plone"
payload = {
    "title": "Knowledge Curator",
    "profile_id": _DEFAULT_PROFILE,
    "distribution_name": "volto",
    "setup_content": False,
    "default_language": "en",
    "portal_timezone": "UTC",
}

print(f"Existing sites: {list(app.objectIds())}")

if site_id in app.objectIds() and DELETE_EXISTING:
    print(f"Deleting existing site: {site_id}")
    app.manage_delObjects([site_id])
    transaction.commit()
    app._p_jar.sync()
    print("Site deleted successfully")

if site_id not in app.objectIds():
    print(f"Creating new site: {site_id}")
    site = addPloneSite(app, site_id, **payload)
    transaction.commit()
    print("Base site created successfully")

    portal_setup: SetupTool = site.portal_setup
    print("Installing Knowledge Curator profile...")
    try:
        portal_setup.runAllImportStepsFromProfile("profile-knowledge.curator:default")
        transaction.commit()
        print("Knowledge Curator profile installed successfully!")
    except Exception as e:
        print(f"ERROR installing Knowledge Curator profile: {e}")
        import traceback

        traceback.print_exc()

    app._p_jar.sync()
    print("Site creation completed")
    
    # Create demo data if requested
    if CREATE_DEMO_DATA:
        print("\n=== CREATING DEMO DATA ===")
        try:
            # Import and execute demo data creation
            from knowledge.curator.scripts.create_demo_data import create_demo_data
            
            # Execute demo data creation in the context of the newly created site
            create_demo_data()
            print("Demo data creation completed successfully!")
            
        except Exception as e:
            print(f"ERROR creating demo data: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing without demo data...")
else:
    print(f"Site {site_id} already exists and DELETE_EXISTING is False")
    
    # Still try to create demo data if requested and site exists
    if CREATE_DEMO_DATA:
        print("\n=== CREATING DEMO DATA FOR EXISTING SITE ===")
        try:
            from knowledge.curator.scripts.create_demo_data import create_demo_data
            create_demo_data()
            print("Demo data creation completed successfully!")
            
        except Exception as e:
            print(f"ERROR creating demo data: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing without demo data...")

print("=== CREATE SITE SCRIPT COMPLETED ===")
