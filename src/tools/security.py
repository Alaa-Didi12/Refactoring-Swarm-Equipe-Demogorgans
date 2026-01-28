# src/tools/security.py
import os
from pathlib import Path
from typing import Union

class SecurityManager:
    """Gère la sécurité et le confinement des fichiers."""
    
    def __init__(self, workspace_root: Union[str, Path]):
        """
        Args:
            workspace_root: Le dossier cible (target_dir) où tout le travail doit rester
        """
        self.workspace_root = Path(workspace_root).resolve()
        print(f"🔒 SecurityManager initialisé sur : {self.workspace_root}")
    
    def validate_and_resolve(self, target_path: Union[str, Path]) -> Path:
        """
        Valide qu'un chemin est dans le workspace et retourne le chemin résolu.
        
        Args:
            target_path: Chemin relatif ou absolu
            
        Returns:
            Path: Chemin absolu résolu et validé
            
        Raises:
            SecurityError: Si le chemin sort du workspace
        """
        # Convertir en Path
        target = Path(target_path)
        
        # Si c'est un chemin relatif, le résoudre par rapport au workspace
        if not target.is_absolute():
            resolved = (self.workspace_root / target).resolve()
        else:
            resolved = target.resolve()
        
        # Vérifier qu'il est dans le workspace
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityError(
                f"Tentative d'accès hors workspace : {resolved}\n"
                f"Workspace autorisé : {self.workspace_root}"
            )
        
        return resolved
    
    def get_relative_path(self, absolute_path: Union[str, Path]) -> str:
        """Convertit un chemin absolu en chemin relatif au workspace."""
        absolute = Path(absolute_path).resolve()
        return str(absolute.relative_to(self.workspace_root))

class SecurityError(Exception):
    """Exception pour les violations de sécurité."""
    pass

# Instance globale qui sera configurée dans main.py
security_manager = None

def init_security(workspace_root: str) -> SecurityManager:
    """Initialise le gestionnaire de sécurité (à appeler au démarrage)."""
    global security_manager
    security_manager = SecurityManager(workspace_root)
    return security_manager