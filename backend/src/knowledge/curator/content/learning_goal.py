"""Learning Goal content type."""

from datetime import datetime
from knowledge.curator.interfaces import ILearningGoal, ILearningMilestone, ILearningObjective, IAssessmentCriterion, ICompetency
from plone.dexterity.content import Container
from zope.interface import implementer
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
import uuid


@implementer(ILearningGoal)
class LearningGoal(Container):
    """Learning Goal content type implementation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize structured lists
        if not hasattr(self, 'milestones'):
            self.milestones = PersistentList()
        if not hasattr(self, 'learning_objectives'):
            self.learning_objectives = PersistentList()
        if not hasattr(self, 'assessment_criteria'):
            self.assessment_criteria = PersistentList()
        if not hasattr(self, 'competencies'):
            self.competencies = PersistentList()
        if not hasattr(self, 'prerequisite_knowledge'):
            self.prerequisite_knowledge = PersistentList()

    def add_milestone(self, title, description, target_date=None, status='not_started', progress_percentage=0, completion_criteria=None):
        """Add a structured milestone to the learning goal."""
        if not hasattr(self, 'milestones'):
            self.milestones = PersistentList()

        milestone = PersistentMapping()
        milestone['id'] = f"milestone-{str(uuid.uuid4())[:8]}"
        milestone['title'] = title
        milestone['description'] = description
        milestone['target_date'] = target_date
        milestone['status'] = status
        milestone['progress_percentage'] = progress_percentage
        milestone['completion_criteria'] = completion_criteria
        
        self.milestones.append(milestone)
        return milestone

    def update_milestone(self, milestone_id, **kwargs):
        """Update a specific milestone."""
        if not hasattr(self, 'milestones'):
            return None

        for milestone in self.milestones:
            if milestone.get("id") == milestone_id:
                milestone.update(kwargs)
                if kwargs.get("status") == 'completed' and milestone['status'] != 'completed':
                    milestone["completed_date"] = datetime.now()
                return milestone
        return None

    def complete_milestone(self, milestone_id):
        """Mark a milestone as completed."""
        return self.update_milestone(milestone_id, status='completed', progress_percentage=100)

    def add_learning_objective(self, objective_text, measurable=False, achievable=False, 
                             relevant=False, time_bound=False, success_metrics=None):
        """Add a SMART learning objective."""
        if not hasattr(self, 'learning_objectives'):
            self.learning_objectives = PersistentList()
        
        objective = PersistentMapping()
        objective['objective_text'] = objective_text
        objective['measurable'] = measurable
        objective['achievable'] = achievable
        objective['relevant'] = relevant
        objective['time_bound'] = time_bound
        objective['success_metrics'] = success_metrics or []
        
        self.learning_objectives.append(objective)
        return objective

    def add_assessment_criterion(self, criterion, weight=1.0, description=None):
        """Add an assessment criterion."""
        if not hasattr(self, 'assessment_criteria'):
            self.assessment_criteria = PersistentList()
        
        assessment = PersistentMapping()
        assessment['criterion'] = criterion
        assessment['weight'] = weight
        assessment['description'] = description
        
        self.assessment_criteria.append(assessment)
        return assessment

    def add_competency(self, name, description=None, level='beginner', category=None):
        """Add a competency to be developed."""
        if not hasattr(self, 'competencies'):
            self.competencies = PersistentList()
        
        competency = PersistentMapping()
        competency['name'] = name
        competency['description'] = description
        competency['level'] = level
        competency['category'] = category
        
        self.competencies.append(competency)
        return competency

    def calculate_progress(self):
        """Calculate progress based on milestone completion."""
        if not hasattr(self, 'milestones') or not self.milestones:
            return 0

        total_progress = sum(m.get('progress_percentage', 0) for m in self.milestones)
        total_milestones = len(self.milestones)

        if total_milestones == 0:
            return 0

        return int(total_progress / total_milestones)

    def update_progress(self):
        """Update the progress field based on milestones."""
        self.progress = self.calculate_progress()

    def add_related_note(self, note_uid):
        """Add a related research note."""
        if not hasattr(self, 'related_notes'):
            self.related_notes = PersistentList()
        if note_uid not in self.related_notes:
            self.related_notes.append(note_uid)

    def remove_related_note(self, note_uid):
        """Remove a related research note."""
        if hasattr(self, 'related_notes') and note_uid in self.related_notes:
            self.related_notes.remove(note_uid)

    def is_overdue(self):
        """Check if the goal is overdue."""
        if not self.target_date:
            return False
        return datetime.now().date() > self.target_date and self.progress < 100

    def migrate_legacy_milestones(self):
        """Migrate legacy text milestones to structured format."""
        # Check if we have old-style milestones
        if hasattr(self, 'milestones') and self.milestones:
            # Check if first item is a string or dict without proper structure
            if self.milestones and (isinstance(self.milestones[0], str) or 
                                   (isinstance(self.milestones[0], dict) and 
                                    'status' not in self.milestones[0])):
                old_milestones = list(self.milestones)
                self.milestones = PersistentList()
                
                for idx, milestone in enumerate(old_milestones):
                    if isinstance(milestone, str):
                        self.add_milestone(
                            title=milestone,
                            description='',
                            status='not_started'
                        )
                    elif isinstance(milestone, dict):
                        # Old dict format migration
                        self.add_milestone(
                            title=milestone.get('title', f'Milestone {idx+1}'),
                            description=milestone.get('description', ''),
                            target_date=milestone.get('target_date'),
                            status='completed' if milestone.get('completed') else 'not_started',
                            progress_percentage=100 if milestone.get('completed') else 0
                        )
                return True
        return False

    def validate_learning_path(self):
        """Validate the learning path graph for cycles, connectivity, and consistency.
        
        Returns:
            dict with 'valid' (bool) and 'errors' (list of error messages)
        """
        errors = []
        
        # Check if we have necessary fields
        if not hasattr(self, 'starting_knowledge_item') or not self.starting_knowledge_item:
            errors.append("No starting knowledge item defined for learning path")
            return {'valid': False, 'errors': errors}
        
        if not hasattr(self, 'target_knowledge_items') or not self.target_knowledge_items:
            errors.append("No target knowledge items defined for learning path")
            return {'valid': False, 'errors': errors}
        
        if not hasattr(self, 'knowledge_item_connections') or not self.knowledge_item_connections:
            errors.append("No connections defined in learning path")
            return {'valid': False, 'errors': errors}
        
        # Build adjacency list and validate connections exist
        from plone import api
        graph = {}
        reverse_graph = {}
        connection_map = {}  # Maps (source, target) to connection object
        all_items = set()
        
        for conn in self.knowledge_item_connections:
            source_uid = conn.get('source_item_uid')
            target_uid = conn.get('target_item_uid')
            
            if not source_uid or not target_uid:
                errors.append("Connection missing source or target UID")
                continue
            
            # Validate that the items exist
            source_item = api.content.get(UID=source_uid)
            target_item = api.content.get(UID=target_uid)
            
            if not source_item:
                errors.append(f"Source item {source_uid} not found")
                continue
            if not target_item:
                errors.append(f"Target item {target_uid} not found")
                continue
            
            # Build graph structures
            if source_uid not in graph:
                graph[source_uid] = []
            graph[source_uid].append(target_uid)
            
            if target_uid not in reverse_graph:
                reverse_graph[target_uid] = []
            reverse_graph[target_uid].append(source_uid)
            
            all_items.add(source_uid)
            all_items.add(target_uid)
            
            # Store connection for later validation
            connection_map[(source_uid, target_uid)] = conn
        
        # 1. Cycle Detection using DFS
        def has_cycle_dfs(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle_dfs(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        # Found a back edge (cycle)
                        errors.append(f"Cycle detected involving items {node} and {neighbor}")
                        return True
            
            rec_stack.remove(node)
            return False
        
        # Check for cycles starting from each unvisited node
        visited = set()
        for item_uid in all_items:
            if item_uid not in visited:
                if has_cycle_dfs(item_uid, visited, set()):
                    # Cycle found, but error already added in the recursive function
                    pass
        
        # 2. Verify all target items are reachable from starting item
        def find_reachable(start_uid):
            reachable = set()
            queue = [start_uid]
            
            while queue:
                current = queue.pop(0)
                if current in reachable:
                    continue
                    
                reachable.add(current)
                
                if current in graph:
                    for neighbor in graph[current]:
                        if neighbor not in reachable:
                            queue.append(neighbor)
            
            return reachable
        
        reachable_from_start = find_reachable(self.starting_knowledge_item)
        
        # Check if starting item exists
        if self.starting_knowledge_item not in all_items:
            starting_item = api.content.get(UID=self.starting_knowledge_item)
            if not starting_item:
                errors.append(f"Starting knowledge item {self.starting_knowledge_item} not found")
            else:
                errors.append(f"Starting knowledge item {self.starting_knowledge_item} is not connected in the graph")
        
        # Check each target item
        for target_uid in self.target_knowledge_items:
            if target_uid not in reachable_from_start:
                target_item = api.content.get(UID=target_uid)
                if not target_item:
                    errors.append(f"Target knowledge item {target_uid} not found")
                else:
                    errors.append(f"Target knowledge item '{target_item.title}' ({target_uid}) is not reachable from starting item")
        
        # 3. Check for orphaned connections (nodes not connected to starting or target items)
        # Find all items that can reach any target
        can_reach_target = set()
        for target_uid in self.target_knowledge_items:
            if target_uid in reverse_graph:
                # Do reverse BFS from target
                queue = [target_uid]
                visited_reverse = set()
                
                while queue:
                    current = queue.pop(0)
                    if current in visited_reverse:
                        continue
                    
                    visited_reverse.add(current)
                    can_reach_target.add(current)
                    
                    if current in reverse_graph:
                        for predecessor in reverse_graph[current]:
                            if predecessor not in visited_reverse:
                                queue.append(predecessor)
        
        # Find orphaned items (in graph but neither reachable from start nor can reach target)
        for item_uid in all_items:
            if (item_uid not in reachable_from_start and 
                item_uid not in can_reach_target and
                item_uid != self.starting_knowledge_item and
                item_uid not in self.target_knowledge_items):
                item = api.content.get(UID=item_uid)
                item_title = item.title if item else "Unknown"
                errors.append(f"Knowledge item '{item_title}' ({item_uid}) is orphaned - not connected to learning path")
        
        # 4. Validate connection strength and mastery requirement consistency
        for conn in self.knowledge_item_connections:
            source_uid = conn.get('source_item_uid')
            target_uid = conn.get('target_item_uid')
            connection_type = conn.get('connection_type', '')
            strength = conn.get('strength', 0.5)
            mastery_req = conn.get('mastery_requirement', 0.8)
            
            # Validate connection type specific constraints
            if connection_type == 'prerequisite':
                if mastery_req < 0.7:
                    errors.append(
                        f"Prerequisite connection from {source_uid} to {target_uid} "
                        f"has low mastery requirement ({mastery_req}). "
                        "Prerequisites should require at least 0.7 mastery."
                    )
                if strength < 0.7:
                    errors.append(
                        f"Prerequisite connection from {source_uid} to {target_uid} "
                        f"has low strength ({strength}). "
                        "Prerequisites should have strength of at least 0.7."
                    )
            
            elif connection_type == 'builds_on':
                if strength < 0.3 or strength > 0.7:
                    errors.append(
                        f"Builds-on connection from {source_uid} to {target_uid} "
                        f"has inappropriate strength ({strength}). "
                        "Builds-on connections should have moderate strength (0.3-0.7)."
                    )
            
            # Check for duplicate connections with different parameters
            for other_conn in self.knowledge_item_connections:
                if (other_conn != conn and
                    other_conn.get('source_item_uid') == source_uid and
                    other_conn.get('target_item_uid') == target_uid):
                    errors.append(
                        f"Duplicate connection found from {source_uid} to {target_uid}. "
                        "Each pair of items should have only one connection."
                    )
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def add_knowledge_item_connection(self, source_item_uid, target_item_uid, 
                                    connection_type='builds_on', strength=0.5, 
                                    mastery_requirement=0.8, notes=None):
        """Add a connection between knowledge items with validation.
        
        Args:
            source_item_uid: UID of the source knowledge item
            target_item_uid: UID of the target knowledge item
            connection_type: Type of connection ('prerequisite', 'builds_on', 'related', etc.)
            strength: Connection strength (0.0 to 1.0)
            mastery_requirement: Required mastery level of source before moving to target (0.0 to 1.0)
            notes: Optional notes about the connection
            
        Returns:
            dict with 'success' (bool), 'connection' (dict) or 'error' (str)
        """
        from plone import api
        
        # Initialize connections list if not exists
        if not hasattr(self, 'knowledge_item_connections'):
            self.knowledge_item_connections = PersistentList()
        
        # Validation
        if not source_item_uid or not target_item_uid:
            return {'success': False, 'error': 'Source and target UIDs are required'}
        
        if source_item_uid == target_item_uid:
            return {'success': False, 'error': 'Cannot create self-referencing connection'}
        
        # Validate UIDs exist
        source_item = api.content.get(UID=source_item_uid)
        target_item = api.content.get(UID=target_item_uid)
        
        if not source_item:
            return {'success': False, 'error': f'Source knowledge item {source_item_uid} not found'}
        if not target_item:
            return {'success': False, 'error': f'Target knowledge item {target_item_uid} not found'}
        
        # Validate parameters
        if strength < 0.0 or strength > 1.0:
            return {'success': False, 'error': 'Strength must be between 0.0 and 1.0'}
        
        if mastery_requirement < 0.0 or mastery_requirement > 1.0:
            return {'success': False, 'error': 'Mastery requirement must be between 0.0 and 1.0'}
        
        # Connection type specific validation
        if connection_type == 'prerequisite':
            if mastery_requirement < 0.7:
                return {
                    'success': False, 
                    'error': 'Prerequisite connections should require at least 0.7 mastery'
                }
            if strength < 0.7:
                return {
                    'success': False,
                    'error': 'Prerequisite connections should have strength of at least 0.7'
                }
        elif connection_type == 'builds_on':
            if strength < 0.3 or strength > 0.7:
                return {
                    'success': False,
                    'error': 'Builds-on connections should have moderate strength (0.3-0.7)'
                }
        
        # Check for duplicate connections
        for conn in self.knowledge_item_connections:
            if (conn.get('source_item_uid') == source_item_uid and 
                conn.get('target_item_uid') == target_item_uid):
                return {
                    'success': False,
                    'error': 'Connection already exists between these items'
                }
        
        # Create connection
        connection = PersistentMapping()
        connection['id'] = f"conn-{str(uuid.uuid4())[:8]}"
        connection['source_item_uid'] = source_item_uid
        connection['target_item_uid'] = target_item_uid
        connection['connection_type'] = connection_type
        connection['strength'] = strength
        connection['mastery_requirement'] = mastery_requirement
        connection['notes'] = notes
        connection['created_date'] = datetime.now()
        
        # Add to connections list
        self.knowledge_item_connections.append(connection)
        
        # Validate the graph after adding (check for cycles)
        validation_result = self.validate_learning_path()
        if not validation_result['valid']:
            # Remove the connection if it creates an invalid graph
            self.knowledge_item_connections.remove(connection)
            cycle_errors = [e for e in validation_result['errors'] if 'Cycle detected' in e]
            if cycle_errors:
                return {
                    'success': False,
                    'error': f'Connection would create a cycle in the learning path: {cycle_errors[0]}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Connection creates invalid learning path: {"; ".join(validation_result["errors"])}'
                }
        
        return {
            'success': True,
            'connection': connection
        }
    
    def get_next_knowledge_items(self, current_mastery_levels=None, 
                                max_recommendations=5, 
                                min_strength_threshold=0.3,
                                include_prerequisites=True):
        """Get recommended next knowledge items based on current mastery and connections.
        
        Args:
            current_mastery_levels: dict mapping knowledge item UIDs to mastery levels (0.0 to 1.0)
            max_recommendations: Maximum number of items to recommend
            min_strength_threshold: Minimum connection strength to consider
            include_prerequisites: Whether to check prerequisite satisfaction
            
        Returns:
            List of dicts containing:
                - item_uid: UID of recommended item
                - item: The knowledge item object
                - score: Recommendation score
                - reason: Why this item is recommended
                - prerequisites_met: Whether all prerequisites are satisfied
                - connections: List of connections leading to this item
        """
        from plone import api
        
        if not hasattr(self, 'knowledge_item_connections') or not self.knowledge_item_connections:
            return []
        
        if current_mastery_levels is None:
            current_mastery_levels = {}
        
        # Build graph structures
        incoming_connections = {}  # target -> list of connections
        outgoing_connections = {}  # source -> list of connections
        
        for conn in self.knowledge_item_connections:
            source_uid = conn.get('source_item_uid')
            target_uid = conn.get('target_item_uid')
            strength = conn.get('strength', 0.5)
            
            # Skip weak connections
            if strength < min_strength_threshold:
                continue
            
            if target_uid not in incoming_connections:
                incoming_connections[target_uid] = []
            incoming_connections[target_uid].append(conn)
            
            if source_uid not in outgoing_connections:
                outgoing_connections[source_uid] = []
            outgoing_connections[source_uid].append(conn)
        
        recommendations = []
        
        # Find all unique target items
        all_target_uids = set(incoming_connections.keys())
        
        for target_uid in all_target_uids:
            # Skip if already mastered
            if current_mastery_levels.get(target_uid, 0) >= 0.8:
                continue
            
            target_item = api.content.get(UID=target_uid)
            if not target_item:
                continue
            
            # Calculate recommendation score
            score = 0.0
            reasons = []
            prerequisites_met = True
            relevant_connections = []
            
            # Check all incoming connections
            for conn in incoming_connections[target_uid]:
                source_uid = conn.get('source_item_uid')
                connection_type = conn.get('connection_type', '')
                strength = conn.get('strength', 0.5)
                mastery_req = conn.get('mastery_requirement', 0.8)
                
                source_mastery = current_mastery_levels.get(source_uid, 0)
                
                # Check if this is a prerequisite
                if connection_type == 'prerequisite':
                    if source_mastery < mastery_req:
                        prerequisites_met = False
                        if include_prerequisites:
                            continue  # Skip this recommendation
                    else:
                        score += strength * 2.0  # Prerequisites satisfied add high value
                        reasons.append(f"Prerequisite satisfied ({source_uid})")
                
                # Check builds_on connections
                elif connection_type == 'builds_on':
                    if source_mastery >= mastery_req:
                        score += strength * 1.5 * source_mastery
                        reasons.append(f"Builds on mastered content ({source_uid})")
                    else:
                        # Partial credit if partially mastered
                        score += strength * 0.5 * (source_mastery / mastery_req)
                        reasons.append(f"Partially builds on {source_uid}")
                
                # Related items
                elif connection_type == 'related':
                    if source_mastery > 0:
                        score += strength * source_mastery
                        reasons.append(f"Related to studied content ({source_uid})")
                
                relevant_connections.append(conn)
            
            # Skip if prerequisites not met and we're enforcing them
            if include_prerequisites and not prerequisites_met:
                continue
            
            # Check if this is directly connected to starting item
            if hasattr(self, 'starting_knowledge_item'):
                if target_uid in outgoing_connections.get(self.starting_knowledge_item, []):
                    score += 0.5
                    reasons.append("Directly connected to starting item")
            
            # Check if this leads to target items
            if hasattr(self, 'target_knowledge_items'):
                for final_target in self.target_knowledge_items:
                    if final_target in outgoing_connections.get(target_uid, []):
                        score += 1.0
                        reasons.append(f"Leads directly to target item {final_target}")
            
            # Add proximity bonus for items with many satisfied prerequisites
            satisfied_prereqs = sum(1 for conn in relevant_connections 
                                  if conn.get('connection_type') == 'prerequisite' 
                                  and current_mastery_levels.get(conn.get('source_item_uid'), 0) >= conn.get('mastery_requirement', 0.8))
            if satisfied_prereqs > 0:
                score += 0.3 * satisfied_prereqs
                reasons.append(f"{satisfied_prereqs} prerequisites satisfied")
            
            # Only recommend if score is positive
            if score > 0:
                recommendations.append({
                    'item_uid': target_uid,
                    'item': target_item,
                    'score': score,
                    'reason': '; '.join(reasons) if reasons else 'Connected in learning path',
                    'prerequisites_met': prerequisites_met,
                    'connections': relevant_connections
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:max_recommendations]
    
    def calculate_overall_progress(self, knowledge_item_mastery=None):
        """Calculate overall learning goal progress based on knowledge item mastery levels.
        
        This method aggregates mastery across the learning graph, weighing items by:
        - Their connection strengths and types
        - Prerequisite completion requirements
        - Position in the learning path (distance from start to targets)
        
        Args:
            knowledge_item_mastery: dict mapping knowledge item UIDs to mastery levels (0.0 to 1.0)
                                  If None, assumes no items have been mastered
        
        Returns:
            dict containing:
                - overall_percentage: Overall completion percentage (0-100)
                - weighted_progress: Weighted progress value (0.0-1.0)
                - items_mastered: Number of items with mastery >= 0.8
                - total_items: Total number of items in learning path
                - prerequisite_satisfaction: Percentage of prerequisites satisfied
                - path_segments: Progress data for each segment of the learning path
                - visualization_data: Data structure for graph-based progress visualization
                - bottlenecks: List of items blocking progress
                - next_milestones: List of nearly-completed items (mastery 0.6-0.8)
        """
        from plone import api
        
        if knowledge_item_mastery is None:
            knowledge_item_mastery = {}
        
        # Initialize result structure
        result = {
            'overall_percentage': 0,
            'weighted_progress': 0.0,
            'items_mastered': 0,
            'total_items': 0,
            'prerequisite_satisfaction': 0.0,
            'path_segments': [],
            'visualization_data': {
                'nodes': [],
                'edges': [],
                'progress_by_level': {}
            },
            'bottlenecks': [],
            'next_milestones': []
        }
        
        # Validate we have required fields
        if not hasattr(self, 'knowledge_item_connections') or not self.knowledge_item_connections:
            return result
        
        if not hasattr(self, 'starting_knowledge_item') or not self.starting_knowledge_item:
            return result
        
        if not hasattr(self, 'target_knowledge_items') or not self.target_knowledge_items:
            return result
        
        # Build graph structures
        graph = {}  # source -> [(target, connection)]
        reverse_graph = {}  # target -> [(source, connection)]
        all_items = set()
        connection_map = {}  # (source, target) -> connection
        
        for conn in self.knowledge_item_connections:
            source_uid = conn.get('source_item_uid')
            target_uid = conn.get('target_item_uid')
            
            if not source_uid or not target_uid:
                continue
            
            # Add to graph structures
            if source_uid not in graph:
                graph[source_uid] = []
            graph[source_uid].append((target_uid, conn))
            
            if target_uid not in reverse_graph:
                reverse_graph[target_uid] = []
            reverse_graph[target_uid].append((source_uid, conn))
            
            all_items.add(source_uid)
            all_items.add(target_uid)
            connection_map[(source_uid, target_uid)] = conn
        
        # Ensure starting and target items are in the set
        all_items.add(self.starting_knowledge_item)
        for target in self.target_knowledge_items:
            all_items.add(target)
        
        result['total_items'] = len(all_items)
        
        # Calculate distance from start to each item (BFS)
        distances_from_start = {self.starting_knowledge_item: 0}
        queue = [(self.starting_knowledge_item, 0)]
        
        while queue:
            current, dist = queue.pop(0)
            
            if current in graph:
                for neighbor, conn in graph[current]:
                    if neighbor not in distances_from_start:
                        distances_from_start[neighbor] = dist + 1
                        queue.append((neighbor, dist + 1))
        
        # Calculate minimum distance to any target from each item (reverse BFS)
        distances_to_target = {}
        for target in self.target_knowledge_items:
            distances_to_target[target] = 0
            queue = [(target, 0)]
            
            while queue:
                current, dist = queue.pop(0)
                
                if current in reverse_graph:
                    for neighbor, conn in reverse_graph[current]:
                        if neighbor not in distances_to_target or distances_to_target[neighbor] > dist + 1:
                            distances_to_target[neighbor] = dist + 1
                            queue.append((neighbor, dist + 1))
        
        # Calculate importance weight for each item
        item_weights = {}
        max_path_length = 0
        
        for item_uid in all_items:
            # Skip if item is not on a valid path
            if item_uid not in distances_from_start or item_uid not in distances_to_target:
                item_weights[item_uid] = 0.1  # Minimal weight for disconnected items
                continue
            
            # Calculate position-based weight
            total_distance = distances_from_start[item_uid] + distances_to_target[item_uid]
            if total_distance > max_path_length:
                max_path_length = total_distance
            
            # Items closer to targets get higher weight
            position_weight = 1.0 + (0.5 * (1.0 - distances_to_target[item_uid] / (total_distance + 1)))
            
            # Adjust weight based on connections
            connection_weight = 1.0
            
            # Check incoming connections
            if item_uid in reverse_graph:
                for source_uid, conn in reverse_graph[item_uid]:
                    conn_type = conn.get('connection_type', '')
                    strength = conn.get('strength', 0.5)
                    
                    if conn_type == 'prerequisite':
                        connection_weight *= (1.0 + strength * 0.5)  # Prerequisites increase importance
                    elif conn_type == 'builds_on':
                        connection_weight *= (1.0 + strength * 0.3)
            
            # Check outgoing connections
            if item_uid in graph:
                num_outgoing = len(graph[item_uid])
                if num_outgoing > 1:
                    connection_weight *= (1.0 + 0.1 * num_outgoing)  # Junction points are important
            
            # Special weight for start and target items
            if item_uid == self.starting_knowledge_item:
                connection_weight *= 1.5
            elif item_uid in self.target_knowledge_items:
                connection_weight *= 2.0
            
            item_weights[item_uid] = position_weight * connection_weight
        
        # Normalize weights
        total_weight = sum(item_weights.values())
        if total_weight > 0:
            for item_uid in item_weights:
                item_weights[item_uid] /= total_weight
        
        # Calculate weighted progress
        weighted_progress = 0.0
        items_mastered = 0
        prerequisite_checks = []
        
        # Build visualization data and calculate progress
        for item_uid in all_items:
            mastery = knowledge_item_mastery.get(item_uid, 0.0)
            weight = item_weights.get(item_uid, 0.0)
            
            # Get item details
            item = api.content.get(UID=item_uid)
            item_title = item.title if item else f"Unknown ({item_uid[:8]})"
            
            # Add to weighted progress
            weighted_progress += mastery * weight
            
            # Count mastered items
            if mastery >= 0.8:
                items_mastered += 1
            
            # Check for bottlenecks (required prerequisites not met)
            is_bottleneck = False
            if item_uid in graph:
                for target_uid, conn in graph[item_uid]:
                    if (conn.get('connection_type') == 'prerequisite' and 
                        mastery < conn.get('mastery_requirement', 0.8) and
                        knowledge_item_mastery.get(target_uid, 0.0) < 0.1):  # Target is not started
                        is_bottleneck = True
                        break
            
            if is_bottleneck:
                result['bottlenecks'].append({
                    'item_uid': item_uid,
                    'title': item_title,
                    'mastery': mastery,
                    'required_for': [t for t, c in graph.get(item_uid, []) 
                                   if c.get('connection_type') == 'prerequisite']
                })
            
            # Check for next milestones (nearly complete)
            if 0.6 <= mastery < 0.8:
                result['next_milestones'].append({
                    'item_uid': item_uid,
                    'title': item_title,
                    'mastery': mastery,
                    'completion_gap': 0.8 - mastery
                })
            
            # Add node to visualization data
            level = distances_from_start.get(item_uid, -1)
            node_data = {
                'id': item_uid,
                'title': item_title,
                'mastery': mastery,
                'weight': weight,
                'level': level,
                'is_start': item_uid == self.starting_knowledge_item,
                'is_target': item_uid in self.target_knowledge_items,
                'is_bottleneck': is_bottleneck,
                'is_mastered': mastery >= 0.8
            }
            result['visualization_data']['nodes'].append(node_data)
            
            # Track progress by level
            if level >= 0:
                if level not in result['visualization_data']['progress_by_level']:
                    result['visualization_data']['progress_by_level'][level] = {
                        'total_items': 0,
                        'mastered_items': 0,
                        'total_mastery': 0.0,
                        'average_mastery': 0.0
                    }
                
                level_data = result['visualization_data']['progress_by_level'][level]
                level_data['total_items'] += 1
                level_data['total_mastery'] += mastery
                if mastery >= 0.8:
                    level_data['mastered_items'] += 1
        
        # Calculate average mastery per level
        for level, data in result['visualization_data']['progress_by_level'].items():
            if data['total_items'] > 0:
                data['average_mastery'] = data['total_mastery'] / data['total_items']
        
        # Add edges to visualization data
        for conn in self.knowledge_item_connections:
            source_uid = conn.get('source_item_uid')
            target_uid = conn.get('target_item_uid')
            
            if source_uid and target_uid:
                edge_data = {
                    'source': source_uid,
                    'target': target_uid,
                    'type': conn.get('connection_type', 'related'),
                    'strength': conn.get('strength', 0.5),
                    'mastery_requirement': conn.get('mastery_requirement', 0.8),
                    'is_satisfied': knowledge_item_mastery.get(source_uid, 0.0) >= conn.get('mastery_requirement', 0.8)
                }
                result['visualization_data']['edges'].append(edge_data)
        
        # Calculate prerequisite satisfaction
        total_prerequisites = 0
        satisfied_prerequisites = 0
        
        for conn in self.knowledge_item_connections:
            if conn.get('connection_type') == 'prerequisite':
                total_prerequisites += 1
                source_mastery = knowledge_item_mastery.get(conn.get('source_item_uid'), 0.0)
                if source_mastery >= conn.get('mastery_requirement', 0.8):
                    satisfied_prerequisites += 1
        
        if total_prerequisites > 0:
            result['prerequisite_satisfaction'] = (satisfied_prerequisites / total_prerequisites) * 100
        else:
            result['prerequisite_satisfaction'] = 100.0
        
        # Calculate path segments progress
        # Group items by their level (distance from start)
        levels = {}
        for item_uid in all_items:
            if item_uid in distances_from_start:
                level = distances_from_start[item_uid]
                if level not in levels:
                    levels[level] = []
                levels[level].append(item_uid)
        
        # Calculate progress for each segment
        for level in sorted(levels.keys()):
            items_in_level = levels[level]
            level_mastery_sum = sum(knowledge_item_mastery.get(uid, 0.0) for uid in items_in_level)
            level_average = level_mastery_sum / len(items_in_level) if items_in_level else 0.0
            
            segment_data = {
                'level': level,
                'item_count': len(items_in_level),
                'average_mastery': level_average,
                'completion_percentage': (level_average * 100),
                'items': items_in_level
            }
            
            # Add segment type description
            if level == 0:
                segment_data['description'] = 'Starting Knowledge'
            elif level == max_path_length:
                segment_data['description'] = 'Target Knowledge'
            else:
                segment_data['description'] = f'Intermediate Level {level}'
            
            result['path_segments'].append(segment_data)
        
        # Set final results
        result['weighted_progress'] = weighted_progress
        result['overall_percentage'] = int(weighted_progress * 100)
        result['items_mastered'] = items_mastered
        
        # Sort bottlenecks and milestones by importance
        result['bottlenecks'].sort(key=lambda x: item_weights.get(x['item_uid'], 0.0), reverse=True)
        result['next_milestones'].sort(key=lambda x: x['completion_gap'])
        
        return result
