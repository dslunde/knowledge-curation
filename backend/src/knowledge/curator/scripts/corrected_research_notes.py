#!/usr/bin/env python3

"""
Fully corrected ResearchNote creation with proper data structures.
"""

import requests
import json
from datetime import datetime

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
    """Create Research Notes with correct data structures."""
    
    # Current timestamp for key insights
    now = datetime.now().isoformat()
    
    research_note_1_data = {
        "title": "React Component Best Practices",
        "description": "Research findings on React component design patterns and best practices.",
        "id": "react-component-best-practices",
        
        # REQUIRED: content as RichText format
        "content": {
            "content-type": "text/html",
            "data": """
            <h2>Research Overview</h2>
            <p>This research examines the most effective patterns for React component architecture, focusing on maintainability, reusability, and performance.</p>
            
            <h3>Key Findings</h3>
            <ul>
                <li>Composition over inheritance leads to more flexible component hierarchies</li>
                <li>Single responsibility principle reduces complexity and improves testability</li>
                <li>Proper state management prevents common rendering issues</li>
            </ul>
            
            <h3>Best Practices Identified</h3>
            <ol>
                <li><strong>Component Structure:</strong> Keep components small and focused</li>
                <li><strong>Props Design:</strong> Use TypeScript interfaces for clear contracts</li>
                <li><strong>State Management:</strong> Lift state only when necessary</li>
                <li><strong>Performance:</strong> Use React.memo and useMemo judiciously</li>
            </ol>
            
            <h3>Methodology</h3>
            <p>Literature review and analysis of popular React projects including React Router, Material-UI, and Ant Design.</p>
            """
        },
        
        "tags": ["react", "components", "best-practices", "architecture"],
        
        # Optional: Research-specific fields
        "research_question": "What are the most effective patterns for React component architecture?",
        "research_method": "Literature review and analysis of popular React projects",
        
        # Optional: Authors as List of Objects (IAuthor schema)
        "authors": [
            {
                "name": "Knowledge Curator Demo",
                "email": "demo@example.com",
                "orcid": None,
                "affiliation": "Demo Research Institute"
            }
        ],
        
        # Optional: Key insights as List of Objects (IKeyInsight schema)
        "key_insights": [
            {
                "text": "Composition patterns result in 40% fewer coupling issues compared to inheritance-based designs",
                "importance": "high",
                "evidence": "Analysis of 50 React projects showed consistent reduction in modification impact",
                "timestamp": now
            },
            {
                "text": "Single responsibility components have 60% fewer bugs in production",
                "importance": "high", 
                "evidence": "Tracking data from 10 enterprise applications over 6 months",
                "timestamp": now
            }
        ],
        
        # Optional: Research relationships (Lists of UIDs)
        "builds_upon": [],  # Empty list for now
        "contradicts": [],  # Empty list for now
        "replication_studies": [],  # Empty list for now
        
        # REQUIRED: Annotation fields with CORRECT names and values
        "annotated_knowledge_items": [KI_UIDS["component-architecture"], KI_UIDS["jsx-syntax"]],
        "annotation_type": "insight",  # Valid: insight, question, critique, extension, example, clarification
        "annotation_scope": "whole_item",  # Valid: whole_item, specific_section, atomic_concept, metadata
        "evidence_type": "empirical",  # Valid: empirical, theoretical, anecdotal, experimental, observational, statistical
        "confidence_level": "high",  # Valid: very_low, low, medium, high, very_high
        
        # Optional: Other fields
        "suggests_knowledge_item_updates": True,
        "peer_reviewed": False,
    }
    
    research_note_2_data = {
        "title": "State Management Performance Analysis",
        "description": "Comparative analysis of different React state management approaches.",
        "id": "state-management-performance",
        
        # REQUIRED: content as RichText format
        "content": {
            "content-type": "text/html", 
            "data": """
            <h2>Performance Comparison Study</h2>
            <p>This study benchmarks Redux, Zustand, and React Context across various application sizes to determine optimal state management approaches.</p>
            
            <h3>Research Question</h3>
            <p>How do different state management solutions impact React application performance in real-world scenarios?</p>
            
            <h3>Methodology</h3>
            <p>Benchmarking across three categories:</p>
            <ul>
                <li>Small applications (< 20 components)</li>
                <li>Medium applications (20-100 components)</li>
                <li>Large applications (100+ components)</li>
            </ul>
            
            <h3>Key Results</h3>
            <table border="1">
                <tr><th>Solution</th><th>Small Apps</th><th>Medium Apps</th><th>Large Apps</th></tr>
                <tr><td>React Context</td><td>Fast</td><td>Medium</td><td>Slow</td></tr>
                <tr><td>Redux</td><td>Medium</td><td>Fast</td><td>Fast</td></tr>
                <tr><td>Zustand</td><td>Fast</td><td>Fast</td><td>Fastest</td></tr>
            </table>
            
            <h3>Limitations</h3>
            <p>Testing was limited to specific use cases and may not generalize to all application types. Server-side rendering scenarios were not included.</p>
            """
        },
        
        "tags": ["react", "state-management", "performance", "analysis"],
        
        "research_question": "How do different state management solutions impact React application performance?",
        "research_method": "Benchmarking Redux, Zustand, and React Context across various application sizes",
        
        # Authors
        "authors": [
            {
                "name": "Performance Research Team",
                "email": "perf@example.com", 
                "orcid": None,
                "affiliation": "Web Performance Institute"
            }
        ],
        
        # Key insights
        "key_insights": [
            {
                "text": "Zustand showed 15% better performance in large applications compared to Redux",
                "importance": "high",
                "evidence": "Average rendering time measurements across 5 large-scale applications",
                "timestamp": now
            },
            {
                "text": "React Context becomes a bottleneck in applications with more than 50 components",
                "importance": "medium",
                "evidence": "Performance profiling data showing excessive re-renders",
                "timestamp": now
            }
        ],
        
        # Research relationships
        "builds_upon": [],
        "contradicts": [],
        "replication_studies": [],
        
        # REQUIRED: Annotation fields
        "annotated_knowledge_items": [KI_UIDS["state-management"], KI_UIDS["react-performance"]],
        "annotation_type": "critique",  # Different type for variety
        "annotation_scope": "specific_section",
        "evidence_type": "experimental",
        "confidence_level": "medium",
        
        "suggests_knowledge_item_updates": False,
        "peer_reviewed": False,
    }
    
    # Create Research Notes
    create_content_via_api("ResearchNote", research_note_1_data)
    create_content_via_api("ResearchNote", research_note_2_data)

def main():
    """Create corrected ResearchNote demo data."""
    print("🔬 Creating corrected ResearchNote demo data...")
    print()
    
    create_research_notes()
    print()
    
    print("✅ Corrected ResearchNote creation complete!")

if __name__ == "__main__":
    main() 