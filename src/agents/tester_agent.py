"""
Tester Agent - Test Execution and Validation
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from src.utils.prompts import Prompts
from src.utils.logger import log_experiment, ActionType
from src.tools.file_operations import FileOperations
from src.tools.test_runner import TestRunner
from src.tools.code_analyzer import CodeAnalyzer


class TesterAgent:
    """Agent responsible for running tests and validating fixes."""

    def __init__(self, sandbox_root: str, llm):
        """
        Initialize Tester Agent.

        Args:
            sandbox_root: Root directory for file operations
            llm: LLM instance (Gemini-2.5-Flash)
        """
        self.file_ops = FileOperations(sandbox_root)
        self.test_runner = TestRunner(sandbox_root)
        self.analyzer = CodeAnalyzer(sandbox_root)
        self.llm = llm
        self.agent_name = "Tester_Agent"
        self.sandbox_root = sandbox_root

    def test_file(self, filepath: str) -> Dict:
        """
        Test a Python file.
        
        Args:
            filepath: Path to Python file (relative to sandbox)
        
        Returns:
            Dictionary containing test results and recommendations
        """
        print(f"⚖️  Testing {filepath}")
        print(f"   Sandbox root: {self.sandbox_root}")
        
        try:
            # Check for existing tests
            has_tests = self.test_runner.has_tests()
            print(f"   Has existing tests: {has_tests}")
            
            test_file_created = None
            
            if not has_tests:
                print(f"   No tests found, generating tests for {filepath}")
                test_gen_result = self._generate_tests(filepath)
                
                if test_gen_result.get("success"):
                    test_file_created = test_gen_result.get("test_file")
                    print(f"   ✅ Generated test file: {test_file_created}")
                    # Update has_tests after generation
                    has_tests = self.test_runner.has_tests()
                    print(f"   Has tests after generation: {has_tests}")
                else:
                    print(f"   ❌ Test generation failed: {test_gen_result.get('error', 'Unknown error')}")
                    # Handle test generation failure
                    return self._handle_test_generation_failure(filepath, test_gen_result)
            
            # Run tests if we have them
            if has_tests:
                print(f"   Running tests...")
                test_results = self.test_runner.run_tests()
                print(f"   Test results: success={test_results.get('success')}, "
                      f"total={test_results.get('total_tests', 0)}, "
                      f"passed={test_results.get('passed', 0)}, "
                      f"failed={test_results.get('failed', 0)}")
                
                # Check if any tests were actually collected and run
                if test_results.get("total_tests", 0) == 0:
                    print(f"   ⚠️  No tests were collected/run, using static analysis")
                    return self._validate_without_tests(filepath)
                
                # Analyze failures if any
                if not test_results.get("success", False) and test_results.get("failed", 0) > 0:
                    print(f"   Analyzing test failures...")
                    analysis = self._analyze_failures(filepath, test_results)
                else:
                    analysis = {
                        "test_passed": test_results.get("success", False),
                        "total_tests": test_results.get("total_tests", 0),
                        "failed_tests": test_results.get("failed", 0),
                        "root_causes": [],
                        "recommended_fixes": [],
                        "retry_needed": False
                    }
            else:
                # If we still don't have tests, use static analysis
                print(f"   No tests available, using static analysis")
                return self._validate_without_tests(filepath)
            
            # Log experiment
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.DEBUG if not test_results.get("success") else ActionType.ANALYSIS,
                details={
                    "file_tested": filepath,
                    "test_file_created": test_file_created,
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
            print(f"   ❌ Exception in test_file: {str(e)}")
            import traceback
            traceback.print_exc()
            
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.DEBUG,
                details={
                    "file_tested": filepath,
                    "input_prompt": "Testing failed before execution",
                    "output_response": f"ERROR: {str(e)}",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                status="FAILURE"
            )
            return {
                "success": False, 
                "filepath": filepath, 
                "error": str(e), 
                "retry_needed": True
            }

    def _validate_without_tests(self, filepath: str) -> Dict:
        """Validate code without tests using static analysis."""
        print(f"   ⚠️  No tests found for {filepath}, using static analysis only")
        
        analysis = self.analyzer.analyze_file(filepath)
        has_errors = any(msg.get("type") in ["error", "fatal"] for msg in analysis.get("messages", []))
        
        # Be stricter about what constitutes "success"
        pylint_score = analysis.get("score", 0)
        success = (not has_errors and pylint_score > 7.0)  # Require higher score
        
        print(f"   Static analysis - Score: {pylint_score}, Has errors: {has_errors}, Success: {success}")
        
        return {
            "success": success,
            "filepath": filepath,
            "test_results": {
                "success": success,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "duration": 0.0,
                "note": "No tests available, validated with pylint only",
                "pylint_score": pylint_score,
                "has_errors": has_errors,
                "stdout": "No tests run - static analysis only",
                "stderr": ""
            },
            "analysis": {
                "test_passed": success,
                "validation_method": "static_analysis",
                "pylint_score": pylint_score,
                "has_errors": has_errors,
                "total_tests": 0,
                "failed_tests": 0,
                "root_causes": ["No unit tests available"] if not has_errors else ["Code has syntax/logic errors"],
                "recommended_fixes": ["Add comprehensive unit tests"] if not has_errors else ["Fix code errors and add tests"],
                "retry_needed": True  # Always retry if we didn't have proper tests
            },
            "retry_needed": True  # Force retry to generate proper tests
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
            
            print(f"   Sending analysis request to LLM...")
            response = self.llm.generate(full_prompt, temperature=0.3)
            print(f"   LLM response received ({len(response)} chars)")
            
            try:
                analysis = self._parse_analysis(response)
                print(f"   Successfully parsed analysis")
            except Exception as parse_error:
                print(f"   Failed to parse LLM response: {parse_error}")
                print(f"   Response preview: {response[:200]}")
                analysis = {
                    "test_passed": False,
                    "total_tests": test_results.get("total_tests", 0),
                    "failed_tests": test_results.get("failed", 0),
                    "root_causes": ["Test execution failed", f"Parse error: {str(parse_error)}"],
                    "recommended_fixes": ["Review test output and fix errors", "Check LLM response format"],
                    "retry_needed": True
                }
            
            return analysis
            
        except Exception as e:
            print(f"   Error in _analyze_failures: {str(e)}")
            return {
                "test_passed": False, 
                "error": str(e), 
                "retry_needed": True,
                "total_tests": test_results.get("total_tests", 0),
                "failed_tests": test_results.get("failed", 0),
                "root_causes": [f"Analysis failed: {str(e)}"],
                "recommended_fixes": ["Check LLM connection and configuration"]
            }

    def _parse_analysis(self, response: str) -> Dict:
        """Parse LLM response safely to extract JSON analysis."""
        response = response.strip()
        
        # Remove code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            # Try to find any code block
            parts = response.split("```")
            if len(parts) >= 2:
                # Take the first code block content
                response = parts[1].strip()
                # If it starts with "json\n", remove that
                if response.startswith("json\n"):
                    response = response[5:].strip()
        
        # Try to find JSON object
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, response)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            
            # Fallback to simple structure
            return {
                "test_passed": False,
                "total_tests": 0,
                "failed_tests": 0,
                "root_causes": ["Failed to parse LLM response as JSON"],
                "recommended_fixes": ["Ensure LLM returns valid JSON"],
                "retry_needed": True
            }

    def _generate_tests(self, filepath: str) -> Dict:
        """Generate unit tests safely using Gemini-2.5-Flash."""
        try:
            print(f"   Reading file: {filepath}")
            code_content = self.file_ops.read_file(filepath)
            print(f"   File content length: {len(code_content)} chars")
            
            prompt = Prompts.format_test_generator_prompt(
                filename=filepath,
                code_content=code_content
            )
            full_prompt = f"{Prompts.TEST_GENERATOR_SYSTEM}\n\n{prompt}"
            
            # Add debugging
            print(f"   Generating tests for {filepath}")
            print(f"   Prompt length: {len(full_prompt)} chars")
            
            response = self.llm.generate(full_prompt, temperature=0.5, max_tokens=2000)
            print(f"   LLM Response length: {len(response)} chars")
            print(f"   LLM Response preview: {response[:200]}...")
            
            test_code = self._extract_test_code(response)
            print(f"   Extracted test code length: {len(test_code)} chars")
            
            if not test_code.strip():
                print(f"   ERROR: No valid test code extracted")
                print(f"   Raw response: {response}")
                return {"success": False, "error": "LLM returned no valid test code"}
            
            # Validate test code has test functions
            if "def test_" not in test_code and "class Test" not in test_code:
                print(f"   WARNING: Generated code doesn't appear to contain test functions")
            
            test_filename = f"test_{Path(filepath).stem}.py"
            print(f"   Writing tests to: {test_filename}")
            self.file_ops.write_file(test_filename, test_code)
            
            # Verify the test file was created
            if not self.file_ops.file_exists(test_filename):
                return {"success": False, "error": f"Failed to create {test_filename}"}
            
            # Read back to verify
            written_content = self.file_ops.read_file(test_filename)
            print(f"   Test file created successfully, size: {len(written_content)} chars")
            
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.GENERATION,
                details={
                    "file_tested": filepath,
                    "input_prompt": full_prompt[:500],  # First 500 chars
                    "output_response": response[:500],  # First 500 chars
                    "test_file_created": test_filename,
                    "test_code_length": len(test_code)
                },
                status="SUCCESS"
            )
            
            return {"success": True, "test_file": test_filename}
            
        except Exception as e:
            print(f"   ERROR in test generation: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _extract_test_code(self, response: str) -> str:
        """Extract valid Python test code safely."""
        response = response.strip()
        
        # Try to extract from code blocks
        patterns = [
            r'```python\s*(.*?)\s*```',
            r'```\s*python\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                if extracted and len(extracted) > 10:  # Reasonable minimum
                    return extracted
        
        # Fallback: if no code blocks, use entire response but clean it
        lines = []
        for line in response.splitlines():
            line = line.strip()
            # Remove common LLM prefixes/markers
            if line.startswith("Here's") or line.startswith("```") or line == "":
                continue
            # Remove markdown-style code indicators
            if line == "python" or line == "```python":
                continue
            lines.append(line)
        
        result = "\n".join(lines).strip()
        
        # Final check: ensure it looks like Python code
        if "import" in result or "def " in result or "class " in result:
            return result
        
        # If still nothing, return original but cleaned
        return response

    def _handle_test_generation_failure(self, filepath: str, test_gen_result: Dict) -> Dict:
        """Handle case when test generation fails."""
        error_msg = test_gen_result.get('error', 'Unknown error')
        
        # Try to analyze why generation failed
        analysis = self.analyzer.analyze_file(filepath)
        has_errors = any(msg.get("type") in ["error", "fatal"] for msg in analysis.get("messages", []))
        
        return {
            "success": False,
            "filepath": filepath,
            "error": f"Test generation failed: {error_msg}",
            "test_results": {
                "success": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "duration": 0.0,
                "note": "Test generation failed, cannot run tests",
                "generation_error": error_msg,
                "pylint_has_errors": has_errors,
                "stdout": "Test generation failed",
                "stderr": error_msg
            },
            "analysis": {
                "test_passed": False,
                "total_tests": 0,
                "failed_tests": 0,
                "root_causes": [f"Test generation failed: {error_msg}"],
                "recommended_fixes": ["Fix code issues and retry test generation", 
                                     "Check LLM configuration and connection"],
                "retry_needed": True
            },
            "retry_needed": True
        }

    def get_final_score(self) -> Dict:
        """Get final quality score for all files."""
        return self.analyzer.analyze_directory()