"""Event handlers for Research Note content type."""

from plone import api
from zope.component import adapter
from zope.lifecycleevent.interfaces import (
    IObjectCreatedEvent,
    IObjectModifiedEvent,
    IObjectAddedEvent,
)
from Products.CMFCore.interfaces import IActionSucceededEvent
from knowledge.curator.interfaces import IResearchNote
from knowledge.curator.content.validators import validate_annotated_knowledge_items
from zope.interface import Invalid
import logging

logger = logging.getLogger('knowledge.curator.research_note')


@adapter(IResearchNote, IObjectCreatedEvent)
def validate_research_note_on_create(obj, event):
    """Validate Research Note has at least one annotated Knowledge Item on creation.
    
    This handler ensures that every Research Note created has at least one
    Knowledge Item reference.
    """
    try:
        # Validate annotated_knowledge_items
        annotated_items = getattr(obj, 'annotated_knowledge_items', None)
        validate_annotated_knowledge_items(annotated_items)
        
        logger.info(
            f"Research Note '{obj.Title()}' created with {len(annotated_items)} "
            f"annotated Knowledge Items"
        )
    except Invalid as e:
        # Log the error - the validation should already prevent this in the form
        logger.error(
            f"Research Note validation failed on creation: {str(e)}"
        )
        # Re-raise to ensure the creation fails
        raise


@adapter(IResearchNote, IObjectModifiedEvent)
def validate_research_note_on_modify(obj, event):
    """Validate Research Note maintains at least one annotated Knowledge Item on modification.
    
    This handler ensures that Research Notes cannot be modified to remove all
    Knowledge Item references.
    """
    # Skip validation during object creation (handled by create event)
    if IObjectAddedEvent.providedBy(event):
        return
    
    try:
        # Validate annotated_knowledge_items
        annotated_items = getattr(obj, 'annotated_knowledge_items', None)
        validate_annotated_knowledge_items(annotated_items)
        
        logger.info(
            f"Research Note '{obj.Title()}' modified, maintains {len(annotated_items)} "
            f"annotated Knowledge Items"
        )
    except Invalid as e:
        # Log the error
        logger.error(
            f"Research Note validation failed on modification: {str(e)}"
        )
        # Re-raise to ensure the modification fails
        raise


@adapter(IResearchNote, IActionSucceededEvent)
def log_research_note_workflow_changes(obj, event):
    """Log workflow state changes for Research Notes.
    
    This can be used to track when Research Notes change workflow states
    and ensure they maintain proper Knowledge Item associations.
    """
    if event.action:
        annotated_count = len(getattr(obj, 'annotated_knowledge_items', []))
        logger.info(
            f"Research Note '{obj.Title()}' workflow action '{event.action}' "
            f"succeeded. Has {annotated_count} annotated Knowledge Items."
        )


def get_available_knowledge_items(context=None):
    """Helper function to get available Knowledge Items for selection.
    
    Args:
        context: The context object (usually the Research Note being edited)
        
    Returns:
        list: List of dicts with 'uid', 'title', and 'description' for each Knowledge Item
    """
    catalog = api.portal.get_tool('portal_catalog')
    
    # Query for all Knowledge Items
    brains = catalog(
        portal_type='KnowledgeItem',
        sort_on='sortable_title',
        sort_order='ascending',
    )
    
    items = []
    for brain in brains:
        items.append({
            'uid': brain.UID,
            'title': brain.Title,
            'description': brain.Description or '',
            'path': brain.getPath(),
            'review_state': brain.review_state,
        })
    
    return items


def suggest_knowledge_items_for_annotation(research_note_text, limit=10):
    """Suggest relevant Knowledge Items based on Research Note content.
    
    This helper method analyzes the research note's content and suggests
    the most relevant Knowledge Items that could be annotated.
    
    Args:
        research_note_text: The text content of the research note
        limit: Maximum number of suggestions to return
        
    Returns:
        list: List of suggested Knowledge Item UIDs with relevance scores
    """
    if not research_note_text:
        return []
    
    catalog = api.portal.get_tool('portal_catalog')
    
    # Extract key terms from the research note text
    # This is a simple implementation - could be enhanced with NLP
    words = research_note_text.lower().split()
    
    # Filter out common words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
        'why', 'how'
    }
    
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]
    
    # Get unique keywords
    unique_keywords = list(set(keywords))[:20]  # Limit to 20 keywords
    
    if not unique_keywords:
        return []
    
    # Search for Knowledge Items containing these keywords
    # Build a query that looks for any of the keywords
    query_parts = []
    for keyword in unique_keywords:
        query_parts.append(f'"{keyword}"')
    
    search_query = ' OR '.join(query_parts)
    
    # Search in SearchableText (includes title, description, and content)
    results = catalog(
        portal_type='KnowledgeItem',
        SearchableText=search_query,
        sort_on='relevance',
        sort_limit=limit * 2,  # Get more results to filter
    )
    
    suggestions = []
    seen_uids = set()
    
    for brain in results[:limit]:
        if brain.UID not in seen_uids:
            seen_uids.add(brain.UID)
            
            # Calculate a simple relevance score based on keyword matches
            title_lower = brain.Title.lower()
            desc_lower = (brain.Description or '').lower()
            
            score = 0
            for keyword in unique_keywords:
                if keyword in title_lower:
                    score += 2  # Title matches are worth more
                if keyword in desc_lower:
                    score += 1
            
            suggestions.append({
                'uid': brain.UID,
                'title': brain.Title,
                'description': brain.Description or '',
                'score': score,
                'review_state': brain.review_state,
            })
    
    # Sort by score (highest first)
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    
    return suggestions


def validate_knowledge_item_exists(uid):
    """Validate that a Knowledge Item with the given UID exists.
    
    Args:
        uid: The UID to check
        
    Returns:
        bool: True if the Knowledge Item exists, False otherwise
    """
    if not uid:
        return False
    
    try:
        obj = api.content.get(UID=uid)
        return obj is not None and obj.portal_type == 'KnowledgeItem'
    except:
        return False


def get_annotation_type_description(annotation_type):
    """Get a human-readable description for an annotation type.
    
    Args:
        annotation_type: The annotation type value
        
    Returns:
        str: Description of what this annotation type means
    """
    descriptions = {
        'general': 'General notes or observations about the Knowledge Item',
        'clarification': 'Clarifies or explains concepts in the Knowledge Item',
        'correction': 'Corrects errors or inaccuracies in the Knowledge Item',
        'expansion': 'Expands on topics covered in the Knowledge Item',
        'example': 'Provides examples or use cases for the Knowledge Item',
        'connection': 'Shows connections to other Knowledge Items or concepts',
        'question': 'Raises questions about the Knowledge Item content',
        'critique': 'Provides critical analysis of the Knowledge Item',
        'validation': 'Validates or confirms information in the Knowledge Item',
        'contradiction': 'Points out contradictions or conflicting information',
        'application': 'Shows practical applications of the Knowledge Item',
        'cross_reference': 'Cross-references with other sources or Knowledge Items',
    }
    
    return descriptions.get(annotation_type, 'Annotation of the Knowledge Item')