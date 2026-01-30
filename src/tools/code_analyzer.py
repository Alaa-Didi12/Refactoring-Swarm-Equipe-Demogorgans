"""
Code analysis toolkit using pylint.
Provides static code analysis capabilities for agents.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional


class CodeAnalyzer:
    """Static code analysis using pylint."""
    
    def __init__(self, sandbox_root: str):
        """
        Initialize code analyzer.
        
        Args:
            sandbox_root: Root directory for code analysis
        """
        self.sandbox_root = Path(sandbox_root).resolve()
    
    def analyze_file(self, filepath: str) -> Dict:
        """
        Analyze a single Python file with pylint.
        
        Args:
            filepath: Path to Python file (relative to sandbox)
            
        Returns:
            Dictionary containing analysis results
        """
        full_path = self.sandbox_root / filepath
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Run pylint with JSON output
        try:
            result = subprocess.run(
                ['pylint', '--output-format=json', '--score=yes', str(full_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            messages = json.loads(result.stdout) if result.stdout else []
            
            # Extract score from stderr (pylint prints score to stderr)
            score = self._extract_score(result.stderr)
            
            # Categorize issues
            issues_by_type = self._categorize_issues(messages)
            
            return {
                "file": filepath,
                "score": score,
                "total_issues": len(messages),
                "issues_by_type": issues_by_type,
                "messages": messages[:20],  # Limit to first 20 issues
                "analysis_success": True
            }
        
        except subprocess.TimeoutExpired:
            return {
                "file": filepath,
                "score": 0.0,
                "total_issues": 0,
                "error": "Analysis timeout",
                "analysis_success": False
            }
        except Exception as e:
            return {
                "file": filepath,
                "score": 0.0,
                "total_issues": 0,
                "error": str(e),
                "analysis_success": False
            }
    
    def _extract_score(self, stderr: str) -> float:
        """Extract pylint score from stderr output."""
        try:
            for line in stderr.split('\n'):
                if 'rated at' in line.lower():
                    # Extract number before /10
                    parts = line.split('rated at')
                    if len(parts) > 1:
                        score_part = parts[1].split('/')[0].strip()
                        return float(score_part)
            return 0.0
        except:
            return 0.0
    
    def _categorize_issues(self, messages: List[Dict]) -> Dict[str, int]:
        """Categorize issues by type."""
        categories = {
            "convention": 0,
            "refactor": 0,
            "warning": 0,
            "error": 0,
            "fatal": 0
        }
        
        for msg in messages:
            msg_type = msg.get("type", "").lower()
            if msg_type in categories:
                categories[msg_type] += 1
        
        return categories
    
    def analyze_directory(self, directory: str = ".") -> Dict:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Directory to analyze (relative to sandbox)
            
        Returns:
            Aggregated analysis results
        """
        dir_path = self.sandbox_root / directory
        
        python_files = list(dir_path.rglob("*.py"))
        
        if not python_files:
            return {
                "total_files": 0,
                "average_score": 0.0,
                "files": []
            }
        
        results = []
        total_score = 0.0
        successful_analyses = 0
        
        for py_file in python_files:
            rel_path = py_file.relative_to(self.sandbox_root)
            result = self.analyze_file(str(rel_path))
            results.append(result)
            
            if result.get("analysis_success"):
                total_score += result["score"]
                successful_analyses += 1
        
        average_score = total_score / successful_analyses if successful_analyses > 0 else 0.0
        
        return {
            "total_files": len(python_files),
            "analyzed_files": successful_analyses,
            "average_score": round(average_score, 2),
            "files": results
        }
    
    def get_critical_issues(self, filepath: str) -> List[str]:
        """
        Get list of critical issues that must be fixed.
        
        Args:
            filepath: Path to Python file
            
        Returns:
            List of human-readable issue descriptions
        """
        analysis = self.analyze_file(filepath)
        
        if not analysis.get("analysis_success"):
            return [f"Analysis failed: {analysis.get('error', 'Unknown error')}"]
        
        critical = []
        
        for msg in analysis.get("messages", []):
            if msg.get("type") in ["error", "fatal"]:
                critical.append(
                    f"Line {msg.get('line', '?')}: {msg.get('message', 'Unknown issue')}"
                )
        
        return critical