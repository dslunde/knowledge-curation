#!/usr/bin/env python3
"""
Demo Data Creation Script for Knowledge Curator
Creates a comprehensive React learning demo scenario with all content types
"""

from AccessControl.SecurityManagement import newSecurityManager
from knowledge.curator.interfaces import IKnowledgeCuratorLayer
from plone import api
from Testing.makerequest import makerequest
from zope.interface import directlyProvidedBy, directlyProvides
from datetime import datetime, date, timedelta
import transaction
import os
import logging

logger = logging.getLogger(__name__)

# Demo scenario: Learning Modern Web Development (React focused)
DEMO_SCENARIO = {
    'title': 'React Development Mastery Learning Path',
    'description': 'Complete learning journey from web fundamentals to advanced React development'
}

# Knowledge Items - Foundation to Advanced
KNOWLEDGE_ITEMS = [
    {
        'id': 'javascript-fundamentals',
        'title': 'JavaScript Fundamentals',
        'description': 'Core JavaScript concepts: variables, functions, objects, and scope',
        'content': '''
        <p>JavaScript is the foundation of modern web development. Essential concepts include:</p>
        <ul>
            <li><strong>Variables:</strong> let, const, var and proper scoping</li>
            <li><strong>Functions:</strong> Function declarations, expressions, and arrow functions</li>
            <li><strong>Objects:</strong> Object literals, destructuring, and prototypes</li>
            <li><strong>Scope:</strong> Block scope, function scope, and closures</li>
            <li><strong>Async Programming:</strong> Promises, async/await, and event loop</li>
        </ul>
        <p>These fundamentals enable understanding of modern JavaScript frameworks like React.</p>
        ''',
        'knowledge_type': 'factual',
        'atomic_concepts': ['variables', 'functions', 'scope', 'promises', 'objects'],
        'difficulty_level': 'beginner',
        'mastery_threshold': 0.8,
        'tags': ['javascript', 'programming', 'fundamentals']
    },
    {
        'id': 'html-css-basics',
        'title': 'HTML/CSS Basics',
        'description': 'Structural markup and styling fundamentals for web development',
        'content': '''
        <p>HTML and CSS provide the structure and presentation layer of web applications:</p>
        <ul>
            <li><strong>HTML Structure:</strong> Semantic elements, forms, and accessibility</li>
            <li><strong>CSS Styling:</strong> Selectors, box model, and layout techniques</li>
            <li><strong>Responsive Design:</strong> Media queries and flexible layouts</li>
            <li><strong>Modern CSS:</strong> Flexbox, Grid, and CSS variables</li>
        </ul>
        <p>Essential foundation for creating React component interfaces.</p>
        ''',
        'knowledge_type': 'factual',
        'atomic_concepts': ['semantic-html', 'css-selectors', 'box-model', 'responsive-design'],
        'difficulty_level': 'beginner',
        'mastery_threshold': 0.75,
        'tags': ['html', 'css', 'web-design', 'frontend']
    },
    {
        'id': 'component-concepts',
        'title': 'Component Architecture Concepts',
        'description': 'Understanding modular UI design and component-based thinking',
        'content': '''
        <p>Component-based architecture enables scalable and maintainable user interfaces:</p>
        <ul>
            <li><strong>Encapsulation:</strong> Self-contained UI logic and styling</li>
            <li><strong>Reusability:</strong> Components as building blocks</li>
            <li><strong>Composition:</strong> Combining simple components into complex UIs</li>
            <li><strong>Interfaces:</strong> Props as component APIs</li>
            <li><strong>Separation of Concerns:</strong> Presentation vs. logic separation</li>
        </ul>
        <p>This mental model is crucial for effective React development.</p>
        ''',
        'knowledge_type': 'conceptual',
        'atomic_concepts': ['encapsulation', 'reusability', 'composition', 'interfaces'],
        'difficulty_level': 'intermediate',
        'mastery_threshold': 0.75,
        'tags': ['architecture', 'components', 'design-patterns']
    },
    {
        'id': 'jsx-syntax',
        'title': 'JSX Syntax',
        'description': 'JavaScript XML syntax for describing UI components in React',
        'content': '''
        <p>JSX enables writing HTML-like syntax within JavaScript for React components:</p>
        <ul>
            <li><strong>Syntax Basics:</strong> Elements, attributes, and expressions</li>
            <li><strong>JavaScript Integration:</strong> Embedding expressions with {}</li>
            <li><strong>Component References:</strong> Using custom components</li>
            <li><strong>Conditional Rendering:</strong> Dynamic UI based on state</li>
            <li><strong>Lists and Keys:</strong> Rendering collections efficiently</li>
        </ul>
        <p>JSX is transpiled to JavaScript function calls by tools like Babel.</p>
        ''',
        'knowledge_type': 'procedural',
        'atomic_concepts': ['jsx-elements', 'expressions', 'conditional-rendering', 'lists'],
        'difficulty_level': 'intermediate',
        'mastery_threshold': 0.8,
        'tags': ['react', 'jsx', 'syntax', 'babel']
    },
    {
        'id': 'props-data-flow',
        'title': 'Props and Data Flow',
        'description': 'Understanding component communication through props in React',
        'content': '''
        <p>Props enable data flow and communication between React components:</p>
        <ul>
            <li><strong>Prop Passing:</strong> Parent to child communication</li>
            <li><strong>Data Types:</strong> Primitives, objects, and functions as props</li>
            <li><strong>Destructuring:</strong> Clean prop extraction patterns</li>
            <li><strong>Default Props:</strong> Fallback values for components</li>
            <li><strong>Prop Drilling:</strong> Challenges and solutions</li>
        </ul>
        <p>Props create unidirectional data flow that makes React applications predictable.</p>
        ''',
        'knowledge_type': 'procedural',
        'atomic_concepts': ['prop-passing', 'destructuring', 'data-flow', 'component-api'],
        'difficulty_level': 'intermediate',
        'mastery_threshold': 0.8,
        'tags': ['react', 'props', 'data-flow', 'components']
    },
    {
        'id': 'state-management',
        'title': 'State Management',
        'description': 'Managing component state and understanding state updates in React',
        'content': '''
        <p>State management enables dynamic and interactive React applications:</p>
        <ul>
            <li><strong>Local State:</strong> Component-specific state with useState</li>
            <li><strong>State Updates:</strong> Immutable updates and batching</li>
            <li><strong>State Lifting:</strong> Moving state to common ancestors</li>
            <li><strong>State Structure:</strong> Normalizing and organizing state</li>
            <li><strong>State vs Props:</strong> Understanding the distinction</li>
        </ul>
        <p>Proper state management is crucial for building robust React applications.</p>
        ''',
        'knowledge_type': 'procedural',
        'atomic_concepts': ['useState', 'state-updates', 'state-lifting', 'immutability'],
        'difficulty_level': 'intermediate',
        'mastery_threshold': 0.85,
        'tags': ['react', 'state', 'useState', 'component-state']
    },
    {
        'id': 'react-hooks',
        'title': 'React Hooks',
        'description': 'Modern React state management and lifecycle handling with hooks',
        'content': '''
        <p>Hooks revolutionized React by enabling state and lifecycle in functional components:</p>
        <ul>
            <li><strong>useState:</strong> Managing local component state</li>
            <li><strong>useEffect:</strong> Side effects and lifecycle management</li>
            <li><strong>useContext:</strong> Consuming context for shared state</li>
            <li><strong>Custom Hooks:</strong> Reusable stateful logic</li>
            <li><strong>Rules of Hooks:</strong> Consistency and predictability rules</li>
        </ul>
        <p>Hooks provide a more functional approach to React development.</p>
        ''',
        'knowledge_type': 'procedural',
        'atomic_concepts': ['useState', 'useEffect', 'useContext', 'custom-hooks', 'hook-rules'],
        'difficulty_level': 'advanced',
        'mastery_threshold': 0.85,
        'tags': ['react', 'hooks', 'useState', 'useEffect', 'functional-components']
    },
    {
        'id': 'event-handling',
        'title': 'Event Handling',
        'description': 'Managing user interactions and events in React applications',
        'content': '''
        <p>Event handling enables interactive React applications:</p>
        <ul>
            <li><strong>Event Handlers:</strong> onClick, onChange, onSubmit patterns</li>
            <li><strong>Event Objects:</strong> SyntheticEvent and native events</li>
            <li><strong>Event Delegation:</strong> React's event system optimization</li>
            <li><strong>Form Handling:</strong> Controlled vs uncontrolled components</li>
            <li><strong>Performance:</strong> useCallback for event handler optimization</li>
        </ul>
        <p>Efficient event handling is essential for responsive user interfaces.</p>
        ''',
        'knowledge_type': 'procedural',
        'atomic_concepts': ['event-handlers', 'synthetic-events', 'form-handling', 'useCallback'],
        'difficulty_level': 'intermediate',
        'mastery_threshold': 0.8,
        'tags': ['react', 'events', 'forms', 'user-interaction']
    }
]

# Learning Goal with Knowledge Item connections
LEARNING_GOAL = {
    'id': 'react-development-mastery',
    'title': 'React Development Mastery',
    'description': 'Complete learning path from web fundamentals to advanced React development',
    'target_date': date.today() + timedelta(days=90),
    'priority': 'high',
    'starting_knowledge_item': 'javascript-fundamentals',
    'target_knowledge_items': ['react-hooks', 'event-handling', 'state-management'],
    'knowledge_item_connections': [
        {
            'source_item_uid': 'javascript-fundamentals',
            'target_item_uid': 'jsx-syntax',
            'connection_type': 'prerequisite',
            'strength': 0.9,
            'mastery_requirement': 0.8
        },
        {
            'source_item_uid': 'html-css-basics',
            'target_item_uid': 'jsx-syntax',
            'connection_type': 'prerequisite',
            'strength': 0.7,
            'mastery_requirement': 0.75
        },
        {
            'source_item_uid': 'component-concepts',
            'target_item_uid': 'props-data-flow',
            'connection_type': 'builds_on',
            'strength': 0.85,
            'mastery_requirement': 0.75
        },
        {
            'source_item_uid': 'jsx-syntax',
            'target_item_uid': 'props-data-flow',
            'connection_type': 'prerequisite',
            'strength': 0.8,
            'mastery_requirement': 0.8
        },
        {
            'source_item_uid': 'props-data-flow',
            'target_item_uid': 'state-management',
            'connection_type': 'prerequisite',
            'strength': 0.9,
            'mastery_requirement': 0.8
        },
        {
            'source_item_uid': 'state-management',
            'target_item_uid': 'react-hooks',
            'connection_type': 'prerequisite',
            'strength': 0.95,
            'mastery_requirement': 0.85
        },
        {
            'source_item_uid': 'props-data-flow',
            'target_item_uid': 'event-handling',
            'connection_type': 'prerequisite',
            'strength': 0.8,
            'mastery_requirement': 0.8
        }
    ]
}

# Project Log tracking Learning Goal progress
PROJECT_LOG = {
    'id': 'portfolio-website-project',
    'title': 'Personal Portfolio Website Project',
    'description': 'Building a React-based portfolio website to demonstrate and apply learned concepts',
    'start_date': date.today() - timedelta(days=14),
    'status': 'in_progress',
    'attached_learning_goal': 'react-development-mastery',
    'entries': [
        {
            'entry_id': 'entry-1',
            'timestamp': datetime.now() - timedelta(days=14),
            'entry_type': 'milestone',
            'content': 'Project started: Set up development environment and initial React app',
            'mood': 'excited',
            'progress_notes': 'Successfully created initial React app with create-react-app',
            'time_spent': 2.0,
            'energy_level': 'high'
        },
        {
            'entry_id': 'entry-2',
            'timestamp': datetime.now() - timedelta(days=10),
            'entry_type': 'learning',
            'content': 'Deep dive into JavaScript fundamentals review',
            'mood': 'focused',
            'progress_notes': 'Reviewed closures, promises, and async/await patterns',
            'time_spent': 3.5,
            'energy_level': 'medium'
        },
        {
            'entry_id': 'entry-3',
            'timestamp': datetime.now() - timedelta(days=7),
            'entry_type': 'challenge',
            'content': 'Struggled with JSX syntax and component structure',
            'mood': 'frustrated',
            'progress_notes': 'JSX felt confusing at first, but starting to understand the mental model',
            'time_spent': 2.5,
            'energy_level': 'low'
        },
        {
            'entry_id': 'entry-4',
            'timestamp': datetime.now() - timedelta(days=3),
            'entry_type': 'breakthrough',
            'content': 'Props and component communication clicked!',
            'mood': 'accomplished',
            'progress_notes': 'Created reusable header and footer components with props',
            'time_spent': 4.0,
            'energy_level': 'high'
        }
    ],
    'deliverables': [
        {
            'deliverable_id': 'deliverable-1',
            'title': 'Basic Portfolio Layout',
            'description': 'Header, main content area, and footer components',
            'status': 'completed',
            'due_date': date.today() - timedelta(days=5)
        },
        {
            'deliverable_id': 'deliverable-2',
            'title': 'Interactive Portfolio Features',
            'description': 'Contact form and project showcase with state management',
            'status': 'in_progress',
            'due_date': date.today() + timedelta(days=14)
        }
    ]
}

# Research Notes annotating Knowledge Items
RESEARCH_NOTES = [
    {
        'id': 'react-best-practices-research',
        'title': 'React Component Best Practices Research',
        'description': 'Compilation of current React best practices from official docs and community',
        'content': '''
        <p>Key insights from React documentation and community best practices:</p>
        <ul>
            <li><strong>Functional Components:</strong> Prefer functional components over class components for new development</li>
            <li><strong>Props Destructuring:</strong> Use destructuring for props to improve readability and catch errors early</li>
            <li><strong>Single Responsibility:</strong> Each component should have a single, well-defined purpose</li>
            <li><strong>Performance:</strong> Use React.memo for expensive components, but measure first</li>
            <li><strong>Composition:</strong> Favor component composition over inheritance patterns</li>
        </ul>
        <p>These patterns lead to more maintainable and performant React applications.</p>
        ''',
        'tags': ['best-practices', 'react', 'performance'],
        'research_method': 'Documentation analysis and community research',
        'citation_format': 'APA',
        'annotated_knowledge_items': ['component-concepts', 'props-data-flow'],
        'annotation_type': 'insight',
        'annotation_scope': 'entire_item',
        'evidence_type': 'theoretical',
        'confidence_level': 'high',
        'suggests_knowledge_item_updates': True,
        'proposed_updates': 'Add section on React.memo and component composition patterns'
    },
    {
        'id': 'hooks-dependency-confusion',
        'title': 'useEffect Dependencies Confusion',
        'description': 'Personal research note on useEffect dependency array challenges',
        'content': '''
        <p>Encountered confusion with useEffect dependency arrays during portfolio development:</p>
        <ul>
            <li><strong>Object Dependencies:</strong> When should objects be included in dependency arrays?</li>
            <li><strong>Change Detection:</strong> How does React determine if dependencies have changed?</li>
            <li><strong>Performance Impact:</strong> What happens with incorrect dependencies?</li>
            <li><strong>Solutions:</strong> useCallback and useMemo patterns for optimization</li>
        </ul>
        <p>Need to research official React documentation on dependency array best practices.</p>
        ''',
        'tags': ['hooks', 'useEffect', 'dependencies', 'performance'],
        'research_method': 'Experiential learning and problem-solving',
        'citation_format': 'APA',
        'annotated_knowledge_items': ['react-hooks'],
        'annotation_type': 'question',
        'annotation_scope': 'specific_concept',
        'evidence_type': 'experiential',
        'confidence_level': 'low',
        'suggests_knowledge_item_updates': True,
        'proposed_updates': 'Add detailed section on dependency array best practices and common pitfalls'
    }
]

# Bookmark+ resources connected to Knowledge Items
BOOKMARKS = [
    {
        'id': 'react-docs-hooks',
        'title': 'React Official Documentation - Hooks',
        'url': 'https://react.dev/reference/react',
        'notes': 'Comprehensive reference for React Hooks with practical examples. Start with useState and useEffect sections.',
        'importance': 'high',
        'related_knowledge_items': ['react-hooks', 'state-management'],
        'resource_type': 'documentation',
        'content_quality': 'excellent',
        'reading_time_estimate': 45,
        'read_status': 'partially_read',
        'personal_notes': 'Excellent examples, particularly the useEffect section with cleanup patterns',
        'key_quotes': [
            'Hooks let you use state and other React features without writing a class.',
            'Only call Hooks at the top level of your React function.'
        ]
    },
    {
        'id': 'react-performance-guide',
        'title': 'React Performance Best Practices - Web.dev',
        'url': 'https://web.dev/react-performance-optimization/',
        'notes': 'Comprehensive guide on optimizing React application performance with practical examples.',
        'importance': 'medium',
        'related_knowledge_items': ['component-concepts', 'react-hooks'],
        'resource_type': 'article',
        'content_quality': 'high',
        'reading_time_estimate': 25,
        'read_status': 'unread',
        'personal_notes': 'Referenced in React best practices research note',
        'key_quotes': []
    },
    {
        'id': 'component-patterns-guide',
        'title': 'React Component Patterns Guide',
        'url': 'https://kentcdodds.com/blog/react-component-patterns',
        'notes': 'Kent C. Dodds comprehensive guide to React component patterns and composition.',
        'importance': 'high',
        'related_knowledge_items': ['component-concepts', 'props-data-flow'],
        'resource_type': 'article',
        'content_quality': 'excellent',
        'reading_time_estimate': 35,
        'read_status': 'read',
        'personal_notes': 'Excellent breakdown of compound components and render props patterns',
        'key_quotes': [
            'The secret to building maintainable large React applications is to stop building large applications.',
            'Composition gives you more flexibility than inheritance.'
        ]
    }
]


def setup_demo_environment():
    """Set up the request environment for demo data creation"""
    app = makerequest(globals()["app"])
    request = app.REQUEST

    # Add Knowledge Curator layer
    ifaces = [IKnowledgeCuratorLayer]
    for iface in directlyProvidedBy(request):
        ifaces.append(iface)
    directlyProvides(request, *ifaces)

    # Set up admin user
    admin = app.acl_users.getUserById("admin")
    admin = admin.__of__(app.acl_users)
    newSecurityManager(None, admin)

    return app


def create_knowledge_items(portal):
    """Create demo Knowledge Items"""
    print("Creating Knowledge Items...")
    created_items = {}
    
    for item_data in KNOWLEDGE_ITEMS:
        try:
            knowledge_item = api.content.create(
                container=portal,
                type='KnowledgeItem',
                id=item_data['id'],
                title=item_data['title'],
                description=item_data['description'],
                content=item_data['content'],
                knowledge_type=item_data['knowledge_type'],
                atomic_concepts=item_data['atomic_concepts'],
                difficulty_level=item_data['difficulty_level'],
                mastery_threshold=item_data['mastery_threshold'],
                tags=item_data['tags']
            )
            
            # Set workflow state
            api.content.transition(obj=knowledge_item, transition='capture_to_process')
            
            created_items[item_data['id']] = knowledge_item
            print(f"  ✓ Created Knowledge Item: {item_data['title']}")
            
        except Exception as e:
            print(f"  ✗ Failed to create Knowledge Item {item_data['title']}: {e}")
    
    return created_items


def create_learning_goal(portal, knowledge_items):
    """Create demo Learning Goal with Knowledge Item connections"""
    print("Creating Learning Goal...")
    
    try:
        learning_goal = api.content.create(
            container=portal,
            type='LearningGoal',
            id=LEARNING_GOAL['id'],
            title=LEARNING_GOAL['title'],
            description=LEARNING_GOAL['description'],
            target_date=LEARNING_GOAL['target_date'],
            priority=LEARNING_GOAL['priority'],
            starting_knowledge_item=LEARNING_GOAL['starting_knowledge_item'],
            target_knowledge_items=LEARNING_GOAL['target_knowledge_items'],
            knowledge_item_connections=LEARNING_GOAL['knowledge_item_connections']
        )
        
        print(f"  ✓ Created Learning Goal: {LEARNING_GOAL['title']}")
        return learning_goal
        
    except Exception as e:
        print(f"  ✗ Failed to create Learning Goal: {e}")
        return None


def create_project_log(portal, learning_goal):
    """Create demo Project Log attached to Learning Goal"""
    print("Creating Project Log...")
    
    try:
        project_log = api.content.create(
            container=portal,
            type='ProjectLog',
            id=PROJECT_LOG['id'],
            title=PROJECT_LOG['title'],
            description=PROJECT_LOG['description'],
            start_date=PROJECT_LOG['start_date'],
            status=PROJECT_LOG['status'],
            entries=PROJECT_LOG['entries'],
            deliverables=PROJECT_LOG['deliverables']
        )
        
        print(f"  ✓ Created Project Log: {PROJECT_LOG['title']}")
        return project_log
        
    except Exception as e:
        print(f"  ✗ Failed to create Project Log: {e}")
        return None


def create_research_notes(portal, knowledge_items):
    """Create demo Research Notes annotating Knowledge Items"""
    print("Creating Research Notes...")
    created_notes = {}
    
    for note_data in RESEARCH_NOTES:
        try:
            research_note = api.content.create(
                container=portal,
                type='ResearchNote',
                id=note_data['id'],
                title=note_data['title'],
                description=note_data['description'],
                content=note_data['content'],
                tags=note_data['tags'],
                research_method=note_data['research_method'],
                citation_format=note_data['citation_format']
            )
            
            created_notes[note_data['id']] = research_note
            print(f"  ✓ Created Research Note: {note_data['title']}")
            
        except Exception as e:
            print(f"  ✗ Failed to create Research Note {note_data['title']}: {e}")
    
    return created_notes


def create_bookmarks(portal, knowledge_items):
    """Create demo Bookmark+ items connected to Knowledge Items"""
    print("Creating Bookmark+ items...")
    created_bookmarks = {}
    
    for bookmark_data in BOOKMARKS:
        try:
            # Convert knowledge item IDs to UIDs
            related_uids = []
            for item_id in bookmark_data['related_knowledge_items']:
                if item_id in knowledge_items:
                    related_uids.append(knowledge_items[item_id].UID())
            
            bookmark = api.content.create(
                container=portal,
                type='BookmarkPlus',
                id=bookmark_data['id'],
                title=bookmark_data['title'],
                url=bookmark_data['url'],
                notes=bookmark_data['notes'],
                importance=bookmark_data['importance'],
                related_knowledge_items=related_uids,
                resource_type=bookmark_data['resource_type']
            )
            
            created_bookmarks[bookmark_data['id']] = bookmark
            print(f"  ✓ Created Bookmark+: {bookmark_data['title']}")
            
        except Exception as e:
            print(f"  ✗ Failed to create Bookmark+ {bookmark_data['title']}: {e}")
    
    return created_bookmarks


def create_demo_data():
    """Main function to create all demo data"""
    print("=== CREATING DEMO DATA ===")
    
    try:
        app = setup_demo_environment()
        portal = app.Plone
        
        # Create content in logical order
        knowledge_items = create_knowledge_items(portal)
        learning_goal = create_learning_goal(portal, knowledge_items)
        project_log = create_project_log(portal, learning_goal)
        research_notes = create_research_notes(portal, knowledge_items)
        bookmarks = create_bookmarks(portal, knowledge_items)
        
        # Initialize and populate vector database
        print("\n=== INITIALIZING VECTOR DATABASE ===")
        try:
            from knowledge.curator.vector.management import VectorCollectionManager
            
            # Initialize the vector database collection
            manager = VectorCollectionManager()
            print("Initializing vector database collection...")
            success = manager.initialize_database()
            
            if success:
                print("✅ Vector database collection initialized")
                
                # Rebuild the index with all created content
                print("Building vector index from demo content...")
                result = manager.rebuild_index(
                    content_types=["KnowledgeItem", "BookmarkPlus", "ResearchNote", "LearningGoal", "ProjectLog"],
                    clear_first=True
                )
                
                if result.get("success"):
                    print(f"✅ Vector index built successfully - {result['processed']} items indexed")
                else:
                    print(f"⚠️ Vector index build failed: {result.get('error', 'Unknown error')}")
            else:
                print("⚠️ Vector database initialization failed")
                
        except Exception as e:
            print(f"❌ Vector database setup error: {e}")
            print("Demo data will be created without vector search capabilities")
        
        # Commit the transaction
        transaction.commit()
        
        print("\n=== DEMO DATA CREATION COMPLETED ===")
        print(f"Created {len(knowledge_items)} Knowledge Items")
        print(f"Created 1 Learning Goal")
        print(f"Created 1 Project Log")
        print(f"Created {len(research_notes)} Research Notes")
        print(f"Created {len(bookmarks)} Bookmark+ items")
        print("\nDemo scenario: React Development Mastery Learning Path")
        print("Access via: http://knowledge-curator.localhost/")
        
    except Exception as e:
        print(f"ERROR creating demo data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    create_demo_data() 