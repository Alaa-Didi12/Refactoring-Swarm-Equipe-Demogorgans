import argparse
import sys
import os
from dotenv import load_dotenv

# Importe les outils de sécurité
from src.tools.security import init_security

# Importe le logger
from src.utils.logger import log_experiment, ActionType

load_dotenv()

def main():
    # 1. Lire l'argument --target_dir
    parser = argparse.ArgumentParser(description="Refactoring Swarm System")
    parser.add_argument("--target_dir", type=str, required=True, 
                       help="Dossier contenant le code à corriger")
    args = parser.parse_args()
    
    # 2. Vérifier que le dossier existe
    if not os.path.exists(args.target_dir):
        print(f"❌ Erreur : Le dossier {args.target_dir} n'existe pas.")
        sys.exit(1)
    
    print(f"🎯 Cible : {args.target_dir}")
    
    # 3. Initialiser la sécurité (TRÈS IMPORTANT)
    security_manager = init_security(args.target_dir)
    print("🔒 Sécurité activée")
    
    # 4. Log de démarrage
    log_experiment(
        agent_name="Orchestrator",
        model_used="system",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": "Démarrage du système Refactoring Swarm",
            "output_response": f"Dossier cible : {args.target_dir}",
            "operation": "system_start"
        },
        status="STARTED"
    )
    
    # 5. Appeler les agents (pour l'instant, juste un test)
    print("🤖 Démarrage des agents...")
    
    # Ici, on va appeler les agents (étape suivante)
    
    # 6. Fin
    print("\n✅ MISSION TERMINÉE")
    log_experiment(
        agent_name="Orchestrator",
        model_used="system",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": "Fin de la session",
            "output_response": "Mission complétée",
            "operation": "system_shutdown"
        },
        status="SUCCESS"
    )

if __name__ == "__main__":
    main()