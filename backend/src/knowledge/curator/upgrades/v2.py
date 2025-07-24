"""Upgrade to version 2: Add new content types."""

from plone.app.upgrade.utils import loadMigrationProfile


def add_new_content_types(context):
    """Add ResearchNote, LearningGoal, ProjectLog, and BookmarkPlus content types."""
    loadMigrationProfile(
        context, "profile-knowledge.curator:default", steps=["typeinfo"]
    )

    # Refresh catalog for new content types
    loadMigrationProfile(
        context,
        'profile-knowledge.curator:default',
        steps=['catalog']
    )
