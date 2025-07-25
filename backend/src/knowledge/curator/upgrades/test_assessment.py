"""Test script for assessment infrastructure.

This script can be run to test the assessment functionality
and validate the assessment results.
"""

import logging
from pprint import pprint

from plone import api
from knowledge.curator.upgrades.assess_current_state import (
    DataAssessment,
    assess_current_state,
    quick_entity_count,
    check_migration_conflicts,
    assess_content_type
)

logger = logging.getLogger("knowledge.curator.test_assessment")


def test_assessment_functions():
    """Test all assessment functions."""
    print("=" * 50)
    print("TESTING ASSESSMENT INFRASTRUCTURE")
    print("=" * 50)
    
    try:
        # Get portal context
        portal = api.portal.get()
        
        # Test 1: Quick entity count
        print("\n1. Testing quick entity count...")
        entity_counts = quick_entity_count(portal)
        print(f"Entity counts: {entity_counts}")
        
        # Test 2: Migration conflicts
        print("\n2. Testing migration conflict detection...")
        conflicts = check_migration_conflicts(portal)
        print(f"Found {len(conflicts)} conflicts")
        if conflicts:
            print("Sample conflicts:")
            for conflict in conflicts[:3]:  # Show first 3
                pprint(conflict)
        
        # Test 3: Individual content type assessments
        content_types = ['KnowledgeItem', 'ResearchNote', 'LearningGoal', 'ProjectLog']
        
        for content_type in content_types:
            print(f"\n3.{content_types.index(content_type) + 1}. Testing {content_type} assessment...")
            try:
                assessment = assess_content_type(portal, content_type)
                print(f"{content_type} assessment summary:")
                print(f"  - Total count: {assessment.get('total_count', 0)}")
                print(f"  - Migration needs: {assessment.get('migration_needs', {})}")
            except Exception as e:
                print(f"  - Error: {str(e)}")
        
        # Test 4: Comprehensive assessment
        print("\n4. Testing comprehensive assessment...")
        try:
            full_report = assess_current_state(portal)
            print("Full assessment completed successfully!")
            print(f"Assessment metadata: {full_report.get('assessment_metadata', {})}")
            print(f"Migration readiness: {full_report.get('migration_readiness', {})}")
            
            # Show recommendations
            recommendations = full_report.get('recommendations', [])
            if recommendations:
                print(f"\nTop 3 recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. [{rec.get('priority', 'medium')}] {rec.get('recommendation', 'N/A')}")
        
        except Exception as e:
            print(f"Comprehensive assessment failed: {str(e)}")
            logger.error(f"Comprehensive assessment error: {str(e)}")
        
        print("\n" + "=" * 50)
        print("ASSESSMENT TESTING COMPLETED")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Assessment testing failed: {str(e)}")
        logger.error(f"Assessment testing error: {str(e)}")
        return False


def print_assessment_summary(report):
    """Print a human-readable summary of the assessment report."""
    print("\n" + "=" * 60)
    print("MIGRATION ASSESSMENT SUMMARY")
    print("=" * 60)
    
    # Entity counts
    entity_counts = report.get('entity_counts', {})
    print(f"\nENTITY COUNTS:")
    print(f"  Total Items: {entity_counts.get('total_items', 0)}")
    print(f"  Knowledge Items: {entity_counts.get('KnowledgeItem', 0)}")
    print(f"  Research Notes: {entity_counts.get('ResearchNote', 0)}")
    print(f"  Learning Goals: {entity_counts.get('LearningGoal', 0)}")
    print(f"  Project Logs: {entity_counts.get('ProjectLog', 0)}")
    print(f"  Bookmarks: {entity_counts.get('BookmarkPlus', 0)}")
    print(f"  Migration Complexity Score: {entity_counts.get('migration_complexity_score', 0):.1f}")
    
    # Migration readiness
    readiness = report.get('migration_readiness', {})
    print(f"\nMIGRATION READINESS:")
    print(f"  Overall Score: {readiness.get('overall_score', 0)}/100")
    print(f"  Readiness Level: {readiness.get('readiness_level', 'unknown').upper()}")
    print(f"  Blocking Issues: {readiness.get('blocking_issues', 0)}")
    print(f"  Warning Issues: {readiness.get('warning_issues', 0)}")
    print(f"  Est. Migration Time: {readiness.get('estimated_migration_time', 'unknown').upper()}")
    
    # Conflicts summary
    conflicts = report.get('migration_conflicts', [])
    if conflicts:
        conflict_types = {}
        for conflict in conflicts:
            ctype = conflict.get('type', 'unknown')
            if ctype not in conflict_types:
                conflict_types[ctype] = 0
            conflict_types[ctype] += 1
        
        print(f"\nCONFLICTS BY TYPE:")
        for ctype, count in conflict_types.items():
            print(f"  {ctype}: {count}")
    
    # Recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        print(f"\nTOP RECOMMENDATIONS:")
        critical_recs = [r for r in recommendations if r.get('priority') == 'critical']
        high_recs = [r for r in recommendations if r.get('priority') == 'high']
        
        for rec in critical_recs[:3]:
            print(f"  [CRITICAL] {rec.get('recommendation', 'N/A')}")
        
        for rec in high_recs[:3]:
            print(f"  [HIGH] {rec.get('recommendation', 'N/A')}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # This can be run as a standalone script for testing
    test_assessment_functions()