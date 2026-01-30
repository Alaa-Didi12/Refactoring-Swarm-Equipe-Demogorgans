"""
Test execution toolkit using pytest.
Provides test running capabilities for agents.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional


class TestRunner:
    """Test execution using pytest."""
    
    def __init__(self, sandbox_root: str):
        """
        Initialize test runner.
        
        Args:
            sandbox_root: Root directory for test execution
        """
        self.sandbox_root = Path(sandbox_root).resolve()
    
    def run_tests(self, test_path: Optional[str] = None) -> Dict:
        """
        Run pytest tests.
        
        Args:
            test_path: Specific test file or directory (None for all tests)
            
        Returns:
            Dictionary containing test results
        """
        if test_path:
            full_path = self.sandbox_root / test_path
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Test path not found: {test_path}",
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0
                }
            target = str(full_path)
        else:
            target = str(self.sandbox_root)
        
        # Run pytest with JSON report
        try:
            result = subprocess.run(
                [
                    'pytest',
                    target,
                    '--tb=short',
                    '--verbose',
                    '--json-report',
                    '--json-report-file=/tmp/pytest_report.json'
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.sandbox_root)
            )
            
            # Parse results
            try:
                with open('/tmp/pytest_report.json', 'r') as f:
                    report = json.load(f)
                
                summary = report.get('summary', {})
                
                tests_results = {
                    "success": result.returncode == 0,
                    "total_tests": summary.get('total', 0),
                    "passed": summary.get('passed', 0),
                    "failed": summary.get('failed', 0),
                    "errors": summary.get('error', 0),
                    "skipped": summary.get('skipped', 0),
                    "duration": report.get('duration', 0),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
                # Extract failure details
                if tests_results["failed"] > 0:
                    tests_results["failures"] = self._extract_failures(report)
                
                return tests_results
            
            except FileNotFoundError:
                # Fallback: parse stdout
                return self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out (>60s)",
                "total_tests": 0,
                "passed": 0,
                "failed": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}",
                "total_tests": 0,
                "passed": 0,
                "failed": 0
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str, returncode: int) -> Dict:
        """Parse pytest output when JSON report is not available."""
        lines = stdout.split('\n')
        
        # Look for summary line like "5 passed, 2 failed in 1.23s"
        passed = 0
        failed = 0
        total = 0
        
        for line in lines:
            if 'passed' in line or 'failed' in line:
                if 'passed' in line:
                    try:
                        passed = int(line.split('passed')[0].strip().split()[-1])
                    except:
                        pass
                if 'failed' in line:
                    try:
                        failed = int(line.split('failed')[0].strip().split()[-1])
                    except:
                        pass
        
        total = passed + failed
        
        return {
            "success": returncode == 0,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "stdout": stdout,
            "stderr": stderr
        }
    
    def _extract_failures(self, report: Dict) -> List[Dict]:
        """Extract failure details from pytest JSON report."""
        failures = []
        
        for test in report.get('tests', []):
            if test.get('outcome') == 'failed':
                failures.append({
                    "test_name": test.get('nodeid', 'Unknown'),
                    "error": test.get('call', {}).get('longrepr', 'No error details'),
                })
        
        return failures[:5]  # Limit to first 5 failures
    
    def has_tests(self) -> bool:
        """Check if any test files exist in the sandbox."""
        test_files = list(self.sandbox_root.rglob("test_*.py"))
        test_files.extend(self.sandbox_root.rglob("*_test.py"))
        return len(test_files) > 0
    
    def create_basic_test(self, module_name: str, test_content: str) -> None:
        """
        Create a basic test file.
        
        Args:
            module_name: Name of module to test
            test_content: Test code content
        """
        test_file = self.sandbox_root / f"test_{module_name}.py"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)