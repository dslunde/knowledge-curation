#!/usr/bin/env python3
"""
Comprehensive Vector Storage and Advanced Search Test Suite
===========================================================

This script performs thorough testing of:
1. QDrant vector database connectivity and health
2. Vector storage operations (create, read, search)
3. Advanced search API endpoints functionality 
4. Integration between frontend search and vector backend
5. End-to-end search workflow validation

Usage:
    python comprehensive_vector_test.py [--verbose] [--fix-issues]

Results are saved to vector_test_results.json for review.
"""

import json
import logging
import requests
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorTestSuite:
    """Comprehensive test suite for vector storage and search functionality."""
    
    def __init__(self, verbose: bool = False, fix_issues: bool = False):
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.test_results = {
            'test_session': {
                'start_time': datetime.now().isoformat(),
                'test_suite_version': '1.0.0',
                'verbose': verbose,
                'fix_issues': fix_issues
            },
            'infrastructure_tests': {},
            'vector_storage_tests': {},
            'api_endpoint_tests': {},
            'search_functionality_tests': {},
            'integration_tests': {},
            'summary': {},
            'recommendations': []
        }
        
        # Configuration
        self.qdrant_url = "http://localhost:6333"
        self.plone_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:8080"
        self.auth = ('admin', 'admin')
        self.headers = {'Host': 'knowledge-curator.localhost'}
        
    def log_test_result(self, category: str, test_name: str, passed: bool, 
                       details: Dict[str, Any], error: Optional[str] = None):
        """Log a test result with comprehensive details."""
        result = {
            'passed': passed,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        if error:
            result['error'] = error
            
        self.test_results[category][test_name] = result
        
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status} - {test_name}")
        if self.verbose and details:
            logger.info(f"Details: {json.dumps(details, indent=2)}")
        if error:
            logger.error(f"Error: {error}")

    def test_qdrant_connectivity(self) -> bool:
        """Test QDrant database connectivity and basic health."""
        test_name = "QDrant Connectivity"
        try:
            # Test basic connectivity
            response = requests.get(f"{self.qdrant_url}/", timeout=10)
            
            if response.status_code != 200:
                self.log_test_result(
                    'infrastructure_tests', test_name, False,
                    {'status_code': response.status_code},
                    f"QDrant not accessible: HTTP {response.status_code}"
                )
                return False
            
            # Test collections endpoint
            collections_response = requests.get(f"{self.qdrant_url}/collections", timeout=10)
            collections_data = collections_response.json()
            
            details = {
                'qdrant_accessible': True,
                'collections_endpoint': collections_response.status_code == 200,
                'available_collections': collections_data.get('result', {}).get('collections', [])
            }
            
            self.log_test_result('infrastructure_tests', test_name, True, details)
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test_result(
                'infrastructure_tests', test_name, False,
                {'connection_error': str(e)},
                f"QDrant connection failed: {e}"
            )
            return False

    def test_plone_backend_connectivity(self) -> bool:
        """Test Plone backend connectivity and Knowledge Curator availability."""
        test_name = "Plone Backend Connectivity"
        try:
            # Test basic Plone connectivity
            response = requests.get(f"{self.plone_url}/++api++/@site", headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                self.log_test_result(
                    'infrastructure_tests', test_name, False,
                    {'status_code': response.status_code},
                    f"Plone backend not accessible: HTTP {response.status_code}"
                )
                return False
            
            # Test Knowledge Curator API availability
            api_endpoints = [
                '++api++/@vector-management/health',
                '++api++/@vector-management/stats'
            ]
            
            endpoint_results = {}
            for endpoint in api_endpoints:
                try:
                    api_response = requests.get(f"{self.plone_url}/{endpoint}", 
                                              headers=self.headers, timeout=10)
                    endpoint_results[endpoint] = {
                        'status_code': api_response.status_code,
                        'accessible': api_response.status_code < 500
                    }
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'status_code': None,
                        'accessible': False,
                        'error': str(e)
                    }
            
            details = {
                'plone_accessible': True,
                'api_endpoints': endpoint_results
            }
            
            all_endpoints_accessible = all(
                result['accessible'] for result in endpoint_results.values()
            )
            
            self.log_test_result(
                'infrastructure_tests', test_name, all_endpoints_accessible, details
            )
            return all_endpoints_accessible
            
        except requests.exceptions.RequestException as e:
            self.log_test_result(
                'infrastructure_tests', test_name, False,
                {'connection_error': str(e)},
                f"Plone backend connection failed: {e}"
            )
            return False

    def test_vector_management_health(self) -> bool:
        """Test vector management system health via API."""
        test_name = "Vector Management Health"
        try:
            response = requests.get(
                f"{self.plone_url}/++api++/@vector-management/health", 
                headers=self.headers, timeout=15
            )
            
            if response.status_code != 200:
                self.log_test_result(
                    'vector_storage_tests', test_name, False,
                    {'status_code': response.status_code},
                    f"Vector management health check failed: HTTP {response.status_code}"
                )
                return False
            
            health_data = response.json()
            
            # Analyze health data
            overall_healthy = health_data.get('healthy', False)
            
            details = {
                'overall_healthy': overall_healthy,
                'health_data': health_data
            }
            
            # If unhealthy and fix_issues is enabled, try to initialize
            if not overall_healthy and self.fix_issues:
                logger.info("Attempting to fix vector database issues...")
                self.fix_vector_database()
            
            self.log_test_result(
                'vector_storage_tests', test_name, overall_healthy, details
            )
            return overall_healthy
            
        except Exception as e:
            self.log_test_result(
                'vector_storage_tests', test_name, False,
                {'error_type': type(e).__name__},
                f"Health check error: {e}"
            )
            return False

    def fix_vector_database(self) -> bool:
        """Attempt to fix vector database issues."""
        logger.info("Initializing vector database...")
        try:
            # Initialize database
            headers_with_content = self.headers.copy()
            headers_with_content['Content-Type'] = 'application/json'
            init_response = requests.post(
                f"{self.plone_url}/++api++/@vector-management/initialize",
                headers=headers_with_content,
                json={},
                timeout=30
            )
            
            if init_response.status_code == 200:
                logger.info("✓ Vector database initialized")
                return True
            else:
                logger.error(f"✗ Database initialization failed: {init_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Database initialization error: {e}")
            return False

    def test_vector_database_stats(self) -> bool:
        """Test vector database statistics retrieval."""
        test_name = "Vector Database Statistics"
        try:
            response = requests.get(
                f"{self.plone_url}/++api++/@vector-management/stats",
                headers=self.headers, timeout=15
            )
            
            if response.status_code != 200:
                self.log_test_result(
                    'vector_storage_tests', test_name, False,
                    {'status_code': response.status_code},
                    f"Stats retrieval failed: HTTP {response.status_code}"
                )
                return False
            
            stats_data = response.json()
            
            details = {
                'stats_retrieved': True,
                'stats_data': stats_data
            }
            
            # Check if we have meaningful stats
            has_content = (
                'collection_info' in stats_data and 
                stats_data['collection_info'].get('points_count', 0) > 0
            )
            
            details['has_vector_content'] = has_content
            
            self.log_test_result(
                'vector_storage_tests', test_name, True, details
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                'vector_storage_tests', test_name, False,
                {'error_type': type(e).__name__},
                f"Stats retrieval error: {e}"
            )
            return False

    def test_semantic_search_api(self) -> bool:
        """Test semantic search API functionality."""
        test_name = "Semantic Search API"
        try:
            # Test search with a knowledge-related query
            search_queries = [
                "machine learning algorithms",
                "cognitive science research",
                "knowledge management systems"
            ]
            
            search_results = {}
            
            for query in search_queries:
                search_data = {
                    "query": query,
                    "limit": 5,
                    "score_threshold": 0.3
                }
                
                headers_with_content = self.headers.copy()
                headers_with_content['Content-Type'] = 'application/json'
                response = requests.post(
                    f"{self.plone_url}/++api++/@vector-search",
                    headers=headers_with_content,
                    json=search_data,
                    timeout=20
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    search_results[query] = {
                        'success': True,
                        'items_found': result_data.get('items_total', 0),
                        'first_few_results': result_data.get('items', [])[:2]  # Just first 2 for brevity
                    }
                else:
                    search_results[query] = {
                        'success': False,
                        'status_code': response.status_code,
                        'error': response.text
                    }
            
            # Determine overall success
            successful_searches = sum(1 for result in search_results.values() if result['success'])
            overall_success = successful_searches > 0
            
            details = {
                'search_results': search_results,
                'successful_searches': successful_searches,
                'total_queries': len(search_queries)
            }
            
            self.log_test_result(
                'api_endpoint_tests', test_name, overall_success, details
            )
            return overall_success
            
        except Exception as e:
            self.log_test_result(
                'api_endpoint_tests', test_name, False,
                {'error_type': type(e).__name__},
                f"Semantic search API error: {e}"
            )
            return False

    def test_similar_content_api(self) -> bool:
        """Test similar content finding API."""
        test_name = "Similar Content API"
        try:
            # First, try to get some content UIDs
            content_response = requests.get(
                f"{self.plone_url}/++api++/@search?portal_type=KnowledgeItem&metadata_fields=UID",
                headers=self.headers, timeout=15
            )
            
            if content_response.status_code != 200:
                self.log_test_result(
                    'api_endpoint_tests', test_name, False,
                    {'content_search_failed': True},
                    "Could not retrieve Knowledge Items for similarity testing"
                )
                return False
            
            content_data = content_response.json()
            items = content_data.get('items', [])
            
            if not items:
                self.log_test_result(
                    'api_endpoint_tests', test_name, False,
                    {'no_content_available': True},
                    "No Knowledge Items available for similarity testing"
                )
                return False
            
            # Test similarity search with first available item
            test_uid = items[0]['UID']
            
            similarity_response = requests.get(
                f"{self.plone_url}/++api++/@similar-content/{test_uid}?limit=3&threshold=0.5",
                headers=self.headers, timeout=15
            )
            
            if similarity_response.status_code != 200:
                self.log_test_result(
                    'api_endpoint_tests', test_name, False,
                    {'status_code': similarity_response.status_code},
                    f"Similar content API failed: HTTP {similarity_response.status_code}"
                )
                return False
            
            similarity_data = similarity_response.json()
            
            details = {
                'test_uid': test_uid,
                'similar_items_found': similarity_data.get('items_total', 0),
                'similarity_data': similarity_data
            }
            
            self.log_test_result(
                'api_endpoint_tests', test_name, True, details
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                'api_endpoint_tests', test_name, False,
                {'error_type': type(e).__name__},
                f"Similar content API error: {e}"
            )
            return False

    def test_advanced_search_interface(self) -> bool:
        """Test advanced search interface accessibility."""
        test_name = "Advanced Search Interface"
        try:
            # Test advanced search page accessibility
            search_page_response = requests.get(
                f"{self.frontend_url}/advanced-search",
                headers=self.headers, timeout=15
            )
            
            if search_page_response.status_code != 200:
                self.log_test_result(
                    'search_functionality_tests', test_name, False,
                    {'status_code': search_page_response.status_code},
                    f"Advanced search page not accessible: HTTP {search_page_response.status_code}"
                )
                return False
            
            # Check if the page contains expected search elements
            page_content = search_page_response.text
            
            search_indicators = [
                'advanced-search-container',
                'search-input',
                'vector',
                'similarity'
            ]
            
            found_indicators = {}
            for indicator in search_indicators:
                found_indicators[indicator] = indicator.lower() in page_content.lower()
            
            # Check if it's a React/Volto page vs error page
            is_react_page = (
                'react' in page_content.lower() or 
                'volto' in page_content.lower() or
                'advanced-search' in page_content.lower()
            )
            
            details = {
                'page_accessible': True,
                'is_react_page': is_react_page,
                'search_indicators_found': found_indicators,
                'page_size_bytes': len(page_content)
            }
            
            # Success if page is accessible and appears to be the right page
            success = is_react_page or any(found_indicators.values())
            
            self.log_test_result(
                'search_functionality_tests', test_name, success, details
            )
            return success
            
        except Exception as e:
            self.log_test_result(
                'search_functionality_tests', test_name, False,
                {'error_type': type(e).__name__},
                f"Advanced search interface error: {e}"
            )
            return False

    def test_end_to_end_workflow(self) -> bool:
        """Test complete end-to-end search workflow."""
        test_name = "End-to-End Search Workflow"
        try:
            workflow_steps = {}
            
            # Step 1: Check if we have demo data
            content_check = requests.get(
                f"{self.plone_url}/++api++/@search?portal_type=KnowledgeItem",
                headers=self.headers, timeout=15
            )
            
            if content_check.status_code == 200:
                content_data = content_check.json()
                workflow_steps['content_available'] = {
                    'success': True,
                    'count': len(content_data.get('items', []))
                }
            else:
                workflow_steps['content_available'] = {
                    'success': False,
                    'status_code': content_check.status_code
                }
            
            # Step 2: Test vector database has content
            stats_check = requests.get(
                f"{self.plone_url}/++api++/@vector-management/stats",
                headers=self.headers, timeout=15
            )
            
            if stats_check.status_code == 200:
                stats_data = stats_check.json()
                vector_count = stats_data.get('collection_info', {}).get('points_count', 0)
                workflow_steps['vectors_available'] = {
                    'success': vector_count > 0,
                    'count': vector_count
                }
            else:
                workflow_steps['vectors_available'] = {
                    'success': False,
                    'status_code': stats_check.status_code
                }
            
            # Step 3: Test search functionality
            headers_with_content = self.headers.copy()
            headers_with_content['Content-Type'] = 'application/json'
            search_test = requests.post(
                f"{self.plone_url}/++api++/@vector-search",
                headers=headers_with_content,
                json={"query": "research methodology", "limit": 3},
                timeout=15
            )
            
            if search_test.status_code == 200:
                search_data = search_test.json()
                workflow_steps['search_functional'] = {
                    'success': True,
                    'results_count': search_data.get('items_total', 0)
                }
            else:
                workflow_steps['search_functional'] = {
                    'success': False,
                    'status_code': search_test.status_code
                }
            
            # Determine overall workflow success
            all_steps_successful = all(
                step['success'] for step in workflow_steps.values()
            )
            
            details = {
                'workflow_steps': workflow_steps,
                'all_steps_successful': all_steps_successful
            }
            
            self.log_test_result(
                'integration_tests', test_name, all_steps_successful, details
            )
            return all_steps_successful
            
        except Exception as e:
            self.log_test_result(
                'integration_tests', test_name, False,
                {'error_type': type(e).__name__},
                f"End-to-end workflow error: {e}"
            )
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in the comprehensive suite."""
        logger.info("Starting Comprehensive Vector Storage and Search Testing")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Infrastructure Tests
        logger.info("\n🔧 INFRASTRUCTURE TESTS")
        logger.info("-" * 30)
        qdrant_ok = self.test_qdrant_connectivity()
        plone_ok = self.test_plone_backend_connectivity()
        
        # Vector Storage Tests
        logger.info("\n🗄️  VECTOR STORAGE TESTS")
        logger.info("-" * 30)
        vector_health_ok = self.test_vector_management_health()
        vector_stats_ok = self.test_vector_database_stats()
        
        # API Endpoint Tests
        logger.info("\n🔌 API ENDPOINT TESTS")
        logger.info("-" * 30)
        search_api_ok = self.test_semantic_search_api()
        similar_api_ok = self.test_similar_content_api()
        
        # Search Functionality Tests
        logger.info("\n🔍 SEARCH FUNCTIONALITY TESTS")
        logger.info("-" * 30)
        search_interface_ok = self.test_advanced_search_interface()
        
        # Integration Tests
        logger.info("\n🔗 INTEGRATION TESTS")
        logger.info("-" * 30)
        workflow_ok = self.test_end_to_end_workflow()
        
        # Calculate summary
        end_time = time.time()
        total_tests = 8
        passed_tests = sum([
            qdrant_ok, plone_ok, vector_health_ok, vector_stats_ok,
            search_api_ok, similar_api_ok, search_interface_ok, workflow_ok
        ])
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100,
            'duration_seconds': end_time - start_time,
            'overall_success': passed_tests == total_tests
        }
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Add completion timestamp
        self.test_results['test_session']['end_time'] = datetime.now().isoformat()
        
        return self.test_results

    def generate_recommendations(self):
        """Generate actionable recommendations based on test results."""
        recommendations = []
        
        # Check infrastructure issues
        if not self.test_results['infrastructure_tests'].get('QDrant Connectivity', {}).get('passed', True):
            recommendations.append({
                'category': 'Infrastructure',
                'priority': 'HIGH',
                'issue': 'QDrant vector database not accessible',
                'action': 'Check QDrant container status: docker-compose logs qdrant'
            })
        
        if not self.test_results['infrastructure_tests'].get('Plone Backend Connectivity', {}).get('passed', True):
            recommendations.append({
                'category': 'Infrastructure', 
                'priority': 'HIGH',
                'issue': 'Plone backend not accessible',
                'action': 'Check backend container status: docker-compose logs backend'
            })
        
        # Check vector storage issues
        if not self.test_results['vector_storage_tests'].get('Vector Management Health', {}).get('passed', True):
            recommendations.append({
                'category': 'Vector Storage',
                'priority': 'HIGH',
                'issue': 'Vector management system unhealthy',
                'action': 'Run vector database initialization: POST to @@vector-management/initialize'
            })
        
        # Check if no vector content exists
        stats_test = self.test_results['vector_storage_tests'].get('Vector Database Statistics', {})
        if stats_test.get('passed') and not stats_test.get('details', {}).get('has_vector_content'):
            recommendations.append({
                'category': 'Vector Content',
                'priority': 'MEDIUM',
                'issue': 'No vectors found in database',
                'action': 'Run index rebuild to populate vectors: POST to @@vector-management/rebuild'
            })
        
        # Check API functionality
        if not self.test_results['api_endpoint_tests'].get('Semantic Search API', {}).get('passed', True):
            recommendations.append({
                'category': 'API Functionality',
                'priority': 'HIGH',
                'issue': 'Semantic search API not working',
                'action': 'Check vector database health and content availability'
            })
        
        self.test_results['recommendations'] = recommendations

    def save_results(self, filename: str = "vector_test_results.json"):
        """Save test results to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"✓ Test results saved to {filename}")
        except Exception as e:
            logger.error(f"✗ Failed to save results: {e}")

    def print_summary(self):
        """Print a comprehensive test summary."""
        summary = self.test_results['summary']
        recommendations = self.test_results['recommendations']
        
        logger.info("\n" + "=" * 70)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 70)
        
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Duration: {summary['duration_seconds']:.2f} seconds")
        
        if summary['overall_success']:
            logger.info("\n🎉 ALL TESTS PASSED! Vector storage and search functionality is working correctly.")
        else:
            logger.info(f"\n⚠️  {summary['failed_tests']} test(s) failed. See recommendations below.")
        
        if recommendations:
            logger.info("\n🔧 RECOMMENDATIONS")
            logger.info("-" * 30)
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"{i}. [{rec['priority']}] {rec['category']}")
                logger.info(f"   Issue: {rec['issue']}")
                logger.info(f"   Action: {rec['action']}\n")


def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description='Comprehensive Vector Storage Test Suite')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--fix-issues', action='store_true', help='Attempt to fix identified issues')
    parser.add_argument('--output', default='vector_test_results.json', help='Output file for results')
    
    args = parser.parse_args()
    
    # Create and run test suite
    test_suite = VectorTestSuite(verbose=args.verbose, fix_issues=args.fix_issues)
    
    try:
        results = test_suite.run_all_tests()
        test_suite.print_summary()
        test_suite.save_results(args.output)
        
        # Exit with appropriate code
        if results['summary']['overall_success']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 