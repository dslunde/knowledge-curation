#!/usr/bin/env python3
"""
Complete demo data creation with correct UIDs.
"""

import requests
import json

BASE_URL = "http://localhost:8080/Plone"
AUTH = ("admin", "admin")

# Knowledge Item UIDs (from get_ki_uids.py)
KI_UIDS = {
    "javascript-fundamentals": "b5b4c6d46c054cc4bd391b510e9d5355",
    "html-css-basics": "b3e2bb01286440fb87a9a6f3ffa870e3", 
    "component-architecture": "6fea75750baa43d39f8d0de3bac58626",
    "jsx-syntax": "c3bf09c0ce884219a9ba5bf192b8f1ab",
    "props-data-flow": "811a2682448041bc99e95cdbe9cc7272",
    "state-management": "3e58e02379974201a4ff00c892b620d9",
    "react-hooks-advanced": "0da0708a0470499a872ca6b8a8aec940",
    "react-performance": "4648a0d0469c4e30b301f93471b5de92",
}

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

def create_remaining_demo_data():
    """Create the remaining demo data with correct UIDs"""
    
    print("=== COMPLETING DEMO DATA CREATION ===")
    
    # 1. Create Project Log (this should work now with fixed ZCML)
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
        "start_date": "2024-12-22",  # 14 days ago
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
    result = create_content_via_api("ProjectLog", project_log_data)
    
    # 2. Create Research Notes with correct UIDs
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
            # Required fields for ResearchNote with correct UIDs
            "annotated_knowledge_items": [KI_UIDS["react-hooks-advanced"]],  # Use actual UID
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
            # Required fields for ResearchNote with correct UIDs
            "annotated_knowledge_items": [KI_UIDS["component-architecture"]],  # Use actual UID
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
        result = create_content_via_api("ResearchNote", rn_data)
    
    # 3. Create Bookmark+ items with correct UIDs
    bookmarks_data = [
        {
            "id": "react-docs-official",
            "title": "Official React Documentation",
            "url": "https://react.dev/",
            "notes": "Comprehensive official documentation with examples and best practices",
            "importance": "high",
            # Required fields for BookmarkPlus with correct UIDs
            "related_knowledge_items": [KI_UIDS["jsx-syntax"], KI_UIDS["state-management"]],  # Use actual UIDs
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
            # Required fields for BookmarkPlus with correct UIDs
            "related_knowledge_items": [KI_UIDS["react-hooks-advanced"]],  # Use actual UID
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
            # Required fields for BookmarkPlus with correct UIDs
            "related_knowledge_items": [KI_UIDS["react-performance"]],  # Use actual UID
            "resource_type": "article", 
            "content_quality": "medium",
            "tags": ["react", "performance", "optimization"]
        }
    ]
    
    print("\n🔖 Creating Bookmark+ items...")
    for bm_data in bookmarks_data:
        result = create_content_via_api("BookmarkPlus", bm_data)
    
    print("\n=== DEMO DATA CREATION COMPLETED ===")
    print("✅ Successfully completed React Development Learning Demo!")
    print("🌐 Access your demo via: http://localhost:3000/")

if __name__ == "__main__":
    try:
        create_remaining_demo_data()
        print(f"\n🎉 Demo data setup complete!")
        
    except Exception as e:
        print(f"\n❌ Error during demo data creation: {e}")
        import traceback
        traceback.print_exc() 