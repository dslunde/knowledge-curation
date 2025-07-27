#!/usr/bin/env python3
"""
Test script to verify automatic vectorization works for Knowledge Items, Bookmark+, and Research Notes.
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from plone import api
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy, directlyProvides
import transaction
import requests
import json
import time


def setup_environment():
    """Set up the request environment"""
    app = makerequest(globals()["app"])
    request = app.REQUEST

    ifaces = [IKnowledgeCuratorLayer]
    for iface in directlyProvidedBy(request):
        ifaces.append(iface)
    directlyProvides(request, *ifaces)

    admin = app.acl_users.getUserById("admin")
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)

    return app


def check_qdrant_contents():
    """Check QDrant contents"""
    try:
        response = requests.post(
            "http://localhost:6333/collections/plone_knowledge/points/scroll",
            headers={"Content-Type": "application/json"},
            json={"limit": 100, "with_payload": True, "with_vector": False}
        )
        data = response.json()
        return data["result"]["points"]
    except Exception as e:
        print(f"Error checking QDrant: {e}")
        return []


def create_test_content(portal):
    """Create test content objects"""
    created_objects = {}
    
    print("Creating test content for automatic vectorization...")
    
    # 1. Knowledge Item
    try:
        knowledge_item = api.content.create(
            container=portal,
            type='KnowledgeItem',
            id='auto-test-knowledge-item',
            title='Auto-Vectorization Test Knowledge Item',
            description='Testing automatic vectorization for knowledge items',
            content='This knowledge item should be automatically vectorized when created.',
            knowledge_type='factual',
            difficulty_level='beginner',
            tags=['auto-test', 'vectorization']
        )
        created_objects['KnowledgeItem'] = knowledge_item
        print(f"  ✓ Created Knowledge Item (state: {api.content.get_state(knowledge_item)})")
    except Exception as e:
        print(f"  ✗ Failed to create Knowledge Item: {e}")

    # 2. Bookmark+
    try:
        bookmark = api.content.create(
            container=portal,
            type='BookmarkPlus',
            id='auto-test-bookmark',
            title='Auto-Vectorization Test Bookmark',
            description='Testing automatic vectorization for bookmarks',
            url='https://example.com/auto-test',
            notes='This bookmark should be automatically vectorized when created.',
            importance='medium',
            related_knowledge_items=[knowledge_item.UID()] if 'KnowledgeItem' in created_objects else [],
            resource_type='article',
            content_quality='medium',
            tags=['auto-test', 'bookmark']
        )
        created_objects['BookmarkPlus'] = bookmark
        print(f"  ✓ Created Bookmark+ (state: {api.content.get_state(bookmark)})")
    except Exception as e:
        print(f"  ✗ Failed to create Bookmark+: {e}")

    # 3. Research Note (with simplified fields)
    try:
        research_note = api.content.create(
            container=portal,
            type='ResearchNote',
            id='auto-test-research-note',
            title='Auto-Vectorization Test Research Note',
            description='Testing automatic vectorization for research notes',
            content='This research note should be automatically vectorized when created.',
            tags=['auto-test', 'research'],
            research_method='Automated testing methodology',
            # Note: Using defaults for annotation fields to test simplified creation
        )
        created_objects['ResearchNote'] = research_note
        print(f"  ✓ Created Research Note (state: {api.content.get_state(research_note)})")
    except Exception as e:
        print(f"  ✗ Failed to create Research Note: {e}")

    # 4. Learning Goal (should NOT be vectorized)
    try:
        learning_goal = api.content.create(
            container=portal,
            type='LearningGoal',
            id='auto-test-learning-goal',
            title='Auto-Vectorization Test Learning Goal',
            description='This should NOT be vectorized',
            target_date=api.portal.get().restrictedTraverse('@@plone').toLocalizedTime(
                time.time() + (30 * 24 * 60 * 60)  # 30 days from now
            ),
            priority='medium',
            tags=['auto-test', 'should-not-vectorize']
        )
        created_objects['LearningGoal'] = learning_goal
        print(f"  ✓ Created Learning Goal (state: {api.content.get_state(learning_goal)}) - should NOT vectorize")
    except Exception as e:
        print(f"  ✗ Failed to create Learning Goal: {e}")

    return created_objects


def main():
    """Main test function"""
    print("=== AUTOMATIC VECTORIZATION TEST ===")
    
    # Set up environment
    app = setup_environment()
    portal = app.Plone
    
    # Check initial QDrant state
    print("\n1. Checking initial QDrant state...")
    initial_points = check_qdrant_contents()
    initial_count = len(initial_points)
    print(f"   Initial QDrant point count: {initial_count}")
    
    # Create test content
    print("\n2. Creating test content...")
    created_objects = create_test_content(portal)
    
    # Commit transaction to trigger events
    print("\n3. Committing transaction to trigger vectorization events...")
    transaction.commit()
    
    # Wait a moment for async processing
    print("   Waiting 3 seconds for vectorization to complete...")
    time.sleep(3)
    
    # Check final QDrant state
    print("\n4. Checking final QDrant state...")
    final_points = check_qdrant_contents()
    final_count = len(final_points)
    vectors_added = final_count - initial_count
    
    print(f"   Final QDrant point count: {final_count}")
    print(f"   Vectors added: {vectors_added}")
    
    # Analyze results
    print(f"\n5. VECTORIZATION RESULTS:")
    
    if vectors_added > 0:
        print(f"   ✓ SUCCESS: {vectors_added} objects were automatically vectorized")
        
        # Identify which types were vectorized
        vectorized_types = set()
        for point in final_points[initial_count:]:  # Only new points
            payload = point.get('payload', {})
            content_type = payload.get('portal_type')
            if content_type:
                vectorized_types.add(content_type)
        
        print(f"   Vectorized content types: {list(vectorized_types)}")
        
        # Expected: KnowledgeItem, BookmarkPlus, ResearchNote
        # Should NOT include: LearningGoal
        expected_vectorized = {'KnowledgeItem', 'BookmarkPlus', 'ResearchNote'}
        expected_not_vectorized = {'LearningGoal'}
        
        correctly_vectorized = vectorized_types & expected_vectorized
        incorrectly_vectorized = vectorized_types & expected_not_vectorized
        missing_vectorized = expected_vectorized - vectorized_types
        
        if correctly_vectorized:
            print(f"   ✓ Correctly vectorized: {list(correctly_vectorized)}")
        if missing_vectorized:
            print(f"   ⚠️ Missing vectorization: {list(missing_vectorized)}")
        if incorrectly_vectorized:
            print(f"   ❌ Incorrectly vectorized: {list(incorrectly_vectorized)}")
            
        if missing_vectorized or incorrectly_vectorized:
            print(f"   ❌ PARTIAL SUCCESS: Some issues with selective vectorization")
        else:
            print(f"   ✅ COMPLETE SUCCESS: Automatic vectorization working correctly!")
            
    else:
        print(f"   ❌ FAILURE: No automatic vectorization occurred")
        print("   Check configuration and event handlers")
    
    # Summary
    print(f"\n=== AUTOMATIC VECTORIZATION TEST COMPLETED ===")
    print(f"Created objects: {len(created_objects)}")
    print(f"Expected vectorized: KnowledgeItem, BookmarkPlus, ResearchNote")
    print(f"Expected NOT vectorized: LearningGoal")
    print(f"Actual vectors added: {vectors_added}")


if __name__ == "__main__":
    main() 