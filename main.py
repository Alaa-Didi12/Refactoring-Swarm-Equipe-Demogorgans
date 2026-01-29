# main.py - VERSION FINALE POUR LE TP
import argparse
import sys
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Configuration
load_dotenv()

# Import sécurité
from src.tools.security import init_security

# Import orchestrateur
from src.utils.orchestrator import RefactoringOrchestrator

# Import logger
from src.utils.logger import log_experiment, ActionType

def validate_target_dir(target_dir: str) -> Path:
    """Valide et prépare le dossier cible."""
    target_path = Path(target_dir).resolve()
    
    if not target_path.exists():
        print(f"❌ ERREUR: Le dossier {target_dir} n'existe pas.")
        print(f"   Chemin absolu: {target_path}")
        sys.exit(1)
    
    # Vérifier qu'il contient des fichiers Python
    python_files = list(target_path.rglob("*.py"))
    if not python_files:
        print(f"⚠️  AVERTISSEMENT: Aucun fichier Python trouvé dans {target_dir}")
        print("   Le système fonctionnera mais ne pourra rien analyser.")
    
    print(f"🎯 Dossier cible validé: {target_path}")
    print(f"   • Fichiers Python trouvés: {len(python_files)}")
    
    return target_path

def setup_environment(target_dir: str):
    """Configure l'environnement sécurisé."""
    print("\n🔧 CONFIGURATION DE L'ENVIRONNEMENT")
    print("-" * 40)
    
    # 1. Initialiser la sécurité
    security_manager = init_security(target_dir)
    
    # 2. Partager le security_manager avec les outils
    import src.tools.security
    src.tools.security.security_manager = security_manager
    
    # 3. Créer un dossier sandbox pour les tests
    sandbox_dir = Path("sandbox") / "refactoring_workspace"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Sécurité activée")
    print(f"✅ Dossier sandbox: {sandbox_dir}")
    
    return security_manager

def main():
    """Point d'entrée principal."""
    print("\n" + "="*60)
    print("🤖 REFACTORING SWARM - SYSTEME DE MAINTENANCE AUTONOME")
    print("="*60)
    
    # 1. Parser les arguments
    parser = argparse.ArgumentParser(
        description="Système multi-agents de refactoring automatisé",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python main.py --target_dir ./sandbox/mon_projet
  python main.py --target_dir ./sandbox/dataset_inconnu --max_iter 5 --verbose
        """
    )
    parser.add_argument("--target_dir", type=str, required=True,
                       help="Dossier contenant le code Python à refactoriser")
    parser.add_argument("--max_iter", type=int, default=10,
                       help="Nombre maximum d'itérations (défaut: 10)")
    parser.add_argument("--verbose", action="store_true",
                       help="Mode verbeux pour le débogage")
    
    args = parser.parse_args()
    
    # 2. Validation
    target_path = validate_target_dir(args.target_dir)
    
    # 3. Configuration
    security_manager = setup_environment(str(target_path))
    
    # 4. Log de démarrage
    log_experiment(
        agent_name="Orchestrator",
        model_used="gemini-2.0-flash",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": "Démarrage du système Refactoring Swarm",
            "output_response": f"Dossier cible: {target_path}\n"
                             f"Itérations max: {args.max_iter}\n"
                             f"Mode verbeux: {args.verbose}",
            "target_dir": str(target_path),
            "max_iterations": args.max_iter,
            "verbose_mode": args.verbose,
            "python_version": sys.version,
            "platform": sys.platform
        },
        status="STARTED"
    )
    
    # 5. Création et exécution de l'orchestrateur
    print("\n🚀 LANCEMENT DU REFACTORING SWARM")
    print("-" * 40)
    
    orchestrator = RefactoringOrchestrator(
        target_dir=str(target_path),
        max_iterations=args.max_iter,
        verbose=args.verbose
    )
    
    # 6. Exécution principale
    success = orchestrator.run()
    
    # 7. Nettoyage et rapport final
    print("\n🧹 FINALISATION")
    print("-" * 40)
    
    # Vérifier les logs
    log_file = Path("logs/experiment_data.json")
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            print(f"✅ Logs générés: {len(logs)} entrées")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur dans les logs: {e}")
    else:
        print("❌ FICHIER DE LOGS MANQUANT - Vérifiez que le logger fonctionne!")
    
    # Message final
    if success:
        print("\n✨" + "="*50)
        print("✨ MISSION ACCOMPLIE - CODE REFACTORISÉ AVEC SUCCÈS")
        print("✨" + "="*50)
        sys.exit(0)
    else:
        print("\n⚠️" + "="*50)
        print("⚠️  MISSION INCOMPLÈTE - Problèmes détectés")
        print("⚠️" + "="*50)
        sys.exit(1)

if __name__ == "__main__":
    main()