#!/usr/bin/env python3
"""
Get Knowledge Item UIDs for demo data creation.
"""

import requests
import json

BASE_URL = "http://localhost:8080/Plone"
AUTH = ("admin", "admin")

def get_knowledge_item_uids():
    """Get all Knowledge Item UIDs"""
    
    # First get all Knowledge Items  
    headers = {"Accept": "application/json"}
    url = f"{BASE_URL}/++api++/@search?portal_type=KnowledgeItem"
    
    response = requests.get(url, headers=headers, auth=AUTH, timeout=10)
    if response.status_code != 200:
        print(f"Error getting Knowledge Items: {response.status_code}")
        return {}
    
    data = response.json()
    ki_uids = {}
    
    print(f"Found {len(data['items'])} Knowledge Items:")
    
    for item in data['items']:
        # Extract ID from URL 
        url_parts = item['@id'].split('/')
        item_id = url_parts[-1]
        
        # Get full object to retrieve UID
        full_url = f"{item['@id']}/++api++"
        full_response = requests.get(full_url, headers=headers, auth=AUTH, timeout=10)
        
        if full_response.status_code == 200:
            full_data = full_response.json()
            uid = full_data['UID']
            ki_uids[item_id] = uid
            print(f"  {item['title']} (ID: {item_id}) -> UID: {uid}")
        else:
            print(f"  Failed to get UID for {item['title']}")
    
    return ki_uids

if __name__ == "__main__":
    uids = get_knowledge_item_uids()
    
    print("\n# Copy these UIDs for demo data:")
    for item_id, uid in uids.items():
        print(f'"{item_id}": "{uid}",') 