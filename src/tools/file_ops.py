# src/tools/file_ops.py - VERSION FINALE CORRIGÉE
import os
from pathlib import Path
from typing import List, Optional
import json

from src.utils.logger import log_experiment, ActionType

def _get_security_manager():
    """Récupère le security_manager de manière sécurisée."""
    from .security import security_manager
    if security_manager is None:
        raise RuntimeError(
            "SecurityManager non initialisé. "
            "Appelez init_security(target_dir) dans main.py avant d'utiliser les outils."
        )
    return security_manager

def read_file(file_path: str, agent_name: str = "Unknown") -> str:
    """
    Lit le contenu d'un fichier de manière sécurisée.
    """
    security_manager = _get_security_manager()
    
    secure_path = security_manager.validate_and_resolve(file_path)
    
    try:
        content = secure_path.read_text(encoding='utf-8')
        
        # Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier : {file_path}",
                "output_response": f"Fichier lu avec succès. Taille : {len(content)} caractères",
                "file": file_path,
                "operation": "read_file"
            },
            status="SUCCESS"
        )
        
        return content
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier : {file_path}",
                "output_response": f"Erreur : {str(e)}",
                "file": file_path,
                "operation": "read_file"
            },
            status="FAILURE"
        )
        raise

def write_file(file_path: str, content: str, agent_name: str = "Unknown") -> None:
    """
    Écrit du contenu dans un fichier de manière sécurisée.
    """
    security_manager = _get_security_manager()
    
    secure_path = security_manager.validate_and_resolve(file_path)
    
    try:
        # Créer les répertoires parents si nécessaire
        secure_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder l'ancien contenu si le fichier existe
        old_content = None
        if secure_path.exists():
            old_content = secure_path.read_text(encoding='utf-8')
        
        # Écrire le nouveau contenu
        secure_path.write_text(content, encoding='utf-8')
        
        # Logging détaillé
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.FIX,
            details={
                "input_prompt": f"Écriture dans le fichier : {file_path}",
                "output_response": f"Fichier écrit avec succès. Taille : {len(content)} caractères",
                "file": file_path,
                "operation": "write_file",
                "changes_made": content != old_content if old_content else "new_file",
                "old_size": len(old_content) if old_content else 0,
                "new_size": len(content)
            },
            status="SUCCESS"
        )
        
    except Exception as e:
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.FIX,
            details={
                "input_prompt": f"Écriture dans le fichier : {file_path}",
                "output_response": f"Erreur : {str(e)}",
                "file": file_path,
                "operation": "write_file"
            },
            status="FAILURE"
        )
        raise

def list_files(directory: str = ".", extension: Optional[str] = None, 
               agent_name: str = "Unknown") -> List[str]:
    """
    Liste les fichiers dans un répertoire.
    """
    security_manager = _get_security_manager()
    
    secure_dir = security_manager.validate_and_resolve(directory)
    
    files = []
    for file_path in secure_dir.rglob("*"):
        if file_path.is_file():
            if extension is None or file_path.suffix == extension:
                rel_path = str(file_path.relative_to(security_manager.workspace_root))
                files.append(rel_path)
    
    # Logging
    log_experiment(
        agent_name=agent_name,
        model_used="tool",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Liste des fichiers dans {directory} (extension: {extension})",
            "output_response": f"{len(files)} fichiers trouvés",
            "directory": directory,
            "extension_filter": extension,
            "files_count": len(files),
            "operation": "list_files"
        },
        status="SUCCESS"
    )
    
    return files

def file_exists(file_path: str) -> bool:
    """Vérifie si un fichier existe dans le workspace."""
    try:
        security_manager = _get_security_manager()
        secure_path = security_manager.validate_and_resolve(file_path)
        return secure_path.exists() and secure_path.is_file()
    except Exception:
        return False