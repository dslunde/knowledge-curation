#!/usr/bin/env python3
"""
Create demo data for Knowledge Curator via REST API calls.
This script can run while the Plone server is active, using API calls instead of direct database manipulation.
"""

import requests
import json
import time
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:8080/Plone"
AUTH = ("admin", "admin")

def create_content_via_api(content_type, data):
    """Create content via REST API"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    url = f"{BASE_URL}/++api++/"
    
    payload = {
        "@type": content_type,
        **data
    }
    
    try:
        response = requests.post(url, 
                               json=payload, 
                               headers=headers, 
                               auth=AUTH,
                               timeout=30)
        
        if response.status_code in [200, 201]:
            print(f"  ✓ Created {content_type}: {data.get('title', data.get('id', 'Unknown'))}")
            return response.json()
        else:
            print(f"  ✗ Failed to create {content_type}: {response.status_code}")
            print(f"    Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"  ✗ Error creating {content_type}: {e}")
        return None

def check_existing_content():
    """Check what content already exists"""
    try:
        headers = {"Accept": "application/json"}
        
        # Check different content types
        content_types = ["KnowledgeItem", "LearningGoal", "ProjectLog", "ResearchNote", "BookmarkPlus"]
        existing = {}
        
        for content_type in content_types:
            url = f"{BASE_URL}/++api++/@search?portal_type={content_type}"
            response = requests.get(url, headers=headers, auth=AUTH, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                existing[content_type] = [item["title"] for item in data.get("items", [])]
                print(f"Found {len(existing[content_type])} existing {content_type}(s)")
            
        return existing
        
    except Exception as e:
        print(f"Error checking existing content: {e}")
        return {}

def create_react_learning_demo():
    """Create comprehensive React learning demo with all content types"""
    
    print("=== CREATING REACT LEARNING DEMO DATA ===")
    
    # Check existing content
    existing = check_existing_content()
    created_items = {}
    
    # 1. Create Knowledge Items (8 items for React learning path)
    knowledge_items_data = [
        {
            "id": "javascript-fundamentals",
            "title": "JavaScript Fundamentals",
            "description": "Core JavaScript concepts, syntax, and programming patterns essential for React development",
            "content": {
                "content-type": "text/html",
                "data": """<p>JavaScript fundamentals form the foundation for React development:</p>
                <ul>
                    <li><strong>Variables & Scope:</strong> Understanding let, const, var and their scoping rules</li>
                    <li><strong>Functions:</strong> Function declarations, expressions, arrow functions, and closures</li>
                    <li><strong>Objects & Arrays:</strong> Working with complex data structures and destructuring</li>
                    <li><strong>Async Programming:</strong> Promises, async/await, and handling asynchronous operations</li>
                    <li><strong>ES6+ Features:</strong> Template literals, spread operator, modules, and modern syntax</li>
                </ul>
                <p>Mastering these concepts ensures smooth transition to React development patterns.</p>"""
            },
            "knowledge_type": "foundational",
            "difficulty_level": "beginner",
            "atomic_concepts": ["variables", "functions", "objects", "async-programming", "es6-features"]
        },
        {
            "id": "html-css-basics",
            "title": "HTML/CSS Basics",
            "description": "Essential HTML structure and CSS styling knowledge for building user interfaces",
            "content": {
                "content-type": "text/html",
                "data": """<p>HTML and CSS provide the structural foundation for React applications:</p>
                <ul>
                    <li><strong>Semantic HTML:</strong> Using proper HTML elements for accessibility and SEO</li>
                    <li><strong>CSS Selectors:</strong> Targeting elements with class, ID, and attribute selectors</li>
                    <li><strong>Flexbox & Grid:</strong> Modern layout techniques for responsive designs</li>
                    <li><strong>CSS Box Model:</strong> Understanding margin, padding, border, and content areas</li>
                    <li><strong>Responsive Design:</strong> Media queries and mobile-first approaches</li>
                </ul>
                <p>These skills translate directly to React component styling and layout.</p>"""
            },
            "knowledge_type": "foundational",
            "difficulty_level": "beginner",
            "atomic_concepts": ["semantic-html", "css-selectors", "flexbox", "css-box-model", "responsive-design"]
        },
        {
            "id": "component-architecture",
            "title": "Component Architecture Concepts",
            "description": "Understanding component-based architecture and modular UI development principles",
            "content": {
                "content-type": "text/html",
                "data": """<p>Component architecture forms the backbone of modern React applications:</p>
                <ul>
                    <li><strong>Component Composition:</strong> Building complex UIs from simple, reusable components</li>
                    <li><strong>Single Responsibility:</strong> Each component should have one clear purpose</li>
                    <li><strong>Component Hierarchy:</strong> Organizing parent-child relationships effectively</li>
                    <li><strong>Separation of Concerns:</strong> Dividing logic from presentation</li>
                    <li><strong>Reusability Patterns:</strong> Creating components that work in multiple contexts</li>
                </ul>
                <p>These principles guide effective React application structure and maintainability.</p>"""
            },
            "knowledge_type": "conceptual",
            "difficulty_level": "intermediate",
            "atomic_concepts": ["component-composition", "single-responsibility", "component-hierarchy", "separation-concerns", "reusability"]
        },
        {
            "id": "jsx-syntax",
            "title": "JSX Syntax",
            "description": "JavaScript XML syntax for writing React components with HTML-like syntax in JavaScript",
            "content": {
                "content-type": "text/html",
                "data": """<p>JSX enables intuitive React component development:</p>
                <ul>
                    <li><strong>JSX Elements:</strong> Writing HTML-like syntax within JavaScript code</li>
                    <li><strong>JavaScript Expressions:</strong> Embedding dynamic content with curly braces {}</li>
                    <li><strong>Component Rendering:</strong> Returning JSX from React component functions</li>
                    <li><strong>Attributes & Props:</strong> Passing data through JSX attributes</li>
                    <li><strong>Conditional Rendering:</strong> Using JavaScript logic to show/hide elements</li>
                </ul>
                <p>JSX bridges the gap between JavaScript logic and HTML presentation.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "beginner",
            "atomic_concepts": ["jsx-elements", "javascript-expressions", "component-rendering", "attributes-props", "conditional-rendering"]
        },
        {
            "id": "props-data-flow",
            "title": "Props & Data Flow",
            "description": "Understanding how data flows through React component trees via props",
            "content": {
                "content-type": "text/html",
                "data": """<p>Props enable data flow and component communication in React:</p>
                <ul>
                    <li><strong>Props Basics:</strong> Passing data from parent to child components</li>
                    <li><strong>Prop Types:</strong> Ensuring type safety and catching errors early</li>
                    <li><strong>Default Props:</strong> Providing fallback values for optional props</li>
                    <li><strong>Unidirectional Flow:</strong> Data flows down, events flow up pattern</li>
                    <li><strong>Prop Drilling:</strong> Understanding and avoiding deep prop passing</li>
                </ul>
                <p>Proper data flow patterns create predictable and maintainable React applications.</p>"""
            },
            "knowledge_type": "procedural",
            "difficulty_level": "intermediate",
            "atomic_concepts": ["props-basics", "prop-types", "default-props", "unidirectional-flow", "prop-drilling"]
        },
        {
            "id": "state-management",
            "title": "State Management",
            "description": "Managing component state and creating interactive React applications",
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
    created_knowledge_items = []
    for ki_data in knowledge_items_data:
        if "KnowledgeItem" not in existing or ki_data["title"] not in existing.get("KnowledgeItem", []):
            result = create_content_via_api("KnowledgeItem", ki_data)
            if result:
                created_knowledge_items.append(result)
                created_items[ki_data["id"]] = result["@id"]
    
    # 2. Create Learning Goal with proper structured data
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
        "estimated_duration": "12 weeks",
        "priority": "high",
        "target_date": (date.today() + timedelta(days=90)).isoformat(),
        # Add properly structured fields to match schema
        "milestones": [],  # Will be populated later via API
        "learning_objectives": [],  # Will be populated later via API  
        "assessment_criteria": [],  # Will be populated later via API
        "competencies": [],  # Will be populated later via API
        "prerequisite_knowledge": [
            "Basic programming concepts",
            "HTML/CSS fundamentals", 
            "JavaScript ES6+ syntax"
        ]
    }
    
    print("\n🎯 Creating Learning Goal...")
    if "LearningGoal" not in existing or learning_goal_data["title"] not in existing.get("LearningGoal", []):
        result = create_content_via_api("LearningGoal", learning_goal_data)
        if result:
            created_items["learning_goal"] = result["@id"]
            
    # 3. Create Project Log with proper structured data
    project_log_data = {
        "id": "portfolio-website-project",
        "title": "Personal Portfolio Website Project", 
        "description": "Building a React-based portfolio website to demonstrate and apply learned concepts",
        "content": {
            "content-type": "text/html",
            "data": """<p>This project applies React development skills in a practical context:</p>
            <ul>
                <li><strong>Goal:</strong> Create a professional portfolio showcasing React skills</li>
                <li><strong>Timeline:</strong> 8-week development cycle</li>
                <li><strong>Features:</strong> Responsive design, dynamic content, performance optimization</li>
            </ul>"""
        },
        "start_date": (date.today() - timedelta(days=14)).isoformat(),
        "status": "active",  # Valid status from vocabulary
        "attached_learning_goal": "react-development-mastery",  # Required field
        # Add structured fields to match schema
        "entries": [],  # Will be populated later via API
        "deliverables": [],  # Will be populated later via API
        "stakeholders": [],  # Will be populated later via API
        "resources_used": [],  # Will be populated later via API
        "success_metrics": [],  # Will be populated later via API
        "lessons_learned": []  # Will be populated later via API
    }
    
    print("\n📋 Creating Project Log...")
    if "ProjectLog" not in existing or project_log_data["title"] not in existing.get("ProjectLog", []):
        result = create_content_via_api("ProjectLog", project_log_data)
        if result:
            created_items["project_log"] = result["@id"]
    
    # 4. Create Research Notes with required fields
    research_notes_data = [
        {
            "id": "react-hooks-research",
            "title": "React Hooks Best Practices Research",
            "description": "Research findings on effective React Hooks usage patterns and common pitfalls",
            "content": {
                "content-type": "text/html",
                "data": """<p>Research findings on React Hooks effectiveness:</p>
                <ul>
                    <li><strong>Hook Dependencies:</strong> Proper dependency array management prevents infinite loops</li>
                    <li><strong>Custom Hook Patterns:</strong> Extract logic for reusability across components</li>
                    <li><strong>Performance Implications:</strong> useCallback and useMemo should be used judiciously</li>
                </ul>"""
            },
            # Required fields for ResearchNote
            "annotated_knowledge_items": ["react-hooks-advanced"],  # Must reference existing KI
            "annotation_type": "analysis",  # Must be valid vocabulary value
            "annotation_scope": "complete",  # Must be valid vocabulary value
            "evidence_type": "empirical",  # Must be valid vocabulary value
            "confidence_level": "high",  # Must be valid vocabulary value
            # Optional structured fields
            "key_insights": [],
            "builds_upon": [],
            "contradicts": [], 
            "replication_studies": [],
            "authors": []
        },
        {
            "id": "component-architecture-study",
            "title": "Component Architecture Patterns Study",
            "description": "Analysis of effective component organization and architecture patterns",
            "content": {
                "content-type": "text/html", 
                "data": """<p>Study of component architecture effectiveness:</p>
                <ul>
                    <li><strong>Composition over Inheritance:</strong> React favors component composition</li>
                    <li><strong>Container/Presentational:</strong> Separating logic from presentation</li>
                    <li><strong>Atomic Design:</strong> Building systems from small, reusable components</li>
                </ul>"""
            },
            # Required fields for ResearchNote
            "annotated_knowledge_items": ["component-architecture"],
            "annotation_type": "evaluation", 
            "annotation_scope": "partial",
            "evidence_type": "theoretical",
            "confidence_level": "medium",
            # Optional structured fields
            "key_insights": [],
            "builds_upon": [],
            "contradicts": [],
            "replication_studies": [],
            "authors": []
        }
    ]
    
    print("\n🔬 Creating Research Notes...")
    for rn_data in research_notes_data:
        if "ResearchNote" not in existing or rn_data["title"] not in existing.get("ResearchNote", []):
            result = create_content_via_api("ResearchNote", rn_data)
            if result:
                created_items[rn_data["id"]] = result["@id"]
    
    # 5. Create Bookmark+ items with required fields
    bookmarks_data = [
        {
            "id": "react-docs-official",
            "title": "Official React Documentation",
            "url": "https://react.dev/",
            "notes": "Comprehensive official documentation with examples and best practices",
            "importance": "high",
            # Required fields for BookmarkPlus
            "related_knowledge_items": ["jsx-syntax", "state-management"],  # Required, must reference existing KIs
            "resource_type": "documentation",  # Must be valid vocabulary value
            "content_quality": "high",  # Must be valid vocabulary value (low, medium, high)
            "tags": ["react", "documentation", "official"]
        },
        {
            "id": "react-hooks-guide",
            "title": "React Hooks Complete Guide",
            "url": "https://overreacted.io/a-complete-guide-to-useeffect/",
            "notes": "In-depth explanation of useEffect and Hook patterns by Dan Abramov",
            "importance": "high",
            # Required fields for BookmarkPlus  
            "related_knowledge_items": ["react-hooks-advanced"],
            "resource_type": "article",
            "content_quality": "high",
            "tags": ["react", "hooks", "useEffect", "dan-abramov"]
        },
        {
            "id": "react-performance-tips",
            "title": "React Performance Optimization Tips",
            "url": "https://kentcdodds.com/blog/optimize-react-re-renders",
            "notes": "Practical tips for optimizing React application performance",
            "importance": "medium",
            # Required fields for BookmarkPlus
            "related_knowledge_items": ["react-performance"],
            "resource_type": "article", 
            "content_quality": "medium",
            "tags": ["react", "performance", "optimization"]
        }
    ]
    
    print("\n🔖 Creating Bookmark+ items...")
    for bm_data in bookmarks_data:
        if "BookmarkPlus" not in existing or bm_data["title"] not in existing.get("BookmarkPlus", []):
            result = create_content_via_api("BookmarkPlus", bm_data)
            if result:
                created_items[bm_data["id"]] = result["@id"]
    
    print("\n=== DEMO DATA CREATION COMPLETED ===")
    print(f"✅ Successfully created React Development Learning Demo!")
    print(f"📚 Knowledge Items: {len([k for k in created_items.keys() if k.endswith(('-fundamentals', '-basics', '-architecture', '-syntax', '-flow', '-management', '-advanced', '-performance'))])}")
    print(f"🎯 Learning Goals: {1 if 'learning_goal' in created_items else 0}")
    print(f"📋 Project Logs: {1 if 'project_log' in created_items else 0}")
    print(f"🔬 Research Notes: {len([k for k in created_items.keys() if k.endswith(('-research', '-study'))])}")
    print(f"🔖 Bookmark+ items: {len([k for k in created_items.keys() if k.endswith(('-official', '-guide', '-tips'))])}")
    
    return created_items

if __name__ == "__main__":
    try:
        result = create_react_learning_demo()
        print(f"\n🎉 Demo data setup complete!")
        print("🌐 Access your demo via: http://localhost:3000/")
        
    except Exception as e:
        print(f"\n❌ Error during demo data creation: {e}")
        import traceback
        traceback.print_exc() 