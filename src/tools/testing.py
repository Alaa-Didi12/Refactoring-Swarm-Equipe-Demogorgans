# src/tools/testing.py
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


from src.utils.logger import log_experiment, ActionType

def _get_security_manager():
    """Récupère le security_manager de manière sécurisée."""
    try:
        from .security import security_manager
        if security_manager is None:
            raise RuntimeError("SecurityManager non initialisé.")
        return security_manager
    except ImportError:
        raise RuntimeError("Module security non trouvé.")


def run_tests(test_path: str = ".", agent_name: str = "Unknown", 
              verbose: bool = False) -> Dict[str, Any]:
    """
    Exécute les tests avec pytest.
    
    Args:
        test_path: Chemin vers le fichier/dossier de tests
        agent_name: Nom de l'agent pour le logging
        verbose: Mode verbeux
        
    Returns:
        Dict avec les résultats des tests
    """
    security_manager = _get_security_manager()
    if security_manager is None:
        raise RuntimeError("SecurityManager non initialisé.")
    
    secure_path = security_manager.validate_and_resolve(test_path)
    
    try:
        # Construire la commande pytest
        cmd = [sys.executable, "-m", "pytest", str(secure_path), "--tb=short", "-q"]
        if verbose:
            cmd.remove("-q")
            cmd.append("-v")
        
        # Exécuter les tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max pour les tests
        )
        
        # Analyser la sortie
        output_lines = result.stdout.split('\n')
        test_summary = {
            "test_path": test_path,
            "return_code": result.returncode,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "summary": "",
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Extraire le résumé des tests
        for line in output_lines[-10:]:  # Chercher dans les dernières lignes
            if "passed" in line and "failed" in line:
                test_summary["summary"] = line.strip()
                # Extraire les nombres
                import re
                numbers = re.findall(r'\d+', line)
                if len(numbers) >= 3:
                    test_summary["passed"] = int(numbers[0])
                    test_summary["failed"] = int(numbers[1])
                    test_summary["skipped"] = int(numbers[2])
                break
        
        # Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Exécution des tests : {test_path}",
                "output_response": json.dumps(test_summary, indent=2),
                "test_path": test_path,
                "passed": test_summary["passed"],
                "failed": test_summary["failed"],
                "operation": "run_tests"
            },
            status="SUCCESS" if test_summary["success"] else "FAILURE"
        )
        
        return test_summary
        
    except subprocess.TimeoutExpired:
        error_msg = "Timeout lors de l'exécution des tests (120s)"
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Exécution des tests : {test_path}",
                "output_response": error_msg,
                "test_path": test_path,
                "operation": "run_tests"
            },
            status="FAILURE"
        )
        return {
            "error": error_msg,
            "success": False,
            "test_path": test_path
        }
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Exécution des tests : {test_path}",
                "output_response": str(e),
                "test_path": test_path,
                "operation": "run_tests"
            },
            status="FAILURE"
        )
        raise

def check_test_coverage(test_path: str = ".", agent_name: str = "Unknown") -> Dict[str, Any]:
    """
    Vérifie la couverture de code avec pytest-cov.
    
    Args:
        test_path: Chemin vers les tests
        agent_name: Nom de l'agent pour le logging
        
    Returns:
        Dict avec les résultats de couverture
    """
    if security_manager is None:
        raise RuntimeError("SecurityManager non initialisé.")
    
    secure_path = security_manager.validate_and_resolve(test_path)
    
    try:
        # Exécuter avec couverture
        cmd = [
            sys.executable, "-m", "pytest",
            str(secure_path),
            "--cov=.",
            "--cov-report=term-missing",
            "-q"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes pour la couverture
        )
        
        coverage_result = {
            "test_path": test_path,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "coverage_percentage": 0
        }
        
        # Extraire le pourcentage de couverture
        import re
        coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', result.stdout)
        if coverage_match:
            coverage_result["coverage_percentage"] = int(coverage_match.group(1))
        
        # Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Vérification de la couverture de tests : {test_path}",
                "output_response": json.dumps(coverage_result, indent=2),
                "test_path": test_path,
                "coverage_percentage": coverage_result["coverage_percentage"],
                "operation": "check_test_coverage"
            },
            status="SUCCESS"
        )
        
        return coverage_result
        
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Vérification de la couverture de tests : {test_path}",
                "output_response": str(e),
                "test_path": test_path,
                "operation": "check_test_coverage"
            },
            status="FAILURE"
        )
        raise