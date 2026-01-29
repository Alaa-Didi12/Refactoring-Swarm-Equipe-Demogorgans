# src/agents/fixer.py
import json
from src.tools.file_ops import read_file, write_file
from src.utils.logger import log_experiment, ActionType
from src.utils.messaging import MessageBus, Message, MessageType
message_bus = MessageBus()

# Nouvelle fonction pour traiter les messages d'audit
def process_audit_report(audit_data: dict) -> dict:
    """Traite un rapport d'audit et corrige les fichiers."""
    print(f"🔧 Fixer reçoit un audit de {audit_data.get('files_audited', 0)} fichiers")
    
    results = []
    for file_result in audit_data.get("detailed_results", []):
        if file_result.get("has_issues", False):
            # Corriger le fichier
            fix_result = fix_code(
                file_result["file"],
                file_result.get("issues_details", [])
            )
            results.append(fix_result)
    
    summary = {
        "files_processed": len(results),
        "files_fixed": sum(1 for r in results if r.get("changes_made", False)),
        "total_fixes": sum(r.get("issues_fixed", 0) for r in results)
    }
    
    # Envoyer un message au Testeur
    message_bus.send(Message(
        sender="Fixer",
        receiver="Judge",
        msg_type=MessageType.FIX_REQUEST,
        content={
            "fix_summary": summary,
            "project_path": audit_data.get("project", "")
        }
    ))
    
    return summary

# Abonnement aux messages
def subscribe_to_messages():
    """Permet au Fixer de recevoir des messages."""
    def callback(message: Message):
        if message.msg_type == MessageType.AUDIT_REPORT:
            print(f"🔧 Fixer reçoit un rapport d'audit")
            process_audit_report(message.content)
    
    message_bus.subscribe("Fixer", callback)

def fix_code(file_path: str, issues: list) -> dict:
    """
    Essaie de corriger les problèmes dans un fichier.
    """
    print(f"   🔧 Correction de {file_path}")
    
    try:
        # 1. Lire le fichier
        content = read_file(file_path, agent_name="Fixer")
        
        # 2. Corriger un problème simple
        fixed_content = content
        
        # Vérifier si le fichier commence par une shebang ou un import
        lines = content.split('\n')
        
        # Problème simple : ajouter une docstring si manquante
        has_docstring = False
        for line in lines[:5]:  # Chercher dans les premières lignes
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                has_docstring = True
                break
        
        # Si pas de docstring et que le fichier contient des fonctions/classes
        if not has_docstring and ('def ' in content or 'class ' in content):
            # Trouver où insérer la docstring (après les imports)
            insert_line = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('import ') and not line.strip().startswith('from ') and not line.strip().startswith('#'):
                    insert_line = i
                    break
            
            # Ajouter une docstring simple
            docstring = '"""Documentation automatique."""'
            lines.insert(insert_line, docstring)
            fixed_content = '\n'.join(lines)
        
        # 3. Écrire le fichier corrigé (si changé)
        if fixed_content != content:
            write_file(file_path, fixed_content, agent_name="Fixer")
            changes_made = True
            print(f"   ✓ Docstring ajoutée")
        else:
            changes_made = False
            print(f"   ✗ Aucun changement nécessaire")
        
        # 4. Résultat
        result = {
            "file": file_path,
            "changes_made": changes_made,
            "issues_fixed": 1 if changes_made else 0
        }
        
        # 5. Log
        log_experiment(
            agent_name="Fixer",
            model_used="tool",
            action=ActionType.FIX,
            details={
                "input_prompt": f"Correction du fichier {file_path}",
                "output_response": json.dumps(result, indent=2),
                "file": file_path,
                "changes_made": changes_made,
                "operation": "fix_code"
            },
            status="SUCCESS"
        )
        
        return result
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la correction : {e}")
        return {
            "file": file_path, 
            "error": str(e), 
            "changes_made": False,
            "issues_fixed": 0
        }