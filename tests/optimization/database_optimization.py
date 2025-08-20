#!/usr/bin/env python3
"""
Database Optimization and Query Performance Testing
Comprehensive database performance analysis and optimization
"""

import json
import os
import time
import statistics
from typing import Dict, List, Any, Optional
import psutil
import requests
from dataclasses import dataclass


@dataclass
class QueryPerformanceResult:
    """Data class for query performance results"""
    query_type: str
    execution_time: float
    rows_affected: int
    cpu_usage: float
    memory_usage: float
    optimization_suggestions: List[str]


class DatabaseOptimizationSuite:
    """Comprehensive database optimization testing suite"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results = {}
        
    def run_all_optimization_tests(self) -> Dict[str, Any]:
        """Run all database optimization tests"""
        print("🗄️ Starting Database Optimization Suite...")
        
        test_methods = [
            self.test_query_performance,
            self.test_connection_pooling,
            self.test_index_effectiveness,
            self.test_cache_hit_rates,
            self.test_slow_query_detection,
            self.test_database_size_analysis,
            self.test_concurrent_access_performance,
            self.analyze_n_plus_one_queries,
            self.test_bulk_operations_performance,
            self.test_database_backup_performance,
        ]
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method.__name__}...")
                result = test_method()
                self.results[test_method.__name__] = result
                print(f"✅ {test_method.__name__} completed")
            except Exception as e:
                error_msg = f"❌ {test_method.__name__} failed: {str(e)}"
                print(error_msg)
                self.results[test_method.__name__] = {
                    "status": "failed", 
                    "error": str(e)
                }
        
        return self.generate_optimization_report()
    
    def test_query_performance(self) -> Dict[str, Any]:
        """Test query performance across different endpoints"""
        query_tests = {}
        
        endpoints = [
            {'url': '/api/v1/blog/posts/', 'type': 'list_query'},
            {'url': '/api/v1/users/', 'type': 'user_query'},
            {'url': '/api/v1/health/database/', 'type': 'health_check'},
        ]
        
        for endpoint in endpoints:
            try:
                # Measure query performance
                start_cpu = psutil.cpu_percent()
                start_memory = psutil.virtual_memory().percent
                
                start_time = time.time()
                response = requests.get(f"{self.api_url}{endpoint['url']}", timeout=30)
                end_time = time.time()
                
                end_cpu = psutil.cpu_percent()
                end_memory = psutil.virtual_memory().percent
                
                execution_time = end_time - start_time
                
                # Analyze response
                rows_affected = 0
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            rows_affected = len(data)
                        elif isinstance(data, dict) and 'results' in data:
                            rows_affected = len(data['results'])
                        elif isinstance(data, dict) and 'count' in data:
                            rows_affected = data['count']
                    except:
                        pass
                
                # Generate optimization suggestions
                suggestions = []
                if execution_time > 2.0:
                    suggestions.append("Query execution time is slow - consider adding indexes")
                if execution_time > 5.0:
                    suggestions.append("Critical: Query is extremely slow - immediate optimization needed")
                if end_cpu - start_cpu > 20:
                    suggestions.append("High CPU usage during query - optimize query complexity")
                if end_memory - start_memory > 10:
                    suggestions.append("High memory usage - consider query result pagination")
                
                query_tests[endpoint['url']] = {
                    'query_type': endpoint['type'],
                    'execution_time': execution_time,
                    'rows_affected': rows_affected,
                    'cpu_usage_delta': end_cpu - start_cpu,
                    'memory_usage_delta': end_memory - start_memory,
                    'response_status': response.status_code,
                    'optimization_suggestions': suggestions
                }
                
            except Exception as e:
                query_tests[endpoint['url']] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return query_tests
    
    def test_connection_pooling(self) -> Dict[str, Any]:
        """Test database connection pooling effectiveness"""
        try:
            # Test concurrent connections
            import concurrent.futures
            import threading
            
            connection_times = []
            errors = []
            
            def make_db_request():
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.api_url}/api/v1/health/database/", timeout=10)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        return end_time - start_time
                    else:
                        errors.append(f"HTTP {response.status_code}")
                        return None
                except Exception as e:
                    errors.append(str(e))
                    return None
            
            # Test with multiple concurrent connections
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_db_request) for _ in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Filter out None results
            connection_times = [t for t in results if t is not None]
            
            if connection_times:
                avg_connection_time = statistics.mean(connection_times)
                max_connection_time = max(connection_times)
                min_connection_time = min(connection_times)
                
                # Analyze connection pooling effectiveness
                suggestions = []
                if avg_connection_time > 1.0:
                    suggestions.append("Average connection time is high - check connection pool configuration")
                if max_connection_time > 5.0:
                    suggestions.append("Maximum connection time is excessive - increase pool size")
                if len(errors) > len(connection_times) * 0.1:
                    suggestions.append("High error rate - connection pool may be exhausted")
                
                return {
                    'status': 'passed',
                    'total_requests': 20,
                    'successful_requests': len(connection_times),
                    'failed_requests': len(errors),
                    'average_connection_time': avg_connection_time,
                    'max_connection_time': max_connection_time,
                    'min_connection_time': min_connection_time,
                    'error_rate': len(errors) / 20,
                    'errors': errors[:5],  # First 5 errors
                    'optimization_suggestions': suggestions
                }
            else:
                return {
                    'status': 'failed',
                    'message': 'All connection attempts failed',
                    'errors': errors
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_index_effectiveness(self) -> Dict[str, Any]:
        """Test database index effectiveness"""
        try:
            # Test queries that should benefit from indexes
            index_tests = {}
            
            # Test search queries (should use indexes)
            search_queries = [
                {'endpoint': '/api/v1/blog/posts/', 'params': {'search': 'test'}},
                {'endpoint': '/api/v1/users/', 'params': {'username': 'admin'}},
            ]
            
            for query in search_queries:
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"{self.api_url}{query['endpoint']}", 
                        params=query['params'], 
                        timeout=30
                    )
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    
                    # Analyze if indexes are likely being used
                    suggestions = []
                    if execution_time > 1.0:
                        suggestions.append("Slow search query - ensure proper indexes exist")
                    if execution_time > 3.0:
                        suggestions.append("Very slow search - check index usage and query plan")
                    
                    index_tests[f"{query['endpoint']}?{list(query['params'].keys())[0]}"] = {
                        'execution_time': execution_time,
                        'response_status': response.status_code,
                        'likely_using_index': execution_time < 1.0,
                        'optimization_suggestions': suggestions
                    }
                    
                except Exception as e:
                    index_tests[f"{query['endpoint']}?{list(query['params'].keys())[0]}"] = {
                        'status': 'failed',
                        'error': str(e)
                    }
            
            return {
                'status': 'passed',
                'index_tests': index_tests,
                'overall_index_performance': 'good' if all(
                    test.get('likely_using_index', False) 
                    for test in index_tests.values() 
                    if 'likely_using_index' in test
                ) else 'needs_improvement'
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_cache_hit_rates(self) -> Dict[str, Any]:
        """Test database query caching effectiveness"""
        try:
            cache_tests = {}
            
            # Test same query multiple times to check caching
            test_endpoint = '/api/v1/blog/posts/'
            
            # First request (cache miss)
            start_time = time.time()
            response1 = requests.get(f"{self.api_url}{test_endpoint}", timeout=30)
            first_request_time = time.time() - start_time
            
            # Second request (potential cache hit)
            start_time = time.time()
            response2 = requests.get(f"{self.api_url}{test_endpoint}", timeout=30)
            second_request_time = time.time() - start_time
            
            # Third request (should be cache hit)
            start_time = time.time()
            response3 = requests.get(f"{self.api_url}{test_endpoint}", timeout=30)
            third_request_time = time.time() - start_time
            
            # Analyze caching effectiveness
            cache_improvement = (first_request_time - second_request_time) / first_request_time * 100
            consistent_caching = abs(second_request_time - third_request_time) < 0.1
            
            suggestions = []
            if cache_improvement < 20:
                suggestions.append("Low cache improvement - verify query caching is enabled")
            if not consistent_caching:
                suggestions.append("Inconsistent cache performance - check cache configuration")
            if second_request_time > first_request_time:
                suggestions.append("Cache may not be working - second request slower than first")
            
            return {
                'status': 'passed',
                'first_request_time': first_request_time,
                'second_request_time': second_request_time,
                'third_request_time': third_request_time,
                'cache_improvement_percent': cache_improvement,
                'consistent_caching': consistent_caching,
                'cache_effectiveness': 'good' if cache_improvement > 20 and consistent_caching else 'poor',
                'optimization_suggestions': suggestions
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_slow_query_detection(self) -> Dict[str, Any]:
        """Test for slow queries and performance bottlenecks"""
        try:
            slow_queries = []
            
            # Test various endpoints for slow queries
            endpoints = [
                '/api/v1/blog/posts/',
                '/api/v1/users/',
                '/api/v1/analytics/',
                '/api/v1/comments/',
            ]
            
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.api_url}{endpoint}", timeout=30)
                    execution_time = time.time() - start_time
                    
                    if execution_time > 2.0:  # Consider > 2s as slow
                        slow_queries.append({
                            'endpoint': endpoint,
                            'execution_time': execution_time,
                            'response_status': response.status_code,
                            'severity': 'critical' if execution_time > 5.0 else 'warning'
                        })
                        
                except Exception as e:
                    slow_queries.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'severity': 'error'
                    })
            
            suggestions = []
            if slow_queries:
                critical_slow = [q for q in slow_queries if q.get('severity') == 'critical']
                if critical_slow:
                    suggestions.append(f"Critical: {len(critical_slow)} queries are extremely slow (>5s)")
                suggestions.append("Analyze slow queries and add appropriate indexes")
                suggestions.append("Consider query optimization and database tuning")
            else:
                suggestions.append("No slow queries detected - good performance")
            
            return {
                'status': 'passed',
                'slow_queries_detected': len(slow_queries),
                'slow_queries': slow_queries,
                'performance_grade': 'A' if not slow_queries else 'C' if len(slow_queries) < 3 else 'F',
                'optimization_suggestions': suggestions
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_database_size_analysis(self) -> Dict[str, Any]:
        """Analyze database size and growth patterns"""
        try:
            # This would typically connect to database directly
            # For now, we'll estimate based on API responses
            
            size_analysis = {}
            
            # Estimate table sizes based on API responses
            tables = [
                {'name': 'blog_posts', 'endpoint': '/api/v1/blog/posts/'},
                {'name': 'users', 'endpoint': '/api/v1/users/'},
                {'name': 'comments', 'endpoint': '/api/v1/comments/'},
            ]
            
            total_estimated_records = 0
            
            for table in tables:
                try:
                    response = requests.get(f"{self.api_url}{table['endpoint']}", timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Estimate record count
                        record_count = 0
                        if isinstance(data, list):
                            record_count = len(data)
                        elif isinstance(data, dict) and 'count' in data:
                            record_count = data['count']
                        elif isinstance(data, dict) and 'results' in data:
                            record_count = len(data['results'])
                        
                        size_analysis[table['name']] = {
                            'estimated_records': record_count,
                            'response_size_bytes': len(response.content),
                            'status': 'analyzed'
                        }
                        
                        total_estimated_records += record_count
                        
                except Exception as e:
                    size_analysis[table['name']] = {
                        'status': 'failed',
                        'error': str(e)
                    }
            
            # Generate recommendations based on size
            suggestions = []
            if total_estimated_records > 100000:
                suggestions.append("Large dataset detected - consider data archiving strategy")
            if total_estimated_records > 1000000:
                suggestions.append("Very large dataset - implement data partitioning")
            
            for table_name, analysis in size_analysis.items():
                if analysis.get('estimated_records', 0) > 50000:
                    suggestions.append(f"Table {table_name} is large - monitor query performance")
            
            return {
                'status': 'passed',
                'total_estimated_records': total_estimated_records,
                'table_analysis': size_analysis,
                'database_size_category': self._categorize_database_size(total_estimated_records),
                'optimization_suggestions': suggestions
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_concurrent_access_performance(self) -> Dict[str, Any]:
        """Test database performance under concurrent access"""
        try:
            import concurrent.futures
            
            def concurrent_query():
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.api_url}/api/v1/blog/posts/", timeout=30)
                    execution_time = time.time() - start_time
                    
                    return {
                        'execution_time': execution_time,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                except Exception as e:
                    return {
                        'execution_time': None,
                        'success': False,
                        'error': str(e)
                    }
            
            # Test with increasing concurrency levels
            concurrency_results = {}
            
            for concurrent_users in [1, 5, 10, 20]:
                print(f"Testing with {concurrent_users} concurrent users...")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                    futures = [executor.submit(concurrent_query) for _ in range(concurrent_users * 2)]
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                
                successful_results = [r for r in results if r['success']]
                execution_times = [r['execution_time'] for r in successful_results if r['execution_time']]
                
                if execution_times:
                    concurrency_results[concurrent_users] = {
                        'total_requests': len(results),
                        'successful_requests': len(successful_results),
                        'success_rate': len(successful_results) / len(results),
                        'average_execution_time': statistics.mean(execution_times),
                        'max_execution_time': max(execution_times),
                        'min_execution_time': min(execution_times)
                    }
                else:
                    concurrency_results[concurrent_users] = {
                        'total_requests': len(results),
                        'successful_requests': 0,
                        'success_rate': 0,
                        'error': 'All requests failed'
                    }
            
            # Analyze concurrency performance
            suggestions = []
            for users, result in concurrency_results.items():
                if result.get('success_rate', 0) < 0.9:
                    suggestions.append(f"Low success rate ({result['success_rate']:.1%}) at {users} concurrent users")
                if result.get('average_execution_time', 0) > 3.0:
                    suggestions.append(f"Slow response time ({result['average_execution_time']:.2f}s) at {users} concurrent users")
            
            if not suggestions:
                suggestions.append("Database handles concurrent access well")
            
            return {
                'status': 'passed',
                'concurrency_results': concurrency_results,
                'optimization_suggestions': suggestions
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def analyze_n_plus_one_queries(self) -> Dict[str, Any]:
        """Analyze for N+1 query problems"""
        try:
            # Test endpoints that might have N+1 query issues
            n_plus_one_tests = {}
            
            # Test blog posts with related data (comments, authors)
            start_time = time.time()
            response = requests.get(f"{self.api_url}/api/v1/blog/posts/", timeout=30)
            list_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # If we have posts, test individual post access
                if isinstance(data, list) and data:
                    post_id = data[0].get('id') if isinstance(data[0], dict) else None
                    
                    if post_id:
                        start_time = time.time()
                        detail_response = requests.get(f"{self.api_url}/api/v1/blog/posts/{post_id}/", timeout=30)
                        detail_time = time.time() - start_time
                        
                        # Analyze timing patterns
                        time_ratio = detail_time / list_time if list_time > 0 else 0
                        
                        suggestions = []
                        if time_ratio > 2.0:
                            suggestions.append("Detail view much slower than list - possible N+1 query issue")
                        if detail_time > 2.0:
                            suggestions.append("Slow detail view - check for unnecessary database queries")
                        
                        n_plus_one_tests['blog_posts'] = {
                            'list_time': list_time,
                            'detail_time': detail_time,
                            'time_ratio': time_ratio,
                            'potential_n_plus_one': time_ratio > 2.0,
                            'optimization_suggestions': suggestions
                        }
            
            return {
                'status': 'passed',
                'n_plus_one_tests': n_plus_one_tests,
                'overall_assessment': 'good' if not any(
                    test.get('potential_n_plus_one', False) 
                    for test in n_plus_one_tests.values()
                ) else 'needs_review'
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_bulk_operations_performance(self) -> Dict[str, Any]:
        """Test bulk operations performance"""
        try:
            # This would test bulk insert/update operations
            # For now, we'll simulate by testing pagination performance
            
            bulk_tests = {}
            
            # Test pagination performance (simulates bulk data handling)
            page_sizes = [10, 50, 100]
            
            for page_size in page_sizes:
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"{self.api_url}/api/v1/blog/posts/", 
                        params={'page_size': page_size},
                        timeout=30
                    )
                    execution_time = time.time() - start_time
                    
                    suggestions = []
                    if execution_time > page_size * 0.01:  # More than 10ms per record
                        suggestions.append(f"Slow bulk operation for page size {page_size}")
                    
                    bulk_tests[f'page_size_{page_size}'] = {
                        'execution_time': execution_time,
                        'time_per_record': execution_time / page_size if page_size > 0 else 0,
                        'response_status': response.status_code,
                        'optimization_suggestions': suggestions
                    }
                    
                except Exception as e:
                    bulk_tests[f'page_size_{page_size}'] = {
                        'status': 'failed',
                        'error': str(e)
                    }
            
            return {
                'status': 'passed',
                'bulk_operation_tests': bulk_tests,
                'performance_grade': self._calculate_bulk_performance_grade(bulk_tests)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_database_backup_performance(self) -> Dict[str, Any]:
        """Test database backup and recovery performance"""
        # This is a placeholder for backup testing
        # In a real scenario, this would test backup/restore operations
        
        return {
            'status': 'warning',
            'message': 'Database backup testing not implemented - manual verification required',
            'recommendations': [
                'Implement automated database backup testing',
                'Test backup and restore procedures regularly',
                'Monitor backup performance and storage requirements',
                'Verify backup integrity and recovery time objectives'
            ]
        }
    
    def _categorize_database_size(self, record_count: int) -> str:
        """Categorize database size"""
        if record_count < 1000:
            return 'small'
        elif record_count < 100000:
            return 'medium'
        elif record_count < 1000000:
            return 'large'
        else:
            return 'very_large'
    
    def _calculate_bulk_performance_grade(self, bulk_tests: Dict) -> str:
        """Calculate bulk performance grade"""
        total_tests = len(bulk_tests)
        good_performance = 0
        
        for test in bulk_tests.values():
            if isinstance(test, dict) and test.get('time_per_record', float('inf')) < 0.01:
                good_performance += 1
        
        performance_ratio = good_performance / total_tests if total_tests > 0 else 0
        
        if performance_ratio >= 0.9:
            return 'A'
        elif performance_ratio >= 0.7:
            return 'B'
        elif performance_ratio >= 0.5:
            return 'C'
        else:
            return 'D'
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive database optimization report"""
        
        # Collect all optimization suggestions
        all_suggestions = []
        critical_issues = []
        performance_scores = []
        
        for test_name, result in self.results.items():
            if isinstance(result, dict):
                # Collect suggestions
                if 'optimization_suggestions' in result:
                    all_suggestions.extend(result['optimization_suggestions'])
                
                # Collect nested suggestions
                for key, value in result.items():
                    if isinstance(value, dict) and 'optimization_suggestions' in value:
                        all_suggestions.extend(value['optimization_suggestions'])
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and 'optimization_suggestions' in item:
                                all_suggestions.extend(item['optimization_suggestions'])
                
                # Identify critical issues
                if 'slow_queries' in result:
                    critical_slow = [q for q in result.get('slow_queries', []) 
                                   if isinstance(q, dict) and q.get('severity') == 'critical']
                    critical_issues.extend(critical_slow)
                
                # Collect performance grades/scores
                if 'performance_grade' in result:
                    grade = result['performance_grade']
                    if grade in ['A', 'B', 'C', 'D', 'F']:
                        score = {'A': 95, 'B': 85, 'C': 75, 'D': 65, 'F': 50}[grade]
                        performance_scores.append(score)
        
        # Remove duplicate suggestions
        unique_suggestions = list(dict.fromkeys(all_suggestions))
        
        # Calculate overall performance score
        overall_score = statistics.mean(performance_scores) if performance_scores else 70
        
        # Generate overall grade
        if overall_score >= 90:
            overall_grade = 'A'
        elif overall_score >= 80:
            overall_grade = 'B'
        elif overall_score >= 70:
            overall_grade = 'C'
        elif overall_score >= 60:
            overall_grade = 'D'
        else:
            overall_grade = 'F'
        
        # Generate priority recommendations
        priority_recommendations = []
        if critical_issues:
            priority_recommendations.append(f"🚨 CRITICAL: {len(critical_issues)} slow queries need immediate attention")
        
        high_priority = [s for s in unique_suggestions if 'critical' in s.lower() or 'immediate' in s.lower()]
        if high_priority:
            priority_recommendations.extend(high_priority[:3])  # Top 3 high priority
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'overall_performance_grade': overall_grade,
                'overall_performance_score': overall_score,
                'total_tests_run': len(self.results),
                'critical_issues_found': len(critical_issues),
                'total_optimization_suggestions': len(unique_suggestions)
            },
            'detailed_results': self.results,
            'critical_issues': critical_issues,
            'all_optimization_suggestions': unique_suggestions,
            'priority_recommendations': priority_recommendations,
            'next_steps': [
                "Review and implement priority recommendations",
                "Monitor database performance metrics regularly",
                "Set up automated performance testing",
                "Consider database scaling strategies if needed",
                "Schedule regular database maintenance and optimization"
            ]
        }
        
        return report


def main():
    """Main function to run database optimization testing"""
    print("🗄️ Starting Database Optimization Suite...")
    
    suite = DatabaseOptimizationSuite()
    report = suite.run_all_optimization_tests()
    
    # Save report
    os.makedirs('tests/optimization', exist_ok=True)
    with open('tests/optimization/database_optimization_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("DATABASE OPTIMIZATION REPORT")
    print("="*80)
    print(f"Overall Performance Grade: {report['summary']['overall_performance_grade']}")
    print(f"Performance Score: {report['summary']['overall_performance_score']:.1f}/100")
    print(f"Tests Run: {report['summary']['total_tests_run']}")
    print(f"Critical Issues: {report['summary']['critical_issues_found']}")
    print(f"Optimization Suggestions: {report['summary']['total_optimization_suggestions']}")
    
    if report['priority_recommendations']:
        print("\nPRIORITY RECOMMENDATIONS:")
        for i, rec in enumerate(report['priority_recommendations'], 1):
            print(f"{i}. {rec}")
    
    print(f"\nDetailed report saved to: tests/optimization/database_optimization_report.json")


if __name__ == "__main__":
    main()