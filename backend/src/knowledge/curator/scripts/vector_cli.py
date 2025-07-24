#!/usr/bin/env python
"""Command-line interface for vector database management."""

<<<<<<< HEAD
=======
import argparse
import sys
>>>>>>> fixing_linting_and_tests
from knowledge.curator.vector.management import VectorCollectionManager
from knowledge.curator.vector.search import SimilaritySearch
from zope.component.hooks import setSite

import argparse
import sys
import transaction


def initialize_plone(app, site_id="Plone"):
    """Initialize Plone site context."""
    site = app[site_id]
    setSite(site)
    return site


def cmd_init(args, manager):
    """Initialize vector database."""
    print("Initializing vector database...")
    success = manager.initialize_database()
    if success:
        print("✓ Database initialized successfully")
    else:
        print("✗ Failed to initialize database")
        sys.exit(1)


def cmd_rebuild(args, manager):
    """Rebuild vector index."""
    print("Rebuilding vector index...")
    print(f"Content types: {args.content_types or 'all'}")
    print(f"Clear first: {args.clear}")

    result = manager.rebuild_index(
        content_types=args.content_types.split(",") if args.content_types else None,
        clear_first=args.clear,
    )

    if result["success"]:
        print("✓ Index rebuilt successfully")
        print(f"  - Processed: {result['processed']} items")
        print(f"  - Errors: {result['errors']}")
        print(f"  - Duration: {result['duration_seconds']:.2f} seconds")
    else:
        print(f"✗ Failed to rebuild index: {result.get('error')}")
        sys.exit(1)


def cmd_stats(args, manager):
    """Show database statistics."""
    stats = manager.get_database_stats()

    print("Vector Database Statistics")
    print("-" * 40)

    if "collection_info" in stats:
        info = stats["collection_info"]
        print(f"Collection: {manager.adapter.collection_name}")
        print(f"Status: {info.get('status', 'unknown')}")
        print(f"Total vectors: {info.get('points_count', 0)}")

    if "content_type_distribution" in stats:
        print("\nContent Type Distribution:")
        for ct, count in stats["content_type_distribution"].items():
            print(f"  {ct}: {count}")

    if "workflow_state_distribution" in stats:
        print("\nWorkflow State Distribution:")
        for state, count in stats["workflow_state_distribution"].items():
            print(f"  {state}: {count}")


def cmd_health(args, manager):
    """Check system health."""
    health = manager.health_check()

    print("System Health Check")
    print("-" * 40)
    print(f"Overall: {'✓ Healthy' if health['healthy'] else '✗ Unhealthy'}")

    if "qdrant" in health:
        status = "✓ Connected" if health["qdrant"]["healthy"] else "✗ Failed"
        print(f"Qdrant: {status}")
        if health["qdrant"].get("error"):
            print(f"  Error: {health['qdrant']['error']}")

    if "embeddings" in health:
        status = "✓ Ready" if health["embeddings"]["healthy"] else "✗ Failed"
        print(f"Embeddings: {status}")
        if health["embeddings"]["healthy"]:
            print(f"  Model: {health['embeddings']['model']}")
            print(f"  Dimension: {health['embeddings']['dimension']}")

    if "collection" in health:
        status = "✓ Exists" if health["collection"]["exists"] else "✗ Not found"
        print(f"Collection: {status}")


def cmd_search(args, search):
    """Search for similar content."""
    print(f"Searching for: {args.query}")

    results = search.search_by_text(
        args.query, limit=args.limit, score_threshold=args.threshold
    )

    print(f"\nFound {len(results)} results:")
    print("-" * 60)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Type: {result['content_type']}")
        print(f"   Score: {result['score']:.3f}")
        print(f"   Path: {result['path']}")
        if result.get("description"):
            print(f"   Description: {result['description'][:100]}...")


def cmd_backup(args, manager):
    """Backup vector data."""
    print(f"Backing up vectors to: {args.output}")
    success = manager.backup_vectors(args.output)

    if success:
        print("✓ Backup completed successfully")
    else:
        print("✗ Backup failed")
        sys.exit(1)


def cmd_restore(args, manager):
    """Restore vector data."""
    print(f"Restoring vectors from: {args.input}")

    if not args.force:
        response = input("This will clear existing vectors. Continue? (y/N): ")
        if response.lower() != "y":
            print("Restore cancelled")
            return

    success = manager.restore_vectors(args.input)

    if success:
        print("✓ Restore completed successfully")
    else:
        print("✗ Restore failed")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Vector database management for Plone Knowledge System"
    )
    parser.add_argument(
<<<<<<< HEAD
        "--site-id", default="Plone", help="Plone site ID (default: Plone)"
=======
        "--site-id",
        default="Plone",
        help="Plone site ID (default: Plone)"
>>>>>>> fixing_linting_and_tests
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Initialize command
<<<<<<< HEAD
    subparsers.add_parser("init", help="Initialize vector database")
=======
    parser_init = subparsers.add_parser("init", help="Initialize vector database")
>>>>>>> fixing_linting_and_tests

    # Rebuild command
    parser_rebuild = subparsers.add_parser("rebuild", help="Rebuild vector index")
    parser_rebuild.add_argument(
        "--content-types", help="Comma-separated content types (default: all)"
    )
    parser_rebuild.add_argument(
        "--no-clear",
        dest="clear",
        action="store_false",
        help="Don't clear existing vectors",
    )

    # Stats command
<<<<<<< HEAD
    subparsers.add_parser("stats", help="Show database statistics")

    # Health command
    subparsers.add_parser("health", help="Check system health")
=======
    parser_stats = subparsers.add_parser("stats", help="Show database statistics")

    # Health command
    parser_health = subparsers.add_parser("health", help="Check system health")
>>>>>>> fixing_linting_and_tests

    # Search command
    parser_search = subparsers.add_parser("search", help="Search for similar content")
    parser_search.add_argument("query", help="Search query")
    parser_search.add_argument(
        "--limit", type=int, default=10, help="Number of results (default: 10)"
    )
    parser_search.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Similarity threshold (default: 0.5)",
    )

    # Backup command
    parser_backup = subparsers.add_parser("backup", help="Backup vector data")
    parser_backup.add_argument("output", help="Output file path")

    # Restore command
    parser_restore = subparsers.add_parser("restore", help="Restore vector data")
    parser_restore.add_argument("input", help="Input file path")
    parser_restore.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get Plone app from Zope
    from Zope2 import app as zope_app

    app = zope_app()

    try:
<<<<<<< HEAD
        initialize_plone(app, args.site_id)
=======
        site = initialize_plone(app, args.site_id)
>>>>>>> fixing_linting_and_tests

        # Create manager/search instance
        if args.command == "search":
            search = SimilaritySearch()
            cmd_search(args, search)
        else:
            manager = VectorCollectionManager()

            # Execute command
            commands = {
                "init": cmd_init,
                "rebuild": cmd_rebuild,
                "stats": cmd_stats,
                "health": cmd_health,
                "backup": cmd_backup,
                "restore": cmd_restore,
            }

            if args.command in commands:
                commands[args.command](args, manager)
            else:
                print(f"Unknown command: {args.command}")
                sys.exit(1)

        # Commit transaction if needed
        if args.command in ["init", "rebuild", "restore"]:
            transaction.commit()

    finally:
        app._p_jar.close()


if __name__ == "__main__":
    main()
