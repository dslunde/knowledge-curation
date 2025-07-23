"""Upgrade steps for version 2 - Adding new content types."""

from plone import api


def add_new_content_types(context):
    """Add new content types to the site."""
    setup = api.portal.get_tool('portal_setup')
    
    # Import the types
    setup.runImportStepFromProfile(
        'profile-plone.app.knowledge:default',
        'typeinfo'
    )
    
    # Import the permissions
    setup.runImportStepFromProfile(
        'profile-plone.app.knowledge:default',
        'rolemap'
    )
    
    # Reindex the catalog
    catalog = api.portal.get_tool('portal_catalog')
    catalog.clearFindAndRebuild()
    
    return "Added new content types: ResearchNote, LearningGoal, ProjectLog, BookmarkPlus"