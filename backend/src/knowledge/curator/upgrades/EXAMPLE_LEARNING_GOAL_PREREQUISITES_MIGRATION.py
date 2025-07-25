#!/usr/bin/env python
"""
Example usage of the Learning Goal Prerequisites Migration.

This script demonstrates how to use the migrate_learning_goal_prerequisites functionality
to convert text-based prerequisites in Learning Goals to Knowledge Item UID references.
"""

from knowledge.curator.upgrades.migrate_relationships import (
    run_learning_goal_prerequisites_migration,
    LearningGoalPrerequisitesMigration,
    migrate_learning_goal_prerequisites
)


def example_basic_migration(context):
    """
    Example: Basic migration using convenience function.
    
    This is the easiest way to run the migration.
    """
    print("Running basic Learning Goal prerequisites migration...")
    
    # Use default settings (batch_size=25, fuzzy_threshold=0.8)
    results = run_learning_goal_prerequisites_migration(context)
    
    print(f"Migration completed with status: {results['status']}")
    print(f"Processed {results['progress']['processed_items']} Learning Goals")
    print(f"Successful conversions: {results['progress']['successful_items']}")
    print(f"Failed conversions: {results['progress']['failed_items']}")
    
    # Check if manual review is needed
    manual_review = results.get('manual_review_report', {})
    if manual_review.get('total_goals_needing_review', 0) > 0:
        print(f"\\nMANUAL REVIEW REQUIRED:")
        print(f"Goals needing review: {manual_review['total_goals_needing_review']}")
        print(f"Total unmatched items: {manual_review['total_unmatched_items']}")
        
        # Print first few items needing review
        for goal in manual_review['goals_requiring_review'][:3]:
            print(f"\\n  Goal: {goal['goal_title']}")
            for item in goal['manual_review_items'][:2]:
                print(f"    - '{item['prerequisite_text']}' ({item['reason']})")
                if item['suggestions']:
                    print(f"      Suggestions: {len(item['suggestions'])} potential matches")
    
    return results


def example_custom_migration(context):
    """
    Example: Custom migration with specific settings.
    
    This shows how to use custom batch size and fuzzy threshold.
    """
    print("Running custom Learning Goal prerequisites migration...")
    
    # Use custom settings
    results = run_learning_goal_prerequisites_migration(
        context, 
        batch_size=10,  # Smaller batches
        fuzzy_threshold=0.9  # Higher threshold for more strict matching
    )
    
    print(f"Migration completed with {results['progress']['processed_items']} items processed")
    
    # Show statistics
    stats = results.get('statistics', {})
    print(f"\\nStatistics:")
    print(f"  Exact matches: {stats.get('exact_matches', 0)}")
    print(f"  Fuzzy matches by score: {stats.get('fuzzy_matches_by_score', {})}")
    print(f"  Unmatched prerequisites: {len(stats.get('unmatched_prerequisites', []))}")
    print(f"  Duplicate matches: {len(stats.get('duplicate_matches', []))}")
    
    return results


def example_advanced_migration(context):
    """
    Example: Advanced migration using the migration class directly.
    
    This gives you full control over the migration process.
    """
    print("Running advanced Learning Goal prerequisites migration...")
    
    # Create migration instance with custom settings
    migration = LearningGoalPrerequisitesMigration(
        context,
        batch_size=15,
        fuzzy_threshold=0.75
    )
    
    # You can add custom validation hooks
    def custom_validation(item):
        # Example: Skip goals with certain titles
        if 'deprecated' in item.title.lower():
            return False, "Skipping deprecated goal"
        return True, "Valid for migration"
    
    migration.add_validation_hook(custom_validation)
    
    # Run the migration with specific options
    results = migration.run(
        validate_first=True,  # Run validation before migration
        create_backup=True    # Create backup for rollback
    )
    
    print(f"Migration completed: {results['status']}")
    
    # Get detailed manual review report
    manual_review_report = migration.get_manual_review_report()
    print(f"Manual review report:")
    print(f"  Goals needing review: {manual_review_report['total_goals_needing_review']}")
    print(f"  Total unmatched items: {manual_review_report['total_unmatched_items']}")
    
    # You can also access detailed statistics
    print(f"\\nDetailed Statistics:")
    for score_range, count in migration.statistics['fuzzy_matches_by_score'].items():
        print(f"  Matches with score {score_range}: {count}")
    
    return results, migration


def example_rollback_migration(migration):
    """
    Example: How to rollback a migration if needed.
    
    Args:
        migration: LearningGoalPrerequisitesMigration instance from advanced example
    """
    print("Rolling back migration if needed...")
    
    try:
        rollback_results = migration.rollback()
        print(f"Rollback completed: {rollback_results['status']}")
        print(f"Items restored: {rollback_results['progress']['successful_items']}")
    except Exception as e:
        print(f"Rollback failed or not needed: {e}")


def example_standalone_function(context):
    """
    Example: Using the standalone function (deprecated approach).
    
    This shows the original function for backward compatibility.
    """
    print("Running standalone migration function...")
    
    # This is the original function approach
    results = migrate_learning_goal_prerequisites(
        context,
        batch_size=20,
        fuzzy_threshold=0.8
    )
    
    print(f"Standalone migration completed: {results['status']}")
    return results


if __name__ == "__main__":
    # This would be run in a Plone context
    print("Learning Goal Prerequisites Migration Examples")
    print("=" * 50)
    print()
    print("To run these examples in a Plone environment:")
    print("1. Start your Plone instance")
    print("2. Access the ZMI or create a migration script")
    print("3. Get the portal context and call one of these functions")
    print()
    print("Example usage in a Plone script:")
    print("  from plone import api")
    print("  portal = api.portal.get()")
    print("  results = example_basic_migration(portal)")
    print()
    print("Available functions:")
    print("- example_basic_migration(context)")
    print("- example_custom_migration(context)")
    print("- example_advanced_migration(context)")
    print("- example_rollback_migration(migration)")
    print("- example_standalone_function(context)")