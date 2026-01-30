"""
Auditor Agent - Code Analysis and Refactoring Planning
"""

import json
from typing import Dict, Optional
from src.utils.llm_config import LLMConfig
from src.utils.prompts import Prompts
from src.utils.logger import log_experiment, ActionType
from src.tools.file_operations import FileOperations
from src.tools.code_analyzer import CodeAnalyzer


class AuditorAgent:
    """Agent responsible for code analysis and refactoring plan generation."""
    
    def __init__(self, sandbox_root: str, llm_config: LLMConfig):
        """
        Initialize Auditor Agent.
        
        Args:
            sandbox_root: Root directory for file operations
            llm_config: LLM configuration instance
        """
        self.file_ops = FileOperations(sandbox_root)
        self.analyzer = CodeAnalyzer(sandbox_root)
        self.llm = llm_config
        self.agent_name = "Auditor_Agent"
    
    def analyze_file(self, filepath: str) -> Dict:
        """
        Analyze a Python file and generate refactoring plan.
        
        Args:
            filepath: Path to Python file (relative to sandbox)
            
        Returns:
            Dictionary containing analysis and refactoring plan
        """
        print(f"🔍 Auditor analyzing: {filepath}")
        
        try:
            # Read file content
            code_content = self.file_ops.read_file(filepath)
            
            # Run pylint analysis
            pylint_results = self.analyzer.analyze_file(filepath)
            
            # Generate refactoring plan using LLM
            prompt = Prompts.format_auditor_prompt(
                filename=filepath,
                pylint_results=pylint_results,
                code_content=code_content
            )
            
            full_prompt = f"{Prompts.AUDITOR_SYSTEM}\n\n{prompt}"
            
            response = self.llm.generate(full_prompt, temperature=0.3)
            
            # Log the interaction
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": filepath,
                    "input_prompt": full_prompt,
                    "output_response": response,
                    "pylint_score": pylint_results.get("score", 0),
                    "total_issues": pylint_results.get("total_issues", 0)
                },
                status="SUCCESS"
            )
            
            # Parse response
            try:
                plan = self._parse_plan(response)
            except:
                # Fallback to basic plan
                plan = {
                    "overall_score": pylint_results.get("score", 0),
                    "total_issues": pylint_results.get("total_issues", 0),
                    "critical_issues": [],
                    "refactoring_plan": {
                        "priority_1": ["Fix pylint errors", "Add docstrings"],
                        "priority_2": ["Improve code style"]
                    }
                }
            
            return {
                "success": True,
                "filepath": filepath,
                "pylint_score": pylint_results.get("score", 0),
                "plan": plan,
                "raw_response": response
            }
        
        except Exception as e:
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": filepath,
                    "input_prompt": "Analysis failed before prompt generation",
                    "output_response": f"ERROR: {str(e)}",
                    "error": str(e)
                },
                status="FAILURE"
            )
            
            return {
                "success": False,
                "filepath": filepath,
                "error": str(e)
            }
    
    def _parse_plan(self, response: str) -> Dict:
        """Parse LLM response to extract refactoring plan."""
        # Try to extract JSON from response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        return json.loads(response)
    
    def analyze_directory(self) -> Dict:
        """Analyze all Python files in the sandbox."""
        python_files = self.file_ops.list_python_files()
        
        if not python_files:
            return {
                "success": False,
                "error": "No Python files found in sandbox"
            }
        
        results = []
        total_score = 0
        
        for filepath in python_files:
            result = self.analyze_file(filepath)
            results.append(result)
            
            if result.get("success"):
                total_score += result.get("pylint_score", 0)
        
        avg_score = total_score / len(results) if results else 0
        
        return {
            "success": True,
            "total_files": len(python_files),
            "average_score": round(avg_score, 2),
            "files": results
        }