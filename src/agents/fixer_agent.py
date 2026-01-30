"""
Fixer Agent - Code Correction and Refactoring
"""

import re
from typing import Dict, Optional
from src.utils.llm_config import LLMConfig
from src.utils.prompts import Prompts
from src.utils.logger import log_experiment, ActionType
from src.tools.file_operations import FileOperations


class FixerAgent:
    """Agent responsible for fixing code based on refactoring plans."""
    
    def __init__(self, sandbox_root: str, llm_config: LLMConfig):
        """
        Initialize Fixer Agent.
        
        Args:
            sandbox_root: Root directory for file operations
            llm_config: LLM configuration instance
        """
        self.file_ops = FileOperations(sandbox_root)
        self.llm = llm_config
        self.agent_name = "Fixer_Agent"
    
    def fix_file(
        self,
        filepath: str,
        refactoring_plan: Dict,
        previous_errors: Optional[str] = None
    ) -> Dict:
        """
        Fix a Python file according to refactoring plan.
        
        Args:
            filepath: Path to Python file (relative to sandbox)
            refactoring_plan: Refactoring plan from auditor
            previous_errors: Previous test errors if any
            
        Returns:
            Dictionary containing fix results
        """
        print(f"🔧 Fixer working on: {filepath}")
        
        try:
            # Read current code
            code_content = self.file_ops.read_file(filepath)
            
            # Format plan as string
            plan_str = self._format_plan(refactoring_plan)
            
            # Generate fix using LLM
            prompt = Prompts.format_fixer_prompt(
                filename=filepath,
                refactoring_plan=plan_str,
                code_content=code_content,
                previous_errors=previous_errors or "None"
            )
            
            full_prompt = f"{Prompts.FIXER_SYSTEM}\n\n{prompt}"
            
            response = self.llm.generate(full_prompt, temperature=0.4, max_tokens=4000)
            
            # Extract code from response
            fixed_code = self._extract_code(response)
            
            # Write fixed code
            self.file_ops.write_file(filepath, fixed_code)
            
            # Log the interaction
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.FIX,
                details={
                    "file_fixed": filepath,
                    "input_prompt": full_prompt,
                    "output_response": response,
                    "had_previous_errors": previous_errors is not None,
                    "code_length": len(fixed_code)
                },
                status="SUCCESS"
            )
            
            return {
                "success": True,
                "filepath": filepath,
                "fixed_code": fixed_code,
                "message": "Code successfully fixed"
            }
        
        except Exception as e:
            log_experiment(
                agent_name=self.agent_name,
                model_used=self.llm.get_model_name(),
                action=ActionType.FIX,
                details={
                    "file_fixed": filepath,
                    "input_prompt": "Fix failed before prompt generation",
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
    
    def _format_plan(self, plan: Dict) -> str:
        """Format refactoring plan as human-readable string."""
        import json
        
        if isinstance(plan, str):
            return plan
        
        return json.dumps(plan, indent=2)
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response."""
        response = response.strip()
        
        # Try to extract from code blocks
        if "```python" in response:
            # Extract content between ```python and ```
            match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        elif "```" in response:
            # Extract content between ``` and ```
            match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no code blocks, assume entire response is code
        # But clean up common LLM artifacts
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            # Skip common LLM commentary
            if line.strip().startswith(('Here', 'This', 'The', 'I', 'Note:')):
                continue
            code_lines.append(line)
        
        return '\n'.join(code_lines).strip()