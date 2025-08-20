"""
Management command to run comprehensive security scans.
"""

import json
from django.core.management.base import BaseCommand
from apps.core.security_scanner import SecurityScanner


class Command(BaseCommand):
    """Management command to run security vulnerability scan."""
    
    help = 'Run comprehensive security vulnerability scan'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Base URL to scan (default: http://localhost:8000)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for results (JSON format)'
        )
        parser.add_argument(
            '--severity',
            type=str,
            choices=['low', 'medium', 'high', 'critical'],
            default='low',
            help='Minimum severity level to report (default: low)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'text'],
            default='text',
            help='Output format (default: text)'
        )
    
    def handle(self, *args, **options):
        base_url = options['base_url']
        output_file = options.get('output')
        min_severity = options['severity']
        output_format = options['format']
        
        self.stdout.write(
            self.style.SUCCESS(f"Starting security scan of {base_url}")
        )
        
        # Run the scan
        scanner = SecurityScanner(base_url)
        results = scanner.run_full_scan()
        
        # Filter by severity if specified
        if min_severity != 'low':
            severity_order = ['low', 'medium', 'high', 'critical']
            min_index = severity_order.index(min_severity)
            
            filtered_vulns = [
                v for v in results['vulnerabilities']
                if severity_order.index(v['severity']) >= min_index
            ]
            results['vulnerabilities'] = filtered_vulns
            results['vulnerabilities_found'] = len(filtered_vulns)
            
            # Update severity counts
            for severity in results['severity_counts']:
                results['severity_counts'][severity] = sum(
                    1 for v in filtered_vulns if v['severity'] == severity
                )
        
        # Output results
        if output_file:
            with open(output_file, 'w') as f:
                if output_format == 'json':
                    json.dump(results, f, indent=2, default=str)
                else:
                    from apps.core.security_scanner import get_vulnerability_report
                    f.write(get_vulnerability_report(results))
            
            self.stdout.write(
                self.style.SUCCESS(f"Results saved to {output_file}")
            )
        
        # Print summary to console
        self._print_summary(results)
        
        # Exit with error code if critical vulnerabilities found
        critical_count = results['severity_counts']['critical']
        high_count = results['severity_counts']['high']
        
        if critical_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"CRITICAL: {critical_count} critical vulnerabilities found!"
                )
            )
            exit(2)
        elif high_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"WARNING: {high_count} high severity vulnerabilities found!"
                )
            )
            exit(1)
        else:
            self.stdout.write(
                self.style.SUCCESS("No critical or high severity vulnerabilities found.")
            )
    
    def _print_summary(self, results):
        """Print scan summary to console."""
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SECURITY SCAN SUMMARY")
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"Scan ID: {results['scan_id']}")
        self.stdout.write(f"Target: {results['base_url']}")
        self.stdout.write(f"Duration: {results['duration']:.2f} seconds")
        self.stdout.write(f"Tests Run: {len(results['tests_run'])}")
        self.stdout.write(f"Total Vulnerabilities: {results['vulnerabilities_found']}")
        
        self.stdout.write("\nSEVERITY BREAKDOWN:")
        for severity in ['critical', 'high', 'medium', 'low']:
            count = results['severity_counts'][severity]
            if count > 0:
                if severity == 'critical':
                    style = self.style.ERROR
                elif severity == 'high':
                    style = self.style.WARNING
                else:
                    style = self.style.NOTICE
                
                self.stdout.write(style(f"  {severity.capitalize()}: {count}"))
        
        if results['vulnerabilities']:
            self.stdout.write("\nTOP VULNERABILITIES:")
            
            # Sort by severity and show top 5
            severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            sorted_vulns = sorted(
                results['vulnerabilities'],
                key=lambda v: severity_order.get(v['severity'], 0),
                reverse=True
            )
            
            for vuln in sorted_vulns[:5]:
                severity_style = self.style.ERROR if vuln['severity'] in ['critical', 'high'] else self.style.WARNING
                self.stdout.write(
                    severity_style(f"  [{vuln['severity'].upper()}] {vuln['title']}")
                )
                self.stdout.write(f"    Component: {vuln['affected_component']}")
                self.stdout.write(f"    Description: {vuln['description'][:100]}...")
        
        self.stdout.write("\n" + "=" * 60)