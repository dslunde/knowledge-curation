"""Test script for v3 data migration.

This script can be run through Plone's debug instance to test the migration
without going through the full upgrade process.

Usage:
    bin/instance debug
    >>> from knowledge.curator.upgrades.test_v3_migration import test_migration
    >>> test_migration()
"""

from plone import api
from knowledge.curator.upgrades.to_v3 import V3DataMigration
import transaction


def test_migration(dry_run=True):
    """Test the v3 migration on a subset of content.
    
    Args:
        dry_run: If True, changes will be rolled back
    """
    print("Starting test migration...")
    
    app = api.portal.get()
    migration = V3DataMigration(app)
    
    # Test on a limited number of items
    catalog = api.portal.get_tool("portal_catalog")
    
    test_results = {
        'ResearchNote': {'success': 0, 'failed': 0},
        'LearningGoal': {'success': 0, 'failed': 0},
        'ProjectLog': {'success': 0, 'failed': 0}
    }
    
    for portal_type in ['ResearchNote', 'LearningGoal', 'ProjectLog']:
        print(f"\nTesting {portal_type} migration...")
        brains = catalog(portal_type=portal_type)[:5]  # Test on first 5 items
        
        for brain in brains:
            try:
                obj = brain.getObject()
                print(f"  - Migrating {obj.getId()}...")
                
                # Show before state
                if portal_type == 'ResearchNote' and hasattr(obj, 'key_insights'):
                    print(f"    Before: {len(obj.key_insights)} insights")
                    if obj.key_insights:
                        print(f"    First insight type: {type(obj.key_insights[0])}")
                
                # Perform migration
                if portal_type == 'ResearchNote':
                    migration.migrate_research_note(obj)
                elif portal_type == 'LearningGoal':
                    migration.migrate_learning_goal(obj)
                elif portal_type == 'ProjectLog':
                    migration.migrate_project_log(obj)
                
                # Show after state
                if portal_type == 'ResearchNote' and hasattr(obj, 'key_insights'):
                    print(f"    After: {len(obj.key_insights)} insights")
                    if obj.key_insights:
                        print(f"    First insight type: {type(obj.key_insights[0])}")
                        print(f"    First insight structure: {dict(obj.key_insights[0])}")
                
                test_results[portal_type]['success'] += 1
                
            except Exception as e:
                print(f"    ERROR: {str(e)}")
                test_results[portal_type]['failed'] += 1
    
    # Print summary
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    for portal_type, results in test_results.items():
        print(f"{portal_type}:")
        print(f"  - Success: {results['success']}")
        print(f"  - Failed: {results['failed']}")
    
    if dry_run:
        print("\nDRY RUN - Rolling back changes...")
        transaction.abort()
    else:
        print("\nCommitting changes...")
        transaction.commit()
    
    print("\nTest complete!")
    

def check_content_state():
    """Check the current state of content before migration."""
    catalog = api.portal.get_tool("portal_catalog")
    
    for portal_type in ['ResearchNote', 'LearningGoal', 'ProjectLog']:
        print(f"\n{portal_type} content state:")
        brains = catalog(portal_type=portal_type)
        print(f"  Total items: {len(brains)}")
        
        if brains:
            # Check first item
            obj = brains[0].getObject()
            print(f"  Sample item: {obj.getId()}")
            
            if portal_type == 'ResearchNote':
                if hasattr(obj, 'key_insights'):
                    print(f"    - key_insights: {type(obj.key_insights)}")
                    if obj.key_insights:
                        print(f"    - First insight: {repr(obj.key_insights[0])}")
                if hasattr(obj, 'connections'):
                    print(f"    - connections: {len(getattr(obj, 'connections', []))} items")
                    
            elif portal_type == 'LearningGoal':
                if hasattr(obj, 'milestones'):
                    print(f"    - milestones: {type(obj.milestones)}")
                    if obj.milestones:
                        print(f"    - First milestone: {repr(obj.milestones[0])}")
                        
            elif portal_type == 'ProjectLog':
                if hasattr(obj, 'entries'):
                    print(f"    - entries: {type(obj.entries)}")
                    if obj.entries:
                        print(f"    - First entry: {repr(obj.entries[0])}")
                if hasattr(obj, 'deliverables'):
                    print(f"    - deliverables: {type(obj.deliverables)}")
                    if obj.deliverables:
                        print(f"    - First deliverable: {repr(obj.deliverables[0])}")


def create_test_content():
    """Create test content with old-style data for migration testing."""
    from persistent.list import PersistentList
    
    portal = api.portal.get()
    
    # Create test ResearchNote with old-style data
    research_note = api.content.create(
        container=portal,
        type='ResearchNote',
        id='test-research-note-v3',
        title='Test Research Note for V3 Migration'
    )
    research_note.key_insights = PersistentList([
        "This is a simple text insight",
        "Another important finding",
        "Critical observation about the research"
    ])
    research_note.connections = PersistentList(['some-uid-1', 'some-uid-2'])
    
    # Create test LearningGoal with old-style data
    learning_goal = api.content.create(
        container=portal,
        type='LearningGoal',
        id='test-learning-goal-v3',
        title='Test Learning Goal for V3 Migration'
    )
    learning_goal.milestones = PersistentList([
        "Complete chapter 1",
        "Practice exercises",
        "Final assessment"
    ])
    
    # Create test ProjectLog with old-style data
    project_log = api.content.create(
        container=portal,
        type='ProjectLog',
        id='test-project-log-v3',
        title='Test Project Log for V3 Migration'
    )
    project_log.entries = PersistentList([
        "Started project planning",
        "Completed initial design",
        "First prototype ready"
    ])
    project_log.deliverables = PersistentList([
        "Design document",
        "Prototype",
        "Final report"
    ])
    
    transaction.commit()
    print("Test content created successfully!")
    
    return {
        'research_note': research_note,
        'learning_goal': learning_goal,
        'project_log': project_log
    }