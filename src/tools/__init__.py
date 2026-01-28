# src/tools/__init__.py
"""
Boîte à outils pour le Refactoring Swarm.
Tous les outils doivent être utilisés via les agents avec logging automatique.
"""

from .security import init_security, security_manager, SecurityError
from .file_ops import read_file, write_file, list_files, file_exists
from .analysis import run_static_analysis, get_code_metrics, analyze_project
from .testing import run_tests, check_test_coverage

# Liste de tous les outils disponibles
__all__ = [
    # Sécurité
    "init_security",
    "security_manager", 
    "SecurityError",
    
    # Opérations sur fichiers
    "read_file",
    "write_file", 
    "list_files",
    "file_exists",
    
    # Analyse de code
    "run_static_analysis",
    "get_code_metrics", 
    "analyze_project",
    
    # Tests
    "run_tests",
    "check_test_coverage",
]

# Version
__version__ = "1.0.0"