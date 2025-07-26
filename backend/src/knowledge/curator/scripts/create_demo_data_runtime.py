#!/usr/bin/env python3
"""
Runtime Demo Data Creation Script
Creates demo data via API calls while the server is running
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080/Plone"
AUTH = ("admin", "admin")
HEADERS = {"Content-Type": "application/json"}

def create_content_via_api(content_type, data):
    """Create content via REST API"""
    url = f"{BASE_URL}/++api++"
    
    content_data = {
        "@type": content_type,
        **data
    }
    
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=content_data)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Created {content_type}: {data['title']}")
        return result
    else:
        print(f"❌ Failed to create {content_type}: {data['title']}")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def check_existing_content():
    """Check what content already exists"""
    url = f"{BASE_URL}/++api++/@search"
    response = requests.get(url, auth=AUTH)
    
    if response.status_code == 200:
        data = response.json()
        existing = {}
        for item in data['items']:
            content_type = item['@type']
            if content_type not in existing:
                existing[content_type] = []
            existing[content_type].append(item['title'])
        return existing
    return {}

def create_react_learning_demo():
    """Create the complete React learning demo scenario"""
    print("🚀 Creating React Development Mastery Learning Path Demo...")
    
    # Check existing content
    existing = check_existing_content()
    print(f"📊 Existing content: {existing}")
    
    created_items = {}
    
    # 1. Create Knowledge Items (atomic knowledge units)
    knowledge_items = [
        {
            "id": "javascript-fundamentals",
            "title": "JavaScript Fundamentals",
            "description": "Core JavaScript concepts: variables, functions, objects, and scope",
            "content": {
                "content-type": "text/html",
                "data": """<p>JavaScript is the foundation of modern web development. Essential concepts include:</p>
                <ul>
                    <li><strong>Variables:</strong> let, const, var and proper scoping</li>
                    <li><strong>Functions:</strong> Function declarations, expressions, and arrow functions</li>
                    <li><strong>Objects:</strong> Object literals, destructuring, and prototypes</li>
                    <li><strong>Scope:</strong> Block scope, function scope, and closures</li>
                    <li><strong>Async Programming:</strong> Promises, async/await, and event loop</li>
                </ul>
                <p>These fundamentals enable understanding of modern JavaScript frameworks like React.</p>"""
            },
            "knowledge_type": "factual",
            "difficulty_level": "beginner",
            "atomic_concepts": ["variables", "functions", "objects", "scope", "closures", "promises"]
        },
        {
            "id": "html-css-basics",
            "title": "HTML/CSS Basics",
            "description": "Semantic markup and styling fundamentals for web development",
            "content": {
                "content-type": "text/html", 
                "data": """<p>HTML and CSS form the structure and presentation layer of web applications:</p>
                <ul>
                    <li><strong>Semantic HTML:</strong> Using appropriate tags for content meaning</li>
                    <li><strong>CSS Selectors:</strong> Targeting elements for styling</li>
                    <li><strong>Box Model:</strong> Understanding padding, margin, border, content</li>
                    <li><strong>Flexbox & Grid:</strong> Modern layout techniques</li>
                    <li><strong>Responsive Design:</strong> Media queries and mobile-first approaches</li>
                </ul>
                <p>Essential foundation for React component styling and structure.</p>"""
            },
            "knowledge_type": "factual",
            "difficulty_level": "beginner",
            "atomic_concepts": ["semantic-html", "css-selectors", "box-model", "flexbox", "responsive-design"]
        },
        {
            "id": "component-architecture",
            "title": "Component Architecture Concepts",
            "description": "Modular UI design patterns and component-based thinking",
            "content": {
                "content-type": "text/html",
                "data": """<p>Component architecture enables scalable, maintainable UI development:</p>
                <ul>
                    <li><strong>Single Responsibility:</strong> Each component has one clear purpose</li>
                    <li><strong>Composition:</strong> Building complex UIs from simple components</li>
                    <li><strong>Reusability:</strong> Creating components that work in multiple contexts</li>
                    <li><strong>Props Interface:</strong> Clear data flow and configuration</li>
                    <li><strong>State Management:</strong> Where and how to manage component state</li>
                </ul>
                <p>These patterns are fundamental to React's component model.</p>"""
            },
            "knowledge_type": "conceptual",
            "difficulty_level": "intermediate",
            "atomic_concepts": ["single-responsibility", "composition", "reusability", "data-flow"]
        },
        {
            "id": "jsx-syntax",
            "title": "JSX Syntax",
            "description": "JavaScript XML syntax for describing UI elements in React",
            "content": {
                "content-type": "text/html",
                "data": """<p>JSX allows writing HTML-like syntax within JavaScript:</p>
                <ul>
                    <li><strong>Element Creation:</strong> <code>&lt;div&gt;Hello World&lt;/div&gt;</code></li>
                    <li><strong>Expression Embedding:</strong> <code>{variable}</code> and <code>{expression()}</code></li>
                    <li><strong>Attributes:</strong> className, htmlFor, and camelCase properties</li>
                    <li><strong>Event Handlers:</strong> onClick, onChange, onSubmit patterns</li>
                    <li><strong>Conditional Rendering:</strong> {condition && &lt;Element /&gt;}</li>
                </ul>
                <p>JSX compiles to React.createElement calls for efficient virtual DOM creation.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "beginner",
            "atomic_concepts": ["jsx-elements", "expression-embedding", "attributes", "event-handlers"]
        },
        {
            "id": "props-data-flow",
            "title": "Props & Data Flow",
            "description": "Passing data between React components through props",
            "content": {
                "content-type": "text/html",
                "data": """<p>Props enable data flow and component communication in React:</p>
                <ul>
                    <li><strong>Props Passing:</strong> <code>&lt;Child name="value" /&gt;</code></li>
                    <li><strong>Props Destructuring:</strong> <code>function Child({name}) {}</code></li>
                    <li><strong>Default Props:</strong> Setting fallback values</li>
                    <li><strong>Children Prop:</strong> <code>props.children</code> for composition</li>
                    <li><strong>Callback Props:</strong> Passing functions for child-to-parent communication</li>
                </ul>
                <p>Understanding data flow is crucial for React architecture and debugging.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "beginner",
            "atomic_concepts": ["props-passing", "destructuring", "children-prop", "callback-props"]
        },
        {
            "id": "state-management",
            "title": "State Management",
            "description": "Managing component state with useState and useReducer hooks",
            "content": {
                "content-type": "text/html",
                "data": """<p>State management enables interactive React components:</p>
                <ul>
                    <li><strong>useState Hook:</strong> <code>const [value, setValue] = useState(initial)</code></li>
                    <li><strong>State Updates:</strong> Triggering re-renders with state changes</li>
                    <li><strong>Complex State:</strong> useReducer for complex state logic</li>
                    <li><strong>State Lifting:</strong> Moving state up to share between components</li>
                    <li><strong>Local vs Global:</strong> When to use component vs application state</li>
                </ul>
                <p>Proper state management is key to predictable React applications.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "intermediate",
            "atomic_concepts": ["useState", "useReducer", "state-lifting", "local-global-state"]
        },
        {
            "id": "react-hooks-advanced",
            "title": "React Hooks Advanced",
            "description": "useEffect, custom hooks, and advanced Hook patterns",
            "content": {
                "content-type": "text/html",
                "data": """<p>Advanced React Hooks enable sophisticated component behavior:</p>
                <ul>
                    <li><strong>useEffect:</strong> Side effects, cleanup, and dependency arrays</li>
                    <li><strong>Custom Hooks:</strong> Extracting and reusing stateful logic</li>
                    <li><strong>useContext:</strong> Consuming context for global state</li>
                    <li><strong>useMemo/useCallback:</strong> Performance optimization</li>
                    <li><strong>Hook Rules:</strong> Only call at top level, only in React functions</li>
                </ul>
                <p>Mastering hooks unlocks the full power of modern React development.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "advanced",
            "atomic_concepts": ["useEffect", "custom-hooks", "useContext", "useMemo", "hook-rules"]
        },
        {
            "id": "react-performance",
            "title": "React Performance Optimization",
            "description": "Optimizing React applications for production performance",
            "content": {
                "content-type": "text/html",
                "data": """<p>Performance optimization ensures smooth user experiences:</p>
                <ul>
                    <li><strong>React.memo:</strong> Preventing unnecessary component re-renders</li>
                    <li><strong>Code Splitting:</strong> Lazy loading with React.lazy and Suspense</li>
                    <li><strong>Virtual DOM:</strong> Understanding reconciliation and keys</li>
                    <li><strong>Profiling:</strong> Using React DevTools for performance analysis</li>
                    <li><strong>Bundle Optimization:</strong> Tree shaking and build optimization</li>
                </ul>
                <p>Performance optimization is crucial for production React applications.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "advanced",
            "atomic_concepts": ["react-memo", "code-splitting", "virtual-dom", "profiling", "bundle-optimization"]
        }
    ]
    
    # Create Knowledge Items
    print("\n📚 Creating Knowledge Items...")
    for item_data in knowledge_items:
        if "KnowledgeItem" not in existing or item_data["title"] not in existing.get("KnowledgeItem", []):
            result = create_content_via_api("KnowledgeItem", item_data)
            if result:
                created_items[item_data["id"]] = result["@id"]
                time.sleep(1)  # Rate limiting
    
    # 2. Create Learning Goal
    learning_goal_data = {
        "id": "react-development-mastery",
        "title": "React Development Mastery",
        "description": "Complete learning path from web fundamentals to advanced React development",
        "content": {
            "content-type": "text/html",
            "data": """<p>This learning goal guides you through a comprehensive React development journey:</p>
            <ol>
                <li><strong>Foundation:</strong> JavaScript, HTML/CSS fundamentals</li>
                <li><strong>Core React:</strong> Components, JSX, props, and state</li>
                <li><strong>Advanced Patterns:</strong> Hooks, performance, and optimization</li>
            </ol>
            <p>By completing this path, you'll be ready to build production React applications.</p>"""
        },
        "goal_type": "skill_development",
        "complexity_level": "intermediate",
        "estimated_duration": "12 weeks"
    }
    
    print("\n🎯 Creating Learning Goal...")
    if "LearningGoal" not in existing or learning_goal_data["title"] not in existing.get("LearningGoal", []):
        result = create_content_via_api("LearningGoal", learning_goal_data)
        if result:
            created_items["learning_goal"] = result["@id"]
    
    # 3. Create Project Log
    project_log_data = {
        "id": "portfolio-website-project",
        "title": "Portfolio Website Project",
        "description": "Building a personal portfolio website to demonstrate React skills",
        "content": {
            "content-type": "text/html",
            "data": """<p>This project applies React learning through building a real portfolio website:</p>
            <ul>
                <li><strong>Phase 1:</strong> Static components and layout</li>
                <li><strong>Phase 2:</strong> Interactive features and state management</li>
                <li><strong>Phase 3:</strong> Performance optimization and deployment</li>
            </ul>
            <p>The project serves as both learning vehicle and professional showcase.</p>"""
        },
        "project_type": "learning_project",
        "status": "in_progress",
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    }
    
    print("\n📋 Creating Project Log...")
    if "ProjectLog" not in existing or project_log_data["title"] not in existing.get("ProjectLog", []):
        result = create_content_via_api("ProjectLog", project_log_data)
        if result:
            created_items["project_log"] = result["@id"]
    
    # 4. Create Research Notes
    research_notes = [
        {
            "id": "react-best-practices-research",
            "title": "React Best Practices Research",
            "description": "Compilation of React best practices from industry sources",
            "content": {
                "content-type": "text/html",
                "data": """<p>Key findings from React best practices research:</p>
                <ul>
                    <li><strong>Component Design:</strong> Keep components small and focused</li>
                    <li><strong>State Management:</strong> Use local state when possible, global when necessary</li>
                    <li><strong>Performance:</strong> Profile before optimizing, avoid premature optimization</li>
                    <li><strong>Testing:</strong> Test behavior, not implementation details</li>
                    <li><strong>Code Organization:</strong> Feature-based folder structure</li>
                </ul>
                <p>Sources: React docs, Kent C. Dodds, Dan Abramov, React team blog posts.</p>"""
            },
            "research_type": "best_practices",
            "confidence_level": "high"
        },
        {
            "id": "learning-challenges-notes",
            "title": "Learning Challenges & Solutions",
            "description": "Personal notes on React learning challenges and breakthrough moments",
            "content": {
                "content-type": "text/html",
                "data": """<p>Documentation of learning challenges and solutions discovered:</p>
                <ul>
                    <li><strong>State Updates:</strong> Understanding async nature of setState</li>
                    <li><strong>useEffect Dependencies:</strong> Learning to manage dependency arrays</li>
                    <li><strong>Component Re-renders:</strong> Debugging unnecessary re-renders</li>
                    <li><strong>Props vs State:</strong> Deciding when to use each</li>
                    <li><strong>Hook Rules:</strong> Understanding why hooks have rules</li>
                </ul>
                <p>These insights help avoid common pitfalls and accelerate learning.</p>"""
            },
            "research_type": "personal_insights",
            "confidence_level": "medium"
        }
    ]
    
    print("\n📝 Creating Research Notes...")
    for note_data in research_notes:
        if "ResearchNote" not in existing or note_data["title"] not in existing.get("ResearchNote", []):
            result = create_content_via_api("ResearchNote", note_data)
            if result:
                created_items[note_data["id"]] = result["@id"]
                time.sleep(1)
    
    # 5. Create Bookmark+ Resources
    bookmarks = [
        {
            "id": "react-official-docs",
            "title": "React Official Documentation",
            "url": "https://react.dev/",
            "description": "The official React documentation with tutorials and API reference",
            "resource_type": "documentation",
            "content_quality": "excellent",
            "reading_time_estimate": 480
        },
        {
            "id": "javascript-info",
            "title": "JavaScript.info - Modern JavaScript Tutorial",
            "url": "https://javascript.info/",
            "description": "Comprehensive JavaScript tutorial covering modern ES6+ features",
            "resource_type": "tutorial",
            "content_quality": "excellent",
            "reading_time_estimate": 960
        },
        {
            "id": "react-hooks-explained",
            "title": "A Complete Guide to useEffect",
            "url": "https://overreacted.io/a-complete-guide-to-useeffect/",
            "description": "Dan Abramov's deep dive into React useEffect hook",
            "resource_type": "article",
            "content_quality": "excellent",
            "reading_time_estimate": 45
        }
    ]
    
    print("\n🔖 Creating Bookmark+ Resources...")
    for bookmark_data in bookmarks:
        if "BookmarkPlus" not in existing or bookmark_data["title"] not in existing.get("BookmarkPlus", []):
            result = create_content_via_api("BookmarkPlus", bookmark_data)
            if result:
                created_items[bookmark_data["id"]] = result["@id"]
                time.sleep(1)
    
    print(f"\n✅ Demo data creation completed!")
    print(f"📊 Created {len(created_items)} new items")
    return created_items

if __name__ == "__main__":
    try:
        result = create_react_learning_demo()
        print("\n🎉 React Development Mastery Learning Path is ready!")
        print("🌐 Visit: http://localhost:8080/Plone/ClassicUI")
        print("🔧 Login: admin / admin")
        print("📚 Explore the demo content in the site!")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        import traceback
        traceback.print_exc() 