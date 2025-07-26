#!/usr/bin/env python3
"""
Diagnostic script to test the @types/LearningGoal endpoint
and understand what's causing the schema resolution error.
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides
import os
import transaction


def test_types_endpoint():
    """Test the @types/LearningGoal endpoint directly"""
    
    portal_id = os.environ.get("PLONE_SITE_ID", "Plone")
    
    print("=== TESTING @types/LearningGoal ENDPOINT ===")
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
    
    # Set up security context as anonymous first
    print("\n1. Testing as ANONYMOUS user:")
    try:
        # Get the types tool
        portal_types = site.portal_types
        learning_goal_fti = portal_types.get('LearningGoal')
        
        if learning_goal_fti is None:
            print("❌ LearningGoal FTI not found in portal_types!")
            return False
            
        print(f"✅ LearningGoal FTI found: {learning_goal_fti}")
        
        # Try to get the schema
        print("Attempting to get schema...")
        try:
            schema = learning_goal_fti.lookupSchema()
            print(f"✅ Schema lookup successful: {schema}")
        except Exception as e:
            print(f"❌ Schema lookup failed: {e}")
            import traceback
            traceback.print_exc()
            
        # Try to get the model
        print("Attempting to get model...")
        try:
            model = learning_goal_fti.lookupModel()
            print(f"✅ Model lookup successful: {model}")
        except Exception as e:
            print(f"❌ Model lookup failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ General error testing as anonymous: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testing as ADMIN user:")
    # Set up security context as admin
    admin = app.acl_users.getUserById("admin")
    if admin is None:
        print("❌ Admin user not found!")
        return False
        
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)
    
    try:
        # Test again with admin privileges
        portal_types = site.portal_types
        learning_goal_fti = portal_types.get('LearningGoal')
        
        print("Attempting to get schema as admin...")
        try:
            schema = learning_goal_fti.lookupSchema()
            print(f"✅ Schema lookup successful as admin: {schema}")
        except Exception as e:
            print(f"❌ Schema lookup failed as admin: {e}")
            import traceback
            traceback.print_exc()
            
        print("Attempting to get model as admin...")
        try:
            model = learning_goal_fti.lookupModel()
            print(f"✅ Model lookup successful as admin: {model}")
        except Exception as e:
            print(f"❌ Model lookup failed as admin: {e}")
            import traceback
            traceback.print_exc()
            
        # Try to simulate the REST API call
        print("\n3. Testing REST API types endpoint simulation:")
        try:
            from plone.restapi.types.utils import get_info_for_type
            type_info = get_info_for_type('LearningGoal', site, request)
            print(f"✅ REST API type info successful: keys = {list(type_info.keys())}")
            
            if '@components' in type_info:
                print(f"✅ @components present: {list(type_info['@components'].keys())}")
            else:
                print("❌ @components missing from type info!")
                
        except Exception as e:
            print(f"❌ REST API simulation failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ General error testing as admin: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n4. Checking behavior registration:")
    try:
        from plone.behavior.interfaces import IBehavior
        from zope.component import getUtility
        
        behaviors_to_check = [
            'plone.app.discussion.behaviors.IAllowDiscussion',
            'knowledge.curator.knowledge_graph',
            'knowledge.curator.ai_enhanced',
            'knowledge.curator.spaced_repetition'
        ]
        
        for behavior_name in behaviors_to_check:
            try:
                behavior = getUtility(IBehavior, name=behavior_name)
                print(f"✅ Behavior '{behavior_name}' is registered: {behavior}")
            except Exception as e:
                print(f"❌ Behavior '{behavior_name}' not found: {e}")
                
    except Exception as e:
        print(f"❌ Error checking behaviors: {e}")
        import traceback
        traceback.print_exc()
    
    return True


if __name__ == "__main__":
    success = test_types_endpoint()
    if success:
        print("\n✅ Diagnostic completed!")
    else:
        print("\n❌ Diagnostic failed!") 