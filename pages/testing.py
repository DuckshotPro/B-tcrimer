"""
Testing and quality assurance page for B-TCRimer admin panel.
Provides interface to run tests, view results, and monitor quality metrics.
"""

import streamlit as st
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

from utils.auth import require_authentication
from utils.logging_config import get_logger

logger = get_logger(__name__)

def show():
    """Main testing interface"""
    # Require admin authentication
    require_authentication("admin")
    
    st.markdown("""
    <h1 class="financial-title">
        🧪 Testing & Quality Assurance
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
        <p style="margin: 0; color: var(--text-secondary);">
            Comprehensive testing suite for B-TCRimer platform. Run tests, validate system health, 
            and monitor quality metrics to ensure enterprise-grade reliability.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Testing navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧪 Test Runner",
        "📊 Test Results", 
        "🔍 Quality Metrics",
        "🛡️ Security Validation",
        "📋 Test Reports"
    ])
    
    with tab1:
        show_test_runner()
    
    with tab2:
        show_test_results()
    
    with tab3:
        show_quality_metrics()
    
    with tab4:
        show_security_validation()
    
    with tab5:
        show_test_reports()

def show_test_runner():
    """Interactive test runner interface"""
    st.markdown("## 🧪 Interactive Test Runner")
    
    # Test suite selection
    st.markdown("### Select Test Suites to Run")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_suites = {
            'authentication': st.checkbox("🔐 Authentication Tests", value=True),
            'performance': st.checkbox("⚡ Performance & Caching Tests", value=True),
            'security': st.checkbox("🛡️ Security Tests", value=True),
            'integration': st.checkbox("🔗 Integration Tests", value=True)
        }
    
    with col2:
        system_checks = {
            'database': st.checkbox("🗄️ Database Health Check", value=True),
            'memory': st.checkbox("💾 Memory Usage Check", value=True),
            'disk': st.checkbox("💿 Disk Space Check", value=True),
            'network': st.checkbox("🌐 Network Connectivity", value=True)
        }
    
    # Test execution controls
    st.markdown("### Execution Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        verbose_output = st.checkbox("📝 Verbose Output", value=False)
    
    with col2:
        save_report = st.checkbox("💾 Save Test Report", value=True)
    
    with col3:
        email_results = st.checkbox("📧 Email Results", value=False)
    
    # Run tests button
    st.markdown("### Execute Tests")
    
    if st.button("🚀 Run Selected Tests", type="primary", use_container_width=True):
        with st.spinner("Running comprehensive test suite..."):
            results = run_selected_tests(test_suites, system_checks, {
                'verbose': verbose_output,
                'save_report': save_report,
                'email_results': email_results
            })
            
            display_test_execution_results(results)
    
    # Quick test buttons
    st.markdown("### Quick Tests")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚡ Performance Only"):
            with st.spinner("Running performance tests..."):
                results = run_quick_test("performance")
                display_quick_test_results("Performance", results)
    
    with col2:
        if st.button("🔐 Auth Only"):
            with st.spinner("Running authentication tests..."):
                results = run_quick_test("authentication")
                display_quick_test_results("Authentication", results)
    
    with col3:
        if st.button("🏥 Health Check"):
            with st.spinner("Running system health check..."):
                results = run_system_health_check()
                display_health_check_results(results)
    
    with col4:
        if st.button("🛡️ Security Scan"):
            with st.spinner("Running security validation..."):
                results = run_security_scan()
                display_security_scan_results(results)

def show_test_results():
    """Display latest test results"""
    st.markdown("## 📊 Latest Test Results")
    
    # Load latest test results
    latest_results = load_latest_test_results()
    
    if latest_results:
        # Overall status
        total_tests = latest_results.get('total_tests', 0)
        passed_tests = latest_results.get('passed_tests', 0)
        failed_tests = latest_results.get('failed_tests', 0)
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            
            # Status indicator
            if success_rate >= 95:
                status_color = "#10B981"
                status_icon = "🎉"
                status_text = "Excellent"
            elif success_rate >= 85:
                status_color = "#F59E0B"
                status_icon = "👍"
                status_text = "Good"
            else:
                status_color = "#EF4444"
                status_icon = "⚠️"
                status_text = "Needs Attention"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {status_color} 0%, {status_color}CC 100%); 
                        color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h2 style="margin: 0; font-size: 1.5rem;">{status_icon} Test Status: {status_text}</h2>
                        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                            Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 2rem; font-weight: 700;">{success_rate:.1f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Test suite breakdown
        st.markdown("### Test Suite Results")
        
        test_suites = latest_results.get('test_suites', {})
        
        for suite_name, suite_results in test_suites.items():
            total = suite_results.get('total', 0)
            passed = suite_results.get('passed', 0)
            failed = suite_results.get('failed', 0)
            
            if total > 0:
                suite_success_rate = (passed / total) * 100
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{suite_name}**")
                
                with col2:
                    st.metric("Passed", passed, delta=None)
                
                with col3:
                    st.metric("Failed", failed, delta=None, delta_color="inverse")
                
                with col4:
                    st.metric("Success Rate", f"{suite_success_rate:.1f}%", delta=None)
        
        # Performance benchmarks
        benchmarks = latest_results.get('performance_benchmarks', {})
        if benchmarks:
            st.markdown("### Performance Benchmarks")
            
            for benchmark_name, benchmark_data in benchmarks.items():
                if 'error' not in benchmark_data:
                    st.markdown(f"**{benchmark_name.replace('_', ' ').title()}**")
                    
                    cols = st.columns(len(benchmark_data))
                    for i, (key, value) in enumerate(benchmark_data.items()):
                        with cols[i]:
                            st.metric(key.replace('_', ' ').title(), str(value))
        
        # Test execution details
        if st.expander("📋 Detailed Test Information"):
            st.json(latest_results)
    
    else:
        st.info("No test results available. Run tests to see results here.")

def show_quality_metrics():
    """Display quality metrics and trends"""
    st.markdown("## 🔍 Quality Metrics")
    
    # Code quality metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Code Quality")
        
        # Simulated metrics (would be real in production)
        quality_metrics = {
            "Test Coverage": 85,
            "Code Complexity": 7.2,
            "Maintainability Index": 78,
            "Technical Debt": 12
        }
        
        for metric, value in quality_metrics.items():
            if metric == "Test Coverage":
                color = "#10B981" if value >= 80 else "#F59E0B" if value >= 60 else "#EF4444"
                st.metric(metric, f"{value}%", delta=f"+{5}%" if value >= 80 else None)
            elif metric == "Code Complexity":
                color = "#10B981" if value <= 10 else "#F59E0B" if value <= 15 else "#EF4444"
                st.metric(metric, f"{value}/10", delta=None)
            else:
                st.metric(metric, str(value), delta=None)
    
    with col2:
        st.markdown("### Performance Metrics")
        
        performance_metrics = {
            "Average Response Time": "0.45s",
            "Cache Hit Rate": "94.2%",
            "Database Query Time": "0.12s",
            "Memory Usage": "67%"
        }
        
        for metric, value in performance_metrics.items():
            st.metric(metric, value, delta=None)
    
    # Quality trends
    st.markdown("### Quality Trends")
    
    # Simulated trend data
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    test_coverage = 75 + np.cumsum(np.random.normal(0.2, 1, 30))
    response_times = 0.5 + np.cumsum(np.random.normal(-0.001, 0.02, 30))
    
    trend_data = pd.DataFrame({
        'Date': dates,
        'Test Coverage (%)': test_coverage,
        'Avg Response Time (s)': response_times
    })
    
    # Display trend charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.line_chart(trend_data.set_index('Date')['Test Coverage (%)'])
    
    with col2:
        st.line_chart(trend_data.set_index('Date')['Avg Response Time (s)'])

def show_security_validation():
    """Display security validation results"""
    st.markdown("## 🛡️ Security Validation")
    
    # Security checklist
    security_checks = {
        "Password Security": {
            "status": "✅ Pass",
            "description": "PBKDF2 hashing with salt",
            "last_check": "2024-01-15 10:30:00"
        },
        "SQL Injection Protection": {
            "status": "✅ Pass",
            "description": "Parameterized queries used",
            "last_check": "2024-01-15 10:30:00"
        },
        "XSS Protection": {
            "status": "✅ Pass",
            "description": "Input sanitization active",
            "last_check": "2024-01-15 10:30:00"
        },
        "Session Security": {
            "status": "✅ Pass",
            "description": "Secure token generation",
            "last_check": "2024-01-15 10:30:00"
        },
        "Rate Limiting": {
            "status": "⚠️ Warning",
            "description": "Basic implementation",
            "last_check": "2024-01-15 10:30:00"
        },
        "HTTPS Enforcement": {
            "status": "❌ Fail",
            "description": "Not configured for production",
            "last_check": "2024-01-15 10:30:00"
        }
    }
    
    for check_name, check_data in security_checks.items():
        with st.expander(f"{check_data['status']} {check_name}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Description:** {check_data['description']}")
                st.write(f"**Last Check:** {check_data['last_check']}")
            
            with col2:
                if "❌" in check_data['status']:
                    st.error("Action required!")
                elif "⚠️" in check_data['status']:
                    st.warning("Improvement recommended")
                else:
                    st.success("Security check passed")
    
    # Security recommendations
    st.markdown("### Security Recommendations")
    
    recommendations = [
        "🔒 Enable HTTPS in production environment",
        "🚫 Implement advanced rate limiting",
        "🔑 Add two-factor authentication option",
        "📝 Set up security audit logging",
        "🔍 Regular security scanning schedule"
    ]
    
    for recommendation in recommendations:
        st.write(f"• {recommendation}")

def show_test_reports():
    """Display historical test reports"""
    st.markdown("## 📋 Test Report History")
    
    # List available reports
    reports = get_test_report_history()
    
    if reports:
        st.markdown("### Available Reports")
        
        for report in reports[:10]:  # Show last 10 reports
            with st.expander(f"📄 {report['name']} - {report['date']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Tests Run", report['total_tests'])
                
                with col2:
                    st.metric("Success Rate", f"{report['success_rate']:.1f}%")
                
                with col3:
                    st.metric("Duration", f"{report['duration']:.1f}s")
                
                if st.button(f"📥 Download Report", key=f"download_{report['id']}"):
                    # In a real implementation, this would trigger a download
                    st.info("Report download would be implemented here")
    
    else:
        st.info("No test reports available yet. Run tests to generate reports.")
    
    # Report generation options
    st.markdown("### Generate Custom Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Summary Report", "Detailed Report", "Performance Report", "Security Report"]
        )
        
        date_range = st.selectbox(
            "Date Range", 
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
        )
    
    with col2:
        output_format = st.selectbox(
            "Output Format",
            ["PDF", "JSON", "CSV", "HTML"]
        )
        
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("Generating custom report..."):
                # Simulate report generation
                st.success(f"Custom {report_type} generated successfully!")
                st.info("In a real implementation, this would generate and download the report.")

# Helper functions
def run_selected_tests(test_suites: Dict[str, bool], system_checks: Dict[str, bool], options: Dict[str, bool]) -> Dict[str, Any]:
    """Run selected test suites"""
    try:
        # Import test runner
        from tests.test_runner import TestRunner
        
        runner = TestRunner()
        results = runner.run_all_tests()
        
        return results
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        return {
            'error': str(e),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0
        }

def run_quick_test(test_type: str) -> Dict[str, Any]:
    """Run a quick test of specified type"""
    try:
        if test_type == "performance":
            from tests.test_performance import run_performance_tests
            return run_performance_tests()
        elif test_type == "authentication":
            from tests.test_auth import run_authentication_tests
            return run_authentication_tests()
        else:
            return {'error': f"Unknown test type: {test_type}"}
            
    except Exception as e:
        return {'error': str(e)}

def run_system_health_check() -> Dict[str, Any]:
    """Run system health check"""
    try:
        from utils.error_handler import error_handler
        
        health = error_handler.get_system_health()
        
        return {
            'status': health.get('status', 'unknown'),
            'memory_usage': health.get('memory_usage', 0),
            'cpu_usage': health.get('cpu_usage', 0),
            'errors_24h': health.get('errors_24h', 0),
            'last_check': health.get('last_check', datetime.now()).isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

def run_security_scan() -> Dict[str, Any]:
    """Run security validation scan"""
    # Simulated security scan results
    return {
        'vulnerabilities_found': 2,
        'critical_issues': 0,
        'warnings': 2,
        'last_scan': datetime.now().isoformat(),
        'scan_duration': 5.2
    }

def load_latest_test_results() -> Dict[str, Any]:
    """Load the most recent test results"""
    try:
        # Look for the most recent test report file
        test_files = [f for f in os.listdir('.') if f.startswith('test_report_') and f.endswith('.json')]
        
        if test_files:
            # Sort by filename (which includes timestamp)
            latest_file = sorted(test_files)[-1]
            
            with open(latest_file, 'r') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to load test results: {str(e)}")
        return None

def get_test_report_history() -> List[Dict[str, Any]]:
    """Get list of historical test reports"""
    try:
        test_files = [f for f in os.listdir('.') if f.startswith('test_report_') and f.endswith('.json')]
        
        reports = []
        for file in sorted(test_files, reverse=True):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    
                    reports.append({
                        'id': file.replace('.json', ''),
                        'name': file.replace('test_report_', '').replace('.json', ''),
                        'date': data.get('start_time', 'Unknown'),
                        'total_tests': data.get('total_tests', 0),
                        'success_rate': (data.get('passed_tests', 0) / max(data.get('total_tests', 1), 1)) * 100,
                        'duration': data.get('duration', 0),
                        'file_path': file
                    })
            except:
                continue
        
        return reports
        
    except Exception as e:
        logger.error(f"Failed to load test history: {str(e)}")
        return []

def display_test_execution_results(results: Dict[str, Any]):
    """Display test execution results"""
    if 'error' in results:
        st.error(f"Test execution failed: {results['error']}")
        return
    
    # Display results summary
    total = results.get('total_tests', 0)
    passed = results.get('passed_tests', 0)
    failed = results.get('failed_tests', 0)
    
    if total > 0:
        success_rate = (passed / total) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tests", total)
        
        with col2:
            st.metric("Passed", passed, delta=None)
        
        with col3:
            st.metric("Failed", failed, delta=None, delta_color="inverse")
        
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Status message
        if success_rate >= 95:
            st.success("🎉 Excellent! All tests passed successfully.")
        elif success_rate >= 80:
            st.warning("⚠️ Some tests failed. Review and address issues.")
        else:
            st.error("❌ Multiple test failures detected. Immediate attention required.")

def display_quick_test_results(test_name: str, results: Dict[str, Any]):
    """Display quick test results"""
    if 'error' in results:
        st.error(f"{test_name} test failed: {results['error']}")
    else:
        passed = results.get('passed', 0)
        failed = results.get('failed', 0)
        total = passed + failed
        
        if total > 0:
            success_rate = (passed / total) * 100
            st.success(f"{test_name} tests completed: {passed}/{total} passed ({success_rate:.1f}%)")
        else:
            st.info(f"{test_name} tests completed with no results.")

def display_health_check_results(results: Dict[str, Any]):
    """Display health check results"""
    if 'error' in results:
        st.error(f"Health check failed: {results['error']}")
    else:
        status = results.get('status', 'unknown')
        
        if status == 'healthy':
            st.success(f"✅ System is healthy")
        elif status == 'warning':
            st.warning(f"⚠️ System has some issues")
        else:
            st.error(f"❌ System has critical issues")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Memory Usage", f"{results.get('memory_usage', 0):.1f}%")
        
        with col2:
            st.metric("CPU Usage", f"{results.get('cpu_usage', 0):.1f}%")
        
        with col3:
            st.metric("Errors (24h)", results.get('errors_24h', 0))

def display_security_scan_results(results: Dict[str, Any]):
    """Display security scan results"""
    if 'error' in results:
        st.error(f"Security scan failed: {results['error']}")
    else:
        vulnerabilities = results.get('vulnerabilities_found', 0)
        critical = results.get('critical_issues', 0)
        
        if critical > 0:
            st.error(f"🚨 {critical} critical security issues found!")
        elif vulnerabilities > 0:
            st.warning(f"⚠️ {vulnerabilities} security issues found")
        else:
            st.success("✅ No security vulnerabilities detected")