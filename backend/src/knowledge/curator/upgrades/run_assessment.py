#!/usr/bin/env python3
"""Command-line utility to run migration assessment.

This script can be executed to generate assessment reports and save them to files.
It provides a convenient way to run assessments outside of the Plone interface.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("knowledge.curator.run_assessment")


def save_report_to_file(report, output_path=None):
    """Save assessment report to JSON file."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"migration_assessment_{timestamp}.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Assessment report saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to save report: {str(e)}")
        return None


def print_summary(report):
    """Print a concise summary of the assessment results."""
    print("\n" + "=" * 60)
    print("MIGRATION ASSESSMENT SUMMARY")
    print("=" * 60)
    
    # Basic info
    metadata = report.get('assessment_metadata', {})
    print(f"Assessment Time: {metadata.get('timestamp', 'unknown')}")
    print(f"Plone Version: {metadata.get('plone_version', 'unknown')}")
    
    # Entity counts
    counts = report.get('entity_counts', {})
    print(f"\nCONTENT SUMMARY:")
    print(f"  Total Items: {counts.get('total_items', 0)}")
    
    content_types = ['KnowledgeItem', 'ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
    for ctype in content_types:
        count = counts.get(ctype, 0)
        if count > 0:
            print(f"  {ctype}: {count}")
    
    complexity = counts.get('migration_complexity_score', 0)
    print(f"  Migration Complexity Score: {complexity:.1f}")
    
    # Readiness
    readiness = report.get('migration_readiness', {})
    score = readiness.get('overall_score', 0)
    level = readiness.get('readiness_level', 'unknown').upper()
    blocking = readiness.get('blocking_issues', 0)
    warnings = readiness.get('warning_issues', 0)
    
    print(f"\nMIGRATION READINESS:")
    print(f"  Overall Score: {score}/100")
    print(f"  Readiness Level: {level}")
    print(f"  Blocking Issues: {blocking}")
    print(f"  Warning Issues: {warnings}")
    
    # Conflicts
    conflicts = report.get('migration_conflicts', [])
    if conflicts:
        conflict_types = {}
        for conflict in conflicts:
            ctype = conflict.get('type', 'unknown')
            severity = conflict.get('severity', 'unknown')
            key = f"{ctype} ({severity})"
            conflict_types[key] = conflict_types.get(key, 0) + 1
        
        print(f"\nCONFLICTS DETECTED:")
        for conflict_type, count in sorted(conflict_types.items()):
            print(f"  {conflict_type}: {count}")
    
    # Top recommendations
    recommendations = report.get('recommendations', [])
    if recommendations:
        print(f"\nTOP RECOMMENDATIONS:")
        
        # Show critical and high priority recommendations
        critical_recs = [r for r in recommendations if r.get('priority') == 'critical']
        high_recs = [r for r in recommendations if r.get('priority') == 'high']
        
        for rec in critical_recs[:3]:
            print(f"  [CRITICAL] {rec.get('recommendation', 'N/A')}")
        
        for rec in high_recs[:3]:
            print(f"  [HIGH] {rec.get('recommendation', 'N/A')}")
        
        if len(recommendations) > 6:
            print(f"  ... and {len(recommendations) - 6} more recommendations")
    
    print("\n" + "=" * 60)


def run_full_assessment(save_to_file=True, show_summary=True):
    """Run full assessment and optionally save results."""
    try:
        # Import Plone modules (must be done after Plone is available)
        from plone import api
        from knowledge.curator.upgrades.assess_current_state import assess_current_state
        
        print("Starting comprehensive migration assessment...")
        print("This may take a few minutes for large datasets...")
        
        # Get portal context
        portal = api.portal.get()
        
        # Run assessment
        report = assess_current_state(portal)
        
        print("Assessment completed successfully!")
        
        # Show summary
        if show_summary:
            print_summary(report)
        
        # Save to file
        output_path = None
        if save_to_file:
            output_path = save_report_to_file(report)
        
        return report, output_path
        
    except ImportError as e:
        print(f"Error: Cannot import Plone modules. Make sure this script is run in a Plone environment.")
        print(f"Import error: {str(e)}")
        return None, None
        
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        print(f"Assessment failed: {str(e)}")
        return None, None


def run_quick_assessment():
    """Run a quick assessment focusing on counts and major conflicts."""
    try:
        from plone import api
        from knowledge.curator.upgrades.assess_current_state import (
            quick_entity_count,
            check_migration_conflicts
        )
        
        print("Running quick assessment...")
        
        portal = api.portal.get()
        
        # Get entity counts
        counts = quick_entity_count(portal)
        print(f"\nEntity Counts:")
        for key, value in counts.items():
            print(f"  {key}: {value}")
        
        # Check for conflicts
        conflicts = check_migration_conflicts(portal)
        
        if conflicts:
            print(f"\nFound {len(conflicts)} potential conflicts:")
            
            # Group by type and severity
            conflict_summary = {}
            for conflict in conflicts:
                ctype = conflict.get('type', 'unknown')
                severity = conflict.get('severity', 'unknown')
                key = f"{ctype} ({severity})"
                conflict_summary[key] = conflict_summary.get(key, 0) + 1
            
            for conflict_type, count in sorted(conflict_summary.items()):
                print(f"  {conflict_type}: {count}")
        else:
            print("\nNo conflicts detected!")
        
        return counts, conflicts
        
    except Exception as e:
        logger.error(f"Quick assessment failed: {str(e)}")
        print(f"Quick assessment failed: {str(e)}")
        return None, None


def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run migration assessment for Knowledge Curator"
    )
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Run quick assessment (counts and conflicts only)'
    )
    parser.add_argument(
        '--no-save', 
        action='store_true',
        help='Do not save report to file'
    )
    parser.add_argument(
        '--no-summary', 
        action='store_true',
        help='Do not show summary output'
    )
    parser.add_argument(
        '--output', 
        type=str,
        help='Output file path for report'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        print("Running quick migration assessment...")
        counts, conflicts = run_quick_assessment()
        if counts is not None:
            print("\nQuick assessment completed successfully!")
        return counts is not None
    else:
        print("Running full migration assessment...")
        report, output_path = run_full_assessment(
            save_to_file=not args.no_save,
            show_summary=not args.no_summary
        )
        
        # Save with custom path if specified
        if report and args.output and not args.no_save:
            custom_path = save_report_to_file(report, args.output)
            if custom_path:
                print(f"Report also saved to custom path: {custom_path}")
        
        return report is not None


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)