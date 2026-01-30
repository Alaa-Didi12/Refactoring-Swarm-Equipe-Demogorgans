"""
Main entry point for the Refactoring Swarm system.
Automated code refactoring using multi-agent LLM collaboration.
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.orchestrator import RefactoringOrchestrator
from src.utils.logger import log_experiment, get_session_summary, ActionType


def validate_environment():
    """Validate that the environment is properly configured."""
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY not configured")
        print("   Please create a .env file with your Google API key")
        print("   Get a free key at: https://aistudio.google.com/app/apikey")
        return False
    
    return True


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Refactoring Swarm - Automated Code Refactoring with LLM Agents"
    )
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Directory containing Python code to refactor"
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Maximum iterations per file (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Validate target directory
    if not os.path.exists(args.target_dir):
        print(f"❌ ERROR: Directory not found: {args.target_dir}")
        sys.exit(1)
    
    # Log startup
    log_experiment(
        agent_name="System",
        model_used="system",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"System startup with target: {args.target_dir}",
            "output_response": "System initialized successfully",
            "target_directory": args.target_dir,
            "max_iterations": args.max_iterations
        },
        status="SUCCESS"
    )
    
    print(f"🚀 REFACTORING SWARM - STARTING")
    print(f"   Target: {args.target_dir}")
    print(f"   Max iterations: {args.max_iterations}")
    print()
    
    try:
        # Create and run orchestrator
        orchestrator = RefactoringOrchestrator(
            target_dir=args.target_dir,
            max_iterations=args.max_iterations
        )
        
        results = orchestrator.run()
        
        # Log completion
        log_experiment(
            agent_name="System",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "System completion",
                "output_response": f"Processed {results.get('total_files', 0)} files",
                "initial_score": results.get("initial_score", 0),
                "final_score": results.get("final_score", 0),
                "success": results.get("success", False)
            },
            status="SUCCESS" if results.get("success") else "FAILURE"
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        
        summary = get_session_summary()
        print(f"Total agent actions: {summary.get('total_actions', 0)}")
        print(f"Actions by type: {summary.get('actions_by_type', {})}")
        print(f"Actions by agent: {summary.get('actions_by_agent', {})}")
        
        if results.get("success"):
            print("\n✅ MISSION COMPLETE - All files processed successfully")
            sys.exit(0)
        else:
            print(f"\n⚠️  MISSION INCOMPLETE - {results.get('error', 'Unknown error')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        log_experiment(
            agent_name="System",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "System interrupted",
                "output_response": "User cancelled operation",
            },
            status="CANCELLED"
        )
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        
        log_experiment(
            agent_name="System",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "System error",
                "output_response": f"Fatal error: {str(e)}",
                "error": str(e)
            },
            status="FAILURE"
        )
        
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()