#!/usr/bin/env python3
"""
Load Testing and Performance Optimization Suite
Comprehensive performance testing for the entire system
"""

import asyncio
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import requests
import psutil
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass


@dataclass
class LoadTestResult:
    """Data class for load test results"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]


class LoadTestSuite:
    """Comprehensive load testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        
    def run_load_test(self, endpoint: str, num_requests: int = 100, 
                     concurrent_users: int = 10, duration: int = None) -> LoadTestResult:
        """Run load test on specific endpoint"""
        print(f"🔥 Load testing {endpoint} with {num_requests} requests, {concurrent_users} concurrent users")
        
        start_time = time.time()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        def make_request():
            try:
                request_start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                request_time = time.time() - request_start
                
                if response.status_code == 200:
                    return {'success': True, 'response_time': request_time}
                else:
                    return {'success': False, 'response_time': request_time, 
                           'error': f"HTTP {response.status_code}"}
            except Exception as e:
                request_time = time.time() - request_start
                return {'success': False, 'response_time': request_time, 'error': str(e)}
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                response_times.append(result['response_time'])
                
                if result['success']:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    errors.append(result.get('error', 'Unknown error'))
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0
        
        requests_per_second = num_requests / total_time if total_time > 0 else 0
        error_rate = (failed_requests / num_requests) * 100 if num_requests > 0 else 0
        
        return LoadTestResult(
            endpoint=endpoint,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=list(set(errors))  # Remove duplicates
        )
    
    def run_comprehensive_load_tests(self) -> Dict[str, LoadTestResult]:
        """Run load tests on all critical endpoints"""
        endpoints = [
            '/api/v1/',
            '/api/v1/health/',
            '/api/v1/blog/posts/',
            '/api/v1/auth/login/',
            '/api/v1/users/',
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                result = self.run_load_test(endpoint, num_requests=50, concurrent_users=5)
                results[endpoint] = result
                print(f"✅ {endpoint}: {result.requests_per_second:.2f} RPS, "
                      f"{result.average_response_time:.3f}s avg response time")
            except Exception as e:
                print(f"❌ Failed to test {endpoint}: {e}")
        
        return results
    
    def run_stress_test(self, endpoint: str = '/api/v1/health/') -> Dict[str, Any]:
        """Run stress test to find breaking point"""
        print(f"🚨 Running stress test on {endpoint}")
        
        stress_results = {}
        concurrent_users = [1, 5, 10, 20, 50, 100]
        
        for users in concurrent_users:
            print(f"Testing with {users} concurrent users...")
            try:
                result = self.run_load_test(endpoint, num_requests=users*5, concurrent_users=users)
                stress_results[users] = {
                    'requests_per_second': result.requests_per_second,
                    'average_response_time': result.average_response_time,
                    'error_rate': result.error_rate,
                    'successful_requests': result.successful_requests
                }
                
                # Stop if error rate is too high
                if result.error_rate > 50:
                    print(f"⚠️ High error rate ({result.error_rate:.1f}%) at {users} users")
                    break
                    
            except Exception as e:
                print(f"❌ Stress test failed at {users} users: {e}")
                break
        
        return stress_results
    
    def monitor_system_resources(self, duration: int = 60) -> Dict[str, List[float]]:
        """Monitor system resources during load testing"""
        print(f"📊 Monitoring system resources for {duration} seconds")
        
        cpu_usage = []
        memory_usage = []
        disk_usage = []
        network_io = []
        
        start_time = time.time()
        initial_network = psutil.net_io_counters()
        
        while time.time() - start_time < duration:
            cpu_usage.append(psutil.cpu_percent(interval=1))
            memory_usage.append(psutil.virtual_memory().percent)
            disk_usage.append(psutil.disk_usage('/').percent)
            
            current_network = psutil.net_io_counters()
            network_io.append(current_network.bytes_sent + current_network.bytes_recv)
            
            time.sleep(1)
        
        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'network_io': network_io,
            'duration': duration
        }
    
    def generate_performance_report(self, results: Dict[str, LoadTestResult], 
                                  stress_results: Dict[str, Any] = None,
                                  resource_monitoring: Dict[str, List[float]] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        # Calculate overall statistics
        all_response_times = []
        all_rps = []
        all_error_rates = []
        
        for result in results.values():
            all_response_times.append(result.average_response_time)
            all_rps.append(result.requests_per_second)
            all_error_rates.append(result.error_rate)
        
        overall_stats = {
            'average_response_time': statistics.mean(all_response_times) if all_response_times else 0,
            'average_rps': statistics.mean(all_rps) if all_rps else 0,
            'average_error_rate': statistics.mean(all_error_rates) if all_error_rates else 0,
            'total_endpoints_tested': len(results)
        }
        
        # Performance recommendations
        recommendations = []
        
        for endpoint, result in results.items():
            if result.average_response_time > 2.0:
                recommendations.append(f"Optimize {endpoint} - slow response time ({result.average_response_time:.2f}s)")
            
            if result.error_rate > 5:
                recommendations.append(f"Fix errors in {endpoint} - high error rate ({result.error_rate:.1f}%)")
            
            if result.requests_per_second < 10:
                recommendations.append(f"Improve throughput for {endpoint} - low RPS ({result.requests_per_second:.1f})")
        
        # System resource recommendations
        if resource_monitoring:
            avg_cpu = statistics.mean(resource_monitoring['cpu_usage'])
            avg_memory = statistics.mean(resource_monitoring['memory_usage'])
            
            if avg_cpu > 80:
                recommendations.append(f"High CPU usage detected ({avg_cpu:.1f}%) - consider scaling")
            
            if avg_memory > 80:
                recommendations.append(f"High memory usage detected ({avg_memory:.1f}%) - check for memory leaks")
        
        if not recommendations:
            recommendations.append("Performance looks good! No immediate optimizations needed.")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_statistics': overall_stats,
            'endpoint_results': {endpoint: {
                'requests_per_second': result.requests_per_second,
                'average_response_time': result.average_response_time,
                'error_rate': result.error_rate,
                'p95_response_time': result.p95_response_time,
                'successful_requests': result.successful_requests,
                'total_requests': result.total_requests
            } for endpoint, result in results.items()},
            'stress_test_results': stress_results,
            'resource_monitoring': resource_monitoring,
            'recommendations': recommendations,
            'performance_grade': self.calculate_performance_grade(overall_stats)
        }
        
        return report
    
    def calculate_performance_grade(self, stats: Dict[str, float]) -> str:
        """Calculate overall performance grade"""
        score = 100
        
        # Deduct points for slow response times
        if stats['average_response_time'] > 1.0:
            score -= 20
        elif stats['average_response_time'] > 0.5:
            score -= 10
        
        # Deduct points for low throughput
        if stats['average_rps'] < 10:
            score -= 20
        elif stats['average_rps'] < 50:
            score -= 10
        
        # Deduct points for errors
        if stats['average_error_rate'] > 5:
            score -= 30
        elif stats['average_error_rate'] > 1:
            score -= 15
        
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def create_performance_charts(self, results: Dict[str, LoadTestResult], 
                                stress_results: Dict[str, Any] = None):
        """Create performance visualization charts"""
        
        # Response time chart
        endpoints = list(results.keys())
        response_times = [results[ep].average_response_time for ep in endpoints]
        
        plt.figure(figsize=(12, 8))
        
        # Subplot 1: Response times
        plt.subplot(2, 2, 1)
        plt.bar(range(len(endpoints)), response_times)
        plt.xlabel('Endpoints')
        plt.ylabel('Response Time (seconds)')
        plt.title('Average Response Times by Endpoint')
        plt.xticks(range(len(endpoints)), [ep.split('/')[-2] or 'root' for ep in endpoints], rotation=45)
        
        # Subplot 2: Requests per second
        rps_values = [results[ep].requests_per_second for ep in endpoints]
        plt.subplot(2, 2, 2)
        plt.bar(range(len(endpoints)), rps_values)
        plt.xlabel('Endpoints')
        plt.ylabel('Requests per Second')
        plt.title('Throughput by Endpoint')
        plt.xticks(range(len(endpoints)), [ep.split('/')[-2] or 'root' for ep in endpoints], rotation=45)
        
        # Subplot 3: Error rates
        error_rates = [results[ep].error_rate for ep in endpoints]
        plt.subplot(2, 2, 3)
        plt.bar(range(len(endpoints)), error_rates)
        plt.xlabel('Endpoints')
        plt.ylabel('Error Rate (%)')
        plt.title('Error Rates by Endpoint')
        plt.xticks(range(len(endpoints)), [ep.split('/')[-2] or 'root' for ep in endpoints], rotation=45)
        
        # Subplot 4: Stress test results
        if stress_results:
            plt.subplot(2, 2, 4)
            users = list(stress_results.keys())
            rps_stress = [stress_results[u]['requests_per_second'] for u in users]
            plt.plot(users, rps_stress, marker='o')
            plt.xlabel('Concurrent Users')
            plt.ylabel('Requests per Second')
            plt.title('Stress Test: RPS vs Concurrent Users')
        
        plt.tight_layout()
        plt.savefig('tests/performance/performance_charts.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("📊 Performance charts saved to tests/performance/performance_charts.png")


def main():
    """Main function to run performance testing"""
    print("🚀 Starting Performance Testing Suite...")
    
    suite = LoadTestSuite()
    
    # Run comprehensive load tests
    print("\n1. Running comprehensive load tests...")
    load_results = suite.run_comprehensive_load_tests()
    
    # Run stress test
    print("\n2. Running stress test...")
    stress_results = suite.run_stress_test()
    
    # Monitor system resources
    print("\n3. Monitoring system resources...")
    resource_monitoring = suite.monitor_system_resources(duration=30)
    
    # Generate report
    print("\n4. Generating performance report...")
    report = suite.generate_performance_report(load_results, stress_results, resource_monitoring)
    
    # Save report
    import os
    os.makedirs('tests/performance', exist_ok=True)
    
    with open('tests/performance/performance_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Create charts
    suite.create_performance_charts(load_results, stress_results)
    
    # Print summary
    print("\n" + "="*80)
    print("PERFORMANCE TEST REPORT")
    print("="*80)
    print(f"Overall Performance Grade: {report['performance_grade']}")
    print(f"Average Response Time: {report['overall_statistics']['average_response_time']:.3f}s")
    print(f"Average RPS: {report['overall_statistics']['average_rps']:.1f}")
    print(f"Average Error Rate: {report['overall_statistics']['average_error_rate']:.1f}%")
    
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print(f"\nDetailed report saved to: tests/performance/performance_report.json")


if __name__ == "__main__":
    main()