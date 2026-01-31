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
        
        # Initialize progress tracking
        self.progress = {
            "total_files": 0,
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "total_iterations": 0
        }
    
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
            self.progress["total_files"] = len(python_files)
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
            self.progress["processed_files"] += 1
            self.show_progress()
            
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
        
        # Show final progress
        self.show_progress()
        
        return {
            "success": True,
            "initial_score": audit_results.get("average_score", 0),
            "final_score": final_score.get("average_score", 0),
            "total_files": len(python_files),
            "files_processed": len(file_results),
            "file_results": file_results,
            "final_analysis": final_score,
            "progress_summary": self.progress.copy()
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
        print(f"\n   📄 Processing: {filepath}")
        
        iteration = 0
        previous_errors = None
        initial_score = refactoring_plan.get("overall_score", 0)
        file_modified = False
        
        while iteration < self.max_iterations:
            iteration += 1
            self.progress["total_iterations"] += 1
            print(f"      🔄 Iteration {iteration}/{self.max_iterations}")
            
            # Fix the file
            fix_result = self.fixer.fix_file(
                filepath,
                refactoring_plan,
                previous_errors
            )
            
            if not fix_result.get("success"):
                print(f"      ❌ Fix failed: {fix_result.get('error')}")
                self.progress["failed_files"] += 1
                return {
                    "filepath": filepath,
                    "success": False,
                    "iterations": iteration,
                    "error": fix_result.get("error"),
                    "improved": False,
                    "initial_score": initial_score,
                    "final_score": initial_score,
                    "file_modified": file_modified,
                    "error_type": "fix_failed"
                }
            
            # Check if file was actually modified
            if fix_result.get("file_modified", False):
                file_modified = True
                print(f"      📝 File was modified")
            
            # Test the fix
            test_result = self.tester.test_file(filepath)
            
            if test_result.get("success"):
                print(f"      ✅ Tests passed!")
                
                # Get final score
                from src.tools.code_analyzer import CodeAnalyzer
                analyzer = CodeAnalyzer(str(self.sandbox_root))
                final_analysis = analyzer.analyze_file(filepath)
                final_score = final_analysis.get("score", 0)
                
                self.progress["successful_files"] += 1
                
                return {
                    "filepath": filepath,
                    "success": True,
                    "iterations": iteration,
                    "initial_score": initial_score,
                    "final_score": final_score,
                    "improved": final_score > initial_score,
                    "score_improvement": final_score - initial_score,
                    "tests_passed": True,
                    "file_modified": file_modified,
                    "error_type": None
                }
            
            # Tests failed, check if we should retry
            if not test_result.get("retry_needed"):
                print(f"      ⚠️  Tests failed and no retry needed")
                break
            
            # Prepare for retry
            print(f"      🔄 Tests failed, preparing retry...")
            previous_errors = self._format_errors(test_result)
        
        # Max iterations reached OR retry not needed after failure
        print(f"      ⏹️  Stopping after {iteration} iteration(s)")
        
        # Get final score
        from src.tools.code_analyzer import CodeAnalyzer
        analyzer = CodeAnalyzer(str(self.sandbox_root))
        final_analysis = analyzer.analyze_file(filepath)
        final_score = final_analysis.get("score", 0)
        
        # Run one final test to confirm state
        final_test = self.tester.test_file(filepath)
        final_tests_passed = final_test.get("success", False)
        
        if final_tests_passed:
            self.progress["successful_files"] += 1
            success = True
        else:
            self.progress["failed_files"] += 1
            success = False
        
        return {
            "filepath": filepath,
            "success": success,
            "iterations": iteration,
            "initial_score": initial_score,
            "final_score": final_score,
            "improved": final_score > initial_score,
            "score_improvement": final_score - initial_score,
            "max_iterations_reached": iteration >= self.max_iterations,
            "retry_aborted": iteration < self.max_iterations and not final_tests_passed,
            "tests_passed": final_tests_passed,
            "file_modified": file_modified,
            "final_test_result": final_test.get("analysis", {}),
            "error_type": "max_iterations" if iteration >= self.max_iterations else "retry_not_needed"
        }
    
    def _format_errors(self, test_result: Dict) -> str:
        """Format test errors for the fixer."""
        try:
            analysis = test_result.get("analysis", {})
            test_data = test_result.get("test_results", {})
            
            error_parts = []
            
            # Add file info
            error_parts.append(f"File: {test_result.get('filepath', 'Unknown')}")
            
            # Add test summary
            if test_data:
                error_parts.append(f"\nTest Summary:")
                error_parts.append(f"  Total tests: {test_data.get('total_tests', 0)}")
                error_parts.append(f"  Passed: {test_data.get('passed', 0)}")
                error_parts.append(f"  Failed: {test_data.get('failed', 0)}")
                if test_data.get('errors', 0) > 0:
                    error_parts.append(f"  Errors: {test_data.get('errors', 0)}")
            
            # Add root causes
            if analysis.get("root_causes"):
                error_parts.append("\nRoot Causes:")
                for cause in analysis.get("root_causes", []):
                    error_parts.append(f"  - {cause}")
            
            # Add recommended fixes
            if analysis.get("recommended_fixes"):
                error_parts.append("\nRecommended Fixes:")
                for fix in analysis.get("recommended_fixes", []):
                    error_parts.append(f"  - {fix}")
            
            # Add test output (limited)
            if test_data.get("stdout"):
                # Filter for important lines
                lines = test_data["stdout"].split('\n')
                important_lines = [line for line in lines 
                                 if any(keyword in line.lower() 
                                       for keyword in ['failed', 'error', 'assert', 'traceback', 'exception'])]
                
                if important_lines:
                    error_parts.append("\nKey Test Output:")
                    for line in important_lines[:20]:  # Limit to 20 lines
                        error_parts.append(f"  {line}")
                else:
                    # If no important lines, show last 10 lines
                    error_parts.append("\nLast Test Output:")
                    for line in lines[-10:]:
                        error_parts.append(f"  {line}")
            
            # Add any specific errors from the analysis
            if analysis.get("error"):
                error_parts.append(f"\nAnalysis Error: {analysis.get('error')}")
            
            return "\n".join(error_parts) if error_parts else "Tests failed - see detailed logs"
        
        except Exception as e:
            return f"Error formatting test results: {str(e)}\nRaw test result keys: {list(test_result.keys())}"
    
    def show_progress(self):
        """Display current progress."""
        print("\n" + "=" * 60)
        print("📊 PROGRESS REPORT")
        print("=" * 60)
        
        if self.progress["total_files"] > 0:
            processed_pct = (self.progress["processed_files"] / self.progress["total_files"]) * 100 if self.progress["total_files"] > 0 else 0
            success_pct = (self.progress["successful_files"] / self.progress["processed_files"]) * 100 if self.progress["processed_files"] > 0 else 0
            
            print(f"Files: {self.progress['processed_files']}/{self.progress['total_files']} ({processed_pct:.1f}%)")
            print(f"Successful: {self.progress['successful_files']} ({success_pct:.1f}%)")
            print(f"Failed: {self.progress['failed_files']}")
            print(f"Total iterations: {self.progress['total_iterations']}")
            if self.progress['processed_files'] > 0:
                avg_iterations = self.progress['total_iterations'] / self.progress['processed_files']
                print(f"Avg iterations per file: {avg_iterations:.1f}")
        else:
            print("No files processed yet")
        print("=" * 60)
    
    def get_summary(self) -> Dict:
        """
        Get a summary of the refactoring process.
        
        Returns:
            Summary dictionary
        """
        return {
            "total_files": self.progress["total_files"],
            "processed_files": self.progress["processed_files"],
            "successful_files": self.progress["successful_files"],
            "failed_files": self.progress["failed_files"],
            "total_iterations": self.progress["total_iterations"],
            "success_rate": (self.progress["successful_files"] / self.progress["processed_files"] * 100) if self.progress["processed_files"] > 0 else 0,
            "avg_iterations_per_file": self.progress["total_iterations"] / self.progress["processed_files"] if self.progress["processed_files"] > 0 else 0
        }
    
    def cleanup(self):
        """Clean up sandbox directory."""
        import shutil
        if self.sandbox_root.exists():
            print(f"\n🧹 Cleaning up sandbox directory: {self.sandbox_root}")
            try:
                shutil.rmtree(self.sandbox_root)
                print(f"   Sandbox cleaned up successfully")
            except Exception as e:
                print(f"   Warning: Could not clean up sandbox: {e}")


# Example usage
if __name__ == "__main__":
    # Test the orchestrator with a sample directory
    import sys
    import os
    
    # Determine target directory
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        # Use current directory as default
        target_dir = "."
    
    print(f"Target directory: {target_dir}")
    
    # Create orchestrator
    orchestrator = RefactoringOrchestrator(target_dir=target_dir, max_iterations=5)
    
    try:
        # Run the refactoring swarm
        results = orchestrator.run()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 FINAL SUMMARY")
        print("=" * 60)
        
        import json
        print(json.dumps(orchestrator.get_summary(), indent=2))
        
        # Show key metrics
        print(f"\n🔑 Key Metrics:")
        print(f"  Initial Score: {results.get('initial_score', 0):.2f}/10")
        print(f"  Final Score: {results.get('final_score', 0):.2f}/10")
        print(f"  Improvement: {results.get('final_score', 0) - results.get('initial_score', 0):+.2f}")
        
        # List processed files
        print(f"\n📁 Processed Files:")
        for file_result in results.get("file_results", []):
            status = "✅" if file_result.get("success") else "❌"
            improvement = file_result.get("score_improvement", 0)
            improvement_str = f"+{improvement:.2f}" if improvement > 0 else f"{improvement:.2f}"
            print(f"  {status} {file_result.get('filepath')}: {file_result.get('initial_score', 0):.2f} → {file_result.get('final_score', 0):.2f} ({improvement_str})")
        
    except Exception as e:
        print(f"\n❌ Orchestrator failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Optional: cleanup
        # orchestrator.cleanup()
        pass