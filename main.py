# main.py - Version Orchestrateur
import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.orchestrator import RefactoringOrchestrator
from src.utils.logger import log_experiment, ActionType
from src.tools.security import init_security

# Charger les variables d'environnement
load_dotenv()

def validate_environment():
    """Vérifie que l'environnement est correctement configuré."""
    required_keys = ["GOOGLE_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Clés API manquantes dans .env: {', '.join(missing_keys)}")
        print("🔧 Veuillez configurer vos clés dans le fichier .env")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Refactoring Swarm - Système multi-agents de refactoring automatique"
    )
    parser.add_argument(
        "--target_dir", 
        type=str, 
        required=True,
        help="Dossier contenant le code Python à refactoriser"
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Nombre maximum d'itérations de correction (défaut: 10)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mode verbeux pour le débogage"
    )
    
    args = parser.parse_args()

    # Validation du dossier cible
    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)
    
    # Validation de l'environnement
    if not validate_environment():
        sys.exit(1)
    
    print(f"🚀 REFACTORING SWARM - Démmarrage sur : {args.target_dir}")
    print(f"📊 Configuration: max_iterations={args.max_iterations}, verbose={args.verbose}")
    
    # Initialisation de la sécurité
    try:
        init_security(args.target_dir)
        print("🔒 SecurityManager initialisé avec succès")
    except Exception as e:
        print(f"❌ Erreur d'initialisation de la sécurité: {e}")
        sys.exit(1)
    
    # Log de démarrage
    log_experiment(
        agent_name="Orchestrator",
        model_used="system",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Démarrage du Refactoring Swarm sur {args.target_dir}",
            "output_response": f"Initialisation réussie. Max iterations: {args.max_iterations}",
            "target_dir": args.target_dir,
            "max_iterations": args.max_iterations
        },
        status="STARTUP"
    )
    
    try:
        # Création et exécution de l'orchestrateur
        orchestrator = RefactoringOrchestrator(
            target_dir=args.target_dir,
            max_iterations=args.max_iterations,
            verbose=args.verbose
        )
        
        # Lancement du processus de refactoring
        success = orchestrator.run()
        
        if success:
            print("\n✅ MISSION COMPLÈTE - Refactoring terminé avec succès!")
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": "Fin de mission",
                    "output_response": "Refactoring terminé avec succès",
                    "total_iterations": orchestrator.current_iteration,
                    "status": "COMPLETED"
                },
                status="SUCCESS"
            )
        else:
            print(f"\n⚠️  MISSION TERMINÉE AVEC DES PROBLÈMES")
            print(f"   Itérations effectuées: {orchestrator.current_iteration}/{args.max_iterations}")
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": "Fin de mission",
                    "output_response": "Refactoring terminé avec des problèmes",
                    "total_iterations": orchestrator.current_iteration,
                    "max_iterations_reached": orchestrator.current_iteration >= args.max_iterations,
                    "status": "COMPLETED_WITH_ISSUES"
                },
                status="WARNING"
            )
        
    except KeyboardInterrupt:
        print("\n  Processus interrompu par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        log_experiment(
            agent_name="Orchestrator",
            model_used="system",
            action=ActionType.DEBUG,
            details={
                "input_prompt": "Erreur lors de l'exécution",
                "output_response": f"Exception: {str(e)}",
                "error_type": type(e).__name__
            },
            status="FAILURE"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()