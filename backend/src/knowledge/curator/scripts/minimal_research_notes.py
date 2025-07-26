#!/usr/bin/env python3

"""
Minimal ResearchNote creation with explicit empty lists for problematic fields.
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

def create_minimal_research_notes():
    """Create ResearchNotes with minimal fields and explicit empty lists."""
    
    research_note_1_data = {
        "title": "React Component Best Practices",
        "description": "Research findings on React component design patterns and best practices.",
        "id": "react-component-best-practices",
        
        # REQUIRED: content as RichText format
        "content": {
            "content-type": "text/html",
            "data": "<h2>React Component Best Practices</h2><p>This research examines effective patterns for React component architecture.</p>"
        },
        
        # REQUIRED: Annotation fields
        "annotated_knowledge_items": [KI_UIDS["component-architecture"], KI_UIDS["jsx-syntax"]],
        "annotation_type": "insight",
        "annotation_scope": "whole_item", 
        "evidence_type": "empirical",
        "confidence_level": "high",
        
        # EXPLICITLY set problematic Object fields to empty lists
        "key_insights": [],
        "authors": [],
        "builds_upon": [],
        "contradicts": [],
        "replication_studies": [],
        
        # Simple optional fields
        "tags": ["react", "components"],
        "suggests_knowledge_item_updates": False,
        "peer_reviewed": False,
    }
    
    research_note_2_data = {
        "title": "State Management Performance Analysis", 
        "description": "Comparative analysis of different React state management approaches.",
        "id": "state-management-performance",
        
        # REQUIRED: content
        "content": {
            "content-type": "text/html",
            "data": "<h2>Performance Study</h2><p>This study benchmarks Redux, Zustand, and React Context.</p>"
        },
        
        # REQUIRED: Annotation fields  
        "annotated_knowledge_items": [KI_UIDS["state-management"], KI_UIDS["react-performance"]],
        "annotation_type": "critique",
        "annotation_scope": "specific_section",
        "evidence_type": "experimental", 
        "confidence_level": "medium",
        
        # EXPLICITLY set problematic Object fields to empty lists
        "key_insights": [],
        "authors": [],
        "builds_upon": [],
        "contradicts": [],
        "replication_studies": [],
        
        # Simple optional fields
        "tags": ["react", "performance"],
        "suggests_knowledge_item_updates": False,
        "peer_reviewed": False,
    }
    
    # Create Research Notes
    create_content_via_api("ResearchNote", research_note_1_data)
    create_content_via_api("ResearchNote", research_note_2_data)

def main():
    """Create minimal ResearchNote demo data."""
    print("🔬 Creating minimal ResearchNote demo data...")
    print()
    
    create_minimal_research_notes()
    print()
    
    print("✅ Minimal ResearchNote creation complete!")

if __name__ == "__main__":
    main() 