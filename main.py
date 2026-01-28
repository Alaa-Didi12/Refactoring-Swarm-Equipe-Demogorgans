import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment

#  imports pour les agents ---
from src.agents.auditor import Auditor
from src.agents.fixer import Fixer
from src.agents.judge import Judge
#  imports de l'orchestrateur ---
from src.utils.orchestrator import Orchestrator

load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Refactoring Swarm - Système multi-agents de refactoring automatique"
    )
    parser.add_argument("--target_dir", type=str, required=True)
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    if not os.path.isdir(args.target_dir):
        print(f"❌ ERREUR: '{args.target_dir}' n'est pas un dossier.")
        sys.exit(1)

    print(f"🚀 DEMARRAGE SUR : {args.target_dir}")
    log_experiment("System", "STARTUP", f"Target: {args.target_dir}", "INFO")

    #  LOGIQUE D'ORCHESTRATION ---
    
    # Initialiser les agents 
    auditor = Auditor()
    fixer = Fixer()
    judge = Judge()

    # Créer l'orchestrateur
    orchestrator = Orchestrator(
        auditor=auditor,
        fixer=fixer,
        judge=judge,
        max_iterations=10
    )

    #  Lancer le processus
    result = orchestrator.run(args.target_dir)

     #  Logger le résultat
    if result["status"] == "SUCCESS":
        print("✅ MISSION_COMPLETE")
        log_experiment("System", "COMPLETION", 
                      f"Refactoring réussi en {result['iterations']} itérations", 
                      "SUCCESS")
    else:
        print("⚠️  MISSION_INCOMPLETE - Limite d'itérations atteinte")
        log_experiment("System", "COMPLETION", 
                      "Échec après 10 itérations", 
                      "WARNING")

if __name__ == "__main__":
    main()