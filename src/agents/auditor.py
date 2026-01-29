# src/agents/auditor.py
import json
import os
from src.tools.analysis import run_static_analysis, get_code_metrics
from src.utils.logger import log_experiment, ActionType
from src.utils.messaging import MessageBus, Message, MessageType
message_bus = MessageBus()

def audit_file(file_name: str) -> dict:
    """Analyse un fichier et retourne les problèmes trouvés."""
    print(f"   🔍 Audit de {file_name}")
    
    try:
        # 1. Analyse statique avec pylint
        analysis = run_static_analysis(file_name, agent_name="Auditor")
        
        # 2. Métriques du code
        metrics = get_code_metrics(file_name, agent_name="Auditor")
        
        # 3. Résumé
        result = {
            "file": file_name,
            "has_issues": analysis.get("issues_count", 0) > 0,
            "issues_count": analysis.get("issues_count", 0),
            "pylint_score": analysis.get("pylint_return_code", -1),
            "success": analysis.get("success", False),
            "metrics": metrics
        }
        
        # 4. Log
        log_experiment(
            agent_name="Auditor",
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse du fichier {file_name}",
                "output_response": json.dumps(result, indent=2),
                "file": file_name,
                "issues_found": result["issues_count"],
                "operation": "audit_file"
            },
            status="SUCCESS" if result["success"] else "FAILURE"
        )
        
        return result
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'audit : {e}")
        return {
            "file": file_name,
            "has_issues": False,
            "issues_count": 0,
            "error": str(e),
            "success": False
        }

def audit_project(project_path: str) -> dict:
    """Analyse tous les fichiers Python d'un projet."""
    project_path = os.path.abspath(project_path)
    print(f"📁 Audit du projet : {project_path}")
    
    try:
        if not os.path.exists(project_path):
            return {
                "project": project_path,
                "files_audited": 0,
                "files_with_issues": 0,
                "total_issues": 0,
                "error": f"Dossier non trouvé: {project_path}"
            }
        
        files = []
        
        for item in os.listdir(project_path):
            item_path = os.path.join(project_path, item)
            if os.path.isfile(item_path) and item.lower().endswith('.py'):
                files.append(item)  # Stocke juste le nom du fichier
        
        print(f"   📄 {len(files)} fichiers Python trouvés")
        
        results = []
        for file_name in files[:3]:
            result = audit_file(file_name)
            results.append(result)
        
        summary = {
            "project": project_path,
            "files_audited": len(results),
            "files_with_issues": sum(1 for r in results if r.get("has_issues", False)),
            "total_issues": sum(r.get("issues_count", 0) for r in results),
            "all_files_valid": all(r.get("success", False) for r in results),
            "detailed_results": results  # Inclure les résultats détaillés
        }
        
        # ENVOYER UN MESSAGE AU FIXER
        message_bus.send(Message(
            sender="Auditor",
            receiver="Fixer",
            msg_type=MessageType.AUDIT_REPORT,
            content=summary,
            iteration=1  # À ajuster par l'orchestrateur
        ))
        
        return summary
        
    except Exception as e:
        print(f"❌ Erreur lors de l'audit du projet : {e}")
        # Envoyer un message d'erreur
        message_bus.send(Message(
            sender="Auditor",
            receiver="Orchestrator",
            msg_type=MessageType.ERROR_REPORT,
            content={"error": str(e), "operation": "audit_project"}
        ))
        return {
            "project": project_path,
            "error": str(e),
            "success": False
        }