# src/agents/judge.py
import json
from src.tools.testing import run_tests
from src.utils.logger import log_experiment, ActionType

def test_project(project_path: str) -> dict:
    """
    Lance les tests sur le projet.
    """
    print(f"   ⚖️  Tests en cours...")
    
    try:
        # Exécuter les tests
        test_results = run_tests(project_path, agent_name="Judge")
        
        # Résultat
        result = {
            "project": project_path,
            "tests_passed": test_results.get("passed", 0),
            "tests_failed": test_results.get("failed", 0),
            "skipped": test_results.get("skipped", 0),
            "all_passed": test_results.get("success", False),
            "return_code": test_results.get("return_code", -1)
        }
        
        # Log
        log_experiment(
            agent_name="Judge",
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Tests du projet {project_path}",
                "output_response": json.dumps(result, indent=2),
                "project": project_path,
                "tests_passed": result["tests_passed"],
                "tests_failed": result["tests_failed"],
                "operation": "test_project"
            },
            status="SUCCESS" if result["all_passed"] else "FAILURE"
        )
        
        return result
        
    except Exception as e:
        print(f"   ❌ Erreur lors des tests : {e}")
        return {
            "project": project_path,
            "tests_passed": 0,
            "tests_failed": 1,
            "all_passed": False,
            "error": str(e)
        }