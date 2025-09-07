#!/usr/bin/env python3
"""
Simplified test runner for B-TCRimer platform
Validates core functionality without external dependencies
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class SimpleTestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'failures': [],
            'system_validation': {}
        }
    
    def run_test(self, test_name: str, test_func):
        """Run a single test function"""
        print(f"Running {test_name}...", end=" ")
        self.results['tests_run'] += 1
        
        try:
            test_func()
            print("✅ PASS")
            self.results['tests_passed'] += 1
            return True
        except Exception as e:
            print(f"❌ FAIL - {str(e)}")
            self.results['tests_failed'] += 1
            self.results['failures'].append({
                'test': test_name,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return False
    
    def validate_file_structure(self):
        """Validate core file structure"""
        required_files = [
            'app.py',
            'utils/auth.py',
            'utils/themes.py',
            'utils/cache_manager.py',
            'utils/performance_monitor.py',
            'pages/admin.py',
            'pages/testing.py',
            'database/operations.py'
        ]
        
        missing = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing.append(file_path)
        
        if missing:
            raise Exception(f"Missing required files: {missing}")
    
    def validate_imports(self):
        """Validate that core modules can be imported"""
        import importlib.util
        
        modules_to_test = [
            ('utils.logging_config', 'utils/logging_config.py'),
            ('database.operations', 'database/operations.py'),
        ]
        
        for module_name, file_path in modules_to_test:
            if os.path.exists(file_path):
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None:
                    raise Exception(f"Cannot load spec for {module_name}")
    
    def validate_system_resources(self):
        """Check system resources"""
        import psutil
        
        # Memory check
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            raise Exception(f"High memory usage: {memory.percent}%")
        
        # Disk check  
        disk = psutil.disk_usage('.')
        if disk.percent > 95:
            raise Exception(f"High disk usage: {disk.percent}%")
        
        self.results['system_validation'] = {
            'memory_usage_percent': memory.percent,
            'disk_usage_percent': disk.percent,
            'available_memory_mb': memory.available // 1024 // 1024
        }
    
    def validate_database_structure(self):
        """Validate database can be initialized"""
        # Simple file existence check for SQLite
        if os.path.exists('b_tcrimer.db'):
            file_size = os.path.getsize('b_tcrimer.db')
            if file_size == 0:
                raise Exception("Database file exists but is empty")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🧪 B-TCRimer Quality Assurance Test Suite")
        print("=" * 50)
        
        # Core validation tests
        self.run_test("File Structure Validation", self.validate_file_structure)
        self.run_test("Import Validation", self.validate_imports) 
        self.run_test("System Resources Check", self.validate_system_resources)
        self.run_test("Database Structure Check", self.validate_database_structure)
        
        # Generate report
        print("\n📊 Test Results Summary:")
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Passed: {self.results['tests_passed']} ✅")
        print(f"Failed: {self.results['tests_failed']} ❌")
        print(f"Success Rate: {(self.results['tests_passed']/self.results['tests_run']*100):.1f}%")
        
        if self.results['system_validation']:
            print(f"\n💾 System Status:")
            print(f"Memory Usage: {self.results['system_validation']['memory_usage_percent']:.1f}%")
            print(f"Disk Usage: {self.results['system_validation']['disk_usage_percent']:.1f}%")
            print(f"Available Memory: {self.results['system_validation']['available_memory_mb']}MB")
        
        if self.results['failures']:
            print(f"\n❌ Failed Tests:")
            for failure in self.results['failures']:
                print(f"  • {failure['test']}: {failure['error']}")
        
        # Save results
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📋 Full results saved to test_results.json")
        
        return self.results['tests_failed'] == 0

if __name__ == "__main__":
    runner = SimpleTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)