# src/tools/analysis.py
import subprocess
import json
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

from .security import security_manager
from .file_ops import read_file,list_files
from src.utils.logger import log_experiment, ActionType

def run_static_analysis(file_path: str, agent_name: str = "Unknown") -> Dict[str, Any]:
    """
    Exécute pylint sur un fichier Python.
    
    Args:
        file_path: Chemin du fichier Python
        agent_name: Nom de l'agent pour le logging
        
    Returns:
        Dict avec les résultats de l'analyse
    """
    if security_manager is None:
        raise RuntimeError("SecurityManager non initialisé.")
    
    secure_path = security_manager.validate_and_resolve(file_path)
    
    try:
        # Vérifier que c'est un fichier Python
        if secure_path.suffix != '.py':
            raise ValueError(f"Le fichier {file_path} n'est pas un fichier Python")
        
        # Exécuter pylint
        result = subprocess.run(
            ["pylint", "--output-format=json", str(secure_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        issues = []
        if result.stdout:
            try:
                issues = json.loads(result.stdout)
            except json.JSONDecodeError:
                issues = [{"error": "Failed to parse pylint output"}]
        
        analysis_result = {
            "file": file_path,
            "issues": issues,
            "issues_count": len(issues),
            "pylint_return_code": result.returncode,
            "success": result.returncode in [0, 16, 8, 4]  # Codes de sortie acceptables
        }
        
        # Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse statique de {file_path} avec pylint",
                "output_response": json.dumps(analysis_result, indent=2),
                "file": file_path,
                "issues_count": len(issues),
                "operation": "run_static_analysis"
            },
            status="SUCCESS" if analysis_result["success"] else "FAILURE"
        )
        
        return analysis_result
        
    except subprocess.TimeoutExpired:
        error_msg = "Timeout lors de l'exécution de pylint"
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse statique de {file_path}",
                "output_response": error_msg,
                "file": file_path,
                "operation": "run_static_analysis"
            },
            status="FAILURE"
        )
        return {"error": error_msg, "success": False}
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse statique de {file_path}",
                "output_response": str(e),
                "file": file_path,
                "operation": "run_static_analysis"
            },
            status="FAILURE"
        )
        raise

def get_code_metrics(file_path: str, agent_name: str = "Unknown") -> Dict[str, Any]:
    """
    Calcule des métriques de base sur le code.
    
    Args:
        file_path: Chemin du fichier Python
        agent_name: Nom de l'agent pour le logging
        
    Returns:
        Dict avec les métriques calculées
    """
    try:
        content = read_file(file_path, agent_name)
        lines = content.split('\n')
        
        # Métriques basiques
        metrics = {
            "file": file_path,
            "lines_of_code": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "function_count": content.count('def '),
            "class_count": content.count('class '),
            "import_count": content.count('import ') + content.count('from '),
            "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
        }
        
        # Analyse AST pour plus de détails
        try:
            tree = ast.parse(content)
            
            # Compter les fonctions et méthodes
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            methods = [node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]
            
            metrics.update({
                "ast_functions": len(functions),
                "ast_methods": len(methods),
                "ast_valid": True
            })
        except SyntaxError as e:
            metrics.update({
                "ast_valid": False,
                "syntax_error": str(e)
            })
        
        # Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Calcul des métriques pour {file_path}",
                "output_response": json.dumps(metrics, indent=2),
                "file": file_path,
                "operation": "get_code_metrics"
            },
            status="SUCCESS"
        )
        
        return metrics
        
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Calcul des métriques pour {file_path}",
                "output_response": str(e),
                "file": file_path,
                "operation": "get_code_metrics"
            },
            status="FAILURE"
        )
        raise

def analyze_project(project_path: str = ".", agent_name: str = "Unknown") -> Dict[str, Any]:
    """
    Analyse complète d'un projet Python.
    
    Args:
        project_path: Chemin du projet à analyser
        agent_name: Nom de l'agent pour le logging
        
    Returns:
        Dict avec l'analyse complète du projet
    """
    try:
        # Lister tous les fichiers Python
        python_files = list_files(project_path, ".py", agent_name)
        
        project_analysis = {
            "project": project_path,
            "total_files": len(python_files),
            "files": [],
            "summary": {
                "total_issues": 0,
                "files_with_issues": 0
            }
        }
        
        # Analyser chaque fichier
        for file in python_files[:10]:  # Limiter pour éviter les timeouts
            try:
                file_analysis = run_static_analysis(file, agent_name)
                metrics = get_code_metrics(file, agent_name)
                
                file_result = {
                    "file": file,
                    "issues": file_analysis.get("issues", []),
                    "issues_count": file_analysis.get("issues_count", 0),
                    "metrics": metrics
                }
                
                project_analysis["files"].append(file_result)
                project_analysis["summary"]["total_issues"] += file_result["issues_count"]
                
                if file_result["issues_count"] > 0:
                    project_analysis["summary"]["files_with_issues"] += 1
                    
            except Exception as e:
                # Continuer avec les autres fichiers même si un échoue
                project_analysis["files"].append({
                    "file": file,
                    "error": str(e),
                    "issues_count": 0
                })
        
        # Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse complète du projet {project_path}",
                "output_response": json.dumps(project_analysis, indent=2),
                "project": project_path,
                "files_analyzed": len(python_files),
                "operation": "analyze_project"
            },
            status="SUCCESS"
        )
        
        return project_analysis
        
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse complète du projet {project_path}",
                "output_response": str(e),
                "project": project_path,
                "operation": "analyze_project"
            },
            status="FAILURE"
        )
        raise