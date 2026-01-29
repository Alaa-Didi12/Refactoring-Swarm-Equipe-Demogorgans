# src/tools/file_ops.py - VERSION CORRIGÉE AVEC NETTOYAGE NULL BYTES
import os
from pathlib import Path
from typing import List, Optional
import json

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

def read_file(file_path: str, agent_name: str = "Unknown") -> str:
    """
    Lit le contenu d'un fichier de manière sécurisée.
    Nettoie les null bytes avant décodage.
    """
    security_manager = _get_security_manager()
    
    secure_path = security_manager.validate_and_resolve(file_path)
    
    try:
        # 1. Lire en binaire pour nettoyer les null bytes
        content_bytes = secure_path.read_bytes()
        
        # 2. Nettoyer les null bytes (CRITIQUE pour AST parsing)
        null_count = content_bytes.count(b'\x00')
        if null_count > 0:
            print(f"   ⚠️ Nettoyage de {null_count} null bytes dans {os.path.basename(file_path)}")
            content_bytes = content_bytes.replace(b'\x00', b'')
        
        # 3. Essayer différents encodages
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        encoding_used = None
        
        for encoding in encodings_to_try:
            try:
                content = content_bytes.decode(encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        
        # 4. Si aucun encodage ne fonctionne, utiliser latin-1 (accepte tout)
        if content is None:
            content = content_bytes.decode('latin-1', errors='ignore')
            encoding_used = 'latin-1 (fallback)'
        
        print(f"   ✅ {os.path.basename(file_path)} lu avec encodage: {encoding_used}")
        
        # 5. Logging
        log_experiment(
            agent_name=agent_name,
            model_used="tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier : {file_path}",
                "output_response": f"Fichier lu avec succès. Taille : {len(content)} caractères",
                "file": file_path,
                "encoding": encoding_used,
                "null_bytes_removed": null_count,
                "size_bytes": len(content_bytes),
                "size_chars": len(content),
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
        
        # Écrire le nouveau contenu (toujours en UTF-8)
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
                "new_size": len(content),
                "encoding": "utf-8"
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

def clean_file_content(content: str) -> str:
    """
    Nettoie le contenu d'un fichier des caractères problématiques.
    """
    # Supprimer les caractères de contrôle (sauf \n, \t, \r)
    import re
    # Garder : \n (nouvelle ligne), \t (tabulation), \r (retour chariot)
    # Supprimer les autres caractères de contrôle
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
    
    # Normaliser les sauts de ligne
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    return cleaned