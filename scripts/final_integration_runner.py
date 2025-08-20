#!/usr/bin/env python3
"""
Final Integration Test Runner
Orchestrates all final integration testing and optimization
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import concurrent.futures


class FinalIntegrationRunner:
    """Orchestrates all final integration testing"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def run_all_final_tests(self) -> Dict[str, Any]:
        """Run all final integration tests"""
        print("🚀 Starting Final Integration Testing and Optimization Suite...")
        print("="*80)
        
        # Define all test suites
        test_suites = [
            {
                'name': 'Integration Tests',
                'script': 'tests/integration/final_integration_test.py',
                'description': 'Comprehensive system integration testing'
            },
            {
                'name': 'Performance Tests',
                'script': 'tests/performance/load_testing.py',
                'description': 'Load testing and performance optimization'
            },
            {
                'name': 'Security Tests',
                'script': 'tests/security/security_testing.py',
                'description': 'Security vulnerability assessment'
            },
            {
                'name': 'E2E Tests',
                'script': 'tests/e2e/comprehensive_e2e_test.py',
                'description': 'End-to-end user journey testing'
            },
            {
                'name': 'Database Optimization',
                'script': 'tests/optimization/database_optimization.py',
                'description': 'Database performance optimization'
            }
        ]
        
        # Run test suites
        for suite in test_suites:
            print(f"\n🔄 Running {suite['name']}...")
            print(f"   {suite['description']}")
            
            try:
                result = self.run_test_suite(suite)
                self.test_results[suite['name']] = result
                
                if result['status'] == 'passed':
                    print(f"✅ {suite['name']} completed successfully")
                else:
                    print(f"❌ {suite['name']} completed with issues")
                    
            except Exception as e:
                print(f"💥 {suite['name']} failed to run: {e}")
                self.test_results[suite['name']] = {
                    'status': 'failed',
                    'error': str(e),
                    'execution_time': 0
                }
        
        # Generate final comprehensive report
        final_report = self.generate_final_report()
        
        # Save final report
        self.save_final_report(final_report)
        
        # Print final summary
        self.print_final_summary(final_report)
        
        return final_report
    
    def run_test_suite(self, suite: Dict[str, str]) -> Dict[str, Any]:
        """Run individual test suite"""
        start_time = time.time()
        
        try:
            # Check if script exists
            if not os.path.exists(suite['script']):
                return {
                    'status': 'failed',
                    'error': f"Test script not found: {suite['script']}",
                    'execution_time': 0
                }
            
            # Run the test script
            result = subprocess.run([
                sys.executable, suite['script']
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            execution_time = time.time() - start_time
            
            # Parse result
            if result.returncode == 0:
                status = 'passed'
                error = None
            else:
                status = 'failed'
                error = result.stderr or "Test suite failed"
            
            return {
                'status': status,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'error': error
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'failed',
                'error': 'Test suite timed out (5 minutes)',
                'execution_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        total_execution_time = time.time() - self.start_time
        
        # Calculate overall statistics
        total_suites = len(self.test_results)
        passed_suites = len([r for r in self.test_results.values() if r['status'] == 'passed'])
        failed_suites = total_suites - passed_suites
        
        # Load individual test reports if available
        individual_reports = {}
        report_files = [
            ('integration', 'tests/integration/final_integration_report.json'),
            ('performance', 'tests/performance/performance_report.json'),
            ('security', 'tests/security/security_report.json'),
            ('e2e', 'tests/e2e/e2e_report.json'),
            ('database', 'tests/optimization/database_optimization_report.json')
        ]
        
        for report_name, report_file in report_files:
            if os.path.exists(report_file):
                try:
                    with open(report_file, 'r') as f:
                        individual_reports[report_name] = json.load(f)
                except Exception as e:
                    individual_reports[report_name] = {'error': f'Could not load report: {e}'}
        
        # Collect all recommendations
        all_recommendations = []
        critical_issues = []
        
        for report_name, report_data in individual_reports.items():
            if isinstance(report_data, dict):
                # Collect recommendations
                if 'recommendations' in report_data:
                    all_recommendations.extend(report_data['recommendations'])
                
                # Collect critical issues
                if 'critical_issues' in report_data:
                    critical_issues.extend(report_data['critical_issues'])
                
                # Check for high-severity security issues
                if 'results_by_severity' in report_data:
                    critical_security = report_data['results_by_severity'].get('critical', [])
                    high_security = report_data['results_by_severity'].get('high', [])
                    critical_issues.extend(critical_security + high_security)
        
        # Remove duplicate recommendations
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        # Calculate overall system health score
        health_score = self.calculate_system_health_score(individual_reports)
        
        # Generate deployment readiness assessment
        deployment_ready = self.assess_deployment_readiness(individual_reports, critical_issues)
        
        final_report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_execution_time': total_execution_time,
            'summary': {
                'total_test_suites': total_suites,
                'passed_suites': passed_suites,
                'failed_suites': failed_suites,
                'success_rate': (passed_suites / total_suites) * 100 if total_suites > 0 else 0,
                'overall_status': 'PASSED' if failed_suites == 0 else 'FAILED',
                'system_health_score': health_score,
                'deployment_ready': deployment_ready
            },
            'test_suite_results': self.test_results,
            'individual_reports': individual_reports,
            'critical_issues': critical_issues,
            'all_recommendations': unique_recommendations,
            'deployment_assessment': self.generate_deployment_assessment(individual_reports, critical_issues),
            'next_steps': self.generate_next_steps(deployment_ready, critical_issues, unique_recommendations)
        }
        
        return final_report
    
    def calculate_system_health_score(self, reports: Dict[str, Any]) -> float:
        """Calculate overall system health score"""
        scores = []
        
        # Integration test score
        if 'integration' in reports:
            integration_report = reports['integration']
            if 'summary' in integration_report:
                success_rate = integration_report['summary'].get('success_rate', 0)
                scores.append(success_rate)
        
        # Performance score
        if 'performance' in reports:
            perf_report = reports['performance']
            if 'performance_grade' in perf_report:
                grade = perf_report['performance_grade']
                grade_scores = {'A': 95, 'B': 85, 'C': 75, 'D': 65, 'F': 50}
                scores.append(grade_scores.get(grade, 50))
        
        # Security score
        if 'security' in reports:
            security_report = reports['security']
            if 'summary' in security_report:
                security_score = security_report['summary'].get('security_score', 50)
                scores.append(security_score)
        
        # E2E score
        if 'e2e' in reports:
            e2e_report = reports['e2e']
            if 'summary' in e2e_report:
                success_rate = e2e_report['summary'].get('success_rate', 0)
                scores.append(success_rate)
        
        # Database performance score
        if 'database' in reports:
            db_report = reports['database']
            if 'summary' in db_report:
                db_score = db_report['summary'].get('overall_performance_score', 70)
                scores.append(db_score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def assess_deployment_readiness(self, reports: Dict[str, Any], critical_issues: List) -> bool:
        """Assess if system is ready for deployment"""
        
        # Check for critical security issues
        if 'security' in reports:
            security_report = reports['security']
            if 'summary' in security_report:
                critical_security = security_report['summary'].get('critical_issues', 0)
                high_security = security_report['summary'].get('high_issues', 0)
                if critical_security > 0 or high_security > 2:
                    return False
        
        # Check for critical performance issues
        if 'performance' in reports:
            perf_report = reports['performance']
            if 'performance_grade' in perf_report:
                if perf_report['performance_grade'] in ['D', 'F']:
                    return False
        
        # Check integration test success rate
        if 'integration' in reports:
            integration_report = reports['integration']
            if 'summary' in integration_report:
                success_rate = integration_report['summary'].get('success_rate', 0)
                if success_rate < 80:
                    return False
        
        # Check for any critical issues
        if len(critical_issues) > 0:
            return False
        
        return True
    
    def generate_deployment_assessment(self, reports: Dict[str, Any], critical_issues: List) -> Dict[str, Any]:
        """Generate detailed deployment assessment"""
        
        assessment = {
            'ready_for_production': self.assess_deployment_readiness(reports, critical_issues),
            'blockers': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check each area
        if 'security' in reports:
            security_report = reports['security']
            if 'summary' in security_report:
                critical_security = security_report['summary'].get('critical_issues', 0)
                high_security = security_report['summary'].get('high_issues', 0)
                
                if critical_security > 0:
                    assessment['blockers'].append(f"{critical_security} critical security issues must be fixed")
                if high_security > 2:
                    assessment['blockers'].append(f"{high_security} high-severity security issues need attention")
                elif high_security > 0:
                    assessment['warnings'].append(f"{high_security} high-severity security issues should be addressed")
        
        if 'performance' in reports:
            perf_report = reports['performance']
            if 'performance_grade' in perf_report:
                grade = perf_report['performance_grade']
                if grade in ['D', 'F']:
                    assessment['blockers'].append(f"Performance grade {grade} is too low for production")
                elif grade == 'C':
                    assessment['warnings'].append("Performance grade C - consider optimization")
        
        if 'integration' in reports:
            integration_report = reports['integration']
            if 'summary' in integration_report:
                success_rate = integration_report['summary'].get('success_rate', 0)
                if success_rate < 80:
                    assessment['blockers'].append(f"Integration test success rate {success_rate:.1f}% is too low")
                elif success_rate < 95:
                    assessment['warnings'].append(f"Integration test success rate {success_rate:.1f}% could be improved")
        
        # Generate recommendations
        if assessment['ready_for_production']:
            assessment['recommendations'] = [
                "✅ System is ready for production deployment",
                "🔄 Set up monitoring and alerting",
                "📊 Continue performance monitoring",
                "🔒 Schedule regular security assessments",
                "🧪 Implement continuous testing pipeline"
            ]
        else:
            assessment['recommendations'] = [
                "🚨 Address all blockers before deployment",
                "⚠️ Review and fix warnings",
                "🔧 Re-run tests after fixes",
                "📋 Create deployment checklist",
                "👥 Get security and performance team approval"
            ]
        
        return assessment
    
    def generate_next_steps(self, deployment_ready: bool, critical_issues: List, recommendations: List) -> List[str]:
        """Generate next steps based on test results"""
        next_steps = []
        
        if not deployment_ready:
            next_steps.extend([
                "🚨 IMMEDIATE: Address all critical issues before deployment",
                "🔧 Fix failed test suites and re-run tests",
                "👥 Get approval from security and performance teams"
            ])
        
        if critical_issues:
            next_steps.append(f"⚠️ HIGH PRIORITY: Resolve {len(critical_issues)} critical issues")
        
        # Add top recommendations
        if recommendations:
            next_steps.extend(recommendations[:3])
        
        # Always include these
        next_steps.extend([
            "📊 Set up production monitoring and alerting",
            "🔄 Implement automated testing pipeline",
            "📚 Update documentation and runbooks",
            "🎓 Train team on new system architecture",
            "📅 Schedule regular system health checks"
        ])
        
        return next_steps
    
    def save_final_report(self, report: Dict[str, Any]):
        """Save final comprehensive report"""
        os.makedirs('tests/final', exist_ok=True)
        
        # Save main report
        with open('tests/final/final_integration_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save summary report
        summary = {
            'timestamp': report['timestamp'],
            'system_health_score': report['summary']['system_health_score'],
            'deployment_ready': report['summary']['deployment_ready'],
            'overall_status': report['summary']['overall_status'],
            'critical_issues_count': len(report['critical_issues']),
            'recommendations_count': len(report['all_recommendations']),
            'deployment_assessment': report['deployment_assessment']
        }
        
        with open('tests/final/deployment_readiness_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
    
    def print_final_summary(self, report: Dict[str, Any]):
        """Print final summary to console"""
        print("\n" + "="*80)
        print("🎯 FINAL INTEGRATION TESTING COMPLETE")
        print("="*80)
        
        summary = report['summary']
        print(f"System Health Score: {summary['system_health_score']:.1f}/100")
        print(f"Test Suites: {summary['passed_suites']}/{summary['total_test_suites']} passed")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Deployment Ready: {'✅ YES' if summary['deployment_ready'] else '❌ NO'}")
        
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues: {len(report['critical_issues'])}")
            for issue in report['critical_issues'][:3]:  # Show first 3
                if isinstance(issue, dict):
                    print(f"   • {issue.get('description', str(issue))}")
                else:
                    print(f"   • {issue}")
        
        print(f"\n📋 Next Steps:")
        for i, step in enumerate(report['next_steps'][:5], 1):  # Show first 5
            print(f"   {i}. {step}")
        
        print(f"\n📊 Detailed reports saved to:")
        print(f"   • tests/final/final_integration_report.json")
        print(f"   • tests/final/deployment_readiness_summary.json")
        
        print(f"\n⏱️ Total execution time: {report['total_execution_time']:.1f} seconds")
        print("="*80)


def main():
    """Main function"""
    runner = FinalIntegrationRunner()
    final_report = runner.run_all_final_tests()
    
    # Exit with appropriate code
    exit_code = 0 if final_report['summary']['deployment_ready'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()