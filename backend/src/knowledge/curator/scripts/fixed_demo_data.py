#!/usr/bin/env python3

"""
Fixed demo data creation with correct vocabulary values.
"""

import requests
import json

BASE_URL = "http://localhost:8080/Plone"
AUTH = ("admin", "admin")

# Knowledge Item UIDs
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
        response = requests.post(url, headers=headers, json=payload, auth=AUTH, timeout=30)
        print(f"Creating {content_type}: {response.status_code}")
        
        if response.status_code in (200, 201):
            result = response.json()
            print(f"✅ Created {content_type}: {result.get('title', 'Unknown')}")
            return result
        else:
            print(f"❌ Error creating {content_type}:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception creating {content_type}: {e}")
        return None

def create_research_notes():
    """Create Research Notes with correct vocabulary values."""
    
    research_note_1_data = {
        "title": "React Component Best Practices",
        "description": "Research findings on React component design patterns and best practices.",
        "id": "react-component-best-practices",
        "tags": ["react", "components", "best-practices", "architecture"],
        
        # ResearchNote specific fields with CORRECT vocabulary values
        "research_question": "What are the most effective patterns for React component architecture?",
        "methodology": "Literature review and analysis of popular React projects",
        "key_findings": "Composition over inheritance, single responsibility principle, and proper state management are crucial for maintainable React components.",
        "limitations": "Study focused primarily on function components rather than class components",
        "future_work": "Investigate performance implications of different component patterns",
        
        # Use CORRECT vocabulary values
        "annotation_types_extended": ["insight"],  # Valid: insight, question, critique, extension, example, clarification
        "annotation_scope": "whole_item",  # Valid: whole_item, specific_section, atomic_concept, metadata
        "evidence_types": ["empirical"],  # Valid: empirical, theoretical, anecdotal, experimental, observational, statistical
        "confidence_levels": "high",  # Valid: very_low, low, medium, high, very_high
        
        # Knowledge Item relationships (REQUIRED)
        "annotated_knowledge_items": [KI_UIDS["component-architecture"], KI_UIDS["jsx-syntax"]],
        "related_knowledge_items": [KI_UIDS["javascript-fundamentals"], KI_UIDS["props-data-flow"]],
    }
    
    research_note_2_data = {
        "title": "State Management Performance Analysis",
        "description": "Comparative analysis of different React state management approaches.",
        "id": "state-management-performance",
        "tags": ["react", "state-management", "performance", "analysis"],
        
        "research_question": "How do different state management solutions impact React application performance?",
        "methodology": "Benchmarking Redux, Zustand, and React Context across various application sizes",
        "key_findings": "Zustand showed 15% better performance in large applications compared to Redux",
        "limitations": "Testing was limited to specific use cases and may not generalize",
        "future_work": "Expand testing to include server-side rendering scenarios",
        
        # Use CORRECT vocabulary values
        "annotation_types_extended": ["question", "critique"],
        "annotation_scope": "specific_section",
        "evidence_types": ["experimental", "statistical"],
        "confidence_levels": "medium",
        
        # Knowledge Item relationships (REQUIRED)
        "annotated_knowledge_items": [KI_UIDS["state-management"], KI_UIDS["react-performance"]],
        "related_knowledge_items": [KI_UIDS["react-hooks-advanced"]],
    }
    
    # Create Research Notes
    create_content_via_api("ResearchNote", research_note_1_data)
    create_content_via_api("ResearchNote", research_note_2_data)

def create_bookmark_plus():
    """Create BookmarkPlus items with correct vocabulary values."""
    
    bookmark_1_data = {
        "title": "React Official Documentation",
        "description": "Comprehensive guide to React fundamentals and advanced concepts.",
        "id": "react-docs-bookmark",
        
        # REQUIRED fields with CORRECT vocabulary values
        "url": "https://react.dev/",
        "resource_type": "documentation",  # Valid: article, video, podcast, book, paper, course, documentation, tutorial, presentation, tool, other
        "content_quality": "high",  # Valid: low, medium, high
        "related_knowledge_items": [KI_UIDS["javascript-fundamentals"], KI_UIDS["jsx-syntax"]],  # REQUIRED: min_length=1
        
        # Optional fields with CORRECT vocabulary values
        "read_status": "completed",  # Valid: unread, in_progress, completed, archived
        "importance": "high",  # Using ImportanceVocabulary values
        "notes": "Excellent resource for learning React fundamentals. Very well organized and up-to-date.",
        "reading_time_estimate": 120,
        "tags": ["react", "documentation", "official"],
        "personal_notes": "This is the go-to resource for React development. The examples are clear and the explanations are thorough.",
        "key_quotes": [
            "React is a JavaScript library for building user interfaces.",
            "Components let you split the UI into independent, reusable pieces."
        ],
    }
    
    bookmark_2_data = {
        "title": "Modern React Hooks Tutorial",
        "description": "Comprehensive tutorial on using React Hooks effectively.",
        "id": "react-hooks-tutorial",
        
        # REQUIRED fields
        "url": "https://react.dev/reference/react",
        "resource_type": "tutorial",
        "content_quality": "medium",
        "related_knowledge_items": [KI_UIDS["react-hooks-advanced"], KI_UIDS["state-management"]],
        
        # Optional fields
        "read_status": "in_progress",
        "importance": "medium",
        "notes": "Great tutorial covering useState, useEffect, and custom hooks.",
        "reading_time_estimate": 45,
        "tags": ["react", "hooks", "tutorial"],
        "personal_notes": "Good examples, but could use more advanced patterns.",
    }
    
    bookmark_3_data = {
        "title": "React Performance Optimization Video",
        "description": "Video tutorial on optimizing React application performance.",
        "id": "react-performance-video",
        
        # REQUIRED fields
        "url": "https://example.com/react-performance-video",
        "resource_type": "video",
        "content_quality": "high",
        "related_knowledge_items": [KI_UIDS["react-performance"], KI_UIDS["component-architecture"]],
        
        # Optional fields
        "read_status": "unread",
        "importance": "high",
        "notes": "Recommended by several React developers for performance optimization techniques.",
        "reading_time_estimate": 60,
        "tags": ["react", "performance", "video", "optimization"],
    }
    
    # Create BookmarkPlus items
    create_content_via_api("BookmarkPlus", bookmark_1_data)
    create_content_via_api("BookmarkPlus", bookmark_2_data)
    create_content_via_api("BookmarkPlus", bookmark_3_data)

def main():
    """Create all demo data."""
    print("🔧 Creating ResearchNote and BookmarkPlus demo data...")
    print()
    
    print("📚 Creating Research Notes...")
    create_research_notes()
    print()
    
    print("🔖 Creating BookmarkPlus items...")
    create_bookmark_plus()
    print()
    
    print("✅ Demo data creation complete!")

if __name__ == "__main__":
    main() 