"""
Tester Agent - Test Execution and Validation
"""

import json
from typing import Dict, Optional
from src.utils.llm_config import LLMConfig
from src.utils.prompts import Prompts
from src.utils.logger import log_experiment, ActionType
from src.tools.file_operations import FileOperations
from src.tools.test_runner import TestRunner
from src.tools.code_analyzer import CodeAnalyzer


class TesterAgent:
    """Agent responsible for running tests and validating fixes."""
    
    def __init__(self, sandbox_root: str, llm_config: LLMConfig):
        """
        Initialize Tester Agent.
        
        Args:
            sandbox_root: Root directory for file operations
            llm_config: LLM configuration instance
        """
        self.file_ops = FileOperations(sandbox_root)
        self.test_runner = TestRunner(sandbox_root)
        self.analyzer = CodeAnalyzer(sandbox_root)
        self.llm = llm_config
        self.agent_name = "Tester_Agent"
    
    def test_file(self, filepath: str) -> Dict:
        """
        Test a Python file.
        
        Args:
            filepath: Path to Python file (relative to sandbox)
            
        Returns:
            Dictionary containing test results and recommendations
        """
        print(f"⚖️  Tester validating: {filepath}")
        
        try:
            # First, check if there are any tests
            has_tests = self.test_runner.has_tests()
            
            if not has_tests:
                # No tests exist, try to generate basic tests
                print(f"   No tests found, generating tests for {filepath}")
                test_gen_result = self._generate_tests(filepath)
                
                if not test_gen_result.get("success"):
                    # Can't generate tests, do basic validation instead
                    return self._validate_without_tests(filepath)
            
            # Run tests
            test_results = self.test_runner.run_tests()
            
            # Analyze results with LLM if tests failed
            if not test_results.get("success") and test_results.get("failed", 0) > 0:
                analysis = self._analyze_failures(filepath, test_results)
            else:
                analysis = {
                    "test_passed": True,
                    "total_tests": test_results.get("total_tests", 0),
                    "failed_tests": 0,
                    "root_causes": [],
                    "recommended_fixes": [],
                    "retry_needed": False
                }
            
            # Log the interaction
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.DEBUG if not test_results.get("success") else ActionType.ANALYSIS,
                details={
                    "file_tested": filepath,
                    "input_prompt": f"Test validation for {filepath}",
                    "output_response": json.dumps(analysis),
                    "tests_passed": test_results.get("success", False),
                    "total_tests": test_results.get("total_tests", 0),
                    "failed_tests": test_results.get("failed", 0)
                },
                status="SUCCESS" if test_results.get("success") else "FAILURE"
            )
            
            return {
                "success": test_results.get("success", False),
                "filepath": filepath,
                "test_results": test_results,
                "analysis": analysis,
                "retry_needed": analysis.get("retry_needed", False)
            }
        
        except Exception as e:
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.DEBUG,
                details={
                    "file_tested": filepath,
                    "input_prompt": "Testing failed before execution",
                    "output_response": f"ERROR: {str(e)}",
                    "error": str(e)
                },
                status="FAILURE"
            )
            
            return {
                "success": False,
                "filepath": filepath,
                "error": str(e),
                "retry_needed": False
            }
    
    def _validate_without_tests(self, filepath: str) -> Dict:
        """Validate code quality without tests."""
        print(f"   Validating {filepath} using static analysis only")
        
        # Run pylint to check for errors
        analysis = self.analyzer.analyze_file(filepath)
        
        has_errors = any(
            msg.get("type") in ["error", "fatal"]
            for msg in analysis.get("messages", [])
        )
        
        return {
            "success": not has_errors and analysis.get("score", 0) > 5.0,
            "filepath": filepath,
            "test_results": {
                "success": not has_errors,
                "total_tests": 0,
                "note": "No tests available, validated with pylint only"
            },
            "analysis": {
                "test_passed": not has_errors,
                "validation_method": "static_analysis",
                "pylint_score": analysis.get("score", 0),
                "retry_needed": has_errors
            },
            "retry_needed": has_errors
        }
    
    def _analyze_failures(self, filepath: str, test_results: Dict) -> Dict:
        """Analyze test failures using LLM."""
        try:
            code_content = self.file_ops.read_file(filepath)
            
            prompt = Prompts.format_tester_prompt(
                filename=filepath,
                test_results=test_results,
                code_content=code_content
            )
            
            full_prompt = f"{Prompts.TESTER_SYSTEM}\n\n{prompt}"
            
            response = self.llm.generate(full_prompt, temperature=0.3)
            
            # Parse response
            try:
                analysis = self._parse_analysis(response)
            except:
                # Fallback analysis
                analysis = {
                    "test_passed": False,
                    "total_tests": test_results.get("total_tests", 0),
                    "failed_tests": test_results.get("failed", 0),
                    "root_causes": ["Test execution failed"],
                    "recommended_fixes": ["Review test output and fix errors"],
                    "retry_needed": True
                }
            
            return analysis
        
        except Exception as e:
            return {
                "test_passed": False,
                "error": str(e),
                "retry_needed": True
            }
    
    def _parse_analysis(self, response: str) -> Dict:
        """Parse LLM response to extract analysis."""
        response = response.strip()
        
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        return json.loads(response)
    
    def _generate_tests(self, filepath: str) -> Dict:
        """Generate basic unit tests for a file."""
        try:
            code_content = self.file_ops.read_file(filepath)
            
            prompt = Prompts.format_test_generator_prompt(
                filename=filepath,
                code_content=code_content
            )
            
            full_prompt = f"{Prompts.TEST_GENERATOR_SYSTEM}\n\n{prompt}"
            
            response = self.llm.generate(full_prompt, temperature=0.5, max_tokens=2000)
            
            # Extract test code
            test_code = self._extract_test_code(response)
            
            # Save test file
            test_filename = f"test_{filepath.replace('/', '_')}"
            self.file_ops.write_file(test_filename, test_code)
            
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.GENERATION,
                details={
                    "file_tested": filepath,
                    "input_prompt": full_prompt,
                    "output_response": response,
                    "test_file_created": test_filename
                },
                status="SUCCESS"
            )
            
            return {
                "success": True,
                "test_file": test_filename
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_test_code(self, response: str) -> str:
        """Extract test code from LLM response."""
        import re
        
        response = response.strip()
        
        # Try to extract from code blocks
        if "```python" in response:
            match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in response:
            match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return response
    
    def get_final_score(self) -> Dict:
        """Get final quality score for all files."""
        return self.analyzer.analyze_directory()