"""Vocabulary for Knowledge Items."""

from plone import api
from plone.app.vocabularies.catalog import CatalogSource
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class KnowledgeItemsVocabulary:
    """Vocabulary factory for Knowledge Items."""

    def __call__(self, context):
        """Return vocabulary of available knowledge items."""
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(portal_type="KnowledgeItem", sort_on="sortable_title")
        
        terms = []
        for brain in brains:
            # Skip the current item to avoid self-reference
            if hasattr(context, "UID") and brain.UID == context.UID():
                continue
                
            terms.append(
                SimpleTerm(
                    value=brain.UID,
                    token=brain.UID,
                    title=brain.Title
                )
            )
        
        return SimpleVocabulary(terms)


KnowledgeItemsVocabularyFactory = KnowledgeItemsVocabulary()


class KnowledgeItemSource(CatalogSource):
    """Catalog source for Knowledge Items that allows searching."""
    
    def __init__(self, context=None):
        """Initialize with Knowledge Item specific query."""
        super().__init__(
            query={"portal_type": "KnowledgeItem"},
            sort_on="sortable_title"
        )
    
    def __contains__(self, value):
        """Check if value is a valid Knowledge Item UID."""
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog(UID=value, portal_type="KnowledgeItem")
        return len(brains) > 0