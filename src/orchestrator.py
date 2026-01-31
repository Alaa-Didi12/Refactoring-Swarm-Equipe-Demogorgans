"""
Orchestrator - Main workflow coordinator for the Refactoring Swarm
"""

from typing import Dict, List
from pathlib import Path
from src.utils.llm_config import LLMConfig
from src.agents.auditor_agent import AuditorAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.tester_agent import TesterAgent
from src.tools.file_operations import FileOperations


class RefactoringOrchestrator:
    """
    Orchestrates the collaboration between agents.
    Implements the self-healing loop: Auditor -> Fixer -> Tester -> (retry if needed)
    """
    
    def __init__(self, target_dir: str, max_iterations: int = 10):
        """
        Initialize the orchestrator.
        
        Args:
            target_dir: Directory containing code to refactor
            max_iterations: Maximum iterations per file (prevent infinite loops)
        """
        self.target_dir = Path(target_dir).resolve()
        self.max_iterations = max_iterations
        
        # Initialize sandbox
        self.sandbox_root = Path("./sandbox").resolve()
        self.sandbox_root.mkdir(exist_ok=True)
        
        # Initialize LLM
        self.llm_config = LLMConfig()
        
        # Initialize agents
        self.auditor = AuditorAgent(str(self.sandbox_root), self.llm_config)
        self.fixer = FixerAgent(str(self.sandbox_root), self.llm_config)
        self.tester = TesterAgent(str(self.sandbox_root), self.llm_config)
        
        # Initialize file operations
        self.file_ops = FileOperations(str(self.sandbox_root))
    
    def run(self) -> Dict:
        """
        Main orchestration loop.
        
        Returns:
            Dictionary with final results
        """
        print("=" * 60)
        print("🐝 REFACTORING SWARM - MISSION START")
        print("=" * 60)
        
        # Step 1: Copy files to sandbox
        print(f"\n📁 Step 1: Copying files to sandbox...")
        try:
            self.file_ops.copy_to_sandbox(str(self.target_dir))
            python_files = self.file_ops.list_python_files()
            print(f"   Found {len(python_files)} Python files")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to copy files: {str(e)}"
            }
        
        if not python_files:
            return {
                "success": False,
                "error": "No Python files found in target directory"
            }
        
        # Step 2: Audit all files
        print(f"\n🔍 Step 2: Auditing code quality...")
        audit_results = self.auditor.analyze_directory()
        
        if not audit_results.get("success"):
            return {
                "success": False,
                "error": "Audit phase failed",
                "audit_results": audit_results
            }
        
        print(f"   Average initial score: {audit_results.get('average_score', 0)}/10")
        
        # Step 3: Process each file through the self-healing loop
        print(f"\n🔧 Step 3: Self-healing loop for each file...")
        file_results = []
        
        for file_result in audit_results.get("files", []):
            if not file_result.get("success"):
                continue
            
            filepath = file_result["filepath"]
            result = self._process_file(
                filepath,
                file_result.get("plan", {})
            )
            file_results.append(result)
        
        # Step 4: Final validation
        print(f"\n⚖️  Step 4: Final validation...")
        final_score = self.tester.get_final_score()
        
        print(f"\n{'=' * 60}")
        print(f"✅ MISSION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Final average score: {final_score.get('average_score', 0)}/10")
        print(f"Files processed: {len(file_results)}")
        print(f"Files improved: {sum(1 for r in file_results if r.get('improved', False))}")
        
        return {
            "success": True,
            "initial_score": audit_results.get("average_score", 0),
            "final_score": final_score.get("average_score", 0),
            "total_files": len(python_files),
            "files_processed": len(file_results),
            "file_results": file_results,
            "final_analysis": final_score
        }
    
    def _process_file(self, filepath: str, refactoring_plan: Dict) -> Dict:
        """
        Process a single file through the self-healing loop.
        
        Args:
            filepath: Path to file
            refactoring_plan: Initial refactoring plan
            
        Returns:
            Processing results
        """
        print(f"\n   Processing: {filepath}")
        
        iteration = 0
        previous_errors = None
        initial_score = refactoring_plan.get("overall_score", 0)
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f"      Iteration {iteration}/{self.max_iterations}")
            
            # Fix the file
            fix_result = self.fixer.fix_file(
                filepath,
                refactoring_plan,
                previous_errors
            )
            
            if not fix_result.get("success"):
                print(f"      ❌ Fix failed: {fix_result.get('error')}")
                return {
                    "filepath": filepath,
                    "success": False,
                    "iterations": iteration,
                    "error": fix_result.get("error"),
                    "improved": False
                }
            
            # Test the fix
            test_result = self.tester.test_file(filepath)
            
            if test_result.get("success"):
                print(f"      ✅ Tests passed!")
                
                # Get final score
                from src.tools.code_analyzer import CodeAnalyzer
                analyzer = CodeAnalyzer(str(self.sandbox_root))
                final_analysis = analyzer.analyze_file(filepath)
                final_score = final_analysis.get("score", 0)
                
                return {
                    "filepath": filepath,
                    "success": True,
                    "iterations": iteration,
                    "initial_score": initial_score,
                    "final_score": final_score,
                    "improved": final_score > initial_score,
                    "score_improvement": final_score - initial_score
                }
            
            # Tests failed, check if we should retry
            if not test_result.get("retry_needed"):
               
                break
            
            # Prepare for retry
            print(f"      🔄 Tests failed, preparing retry...")
            previous_errors = self._format_errors(test_result)
        
        # Max iterations reached
        
        
        # Get final score anyway
        from src.tools.code_analyzer import CodeAnalyzer
        analyzer = CodeAnalyzer(str(self.sandbox_root))
        final_analysis = analyzer.analyze_file(filepath)
        final_score = final_analysis.get("score", 0)
        
        return {
            "filepath": filepath,
            "success": False,
            "iterations": iteration,
            "initial_score": initial_score,
            "final_score": final_score,
            "improved": final_score > initial_score,
            "score_improvement": final_score - initial_score,
            "max_iterations_reached": True
        }
    
    def _format_errors(self, test_result: Dict) -> str:
        """Format test errors for the fixer."""
        analysis = test_result.get("analysis", {})
        test_data = test_result.get("test_results", {})
        
        error_parts = []
        
        if analysis.get("root_causes"):
            error_parts.append("Root Causes:")
            for cause in analysis["root_causes"]:
                error_parts.append(f"  - {cause}")
        
        if analysis.get("recommended_fixes"):
            error_parts.append("\nRecommended Fixes:")
            for fix in analysis["recommended_fixes"]:
                error_parts.append(f"  - {fix}")
        
        if test_data.get("stdout"):
            error_parts.append("\nTest Output:")
            error_parts.append(test_data["stdout"][:1000])  # Limit output
        
        return "\n".join(error_parts) if error_parts else "Tests failed - see logs"