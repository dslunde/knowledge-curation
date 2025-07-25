"""Assessment Infrastructure for Data Schema Migration.

This module provides core assessment functions to evaluate existing data structure
and migration readiness. It analyzes current content types, identifies migration
patterns, detects potential conflicts, and generates comprehensive reports.
"""

import logging
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set, Optional
import re
import json

from plone import api
from plone.api.exc import InvalidParameterError
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

logger = logging.getLogger("knowledge.curator.assessment")


class AssessmentError(Exception):
    """Custom exception for assessment errors."""
    pass


class DataAssessment:
    """Comprehensive data assessment for migration planning."""
    
    def __init__(self, context=None):
        """Initialize assessment with portal context."""
        self.context = context or api.portal.get()
        self.catalog = api.portal.get_tool("portal_catalog")
        self.assessment_data = {}
        self.conflicts = []
        self.warnings = []
        self.recommendations = []
        
    def assess_knowledge_items(self) -> Dict[str, Any]:
        """Scan and assess all Knowledge Items for migration readiness.
        
        Returns:
            Dict containing assessment results with counts, patterns, and issues
        """
        logger.info("Starting Knowledge Items assessment...")
        
        knowledge_items = self.catalog(portal_type='KnowledgeItem')
        assessment = {
            'total_count': len(knowledge_items),
            'field_analysis': {},
            'data_patterns': {},
            'migration_issues': [],
            'relationships': {},
            'content_quality': {},
            'timestamp': datetime.now().isoformat()
        }
        
        field_stats = defaultdict(lambda: {'populated': 0, 'empty': 0, 'types': Counter(), 'samples': []})
        relationship_counts = {'prerequisites': 0, 'enables': 0, 'circular_refs': []}
        content_issues = []
        
        for brain in knowledge_items:
            try:
                obj = brain.getObject()
                
                # Analyze core fields
                self._analyze_object_fields(obj, field_stats, 'KnowledgeItem')
                
                # Check relationships
                prereqs = getattr(obj, 'prerequisite_items', [])
                enables = getattr(obj, 'enables_items', [])
                
                if prereqs:
                    relationship_counts['prerequisites'] += len(prereqs)
                    # Check for circular dependencies
                    circular = self._detect_circular_dependencies(obj.UID(), prereqs, enables)
                    if circular:
                        relationship_counts['circular_refs'].extend(circular)
                
                if enables:
                    relationship_counts['enables'] += len(enables)
                
                # Assess content quality
                content_quality = self._assess_content_quality(obj)
                if content_quality['issues']:
                    content_issues.append({
                        'uid': obj.UID(),
                        'title': obj.title,
                        'issues': content_quality['issues']
                    })
                    
            except Exception as e:
                logger.error(f"Error assessing Knowledge Item {brain.getPath()}: {str(e)}")
                content_issues.append({
                    'uid': brain.UID,
                    'title': brain.Title,
                    'issues': [f"Assessment error: {str(e)}"]
                })
        
        assessment['field_analysis'] = dict(field_stats)
        assessment['relationships'] = relationship_counts
        assessment['content_quality'] = {'issues_count': len(content_issues), 'items_with_issues': content_issues[:20]}
        
        # Detect migration patterns
        assessment['data_patterns'] = self._detect_migration_patterns(field_stats)
        
        logger.info(f"Knowledge Items assessment completed. Found {assessment['total_count']} items.")
        return assessment
    
    def assess_research_notes(self) -> Dict[str, Any]:
        """Assess Research Notes for migration patterns."""
        logger.info("Starting Research Notes assessment...")
        
        research_notes = self.catalog(portal_type='ResearchNote')
        assessment = {
            'total_count': len(research_notes),
            'field_analysis': {},
            'migration_needs': {},
            'timestamp': datetime.now().isoformat()
        }
        
        field_stats = defaultdict(lambda: {'populated': 0, 'empty': 0, 'types': Counter(), 'samples': []})
        migration_needs = {'text_to_structured': 0, 'connection_migration': 0, 'author_format_issues': 0}
        
        for brain in research_notes:
            try:
                obj = brain.getObject()
                self._analyze_object_fields(obj, field_stats, 'ResearchNote')
                
                # Check for migration needs
                key_insights = getattr(obj, 'key_insights', [])
                if key_insights and isinstance(key_insights[0] if key_insights else None, str):
                    migration_needs['text_to_structured'] += 1
                
                connections = getattr(obj, 'connections', [])
                if connections:
                    migration_needs['connection_migration'] += 1
                
                authors = getattr(obj, 'authors', [])
                if authors and isinstance(authors[0] if authors else None, str):
                    migration_needs['author_format_issues'] += 1
                    
            except Exception as e:
                logger.error(f"Error assessing Research Note {brain.getPath()}: {str(e)}")
        
        assessment['field_analysis'] = dict(field_stats)
        assessment['migration_needs'] = migration_needs
        
        logger.info(f"Research Notes assessment completed. Found {assessment['total_count']} items.")
        return assessment
    
    def assess_learning_goals(self) -> Dict[str, Any]:
        """Assess Learning Goals for migration readiness."""
        logger.info("Starting Learning Goals assessment...")
        
        learning_goals = self.catalog(portal_type='LearningGoal')
        assessment = {
            'total_count': len(learning_goals),
            'field_analysis': {},
            'migration_needs': {},
            'graph_analysis': {},
            'timestamp': datetime.now().isoformat()
        }
        
        field_stats = defaultdict(lambda: {'populated': 0, 'empty': 0, 'types': Counter(), 'samples': []})
        migration_needs = {'milestone_migration': 0, 'objective_migration': 0, 'progress_recalculation': 0}
        graph_stats = {'with_knowledge_items': 0, 'connection_types': Counter()}
        
        for brain in learning_goals:
            try:
                obj = brain.getObject()
                self._analyze_object_fields(obj, field_stats, 'LearningGoal')
                
                # Check migration needs
                milestones = getattr(obj, 'milestones', [])
                if milestones and isinstance(milestones[0] if milestones else None, str):
                    migration_needs['milestone_migration'] += 1
                
                objectives = getattr(obj, 'learning_objectives', [])
                if objectives and isinstance(objectives[0] if objectives else None, str):
                    migration_needs['objective_migration'] += 1
                
                # Check for progress recalculation needs
                progress = getattr(obj, 'progress', None)
                overall_progress = getattr(obj, 'overall_progress', None)
                if progress is not None and overall_progress != progress / 100:
                    migration_needs['progress_recalculation'] += 1
                
                # Analyze knowledge graph connections
                target_items = getattr(obj, 'target_knowledge_items', [])
                connections = getattr(obj, 'knowledge_item_connections', [])
                
                if target_items:
                    graph_stats['with_knowledge_items'] += 1
                
                if connections:
                    for conn in connections:
                        if hasattr(conn, 'connection_type'):
                            graph_stats['connection_types'][conn.connection_type] += 1
                            
            except Exception as e:
                logger.error(f"Error assessing Learning Goal {brain.getPath()}: {str(e)}")
        
        assessment['field_analysis'] = dict(field_stats)
        assessment['migration_needs'] = migration_needs
        assessment['graph_analysis'] = dict(graph_stats)
        
        logger.info(f"Learning Goals assessment completed. Found {assessment['total_count']} items.")
        return assessment
    
    def assess_project_logs(self) -> Dict[str, Any]:
        """Assess Project Logs for migration patterns."""
        logger.info("Starting Project Logs assessment...")
        
        project_logs = self.catalog(portal_type='ProjectLog')
        assessment = {
            'total_count': len(project_logs),
            'field_analysis': {},
            'migration_needs': {},
            'learning_integration': {},
            'timestamp': datetime.now().isoformat()
        }
        
        field_stats = defaultdict(lambda: {'populated': 0, 'empty': 0, 'types': Counter(), 'samples': []})
        migration_needs = {'entry_migration': 0, 'deliverable_migration': 0, 'stakeholder_migration': 0}
        learning_stats = {'with_learning_goals': 0, 'progress_tracking': 0, 'sessions_recorded': 0}
        
        for brain in project_logs:
            try:
                obj = brain.getObject()
                self._analyze_object_fields(obj, field_stats, 'ProjectLog')
                
                # Check migration needs
                entries = getattr(obj, 'entries', [])
                if entries and isinstance(entries[0] if entries else None, str):
                    migration_needs['entry_migration'] += 1
                
                deliverables = getattr(obj, 'deliverables', [])
                if deliverables and isinstance(deliverables[0] if deliverables else None, str):
                    migration_needs['deliverable_migration'] += 1
                
                stakeholders = getattr(obj, 'stakeholders', [])
                if stakeholders and isinstance(stakeholders[0] if stakeholders else None, str):
                    migration_needs['stakeholder_migration'] += 1
                
                # Analyze learning integration
                learning_goal = getattr(obj, 'attached_learning_goal', None)
                if learning_goal:
                    learning_stats['with_learning_goals'] += 1
                
                progress_dict = getattr(obj, 'knowledge_item_progress', {})
                if progress_dict:
                    learning_stats['progress_tracking'] += 1
                
                sessions = getattr(obj, 'learning_sessions', [])
                if sessions:
                    learning_stats['sessions_recorded'] += 1
                    
            except Exception as e:
                logger.error(f"Error assessing Project Log {brain.getPath()}: {str(e)}")
        
        assessment['field_analysis'] = dict(field_stats)
        assessment['migration_needs'] = migration_needs
        assessment['learning_integration'] = learning_stats
        
        logger.info(f"Project Logs assessment completed. Found {assessment['total_count']} items.")
        return assessment
    
    def detect_migration_conflicts(self) -> List[Dict[str, Any]]:
        """Detect potential conflicts that could impact migration."""
        logger.info("Detecting migration conflicts...")
        
        conflicts = []
        
        # Check for UID conflicts
        uid_conflicts = self._check_uid_conflicts()
        if uid_conflicts:
            conflicts.extend(uid_conflicts)
        
        # Check for circular dependencies
        circular_deps = self._check_circular_dependencies()
        if circular_deps:
            conflicts.extend(circular_deps)
        
        # Check for invalid references
        invalid_refs = self._check_invalid_references()
        if invalid_refs:
            conflicts.extend(invalid_refs)
        
        # Check for data type mismatches
        type_mismatches = self._check_data_type_mismatches()
        if type_mismatches:
            conflicts.extend(type_mismatches)
        
        # Check for schema violations
        schema_violations = self._check_schema_violations()
        if schema_violations:
            conflicts.extend(schema_violations)
        
        logger.info(f"Conflict detection completed. Found {len(conflicts)} conflicts.")
        return conflicts
    
    def analyze_data_relationships(self) -> Dict[str, Any]:
        """Analyze relationships between different content types."""
        logger.info("Analyzing data relationships...")
        
        relationships = {
            'cross_content_references': {},
            'dependency_chains': [],
            'orphaned_items': [],
            'relationship_integrity': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Get all content by type
        content_types = ['KnowledgeItem', 'ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
        all_content = {}
        all_uids = set()
        
        for content_type in content_types:
            brains = self.catalog(portal_type=content_type)
            all_content[content_type] = brains
            all_uids.update(brain.UID for brain in brains)
        
        # Analyze cross-references
        ref_counts = defaultdict(int)
        invalid_refs = []
        
        for content_type, brains in all_content.items():
            for brain in brains:
                try:
                    obj = brain.getObject()
                    refs = self._extract_all_references(obj)
                    
                    for ref_uid in refs:
                        if ref_uid in all_uids:
                            ref_counts[f"{content_type}_to_valid"] += 1
                        else:
                            ref_counts[f"{content_type}_to_invalid"] += 1
                            invalid_refs.append({
                                'source': brain.UID,
                                'source_type': content_type,
                                'invalid_ref': ref_uid
                            })
                            
                except Exception as e:
                    logger.error(f"Error analyzing relationships for {brain.getPath()}: {str(e)}")
        
        relationships['cross_content_references'] = dict(ref_counts)
        relationships['relationship_integrity'] = {
            'total_references': sum(ref_counts.values()),
            'invalid_references': len(invalid_refs),
            'invalid_reference_details': invalid_refs[:50]  # Limit for report size
        }
        
        logger.info("Data relationship analysis completed.")
        return relationships
    
    def count_entities(self) -> Dict[str, int]:
        """Count all entities by type for migration planning."""
        logger.info("Counting entities...")
        
        counts = {}
        content_types = [
            'KnowledgeItem', 'ResearchNote', 'LearningGoal', 
            'ProjectLog', 'BookmarkPlus', 'KnowledgeContainer'
        ]
        
        for content_type in content_types:
            try:
                brains = self.catalog(portal_type=content_type)
                counts[content_type] = len(brains)
            except Exception as e:
                logger.error(f"Error counting {content_type}: {str(e)}")
                counts[content_type] = 0
        
        # Count total items
        counts['total_items'] = sum(counts.values())
        
        # Estimate migration complexity
        complexity_score = (
            counts.get('KnowledgeItem', 0) * 1.5 +  # Complex relationships
            counts.get('ResearchNote', 0) * 2.0 +   # Text to structured migration
            counts.get('LearningGoal', 0) * 2.5 +   # Graph integration
            counts.get('ProjectLog', 0) * 3.0 +     # Learning integration
            counts.get('BookmarkPlus', 0) * 1.0 +   # Simple migration
            counts.get('KnowledgeContainer', 0) * 1.2  # Container references
        )
        
        counts['migration_complexity_score'] = complexity_score
        
        logger.info(f"Entity counting completed. Total items: {counts['total_items']}")
        return counts
    
    def generate_assessment_report(self) -> Dict[str, Any]:
        """Generate comprehensive pre-migration assessment report."""
        logger.info("Generating comprehensive assessment report...")
        
        report = {
            'assessment_metadata': {
                'timestamp': datetime.now().isoformat(),
                'plone_version': api.env.plone_version(),
                'catalog_version': self._get_catalog_version(),
                'assessor_version': '1.0.0'
            },
            'entity_counts': self.count_entities(),
            'content_assessments': {},
            'migration_conflicts': self.detect_migration_conflicts(),
            'data_relationships': self.analyze_data_relationships(),
            'migration_readiness': {},
            'recommendations': []
        }
        
        # Assess each content type
        try:
            report['content_assessments']['knowledge_items'] = self.assess_knowledge_items()
        except Exception as e:
            logger.error(f"Knowledge Items assessment failed: {str(e)}")
            report['content_assessments']['knowledge_items'] = {'error': str(e)}
        
        try:
            report['content_assessments']['research_notes'] = self.assess_research_notes()
        except Exception as e:
            logger.error(f"Research Notes assessment failed: {str(e)}")
            report['content_assessments']['research_notes'] = {'error': str(e)}
        
        try:
            report['content_assessments']['learning_goals'] = self.assess_learning_goals()
        except Exception as e:
            logger.error(f"Learning Goals assessment failed: {str(e)}")
            report['content_assessments']['learning_goals'] = {'error': str(e)}
        
        try:
            report['content_assessments']['project_logs'] = self.assess_project_logs()
        except Exception as e:
            logger.error(f"Project Logs assessment failed: {str(e)}")
            report['content_assessments']['project_logs'] = {'error': str(e)}
        
        # Calculate migration readiness
        report['migration_readiness'] = self._calculate_migration_readiness(report)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        logger.info("Assessment report generation completed.")
        return report
    
    # Helper methods
    
    def _analyze_object_fields(self, obj, field_stats: dict, content_type: str):
        """Analyze fields of a content object for patterns."""
        for field_name in dir(obj):
            if field_name.startswith('_') or field_name in ['aq_base', 'meta_type']:
                continue
                
            try:
                value = getattr(obj, field_name, None)
                if callable(value):
                    continue
                
                stats = field_stats[field_name]
                
                if value is None or value == [] or value == '' or value == {}:
                    stats['empty'] += 1
                else:
                    stats['populated'] += 1
                    stats['types'][type(value).__name__] += 1
                    
                    # Store samples for analysis
                    if len(stats['samples']) < 5:
                        if isinstance(value, (str, int, float, bool)):
                            stats['samples'].append(str(value)[:100])
                        elif isinstance(value, (list, tuple)) and value:
                            stats['samples'].append(f"Length: {len(value)}, Type: {type(value[0]).__name__}")
                        else:
                            stats['samples'].append(f"Type: {type(value).__name__}")
                            
            except Exception as e:
                logger.debug(f"Error analyzing field {field_name} on {obj.getId()}: {str(e)}")
    
    def _detect_circular_dependencies(self, uid: str, prerequisites: List, enables: List) -> List[str]:
        """Detect circular dependencies in knowledge item relationships."""
        circular_refs = []
        
        # Simple circular check: if any prerequisite is also in enables
        prereq_uids = [getattr(item, 'UID', lambda: str(item))() if hasattr(item, 'UID') else str(item) for item in prerequisites]
        enable_uids = [getattr(item, 'UID', lambda: str(item))() if hasattr(item, 'UID') else str(item) for item in enables]
        
        common = set(prereq_uids) & set(enable_uids)
        if common:
            circular_refs.extend([f"{uid} <-> {ref}" for ref in common])
        
        return circular_refs
    
    def _assess_content_quality(self, obj) -> Dict[str, Any]:
        """Assess content quality for migration suitability."""
        issues = []
        
        # Check title length
        title = getattr(obj, 'title', '')
        if not title or len(title.strip()) < 3:
            issues.append("Title too short or missing")
        elif len(title) > 200:
            issues.append("Title too long")
        
        # Check content if available
        content = getattr(obj, 'content', None)
        if hasattr(content, 'raw') and content.raw:
            if len(content.raw.strip()) < 20:
                issues.append("Content too short")
        elif hasattr(obj, 'description'):
            desc = getattr(obj, 'description', '')
            if not desc or len(desc.strip()) < 10:
                issues.append("Description too short or missing")
        
        return {'issues': issues, 'quality_score': max(0, 100 - len(issues) * 20)}
    
    def _detect_migration_patterns(self, field_stats: dict) -> Dict[str, Any]:
        """Detect patterns in data that indicate migration needs."""
        patterns = {}
        
        for field_name, stats in field_stats.items():
            if 'str' in stats['types'] and stats['populated'] > 0:
                # Check if this field contains structured data that needs migration
                samples = stats['samples']
                if any('[' in str(sample) or '{' in str(sample) for sample in samples):
                    patterns[field_name] = 'possible_structured_data_in_text'
                elif field_name in ['key_insights', 'milestones', 'entries', 'deliverables']:
                    patterns[field_name] = 'text_to_structured_migration_needed'
        
        return patterns
    
    def _check_uid_conflicts(self) -> List[Dict[str, Any]]:
        """Check for UID conflicts across content types."""
        conflicts = []
        uid_map = defaultdict(list)
        
        # Collect all UIDs
        all_brains = self.catalog()
        for brain in all_brains:
            uid_map[brain.UID].append({
                'path': brain.getPath(),
                'type': brain.portal_type,
                'title': brain.Title
            })
        
        # Find duplicates (should not happen but check anyway)
        for uid, items in uid_map.items():
            if len(items) > 1:
                conflicts.append({
                    'type': 'uid_conflict',
                    'uid': uid,
                    'affected_items': items,
                    'severity': 'high'
                })
        
        return conflicts
    
    def _check_circular_dependencies(self) -> List[Dict[str, Any]]:
        """Check for circular dependencies in knowledge graph."""
        conflicts = []
        
        # Build dependency graph
        dependency_graph = defaultdict(set)
        
        knowledge_items = self.catalog(portal_type='KnowledgeItem')
        for brain in knowledge_items:
            try:
                obj = brain.getObject()
                uid = obj.UID()
                
                prerequisites = getattr(obj, 'prerequisite_items', [])
                for prereq in prerequisites:
                    prereq_uid = getattr(prereq, 'UID', lambda: str(prereq))() if hasattr(prereq, 'UID') else str(prereq)
                    dependency_graph[uid].add(prereq_uid)
                    
            except Exception as e:
                logger.error(f"Error building dependency graph for {brain.getPath()}: {str(e)}")
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in dependency_graph:
            if node not in visited:
                if has_cycle(node):
                    conflicts.append({
                        'type': 'circular_dependency',
                        'affected_item': node,
                        'severity': 'high'
                    })
        
        return conflicts
    
    def _check_invalid_references(self) -> List[Dict[str, Any]]:
        """Check for invalid UID references."""
        conflicts = []
        
        # Get all valid UIDs
        all_uids = set(brain.UID for brain in self.catalog())
        
        # Check references in each content type
        content_types = ['KnowledgeItem', 'ResearchNote', 'LearningGoal', 'ProjectLog', 'BookmarkPlus']
        
        for content_type in content_types:
            brains = self.catalog(portal_type=content_type)
            for brain in brains:
                try:
                    obj = brain.getObject()
                    refs = self._extract_all_references(obj)
                    
                    invalid_refs = [ref for ref in refs if ref not in all_uids]
                    if invalid_refs:
                        conflicts.append({
                            'type': 'invalid_reference',
                            'source_uid': obj.UID(),
                            'source_type': content_type,
                            'invalid_references': invalid_refs,
                            'severity': 'medium'
                        })
                        
                except Exception as e:
                    logger.error(f"Error checking references for {brain.getPath()}: {str(e)}")
        
        return conflicts
    
    def _check_data_type_mismatches(self) -> List[Dict[str, Any]]:
        """Check for data type mismatches that could cause migration issues."""
        conflicts = []
        
        # Define expected types for critical fields
        expected_types = {
            'KnowledgeItem': {
                'atomic_concepts': list,
                'tags': list,
                'learning_progress': (int, float),
                'mastery_threshold': (int, float)
            },
            'ResearchNote': {
                'key_insights': list,
                'tags': list,
                'authors': list
            },
            'LearningGoal': {
                'milestones': list,
                'target_knowledge_items': list,
                'overall_progress': (int, float)
            },
            'ProjectLog': {
                'entries': list,
                'deliverables': list,
                'knowledge_item_progress': dict
            }
        }
        
        for content_type, field_types in expected_types.items():
            brains = self.catalog(portal_type=content_type)
            for brain in brains:
                try:
                    obj = brain.getObject()
                    
                    for field_name, expected_type in field_types.items():
                        value = getattr(obj, field_name, None)
                        if value is not None:
                            if not isinstance(value, expected_type):
                                conflicts.append({
                                    'type': 'data_type_mismatch',
                                    'source_uid': obj.UID(),
                                    'source_type': content_type,
                                    'field': field_name,
                                    'expected_type': str(expected_type),
                                    'actual_type': str(type(value)),
                                    'severity': 'medium'
                                })
                                
                except Exception as e:
                    logger.error(f"Error checking types for {brain.getPath()}: {str(e)}")
        
        return conflicts
    
    def _check_schema_violations(self) -> List[Dict[str, Any]]:
        """Check for schema violations that could impact migration."""
        conflicts = []
        
        # Check for required fields that are missing
        required_fields = {
            'KnowledgeItem': ['title', 'description', 'content', 'knowledge_type'],
            'ResearchNote': ['title', 'content'],
            'LearningGoal': ['title', 'description'],
            'ProjectLog': ['title', 'description']
        }
        
        for content_type, fields in required_fields.items():
            brains = self.catalog(portal_type=content_type)
            for brain in brains:
                try:
                    obj = brain.getObject()
                    
                    for field_name in fields:
                        value = getattr(obj, field_name, None)
                        if not value or (isinstance(value, str) and not value.strip()):
                            conflicts.append({
                                'type': 'missing_required_field',
                                'source_uid': obj.UID(),
                                'source_type': content_type,
                                'field': field_name,
                                'severity': 'high'
                            })
                            
                except Exception as e:
                    logger.error(f"Error checking schema for {brain.getPath()}: {str(e)}")
        
        return conflicts
    
    def _extract_all_references(self, obj) -> List[str]:
        """Extract all UID references from an object."""
        refs = []
        
        # Common reference fields
        ref_fields = [
            'prerequisite_items', 'enables_items', 'target_knowledge_items',
            'related_knowledge_items', 'annotated_knowledge_items',
            'supports_learning_goals', 'attached_learning_goal',
            'builds_upon', 'contradicts', 'replication_studies'
        ]
        
        for field_name in ref_fields:
            value = getattr(obj, field_name, None)
            if value:
                if isinstance(value, (list, tuple)):
                    for item in value:
                        if isinstance(item, str):
                            refs.append(item)
                        elif hasattr(item, 'UID'):
                            refs.append(item.UID())
                elif isinstance(value, str):
                    refs.append(value)
                elif hasattr(value, 'UID'):
                    refs.append(value.UID())
        
        # Check dictionaries for UID keys
        dict_fields = ['knowledge_item_progress', 'sharing_permissions']
        for field_name in dict_fields:
            value = getattr(obj, field_name, None)
            if isinstance(value, dict):
                refs.extend(value.keys())
        
        return refs
    
    def _get_catalog_version(self) -> str:
        """Get portal catalog version for report metadata."""
        try:
            return getattr(self.catalog, '_version', 'unknown')
        except:
            return 'unknown'
    
    def _calculate_migration_readiness(self, report: dict) -> Dict[str, Any]:
        """Calculate overall migration readiness score."""
        readiness = {
            'overall_score': 0,
            'readiness_level': 'unknown',
            'blocking_issues': 0,
            'warning_issues': 0,
            'estimated_migration_time': 'unknown'
        }
        
        # Count issues by severity
        conflicts = report.get('migration_conflicts', [])
        blocking_issues = sum(1 for c in conflicts if c.get('severity') == 'high')
        warning_issues = sum(1 for c in conflicts if c.get('severity') == 'medium')
        
        readiness['blocking_issues'] = blocking_issues
        readiness['warning_issues'] = warning_issues
        
        # Calculate score (0-100)
        total_items = report.get('entity_counts', {}).get('total_items', 1)
        complexity_score = report.get('entity_counts', {}).get('migration_complexity_score', 0)
        
        # Base score starts at 100
        score = 100
        
        # Deduct for blocking issues (more severe)
        score -= blocking_issues * 20
        
        # Deduct for warning issues
        score -= warning_issues * 5
        
        # Adjust for complexity
        if total_items > 0:
            complexity_ratio = complexity_score / total_items
            if complexity_ratio > 2.0:
                score -= 15
            elif complexity_ratio > 1.5:
                score -= 10
        
        readiness['overall_score'] = max(0, score)
        
        # Determine readiness level
        if score >= 90:
            readiness['readiness_level'] = 'excellent'
            readiness['estimated_migration_time'] = 'low'
        elif score >= 75:
            readiness['readiness_level'] = 'good'
            readiness['estimated_migration_time'] = 'medium'
        elif score >= 50:
            readiness['readiness_level'] = 'fair'
            readiness['estimated_migration_time'] = 'high'
        elif score >= 25:
            readiness['readiness_level'] = 'poor'
            readiness['estimated_migration_time'] = 'very high'
        else:
            readiness['readiness_level'] = 'critical'
            readiness['estimated_migration_time'] = 'critical'
        
        return readiness
    
    def _generate_recommendations(self, report: dict) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on assessment."""
        recommendations = []
        
        readiness = report.get('migration_readiness', {})
        conflicts = report.get('migration_conflicts', [])
        
        # Recommendations based on readiness level
        if readiness.get('readiness_level') == 'critical':
            recommendations.append({
                'priority': 'critical',
                'category': 'preparation',
                'recommendation': 'Address all blocking issues before attempting migration',
                'action': 'Review and fix high-severity conflicts in the conflicts report'
            })
        
        # Specific recommendations for common issues
        blocking_issues = readiness.get('blocking_issues', 0)
        if blocking_issues > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'data_integrity',
                'recommendation': f'Fix {blocking_issues} critical data integrity issues',
                'action': 'Review schema violations and missing required fields'
            })
        
        # Recommendations based on content assessments
        content_assessments = report.get('content_assessments', {})
        
        for content_type, assessment in content_assessments.items():
            if isinstance(assessment, dict) and 'migration_needs' in assessment:
                needs = assessment['migration_needs']
                
                if content_type == 'research_notes':
                    if needs.get('text_to_structured', 0) > 0:
                        recommendations.append({
                            'priority': 'medium',
                            'category': 'data_migration',
                            'recommendation': f'Prepare for migration of {needs["text_to_structured"]} Research Notes with text-based insights',
                            'action': 'Review key_insights fields and prepare structured data conversion'
                        })
                
                elif content_type == 'learning_goals':
                    if needs.get('progress_recalculation', 0) > 0:
                        recommendations.append({
                            'priority': 'medium',
                            'category': 'data_migration',
                            'recommendation': f'Recalculate progress for {needs["progress_recalculation"]} Learning Goals',
                            'action': 'Verify progress calculations after migration'
                        })
        
        # General recommendations
        total_items = report.get('entity_counts', {}).get('total_items', 0)
        if total_items > 1000:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'recommendation': 'Consider batch processing for large dataset migration',
                'action': 'Plan migration in smaller batches to avoid timeout issues'
            })
        
        # Backup recommendation
        recommendations.append({
            'priority': 'critical',
            'category': 'safety',
            'recommendation': 'Create complete backup before migration',
            'action': 'Backup both ZODB and any external data stores'
        })
        
        return recommendations


# Main assessment function for use in upgrades
def assess_current_state(context):
    """Main assessment function to evaluate current data state.
    
    Args:
        context: Plone context object
        
    Returns:
        dict: Comprehensive assessment report
    """
    logger.info("Starting comprehensive data assessment...")
    
    try:
        assessor = DataAssessment(context)
        report = assessor.generate_assessment_report()
        
        # Store report for later reference
        registry = queryUtility(IRegistry)
        if registry:
            try:
                registry['knowledge.curator.last_assessment_report'] = json.dumps(report, default=str)
                registry['knowledge.curator.last_assessment_timestamp'] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"Could not store assessment report in registry: {str(e)}")
        
        logger.info("Data assessment completed successfully.")
        return report
        
    except Exception as e:
        logger.error(f"Assessment failed: {str(e)}")
        raise AssessmentError(f"Assessment failed: {str(e)}")


# Utility functions for specific assessments
def quick_entity_count(context):
    """Quick count of entities for migration planning."""
    assessor = DataAssessment(context)
    return assessor.count_entities()


def check_migration_conflicts(context):
    """Quick conflict detection for migration readiness."""
    assessor = DataAssessment(context)
    return assessor.detect_migration_conflicts()


def assess_content_type(context, content_type):
    """Assess a specific content type."""
    assessor = DataAssessment(context)
    
    if content_type == 'KnowledgeItem':
        return assessor.assess_knowledge_items()
    elif content_type == 'ResearchNote':
        return assessor.assess_research_notes()
    elif content_type == 'LearningGoal':
        return assessor.assess_learning_goals()
    elif content_type == 'ProjectLog':
        return assessor.assess_project_logs()
    else:
        raise ValueError(f"Unknown content type: {content_type}")