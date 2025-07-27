#!/usr/bin/env python3
"""
Test script to verify which content types get vectorized in QDrant.
Creates one object of each content type and checks QDrant storage.
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from plone import api
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy, directlyProvides
from datetime import datetime, date, timedelta
import transaction
import requests
import json


def setup_environment():
    """Set up the request environment"""
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


def check_qdrant_contents():
    """Check what's currently in QDrant"""
    try:
        response = requests.get("http://localhost:6333/collections/plone_knowledge")
        collection_info = response.json()
        
        scroll_response = requests.post(
            "http://localhost:6333/collections/plone_knowledge/points/scroll",
            headers={"Content-Type": "application/json"},
            json={"limit": 100, "with_payload": True, "with_vector": False}
        )
        points_data = scroll_response.json()
        
        return {
            "collection_info": collection_info,
            "points": points_data["result"]["points"],
            "count": collection_info["result"]["points_count"]
        }
    except Exception as e:
        print(f"Error checking QDrant: {e}")
        return None


def create_test_content(portal):
    """Create one object of each content type for testing"""
    created_objects = {}
    
    print("Creating test content objects...")
    
    # 1. Knowledge Item
    try:
        knowledge_item = api.content.create(
            container=portal,
            type='KnowledgeItem',
            id='test-knowledge-item',
            title='Test Knowledge Item',
            description='A test knowledge item for vectorization testing',
            content='This is test content for a knowledge item to see if it gets vectorized.',
            knowledge_type='factual',
            difficulty_level='beginner',
            tags=['test', 'vectorization']
        )
        created_objects['KnowledgeItem'] = knowledge_item
        print("  ✓ Created Knowledge Item")
    except Exception as e:
        print(f"  ✗ Failed to create Knowledge Item: {e}")

    # 2. Research Note
    try:
        research_note = api.content.create(
            container=portal,
            type='ResearchNote',
            id='test-research-note',
            title='Test Research Note',
            description='A test research note for vectorization testing',
            content='This is test content for a research note to verify vectorization.',
            tags=['test', 'research'],
            research_method='Testing methodology'
        )
        created_objects['ResearchNote'] = research_note
        print("  ✓ Created Research Note")
    except Exception as e:
        print(f"  ✗ Failed to create Research Note: {e}")

    # 3. Bookmark+
    try:
        bookmark = api.content.create(
            container=portal,
            type='BookmarkPlus',
            id='test-bookmark',
            title='Test Bookmark Plus',
            description='A test bookmark for vectorization testing',
            url='https://example.com',
            notes='This is a test bookmark to check vectorization.',
            importance='medium',
            tags=['test', 'bookmark']
        )
        created_objects['BookmarkPlus'] = bookmark
        print("  ✓ Created Bookmark+")
    except Exception as e:
        print(f"  ✗ Failed to create Bookmark+: {e}")

    # 4. Knowledge Container
    try:
        knowledge_container = api.content.create(
            container=portal,
            type='KnowledgeContainer',
            id='test-knowledge-container',
            title='Test Knowledge Container',
            description='A test knowledge container for vectorization testing',
            collection_type='knowledge_base',
            tags=['test', 'container']
        )
        created_objects['KnowledgeContainer'] = knowledge_container
        print("  ✓ Created Knowledge Container")
    except Exception as e:
        print(f"  ✗ Failed to create Knowledge Container: {e}")

    # 5. Learning Goal
    try:
        learning_goal = api.content.create(
            container=portal,
            type='LearningGoal',
            id='test-learning-goal',
            title='Test Learning Goal',
            description='A test learning goal for vectorization testing',
            target_date=date.today() + timedelta(days=30),
            priority='medium',
            tags=['test', 'learning']
        )
        created_objects['LearningGoal'] = learning_goal
        print("  ✓ Created Learning Goal")
    except Exception as e:
        print(f"  ✗ Failed to create Learning Goal: {e}")

    # 6. Project Log
    try:
        project_log = api.content.create(
            container=portal,
            type='ProjectLog',
            id='test-project-log',
            title='Test Project Log',
            description='A test project log for vectorization testing',
            start_date=date.today(),
            status='planning',
            tags=['test', 'project']
        )
        created_objects['ProjectLog'] = project_log
        print("  ✓ Created Project Log")
    except Exception as e:
        print(f"  ✗ Failed to create Project Log: {e}")

    return created_objects


def trigger_vectorization():
    """Trigger vectorization process"""
    print("\nTriggering vectorization...")
    try:
        from knowledge.curator.vector.management import VectorCollectionManager
        
        manager = VectorCollectionManager()
        result = manager.rebuild_index(
            content_types=["KnowledgeItem", "BookmarkPlus", "ResearchNote", "LearningGoal", "ProjectLog", "KnowledgeContainer"],
            clear_first=False
        )
        
        if result.get("success"):
            print(f"✓ Vectorization completed - {result['processed']} items processed")
            return True
        else:
            print(f"✗ Vectorization failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Vectorization error: {e}")
        return False


def main():
    """Main test function"""
    print("=== TESTING CONTENT TYPE VECTORIZATION ===")
    
    # Set up environment
    app = setup_environment()
    portal = app.Plone
    
    # Check initial QDrant state
    print("\n1. Checking initial QDrant state...")
    initial_state = check_qdrant_contents()
    if initial_state:
        print(f"   Initial QDrant point count: {initial_state['count']}")
    
    # Create test content
    print("\n2. Creating test content...")
    created_objects = create_test_content(portal)
    
    # Commit transaction
    transaction.commit()
    print("   Transaction committed")
    
    # Trigger vectorization
    print("\n3. Triggering vectorization...")
    vectorization_success = trigger_vectorization()
    
    if vectorization_success:
        transaction.commit()
        print("   Vectorization transaction committed")
    
    # Check final QDrant state
    print("\n4. Checking final QDrant state...")
    final_state = check_qdrant_contents()
    
    if final_state:
        print(f"   Final QDrant point count: {final_state['count']}")
        
        if final_state['count'] > 0:
            print("\n5. QDrant Contents Analysis:")
            for i, point in enumerate(final_state['points']):
                payload = point.get('payload', {})
                content_type = payload.get('portal_type', 'Unknown')
                title = payload.get('title', 'No title')
                uid = payload.get('uid', 'No UID')
                print(f"   Point {i+1}: {content_type} - {title} (UID: {uid})")
        else:
            print("\n5. No points found in QDrant after vectorization")
    
    # Summary
    print(f"\n=== VECTORIZATION TEST SUMMARY ===")
    print(f"Created objects: {len(created_objects)}")
    print(f"Content types created: {list(created_objects.keys())}")
    
    if initial_state and final_state:
        vectors_added = final_state['count'] - initial_state['count']
        print(f"Vectors added to QDrant: {vectors_added}")
        
        if vectors_added > 0:
            print(f"\n✓ SUCCESS: {vectors_added} content objects were vectorized")
            
            # Identify which types were vectorized
            vectorized_types = set()
            for point in final_state['points']:
                payload = point.get('payload', {})
                content_type = payload.get('portal_type')
                if content_type:
                    vectorized_types.add(content_type)
            
            print(f"\nVectorized content types: {list(vectorized_types)}")
            
            # Check which types were NOT vectorized
            created_types = set(created_objects.keys())
            not_vectorized = created_types - vectorized_types
            if not_vectorized:
                print(f"NOT vectorized content types: {list(not_vectorized)}")
            else:
                print("All created content types were vectorized!")
                
        else:
            print(f"✗ FAILURE: No content was vectorized")
    
    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    main() 