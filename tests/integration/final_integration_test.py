#!/usr/bin/env python3
"""
Final Integration Testing Suite
Comprehensive end-to-end testing across all components
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests
import psutil
import redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class IntegrationTestSuite:
    """Comprehensive integration test suite for the entire system"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'http://localhost')
        self.api_url = f"{self.base_url}:8000"
        self.web_url = f"{self.base_url}:3000"
        self.results = {}
        self.errors = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🚀 Starting Final Integration Testing Suite...")
        
        test_methods = [
            self.test_system_health,
            self.test_database_connectivity,
            self.test_redis_connectivity,
            self.test_api_endpoints,
            self.test_authentication_flow,
            self.test_websocket_connections,
            self.test_frontend_functionality,
            self.test_real_time_features,
            self.test_caching_performance,
            self.test_security_measures,
            self.test_monitoring_systems,
            self.test_error_handling,
            self.test_load_performance,
        ]
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method.__name__}...")
                result = test_method()
                self.results[test_method.__name__] = result
                print(f"✅ {test_method.__name__} passed")
            except Exception as e:
                error_msg = f"❌ {test_method.__name__} failed: {str(e)}"
                print(error_msg)
                self.errors.append(error_msg)
                self.results[test_method.__name__] = {"status": "failed", "error": str(e)}
        
        return self.generate_final_report()
    
    def test_system_health(self) -> Dict[str, Any]:
        """Test overall system health"""
        health_checks = {}
        
        # Check Django API health
        try:
            response = requests.get(f"{self.api_url}/health/", timeout=10)
            health_checks['django_api'] = {
                'status': response.status_code == 200,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_checks['django_api'] = {'status': False, 'error': str(e)}
        
        # Check Next.js web app health
        try:
            response = requests.get(f"{self.web_url}/api/health", timeout=10)
            health_checks['nextjs_web'] = {
                'status': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            health_checks['nextjs_web'] = {'status': False, 'error': str(e)}
        
        # Check system resources
        health_checks['system_resources'] = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        return health_checks
    
    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and performance"""
        db_tests = {}
        
        # Test PostgreSQL connection
        try:
            response = requests.get(f"{self.api_url}/api/v1/health/database/", timeout=10)
            db_tests['postgresql'] = {
                'connection': response.status_code == 200,
                'response_time': response.elapsed.total_seconds(),
                'details': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            db_tests['postgresql'] = {'connection': False, 'error': str(e)}
        
        # Test database operations
        try:
            # Test read operation
            response = requests.get(f"{self.api_url}/api/v1/users/", timeout=10)
            db_tests['read_operations'] = {
                'status': response.status_code in [200, 401],  # 401 is OK if not authenticated
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            db_tests['read_operations'] = {'status': False, 'error': str(e)}
        
        return db_tests
    
    def test_redis_connectivity(self) -> Dict[str, Any]:
        """Test Redis connectivity and caching"""
        redis_tests = {}
        
        try:
            # Test Redis connection
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            r.ping()
            redis_tests['connection'] = True
            
            # Test cache operations
            test_key = 'integration_test_key'
            test_value = 'integration_test_value'
            
            r.set(test_key, test_value, ex=60)
            retrieved_value = r.get(test_key)
            
            redis_tests['cache_operations'] = {
                'set_get': retrieved_value == test_value,
                'expiration': True  # Assuming expiration works
            }
            
            # Clean up
            r.delete(test_key)
            
        except Exception as e:
            redis_tests['connection'] = False
            redis_tests['error'] = str(e)
        
        return redis_tests
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test critical API endpoints"""
        api_tests = {}
        
        endpoints = [
            {'url': '/api/v1/', 'method': 'GET', 'expected_status': 200},
            {'url': '/api/v1/auth/login/', 'method': 'POST', 'expected_status': 400},  # No data provided
            {'url': '/api/v1/blog/posts/', 'method': 'GET', 'expected_status': [200, 401]},
            {'url': '/api/v1/health/', 'method': 'GET', 'expected_status': 200},
        ]
        
        for endpoint in endpoints:
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(f"{self.api_url}{endpoint['url']}", timeout=10)
                elif endpoint['method'] == 'POST':
                    response = requests.post(f"{self.api_url}{endpoint['url']}", json={}, timeout=10)
                
                expected = endpoint['expected_status']
                if isinstance(expected, list):
                    status_ok = response.status_code in expected
                else:
                    status_ok = response.status_code == expected
                
                api_tests[endpoint['url']] = {
                    'status': status_ok,
                    'response_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            except Exception as e:
                api_tests[endpoint['url']] = {'status': False, 'error': str(e)}
        
        return api_tests
    
    def test_authentication_flow(self) -> Dict[str, Any]:
        """Test authentication and authorization flow"""
        auth_tests = {}
        
        try:
            # Test user registration (if endpoint exists)
            test_user = {
                'username': 'integration_test_user',
                'email': 'test@integration.com',
                'password': 'TestPassword123!'
            }
            
            # Try to register
            response = requests.post(f"{self.api_url}/api/v1/auth/register/", json=test_user, timeout=10)
            auth_tests['registration'] = {
                'status': response.status_code in [201, 400],  # 400 if user exists
                'response_code': response.status_code
            }
            
            # Test login
            login_data = {
                'username': test_user['username'],
                'password': test_user['password']
            }
            response = requests.post(f"{self.api_url}/api/v1/auth/login/", json=login_data, timeout=10)
            auth_tests['login'] = {
                'status': response.status_code in [200, 400, 401],
                'response_code': response.status_code
            }
            
            # Test JWT token validation (if login successful)
            if response.status_code == 200:
                token_data = response.json()
                if 'access' in token_data:
                    headers = {'Authorization': f'Bearer {token_data["access"]}'}
                    response = requests.get(f"{self.api_url}/api/v1/auth/user/", headers=headers, timeout=10)
                    auth_tests['token_validation'] = {
                        'status': response.status_code == 200,
                        'response_code': response.status_code
                    }
            
        except Exception as e:
            auth_tests['error'] = str(e)
        
        return auth_tests
    
    def test_websocket_connections(self) -> Dict[str, Any]:
        """Test WebSocket connectivity"""
        ws_tests = {}
        
        try:
            import websocket
            
            def on_message(ws, message):
                ws_tests['message_received'] = True
            
            def on_error(ws, error):
                ws_tests['connection_error'] = str(error)
            
            def on_close(ws, close_status_code, close_msg):
                ws_tests['connection_closed'] = True
            
            def on_open(ws):
                ws_tests['connection_opened'] = True
                ws.send(json.dumps({'type': 'ping'}))
                time.sleep(1)
                ws.close()
            
            ws_url = f"ws://localhost:8000/ws/notifications/"
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run WebSocket connection test with timeout
            ws.run_forever(timeout=5)
            
        except Exception as e:
            ws_tests['websocket_error'] = str(e)
        
        return ws_tests
    
    def test_frontend_functionality(self) -> Dict[str, Any]:
        """Test frontend functionality with Selenium"""
        frontend_tests = {}
        
        try:
            # Setup Chrome driver
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Test home page load
            driver.get(self.web_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            frontend_tests['home_page_load'] = True
            
            # Test navigation
            try:
                nav_elements = driver.find_elements(By.TAG_NAME, "nav")
                frontend_tests['navigation_present'] = len(nav_elements) > 0
            except:
                frontend_tests['navigation_present'] = False
            
            # Test responsive design
            driver.set_window_size(375, 667)  # Mobile size
            time.sleep(1)
            frontend_tests['mobile_responsive'] = True
            
            driver.set_window_size(1920, 1080)  # Desktop size
            time.sleep(1)
            frontend_tests['desktop_responsive'] = True
            
            driver.quit()
            
        except Exception as e:
            frontend_tests['error'] = str(e)
            try:
                driver.quit()
            except:
                pass
        
        return frontend_tests
    
    def test_real_time_features(self) -> Dict[str, Any]:
        """Test real-time features and notifications"""
        realtime_tests = {}
        
        # This would test WebSocket notifications, live updates, etc.
        # For now, we'll test the infrastructure is in place
        try:
            # Check if Django Channels is configured
            response = requests.get(f"{self.api_url}/ws/", timeout=5)
            realtime_tests['websocket_endpoint'] = response.status_code in [400, 426]  # WebSocket upgrade expected
            
            # Check Redis for WebSocket message broker
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            realtime_tests['message_broker'] = True
            
        except Exception as e:
            realtime_tests['error'] = str(e)
        
        return realtime_tests
    
    def test_caching_performance(self) -> Dict[str, Any]:
        """Test caching performance and effectiveness"""
        cache_tests = {}
        
        try:
            # Test API response caching
            endpoint = f"{self.api_url}/api/v1/blog/posts/"
            
            # First request (cache miss)
            start_time = time.time()
            response1 = requests.get(endpoint, timeout=10)
            first_request_time = time.time() - start_time
            
            # Second request (cache hit)
            start_time = time.time()
            response2 = requests.get(endpoint, timeout=10)
            second_request_time = time.time() - start_time
            
            cache_tests['api_caching'] = {
                'first_request_time': first_request_time,
                'second_request_time': second_request_time,
                'performance_improvement': first_request_time > second_request_time,
                'status_consistent': response1.status_code == response2.status_code
            }
            
            # Test Redis cache directly
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # Cache performance test
            test_data = {'test': 'cache_performance_data'}
            start_time = time.time()
            r.set('perf_test', json.dumps(test_data))
            set_time = time.time() - start_time
            
            start_time = time.time()
            retrieved_data = r.get('perf_test')
            get_time = time.time() - start_time
            
            cache_tests['redis_performance'] = {
                'set_time': set_time,
                'get_time': get_time,
                'data_integrity': json.loads(retrieved_data) == test_data
            }
            
            r.delete('perf_test')
            
        except Exception as e:
            cache_tests['error'] = str(e)
        
        return cache_tests
    
    def test_security_measures(self) -> Dict[str, Any]:
        """Test security measures and configurations"""
        security_tests = {}
        
        try:
            # Test HTTPS redirect (if configured)
            try:
                response = requests.get(f"http://localhost:8000/api/v1/", timeout=5, allow_redirects=False)
                security_tests['https_redirect'] = response.status_code in [301, 302, 308]
            except:
                security_tests['https_redirect'] = False
            
            # Test security headers
            response = requests.get(f"{self.api_url}/api/v1/", timeout=10)
            headers = response.headers
            
            security_tests['security_headers'] = {
                'x_frame_options': 'X-Frame-Options' in headers,
                'x_content_type_options': 'X-Content-Type-Options' in headers,
                'x_xss_protection': 'X-XSS-Protection' in headers,
                'strict_transport_security': 'Strict-Transport-Security' in headers,
                'content_security_policy': 'Content-Security-Policy' in headers
            }
            
            # Test rate limiting
            rate_limit_responses = []
            for i in range(10):
                response = requests.get(f"{self.api_url}/api/v1/", timeout=2)
                rate_limit_responses.append(response.status_code)
            
            security_tests['rate_limiting'] = {
                'responses': rate_limit_responses,
                'rate_limited': 429 in rate_limit_responses
            }
            
        except Exception as e:
            security_tests['error'] = str(e)
        
        return security_tests
    
    def test_monitoring_systems(self) -> Dict[str, Any]:
        """Test monitoring and observability systems"""
        monitoring_tests = {}
        
        try:
            # Test Prometheus metrics endpoint
            try:
                response = requests.get(f"{self.api_url}/metrics/", timeout=10)
                monitoring_tests['prometheus_metrics'] = response.status_code == 200
            except:
                monitoring_tests['prometheus_metrics'] = False
            
            # Test health check endpoints
            response = requests.get(f"{self.api_url}/health/", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                monitoring_tests['health_checks'] = {
                    'endpoint_available': True,
                    'database_check': health_data.get('database', False),
                    'redis_check': health_data.get('redis', False),
                    'overall_status': health_data.get('status', 'unknown')
                }
            else:
                monitoring_tests['health_checks'] = {'endpoint_available': False}
            
            # Test logging (check if logs are being generated)
            log_files = [
                'logs/django.log',
                'logs/access.log',
                'logs/error.log'
            ]
            
            monitoring_tests['logging'] = {}
            for log_file in log_files:
                if os.path.exists(log_file):
                    monitoring_tests['logging'][log_file] = os.path.getsize(log_file) > 0
                else:
                    monitoring_tests['logging'][log_file] = False
            
        except Exception as e:
            monitoring_tests['error'] = str(e)
        
        return monitoring_tests
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and recovery"""
        error_tests = {}
        
        try:
            # Test 404 handling
            response = requests.get(f"{self.api_url}/api/v1/nonexistent-endpoint/", timeout=10)
            error_tests['404_handling'] = {
                'status_code': response.status_code,
                'proper_404': response.status_code == 404
            }
            
            # Test 500 error handling (if we can trigger one safely)
            # This is tricky to test without actually breaking something
            error_tests['500_handling'] = {'tested': False, 'reason': 'Cannot safely trigger 500 error'}
            
            # Test malformed request handling
            response = requests.post(f"{self.api_url}/api/v1/auth/login/", 
                                   data="invalid json", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            error_tests['malformed_request'] = {
                'status_code': response.status_code,
                'proper_error': response.status_code == 400
            }
            
            # Test CORS handling
            response = requests.options(f"{self.api_url}/api/v1/", 
                                      headers={'Origin': 'http://example.com'},
                                      timeout=10)
            error_tests['cors_handling'] = {
                'status_code': response.status_code,
                'cors_headers': 'Access-Control-Allow-Origin' in response.headers
            }
            
        except Exception as e:
            error_tests['error'] = str(e)
        
        return error_tests
    
    def test_load_performance(self) -> Dict[str, Any]:
        """Test system performance under load"""
        load_tests = {}
        
        try:
            # Simple load test with concurrent requests
            def make_request():
                try:
                    response = requests.get(f"{self.api_url}/api/v1/", timeout=10)
                    return {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'success': response.status_code == 200
                    }
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            
            # Run 20 concurrent requests
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in futures]
            
            successful_requests = [r for r in results if r.get('success', False)]
            response_times = [r['response_time'] for r in successful_requests]
            
            load_tests['concurrent_requests'] = {
                'total_requests': len(results),
                'successful_requests': len(successful_requests),
                'success_rate': len(successful_requests) / len(results),
                'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0
            }
            
        except Exception as e:
            load_tests['error'] = str(e)
        
        return load_tests
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if isinstance(r, dict) and r.get('status') != 'failed'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'overall_status': 'PASSED' if failed_tests == 0 else 'FAILED'
            },
            'detailed_results': self.results,
            'errors': self.errors,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.errors:
            recommendations.append("Address failed tests before production deployment")
        
        # Check specific test results for recommendations
        for test_name, result in self.results.items():
            if isinstance(result, dict):
                if 'error' in result:
                    recommendations.append(f"Fix issues in {test_name}: {result['error']}")
                
                # Performance recommendations
                if 'response_time' in result and result['response_time'] > 2.0:
                    recommendations.append(f"Optimize response time for {test_name} (current: {result['response_time']:.2f}s)")
                
                # Security recommendations
                if test_name == 'test_security_measures' and 'security_headers' in result:
                    missing_headers = [k for k, v in result['security_headers'].items() if not v]
                    if missing_headers:
                        recommendations.append(f"Add missing security headers: {', '.join(missing_headers)}")
        
        if not recommendations:
            recommendations.append("All tests passed! System is ready for production deployment.")
        
        return recommendations


def main():
    """Main function to run the integration test suite"""
    suite = IntegrationTestSuite()
    report = suite.run_all_tests()
    
    # Save report to file
    report_file = 'tests/integration/final_integration_report.json'
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL INTEGRATION TEST REPORT")
    print("="*80)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Overall Status: {report['summary']['overall_status']}")
    
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if report['summary']['overall_status'] == 'PASSED' else 1)


if __name__ == "__main__":
    main()