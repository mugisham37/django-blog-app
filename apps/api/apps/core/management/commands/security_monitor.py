"""
Management command for security monitoring and dashboard.
"""

import json
from django.core.management.base import BaseCommand
from apps.core.security_monitoring import security_monitor
from apps.core.security_headers import get_security_headers_status


class Command(BaseCommand):
    """Management command for security monitoring operations."""
    
    help = 'Security monitoring and dashboard operations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['dashboard', 'alerts', 'status', 'test-alert'],
            help='Action to perform'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'text'],
            default='text',
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file for results'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        output_format = options['format']
        output_file = options.get('output')
        
        if action == 'dashboard':
            self._show_dashboard(output_format, output_file)
        elif action == 'alerts':
            self._show_alerts(output_format, output_file)
        elif action == 'status':
            self._show_status(output_format, output_file)
        elif action == 'test-alert':
            self._test_alert()
    
    def _show_dashboard(self, output_format, output_file):
        """Show security dashboard."""
        
        self.stdout.write("Fetching security dashboard data...")
        
        dashboard_data = security_monitor.get_security_dashboard_data()
        
        if output_format == 'json':
            output = json.dumps(dashboard_data, indent=2, default=str)
        else:
            output = self._format_dashboard_text(dashboard_data)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            self.stdout.write(f"Dashboard data saved to {output_file}")
        else:
            self.stdout.write(output)
    
    def _show_alerts(self, output_format, output_file):
        """Show recent security alerts."""
        
        dashboard_data = security_monitor.get_security_dashboard_data()
        alerts = dashboard_data.get('recent_alerts', [])
        
        if output_format == 'json':
            output = json.dumps(alerts, indent=2, default=str)
        else:
            output = self._format_alerts_text(alerts)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            self.stdout.write(f"Alerts data saved to {output_file}")
        else:
            self.stdout.write(output)
    
    def _show_status(self, output_format, output_file):
        """Show security status."""
        
        # Get security monitoring status
        dashboard_data = security_monitor.get_security_dashboard_data()
        
        # Get security headers status
        headers_status = get_security_headers_status()
        
        status_data = {
            'threat_level': dashboard_data.get('threat_level', 'unknown'),
            'recent_events': dashboard_data.get('statistics', {}),
            'security_headers': headers_status,
            'recommendations': dashboard_data.get('recommendations', [])
        }
        
        if output_format == 'json':
            output = json.dumps(status_data, indent=2, default=str)
        else:
            output = self._format_status_text(status_data)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            self.stdout.write(f"Status data saved to {output_file}")
        else:
            self.stdout.write(output)
    
    def _test_alert(self):
        """Test security alert system."""
        
        self.stdout.write("Testing security alert system...")
        
        # Create a test security event
        from apps.core.security_monitoring import log_security_event
        
        log_security_event(
            'test_alert',
            'Test security alert from management command',
            '127.0.0.1',
            metadata={'test': True, 'source': 'management_command'}
        )
        
        self.stdout.write(
            self.style.SUCCESS("Test security event logged successfully")
        )
    
    def _format_dashboard_text(self, data):
        """Format dashboard data as text."""
        
        lines = []
        lines.append("SECURITY DASHBOARD")
        lines.append("=" * 50)
        
        # Threat level
        threat_level = data.get('threat_level', 'unknown').upper()
        if threat_level == 'CRITICAL':
            threat_style = 'CRITICAL THREAT LEVEL'
        elif threat_level == 'HIGH':
            threat_style = 'HIGH THREAT LEVEL'
        elif threat_level == 'MEDIUM':
            threat_style = 'MEDIUM THREAT LEVEL'
        else:
            threat_style = 'LOW THREAT LEVEL'
        
        lines.append(f"Current Threat Level: {threat_style}")
        lines.append("")
        
        # Statistics
        stats = data.get('statistics', {})
        lines.append("SECURITY STATISTICS:")
        lines.append(f"  Total Security Events: {stats.get('total_security_events', 0)}")
        lines.append(f"  Events Last Hour: {stats.get('events_last_hour', 0)}")
        lines.append(f"  Events Last Day: {stats.get('events_last_day', 0)}")
        lines.append(f"  Events Last Week: {stats.get('events_last_week', 0)}")
        lines.append(f"  Blocked IPs: {stats.get('blocked_ips', 0)}")
        lines.append("")
        
        # Recent alerts
        alerts = data.get('recent_alerts', [])
        if alerts:
            lines.append("RECENT ALERTS (Last 5):")
            for alert in alerts[:5]:
                severity = alert.get('severity', 'unknown').upper()
                title = alert.get('title', 'Unknown Alert')
                timestamp = alert.get('timestamp', 'Unknown Time')
                lines.append(f"  [{severity}] {title} - {timestamp}")
        else:
            lines.append("No recent alerts")
        
        lines.append("")
        
        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            lines.append("SECURITY RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)
    
    def _format_alerts_text(self, alerts):
        """Format alerts data as text."""
        
        lines = []
        lines.append("SECURITY ALERTS")
        lines.append("=" * 40)
        
        if not alerts:
            lines.append("No security alerts found")
            return "\n".join(lines)
        
        for alert in alerts:
            lines.append(f"Alert ID: {alert.get('alert_type', 'unknown')}")
            lines.append(f"Severity: {alert.get('severity', 'unknown').upper()}")
            lines.append(f"Title: {alert.get('title', 'Unknown')}")
            lines.append(f"Description: {alert.get('description', 'No description')}")
            lines.append(f"Source IP: {alert.get('source_ip', 'Unknown')}")
            lines.append(f"Timestamp: {alert.get('timestamp', 'Unknown')}")
            
            metadata = alert.get('metadata', {})
            if metadata:
                lines.append("Metadata:")
                for key, value in metadata.items():
                    lines.append(f"  {key}: {value}")
            
            lines.append("-" * 40)
        
        return "\n".join(lines)
    
    def _format_status_text(self, data):
        """Format status data as text."""
        
        lines = []
        lines.append("SECURITY STATUS")
        lines.append("=" * 40)
        
        # Threat level
        threat_level = data.get('threat_level', 'unknown').upper()
        lines.append(f"Current Threat Level: {threat_level}")
        lines.append("")
        
        # Security headers status
        headers = data.get('security_headers', {})
        lines.append("SECURITY HEADERS STATUS:")
        lines.append(f"  Score: {headers.get('score', 0)}/100")
        lines.append(f"  Grade: {headers.get('grade', 'F')}")
        
        issues = headers.get('issues', [])
        if issues:
            lines.append("  Issues:")
            for issue in issues[:5]:  # Show top 5 issues
                lines.append(f"    - {issue}")
        
        lines.append("")
        
        # Recent events
        events = data.get('recent_events', {})
        lines.append("RECENT SECURITY EVENTS:")
        lines.append(f"  Last Hour: {events.get('events_last_hour', 0)}")
        lines.append(f"  Last Day: {events.get('events_last_day', 0)}")
        lines.append(f"  Blocked IPs: {events.get('blocked_ips', 0)}")
        lines.append("")
        
        # Recommendations
        recommendations = data.get('recommendations', [])
        if recommendations:
            lines.append("RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)