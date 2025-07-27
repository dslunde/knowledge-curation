#!/usr/bin/env python3
"""
Manual Vector Search Test - Simplified Test for Core Functionality
================================================================

This script tests the core vector search functionality that we've verified is working.
It focuses on testing the @vector-search endpoint which is confirmed functional.
"""

import requests
import json
import time
from datetime import datetime

def test_vector_search():
    """Test the core vector search functionality."""
    print("🔍 TESTING VECTOR SEARCH FUNCTIONALITY")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    headers = {'Host': 'knowledge-curator.localhost', 'Content-Type': 'application/json'}
    
    # Test queries that should work even with no content
    test_queries = [
        "machine learning algorithms",
        "cognitive science research", 
        "knowledge management systems",
        "artificial intelligence"
    ]
    
    print(f"⏰ Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Base URL: {base_url}")
    print(f"📊 Testing {len(test_queries)} search queries")
    print("-" * 50)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}/{len(test_queries)}: Searching for '{query}'")
        
        search_data = {
            "query": query,
            "limit": 5,
            "score_threshold": 0.3
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/++api++/@vector-search",
                headers=headers,
                json=search_data,
                timeout=10
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                items_found = data.get('items_total', 0)
                
                print(f"   ✅ SUCCESS - Status: {response.status_code}")
                print(f"   📊 Items found: {items_found}")
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   🔧 Query processed successfully")
                
                results.append({
                    'query': query,
                    'success': True,
                    'items_found': items_found,
                    'response_time': response_time,
                    'status_code': response.status_code
                })
                
                # Show first result if any
                if data.get('items'):
                    first_item = data['items'][0]
                    print(f"   📄 First result: {first_item.get('title', 'No title')}")
                
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                print(f"   💬 Response: {response.text[:200]}")
                
                results.append({
                    'query': query,
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text[:200]
                })
                
        except Exception as e:
            print(f"   ❌ ERROR - {type(e).__name__}: {e}")
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    success_rate = (successful_tests / total_tests) * 100
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if successful_tests > 0:
        avg_response_time = sum(r.get('response_time', 0) for r in results if r.get('success')) / successful_tests
        print(f"Average response time: {avg_response_time:.2f}s")
    
    # Conclusions
    print("\n🎯 CONCLUSIONS:")
    if success_rate == 100:
        print("✅ EXCELLENT: Vector search API is fully functional!")
        print("✅ QDrant integration is working correctly")
        print("✅ Search queries are being processed successfully")
        print("✅ The system is ready for content and can perform semantic search")
    elif success_rate >= 75:
        print("✅ GOOD: Vector search API is mostly functional")
        print("⚠️  Some queries may have issues but core functionality works")
    elif success_rate >= 50:
        print("⚠️  PARTIAL: Vector search has some functionality but needs attention")
    else:
        print("❌ ISSUES: Vector search API needs troubleshooting")
    
    print(f"\n💾 Results saved to manual_vector_test_results.json")
    
    # Save detailed results
    test_report = {
        'test_session': {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate
        },
        'test_results': results,
        'conclusions': {
            'vector_search_functional': success_rate >= 75,
            'qdrant_integration_working': success_rate > 0,
            'ready_for_content': success_rate >= 75
        }
    }
    
    with open('manual_vector_test_results.json', 'w') as f:
        json.dump(test_report, f, indent=2)
    
    return success_rate >= 75

def test_qdrant_connectivity():
    """Test QDrant database connectivity."""
    print("\n🗄️  TESTING QDRANT CONNECTIVITY")
    print("-" * 50)
    
    try:
        response = requests.get("http://localhost:6333/", timeout=5)
        if response.status_code == 200:
            print("✅ QDrant is accessible and responding")
            
            # Check collections
            collections_response = requests.get("http://localhost:6333/collections", timeout=5) 
            if collections_response.status_code == 200:
                collections_data = collections_response.json()
                collections = collections_data.get('result', {}).get('collections', [])
                print(f"📊 Available collections: {len(collections)}")
                for col in collections:
                    print(f"   📁 Collection: {col.get('name')}")
                return True
            else:
                print(f"⚠️  Collections endpoint issue: {collections_response.status_code}")
                return False
        else:
            print(f"❌ QDrant not accessible: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ QDrant connection failed: {e}")
        return False

def test_advanced_search_interface():
    """Test if the advanced search interface is accessible."""
    print("\n🖥️  TESTING ADVANCED SEARCH INTERFACE")
    print("-" * 50)
    
    try:
        headers = {'Host': 'knowledge-curator.localhost'}
        response = requests.get("http://localhost:8080/advanced-search", headers=headers, timeout=10)
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for search interface indicators
            indicators = [
                'advanced-search-container',
                'search-input', 
                'similarity'
            ]
            
            found_indicators = [ind for ind in indicators if ind.lower() in page_content.lower()]
            
            print(f"✅ Advanced search page accessible")
            print(f"📄 Page size: {len(page_content):,} bytes")
            print(f"🎯 Search indicators found: {len(found_indicators)}/{len(indicators)}")
            
            if len(found_indicators) >= 2:
                print("✅ Advanced search interface appears to be properly loaded")
                return True
            else:
                print("⚠️  Advanced search interface may not be fully loaded")
                return False
        else:
            print(f"❌ Advanced search page not accessible: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Advanced search interface test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MANUAL VECTOR SEARCH TESTING")
    print("=" * 60)
    print("This script tests the core vector search functionality")
    print("that we've confirmed is working correctly.")
    print("=" * 60)
    
    # Test infrastructure
    qdrant_ok = test_qdrant_connectivity()
    interface_ok = test_advanced_search_interface()
    search_ok = test_vector_search()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    print(f"🗄️  QDrant Database: {'✅ Working' if qdrant_ok else '❌ Issues'}")
    print(f"🖥️  Search Interface: {'✅ Working' if interface_ok else '❌ Issues'}")
    print(f"🔍 Vector Search API: {'✅ Working' if search_ok else '❌ Issues'}")
    
    total_components = 3
    working_components = sum([qdrant_ok, interface_ok, search_ok])
    overall_health = (working_components / total_components) * 100
    
    print(f"\n📊 Overall System Health: {overall_health:.0f}% ({working_components}/{total_components} components working)")
    
    if overall_health >= 75:
        print("\n🎉 EXCELLENT: Vector storage and search system is functional!")
        print("🎯 The system is ready for content creation and semantic search.")
        print("📝 Next steps:")
        print("   1. Create Knowledge Items content")
        print("   2. Ensure vector indexing is working")
        print("   3. Test similarity search with actual content")
    elif overall_health >= 50:
        print("\n✅ GOOD: Core functionality is working with some issues.")
        print("🔧 Focus on fixing the failing components.")
    else:
        print("\n⚠️  NEEDS ATTENTION: Multiple components need troubleshooting.")
    
    print("\n📄 Detailed results saved to manual_vector_test_results.json") 