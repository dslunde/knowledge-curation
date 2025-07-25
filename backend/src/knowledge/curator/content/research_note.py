"""Research Note content type."""

from knowledge.curator.interfaces import IResearchNote, IKeyInsight, IAuthor
from plone.dexterity.content import Container
from zope.interface import implementer
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import uuid
from datetime import datetime


@implementer(IResearchNote)
class ResearchNote(Container):
    """Research Note content type implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize structured lists
        if not hasattr(self, 'key_insights'):
            self.key_insights = PersistentList()
        if not hasattr(self, 'authors'):
            self.authors = PersistentList()
        if not hasattr(self, 'builds_upon'):
            self.builds_upon = PersistentList()
        if not hasattr(self, 'contradicts'):
            self.contradicts = PersistentList()
        if not hasattr(self, 'replication_studies'):
            self.replication_studies = PersistentList()

    def get_embedding(self):
        """Get the embedding vector for this note."""
        return self.embedding_vector or []

    def update_embedding(self, vector):
        """Update the embedding vector."""
        self.embedding_vector = vector

    def add_connection(self, uid):
        """Add a connection to another content item."""
        if not hasattr(self, 'connections'):
            self.connections = PersistentList()
        if uid not in self.connections:
            self.connections.append(uid)

    def remove_connection(self, uid):
        """Remove a connection to another content item."""
        if hasattr(self, 'connections') and uid in self.connections:
            self.connections.remove(uid)

    def get_connections(self):
        """Get all connections."""
        return getattr(self, 'connections', PersistentList())

    def add_insight(self, text, importance='medium', evidence=None):
        """Add a structured key insight."""
        if not hasattr(self, 'key_insights'):
            self.key_insights = PersistentList()
        
        insight = PersistentMapping()
        insight['text'] = text
        insight['importance'] = importance
        insight['evidence'] = evidence
        insight['timestamp'] = datetime.now()
        
        self.key_insights.append(insight)
        return insight

    def add_author(self, name, email=None, orcid=None, affiliation=None):
        """Add an author to this research."""
        if not hasattr(self, 'authors'):
            self.authors = PersistentList()
        
        author = PersistentMapping()
        author['name'] = name
        author['email'] = email
        author['orcid'] = orcid
        author['affiliation'] = affiliation
        
        self.authors.append(author)
        return author

    def add_builds_upon(self, uid):
        """Add a research item this builds upon."""
        if not hasattr(self, 'builds_upon'):
            self.builds_upon = PersistentList()
        if uid not in self.builds_upon:
            self.builds_upon.append(uid)

    def add_contradicts(self, uid):
        """Add a research item this contradicts."""
        if not hasattr(self, 'contradicts'):
            self.contradicts = PersistentList()
        if uid not in self.contradicts:
            self.contradicts.append(uid)

    def add_replication_study(self, uid):
        """Add a replication study."""
        if not hasattr(self, 'replication_studies'):
            self.replication_studies = PersistentList()
        if uid not in self.replication_studies:
            self.replication_studies.append(uid)

    def get_related_research(self):
        """Get all related research (builds upon + contradicts)."""
        related = []
        if hasattr(self, 'builds_upon'):
            related.extend(self.builds_upon)
        if hasattr(self, 'contradicts'):
            related.extend(self.contradicts)
        return list(set(related))  # Remove duplicates

    def get_contradicted_research(self):
        """Get research this work contradicts."""
        return getattr(self, 'contradicts', PersistentList())

    def migrate_legacy_insights(self):
        """Migrate legacy text insights to structured format."""
        # Check if we have old-style insights
        if hasattr(self, 'key_insights') and self.key_insights:
            # Check if first item is a string (old format)
            if self.key_insights and isinstance(self.key_insights[0], str):
                old_insights = list(self.key_insights)
                self.key_insights = PersistentList()
                
                for insight_text in old_insights:
                    self.add_insight(
                        text=insight_text,
                        importance='medium',
                        evidence=None
                    )
                return True
        return False

    def get_annotated_knowledge_items_details(self):
        """Get detailed information about all Knowledge Items referenced in annotations.
        
        Returns:
            list: List of dicts containing Knowledge Item details, each with:
                - uid: The UID of the Knowledge Item
                - title: Title of the Knowledge Item
                - description: Description of the Knowledge Item
                - status: Current workflow status
                - knowledge_type: Type of knowledge (e.g., conceptual, procedural)
                - difficulty_level: Difficulty level of the item
                - mastery_threshold: Required mastery level
                - learning_progress: Current progress level
                - tags: List of tags
                - relationship: Type of annotation relationship
                - error: Error message if item cannot be accessed
        """
        from plone import api
        from zope.component import queryUtility
        from zope.intid.interfaces import IIntIds
        
        details = []
        
        # Get the list of annotated knowledge items
        annotated_items = getattr(self, 'annotated_knowledge_items', [])
        if not annotated_items:
            return details
        
        # Get annotation type for relationship context
        annotation_type = getattr(self, 'annotation_type', 'general')
        
        for uid in annotated_items:
            item_detail = {
                'uid': uid,
                'relationship': annotation_type,
                'error': None
            }
            
            try:
                # Try to get the Knowledge Item by UID
                knowledge_item = api.content.get(UID=uid)
                
                if knowledge_item is None:
                    # Item doesn't exist
                    item_detail.update({
                        'title': f'Missing Knowledge Item ({uid[:8]}...)',
                        'description': 'This Knowledge Item no longer exists',
                        'status': 'missing',
                        'error': 'Knowledge Item not found'
                    })
                elif knowledge_item.portal_type != 'KnowledgeItem':
                    # UID points to wrong content type
                    item_detail.update({
                        'title': knowledge_item.title or 'Untitled',
                        'description': f'Invalid content type: {knowledge_item.portal_type}',
                        'status': 'error',
                        'error': f'Expected KnowledgeItem but found {knowledge_item.portal_type}'
                    })
                else:
                    # Successfully got the Knowledge Item
                    try:
                        # Get workflow state
                        workflow_state = api.content.get_state(knowledge_item)
                    except:
                        workflow_state = 'unknown'
                    
                    # Extract all relevant details
                    item_detail.update({
                        'title': knowledge_item.title or 'Untitled',
                        'description': knowledge_item.description or '',
                        'status': workflow_state,
                        'knowledge_type': getattr(knowledge_item, 'knowledge_type', None),
                        'difficulty_level': getattr(knowledge_item, 'difficulty_level', None),
                        'mastery_threshold': getattr(knowledge_item, 'mastery_threshold', 0.8),
                        'learning_progress': getattr(knowledge_item, 'learning_progress', 0.0),
                        'tags': list(getattr(knowledge_item, 'tags', [])),
                        'atomic_concepts': list(getattr(knowledge_item, 'atomic_concepts', [])),
                        'source_url': getattr(knowledge_item, 'source_url', None),
                        'last_reviewed': getattr(knowledge_item, 'last_reviewed', None),
                        'created': knowledge_item.created().ISO8601() if hasattr(knowledge_item, 'created') else None,
                        'modified': knowledge_item.modified().ISO8601() if hasattr(knowledge_item, 'modified') else None,
                    })
                    
            except api.exc.UserNotAuthorized:
                # User doesn't have permission to access this item
                item_detail.update({
                    'title': f'Restricted Knowledge Item ({uid[:8]}...)',
                    'description': 'You do not have permission to access this item',
                    'status': 'restricted',
                    'error': 'Access denied'
                })
            except Exception as e:
                # Catch any other unexpected errors
                item_detail.update({
                    'title': f'Error accessing item ({uid[:8]}...)',
                    'description': f'An error occurred while accessing this item',
                    'status': 'error',
                    'error': str(e)
                })
            
            details.append(item_detail)
        
        return details
    
    def suggest_related_notes(self, max_results=10):
        """Find and suggest related Research Notes based on various criteria.
        
        This method analyzes:
        - Shared annotated Knowledge Items
        - Similar annotation types
        - Research question overlap
        - Tags similarity
        - Author overlap
        - Referenced research (builds_upon, contradicts)
        
        Args:
            max_results (int): Maximum number of suggestions to return
            
        Returns:
            list: List of dicts with related notes, each containing:
                - uid: UID of the related note
                - title: Title of the related note
                - url: URL to the related note
                - relevance_score: Calculated relevance score (0.0-1.0)
                - connection_reasons: List of reasons why this note is related
                - shared_items: List of shared Knowledge Item UIDs
                - score_breakdown: Dict showing how score was calculated
        """
        from plone import api
        from collections import defaultdict
        import math
        
        # Get catalog
        catalog = api.portal.get_tool('portal_catalog')
        
        # Initialize results storage
        note_scores = defaultdict(lambda: {
            'relevance_score': 0.0,
            'connection_reasons': [],
            'shared_items': [],
            'score_breakdown': defaultdict(float)
        })
        
        # Get this note's data
        my_uid = self.UID()
        my_annotated_items = set(getattr(self, 'annotated_knowledge_items', []))
        my_annotation_type = getattr(self, 'annotation_type', None)
        my_research_question = getattr(self, 'research_question', '')
        my_tags = set(getattr(self, 'tags', []))
        my_authors = getattr(self, 'authors', [])
        my_author_names = {author.get('name') for author in my_authors if author.get('name')}
        
        # Also consider research relationships
        my_builds_upon = set(getattr(self, 'builds_upon', []))
        my_contradicts = set(getattr(self, 'contradicts', []))
        my_related_research = my_builds_upon | my_contradicts
        
        # Search for all other Research Notes
        brains = catalog.searchResults(
            portal_type='ResearchNote',
            UID={'not': my_uid}
        )
        
        for brain in brains:
            try:
                # Get the note object
                note = brain.getObject()
                note_uid = brain.UID
                
                # Skip if we can't access it
                if not note:
                    continue
                
                # Calculate different relevance factors
                
                # 1. Shared Knowledge Items (highest weight)
                note_annotated_items = set(getattr(note, 'annotated_knowledge_items', []))
                shared_items = my_annotated_items & note_annotated_items
                
                if shared_items:
                    # Score based on proportion of shared items
                    shared_ratio = len(shared_items) / max(len(my_annotated_items), len(note_annotated_items))
                    item_score = shared_ratio * 0.4  # Max 0.4 points
                    
                    note_scores[note_uid]['relevance_score'] += item_score
                    note_scores[note_uid]['score_breakdown']['shared_items'] = item_score
                    note_scores[note_uid]['shared_items'] = list(shared_items)
                    note_scores[note_uid]['connection_reasons'].append(
                        f"Shares {len(shared_items)} Knowledge Item{'s' if len(shared_items) > 1 else ''}"
                    )
                
                # 2. Same annotation type (moderate weight)
                note_annotation_type = getattr(note, 'annotation_type', None)
                if my_annotation_type and note_annotation_type == my_annotation_type:
                    type_score = 0.2
                    note_scores[note_uid]['relevance_score'] += type_score
                    note_scores[note_uid]['score_breakdown']['annotation_type'] = type_score
                    note_scores[note_uid]['connection_reasons'].append(
                        f"Same annotation type: {my_annotation_type}"
                    )
                
                # 3. Research question similarity (using simple word overlap)
                note_research_question = getattr(note, 'research_question', '')
                if my_research_question and note_research_question:
                    # Simple word overlap calculation
                    my_words = set(my_research_question.lower().split())
                    note_words = set(note_research_question.lower().split())
                    
                    # Remove common words
                    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                                  'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                                  'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where',
                                  'why', 'how'}
                    
                    my_words = my_words - stop_words
                    note_words = note_words - stop_words
                    
                    if my_words and note_words:
                        word_overlap = len(my_words & note_words)
                        if word_overlap > 0:
                            overlap_ratio = word_overlap / min(len(my_words), len(note_words))
                            question_score = overlap_ratio * 0.15  # Max 0.15 points
                            
                            note_scores[note_uid]['relevance_score'] += question_score
                            note_scores[note_uid]['score_breakdown']['research_question'] = question_score
                            note_scores[note_uid]['connection_reasons'].append(
                                f"Similar research focus ({word_overlap} keyword{'s' if word_overlap > 1 else ''} overlap)"
                            )
                
                # 4. Tag similarity
                note_tags = set(getattr(note, 'tags', []))
                shared_tags = my_tags & note_tags
                
                if shared_tags:
                    tag_ratio = len(shared_tags) / max(len(my_tags), len(note_tags))
                    tag_score = tag_ratio * 0.1  # Max 0.1 points
                    
                    note_scores[note_uid]['relevance_score'] += tag_score
                    note_scores[note_uid]['score_breakdown']['tags'] = tag_score
                    note_scores[note_uid]['connection_reasons'].append(
                        f"Shares {len(shared_tags)} tag{'s' if len(shared_tags) > 1 else ''}"
                    )
                
                # 5. Author overlap
                note_authors = getattr(note, 'authors', [])
                note_author_names = {author.get('name') for author in note_authors if author.get('name')}
                shared_authors = my_author_names & note_author_names
                
                if shared_authors:
                    author_score = 0.05 * len(shared_authors)  # 0.05 per shared author
                    note_scores[note_uid]['relevance_score'] += author_score
                    note_scores[note_uid]['score_breakdown']['authors'] = author_score
                    note_scores[note_uid]['connection_reasons'].append(
                        f"Shared author{'s' if len(shared_authors) > 1 else ''}: {', '.join(list(shared_authors)[:3])}"
                    )
                
                # 6. Research relationship connections
                note_builds_upon = set(getattr(note, 'builds_upon', []))
                note_contradicts = set(getattr(note, 'contradicts', []))
                note_related = note_builds_upon | note_contradicts
                
                # Check if notes reference each other
                if my_uid in note_related or note_uid in my_related_research:
                    relation_score = 0.1
                    note_scores[note_uid]['relevance_score'] += relation_score
                    note_scores[note_uid]['score_breakdown']['direct_reference'] = relation_score
                    note_scores[note_uid]['connection_reasons'].append("Direct research reference")
                
                # Check for shared research references
                shared_references = my_related_research & note_related
                if shared_references:
                    ref_score = 0.05 * min(len(shared_references), 2)  # Max 0.1
                    note_scores[note_uid]['relevance_score'] += ref_score
                    note_scores[note_uid]['score_breakdown']['shared_references'] = ref_score
                    note_scores[note_uid]['connection_reasons'].append(
                        f"References same research ({len(shared_references)} shared)"
                    )
                
            except Exception as e:
                # Skip notes that cause errors
                continue
        
        # Convert to sorted list of results
        results = []
        for note_uid, score_data in note_scores.items():
            # Only include notes with meaningful connections
            if score_data['relevance_score'] > 0:
                try:
                    brain = catalog(UID=note_uid)[0]
                    result = {
                        'uid': note_uid,
                        'title': brain.Title,
                        'url': brain.getURL(),
                        'relevance_score': min(score_data['relevance_score'], 1.0),  # Cap at 1.0
                        'connection_reasons': score_data['connection_reasons'],
                        'shared_items': score_data['shared_items'],
                        'score_breakdown': dict(score_data['score_breakdown'])
                    }
                    results.append(result)
                except:
                    # Skip if we can't get brain info
                    continue
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top results
        return results[:max_results]
    
    def generate_knowledge_item_enhancement_suggestions(self, max_suggestions_per_item=5):
        """Generate actionable suggestions for enhancing annotated Knowledge Items.
        
        This method analyzes Research Note content, annotation types, and evidence to
        suggest specific improvements to annotated Knowledge Items. Suggestions are
        prioritized based on annotation confidence levels and evidence strength.
        
        Args:
            max_suggestions_per_item (int): Maximum suggestions per Knowledge Item
            
        Returns:
            list: List of dicts, each containing:
                - knowledge_item_uid: UID of the Knowledge Item
                - knowledge_item_title: Title of the Knowledge Item
                - suggestions: List of suggestion dicts, each with:
                    - type: Type of suggestion (content_update, add_connection, 
                            status_change, structural_improvement, mastery_adjustment)
                    - priority: Priority level (critical, high, medium, low)
                    - description: Detailed description of the suggestion
                    - action: Specific action to take
                    - evidence: Evidence supporting the suggestion
                    - confidence: Confidence level (0.0-1.0)
                    - rationale: Why this suggestion is important
        """
        from plone import api
        
        suggestions_by_item = []
        
        # Get annotated knowledge items with details
        annotated_items = self.get_annotated_knowledge_items_details()
        
        # Get Research Note metadata for context
        annotation_type = getattr(self, 'annotation_type', 'general')
        annotation_confidence = getattr(self, 'annotation_confidence', 0.5)
        key_insights = getattr(self, 'key_insights', [])
        evidence_sources = getattr(self, 'evidence_sources', [])
        research_question = getattr(self, 'research_question', '')
        
        # Extract insight texts and importance levels
        insight_data = []
        for insight in key_insights:
            if isinstance(insight, dict):
                insight_data.append({
                    'text': insight.get('text', ''),
                    'importance': insight.get('importance', 'medium'),
                    'evidence': insight.get('evidence', '')
                })
            elif isinstance(insight, str):
                # Handle legacy string insights
                insight_data.append({
                    'text': insight,
                    'importance': 'medium',
                    'evidence': ''
                })
        
        # Analyze each Knowledge Item
        for item_detail in annotated_items:
            if item_detail.get('error'):
                # Skip items with errors
                continue
                
            item_suggestions = []
            item_uid = item_detail['uid']
            item_title = item_detail.get('title', 'Unknown')
            
            # 1. Content Update Suggestions based on annotation type
            if annotation_type in ['correction', 'clarification', 'expansion']:
                # High priority content updates for these types
                suggestion = {
                    'type': 'content_update',
                    'priority': 'high' if annotation_confidence > 0.7 else 'medium',
                    'description': f'Update content based on {annotation_type} annotation',
                    'action': f'Review and incorporate the {annotation_type} provided in this research note',
                    'evidence': self._get_relevant_insights(insight_data, ['clarif', 'correct', 'expand', 'update']),
                    'confidence': annotation_confidence,
                    'rationale': f'This research note provides {annotation_type} that should be reflected in the Knowledge Item'
                }
                
                # Add specific actions based on annotation type
                if annotation_type == 'correction':
                    suggestion['action'] = 'Correct the inaccurate information identified in this research'
                    suggestion['priority'] = 'critical' if annotation_confidence > 0.8 else 'high'
                elif annotation_type == 'clarification':
                    suggestion['action'] = 'Add clarifying details to improve understanding'
                elif annotation_type == 'expansion':
                    suggestion['action'] = 'Expand the content with additional information provided'
                    
                item_suggestions.append(suggestion)
            
            # 2. Connection Suggestions
            if annotation_type in ['connection', 'cross_reference']:
                # Look for other Knowledge Items mentioned in insights
                mentioned_items = self._extract_knowledge_item_references(insight_data)
                
                for mentioned_uid, context in mentioned_items.items():
                    if mentioned_uid != item_uid:  # Don't suggest self-connection
                        item_suggestions.append({
                            'type': 'add_connection',
                            'priority': 'medium',
                            'description': f'Add connection to related Knowledge Item',
                            'action': f'Connect to Knowledge Item: {context}',
                            'evidence': f'Referenced in research insights',
                            'confidence': annotation_confidence * 0.8,  # Slightly lower for indirect evidence
                            'rationale': 'Cross-references strengthen the knowledge graph'
                        })
            
            # 3. Status Change Suggestions
            current_status = item_detail.get('status', 'unknown')
            
            # Suggest validation for items with high-confidence positive annotations
            if annotation_type == 'validation' and annotation_confidence > 0.8:
                if current_status in ['draft', 'pending']:
                    item_suggestions.append({
                        'type': 'status_change',
                        'priority': 'high',
                        'description': 'Promote to validated status',
                        'action': 'Change workflow state from draft/pending to validated',
                        'evidence': f'High confidence ({annotation_confidence:.2f}) validation in research',
                        'confidence': annotation_confidence,
                        'rationale': 'Research provides strong validation evidence'
                    })
            
            # Suggest review for items with contradictions
            elif annotation_type == 'contradiction' and annotation_confidence > 0.6:
                if current_status == 'validated':
                    item_suggestions.append({
                        'type': 'status_change',
                        'priority': 'critical',
                        'description': 'Flag for review due to contradiction',
                        'action': 'Change status to "needs_review" and add contradiction note',
                        'evidence': self._get_relevant_insights(insight_data, ['contradict', 'conflict', 'disagree']),
                        'confidence': annotation_confidence,
                        'rationale': 'Contradictory evidence requires immediate review'
                    })
            
            # 4. Structural Improvements
            knowledge_type = item_detail.get('knowledge_type', None)
            
            # Suggest adding atomic concepts if missing
            atomic_concepts = item_detail.get('atomic_concepts', [])
            if not atomic_concepts and any(keyword in research_question.lower() 
                                           for keyword in ['break down', 'component', 'atomic', 'fundamental']):
                item_suggestions.append({
                    'type': 'structural_improvement',
                    'priority': 'medium',
                    'description': 'Add atomic concepts breakdown',
                    'action': 'Identify and add fundamental concepts that compose this knowledge',
                    'evidence': 'Research focuses on component analysis',
                    'confidence': 0.7,
                    'rationale': 'Atomic concepts improve learning path generation'
                })
            
            # Suggest knowledge type classification if missing
            if not knowledge_type:
                # Analyze insights to suggest type
                suggested_type = self._infer_knowledge_type(insight_data)
                if suggested_type:
                    item_suggestions.append({
                        'type': 'structural_improvement',
                        'priority': 'medium',
                        'description': f'Classify knowledge type as "{suggested_type}"',
                        'action': f'Set knowledge_type field to "{suggested_type}"',
                        'evidence': 'Inferred from research content analysis',
                        'confidence': 0.6,
                        'rationale': 'Knowledge type classification enables better learning strategies'
                    })
            
            # 5. Mastery Adjustment Suggestions
            difficulty_level = item_detail.get('difficulty_level', None)
            mastery_threshold = item_detail.get('mastery_threshold', 0.8)
            
            # Check for difficulty-related insights
            if any(keyword in str(insight_data).lower() 
                   for keyword in ['difficult', 'complex', 'challenging', 'advanced']):
                if difficulty_level in [None, 'beginner', 'intermediate']:
                    item_suggestions.append({
                        'type': 'mastery_adjustment',
                        'priority': 'low',
                        'description': 'Consider increasing difficulty level',
                        'action': 'Review and potentially increase difficulty_level to "advanced"',
                        'evidence': 'Research indicates complex concepts',
                        'confidence': 0.5,
                        'rationale': 'Accurate difficulty levels improve learning path recommendations'
                    })
            
            # 6. Evidence and Source Updates
            if evidence_sources and not item_detail.get('source_url'):
                # Suggest adding primary source
                primary_source = evidence_sources[0] if evidence_sources else None
                if primary_source:
                    item_suggestions.append({
                        'type': 'content_update',
                        'priority': 'low',
                        'description': 'Add source reference',
                        'action': f'Add source_url: {primary_source}',
                        'evidence': 'Research cites authoritative source',
                        'confidence': 0.8,
                        'rationale': 'Source attribution improves credibility'
                    })
            
            # Sort suggestions by priority and confidence
            item_suggestions.sort(
                key=lambda x: (
                    self._priority_to_score(x['priority']),
                    x['confidence']
                ),
                reverse=True
            )
            
            # Add to results if there are suggestions
            if item_suggestions:
                suggestions_by_item.append({
                    'knowledge_item_uid': item_uid,
                    'knowledge_item_title': item_title,
                    'suggestions': item_suggestions[:max_suggestions_per_item]
                })
        
        return suggestions_by_item
    
    def _get_relevant_insights(self, insight_data, keywords):
        """Extract insights containing any of the given keywords."""
        relevant = []
        for insight in insight_data:
            text = insight.get('text', '').lower()
            if any(keyword in text for keyword in keywords):
                relevant.append(insight['text'])
        return '; '.join(relevant[:3])  # Return up to 3 relevant insights
    
    def _extract_knowledge_item_references(self, insight_data):
        """Extract potential Knowledge Item references from insights."""
        # This is a simplified implementation
        # In practice, you might use NLP or pattern matching
        references = {}
        
        for insight in insight_data:
            text = insight.get('text', '')
            # Look for patterns like "Knowledge Item X" or "concept Y"
            # This is a placeholder - implement more sophisticated extraction
            if 'knowledge item' in text.lower() or 'concept' in text.lower():
                # Extract the reference (simplified)
                references['placeholder_uid'] = text[:50] + '...'
                
        return references
    
    def _infer_knowledge_type(self, insight_data):
        """Infer knowledge type from insight content."""
        # Analyze insights to determine knowledge type
        all_text = ' '.join([insight.get('text', '') for insight in insight_data]).lower()
        
        # Simple keyword-based inference
        if any(keyword in all_text for keyword in ['procedure', 'steps', 'how to', 'process']):
            return 'procedural'
        elif any(keyword in all_text for keyword in ['concept', 'theory', 'principle', 'definition']):
            return 'conceptual'
        elif any(keyword in all_text for keyword in ['fact', 'data', 'statistic', 'finding']):
            return 'factual'
        elif any(keyword in all_text for keyword in ['analyze', 'evaluate', 'synthesis', 'critical']):
            return 'metacognitive'
            
        return None
    
    def _priority_to_score(self, priority):
        """Convert priority string to numeric score for sorting."""
        priority_scores = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return priority_scores.get(priority, 0)
    
    def get_available_knowledge_items_for_annotation(self):
        """Get available Knowledge Items that can be annotated.
        
        Returns:
            list: List of dicts with Knowledge Item information including:
                - uid: The UID of the Knowledge Item
                - title: Title of the Knowledge Item
                - description: Description
                - knowledge_type: Type of knowledge
                - difficulty_level: Difficulty level
                - tags: List of tags
                - already_annotated: Boolean indicating if already annotated by this note
        """
        from plone import api
        
        catalog = api.portal.get_tool('portal_catalog')
        current_annotated = set(getattr(self, 'annotated_knowledge_items', []))
        
        # Get all Knowledge Items
        brains = catalog(
            portal_type='KnowledgeItem',
            sort_on='sortable_title',
            sort_order='ascending',
        )
        
        items = []
        for brain in brains:
            try:
                obj = brain.getObject()
                items.append({
                    'uid': brain.UID,
                    'title': brain.Title,
                    'description': brain.Description or '',
                    'knowledge_type': getattr(obj, 'knowledge_type', None),
                    'difficulty_level': getattr(obj, 'difficulty_level', None),
                    'tags': list(getattr(obj, 'tags', [])),
                    'review_state': brain.review_state,
                    'already_annotated': brain.UID in current_annotated,
                })
            except:
                # Skip items we can't access
                continue
        
        return items
    
    def suggest_knowledge_items_for_annotation(self, limit=10):
        """Suggest Knowledge Items to annotate based on this note's content.
        
        Args:
            limit: Maximum number of suggestions
            
        Returns:
            list: List of suggested Knowledge Items with relevance scores
        """
        from knowledge.curator.content.research_note_events import (
            suggest_knowledge_items_for_annotation as suggest_items
        )
        
        # Combine various text fields for analysis
        text_parts = []
        
        # Add title and description
        if self.title:
            text_parts.append(self.title)
        if self.description:
            text_parts.append(self.description)
        
        # Add content
        if hasattr(self, 'content') and self.content:
            if hasattr(self.content, 'raw'):
                text_parts.append(self.content.raw)
            else:
                text_parts.append(str(self.content))
        
        # Add research question
        if hasattr(self, 'research_question') and self.research_question:
            text_parts.append(self.research_question)
        
        # Add key insights
        if hasattr(self, 'key_insights') and self.key_insights:
            for insight in self.key_insights:
                if isinstance(insight, dict) and 'text' in insight:
                    text_parts.append(insight['text'])
                elif isinstance(insight, str):
                    text_parts.append(insight)
        
        # Add tags
        if hasattr(self, 'tags') and self.tags:
            text_parts.extend(self.tags)
        
        combined_text = ' '.join(text_parts)
        
        # Get suggestions
        suggestions = suggest_items(combined_text, limit=limit)
        
        # Filter out already annotated items
        current_annotated = set(getattr(self, 'annotated_knowledge_items', []))
        filtered_suggestions = [
            s for s in suggestions
            if s['uid'] not in current_annotated
        ]
        
        return filtered_suggestions
    
    def validate_annotation_requirement(self):
        """Validate that this Research Note has at least one annotated Knowledge Item.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        annotated_items = getattr(self, 'annotated_knowledge_items', None)
        
        if not annotated_items:
            return (False, "Research Note must annotate at least one Knowledge Item")
        
        if not isinstance(annotated_items, list) or len(annotated_items) == 0:
            return (False, "No Knowledge Items are annotated")
        
        # Validate each item exists
        from plone import api
        catalog = api.portal.get_tool('portal_catalog')
        
        invalid_items = []
        for uid in annotated_items:
            brains = catalog(UID=uid, portal_type='KnowledgeItem')
            if not brains:
                invalid_items.append(uid)
        
        if invalid_items:
            return (False, f"Invalid Knowledge Item references: {', '.join(invalid_items[:3])}")
        
        return (True, None)
    
    def add_annotated_knowledge_item(self, uid):
        """Add a Knowledge Item to the annotated items list.
        
        Args:
            uid: UID of the Knowledge Item to add
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if not hasattr(self, 'annotated_knowledge_items'):
            self.annotated_knowledge_items = PersistentList()
        
        if uid not in self.annotated_knowledge_items:
            # Validate the UID
            from plone import api
            catalog = api.portal.get_tool('portal_catalog')
            brains = catalog(UID=uid, portal_type='KnowledgeItem')
            
            if brains:
                self.annotated_knowledge_items.append(uid)
                self._p_changed = True
                return True
        
        return False
    
    def remove_annotated_knowledge_item(self, uid):
        """Remove a Knowledge Item from the annotated items list.
        
        Args:
            uid: UID of the Knowledge Item to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        if hasattr(self, 'annotated_knowledge_items') and uid in self.annotated_knowledge_items:
            # Don't allow removal if it's the last item
            if len(self.annotated_knowledge_items) <= 1:
                return False
            
            self.annotated_knowledge_items.remove(uid)
            self._p_changed = True
            return True
        
        return False
