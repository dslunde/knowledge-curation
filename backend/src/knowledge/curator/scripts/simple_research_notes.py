#!/usr/bin/env python3

"""
Simplified ResearchNote creation focusing on required fields only.
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

def create_simple_research_notes():
    """Create ResearchNotes with only required fields and simple optional fields."""
    
    research_note_1_data = {
        "title": "React Component Best Practices",
        "description": "Research findings on React component design patterns and best practices.",
        "id": "react-component-best-practices",
        
        # REQUIRED: content as RichText format
        "content": {
            "content-type": "text/html",
            "data": "<h2>React Component Best Practices</h2><p>This research examines effective patterns for React component architecture, focusing on maintainability, reusability, and performance.</p><h3>Key Findings</h3><ul><li>Composition over inheritance leads to more flexible component hierarchies</li><li>Single responsibility principle reduces complexity and improves testability</li><li>Proper state management prevents common rendering issues</li></ul>"
        },
        
        # REQUIRED: Annotation fields
        "annotated_knowledge_items": [KI_UIDS["component-architecture"], KI_UIDS["jsx-syntax"]],
        "annotation_type": "insight",
        "annotation_scope": "whole_item", 
        "evidence_type": "empirical",
        "confidence_level": "high",
        
        # Optional simple fields only
        "tags": ["react", "components", "best-practices", "architecture"],
        "research_question": "What are the most effective patterns for React component architecture?",
        "research_method": "Literature review and analysis of popular React projects",
        "suggests_knowledge_item_updates": True,
        "peer_reviewed": False,
        
        # Skip complex Object fields for now:
        # - key_insights (List of Objects)
        # - authors (List of Objects) 
        # - builds_upon, contradicts, replication_studies (keep as empty lists)
        "builds_upon": [],
        "contradicts": [],
        "replication_studies": [],
    }
    
    research_note_2_data = {
        "title": "State Management Performance Analysis", 
        "description": "Comparative analysis of different React state management approaches.",
        "id": "state-management-performance",
        
        # REQUIRED: content
        "content": {
            "content-type": "text/html",
            "data": "<h2>Performance Comparison Study</h2><p>This study benchmarks Redux, Zustand, and React Context across various application sizes.</p><h3>Key Results</h3><p>Zustand showed 15% better performance in large applications compared to Redux. React Context becomes a bottleneck in applications with more than 50 components.</p><h3>Limitations</h3><p>Testing was limited to specific use cases and may not generalize to all application types.</p>"
        },
        
        # REQUIRED: Annotation fields  
        "annotated_knowledge_items": [KI_UIDS["state-management"], KI_UIDS["react-performance"]],
        "annotation_type": "critique",
        "annotation_scope": "specific_section",
        "evidence_type": "experimental", 
        "confidence_level": "medium",
        
        # Optional simple fields
        "tags": ["react", "state-management", "performance", "analysis"],
        "research_question": "How do different state management solutions impact React application performance?",
        "research_method": "Benchmarking Redux, Zustand, and React Context across various application sizes",
        "suggests_knowledge_item_updates": False,
        "peer_reviewed": False,
        
        # Empty lists for complex relationships
        "builds_upon": [],
        "contradicts": [],
        "replication_studies": [],
    }
    
    # Create Research Notes
    create_content_via_api("ResearchNote", research_note_1_data)
    create_content_via_api("ResearchNote", research_note_2_data)

def main():
    """Create simplified ResearchNote demo data."""
    print("🔬 Creating simplified ResearchNote demo data...")
    print()
    
    create_simple_research_notes()
    print()
    
    print("✅ Simplified ResearchNote creation complete!")

if __name__ == "__main__":
    main() 