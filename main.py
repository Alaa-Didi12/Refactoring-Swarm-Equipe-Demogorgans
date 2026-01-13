import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.orchestrator import Orchestrator
#g modifié ici le main un peu ,mais c une version simplifiéde aussi ,je reglerai ça  demog
load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True)
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    print(f"🚀 Lancement du Refactoring Swarm sur : {args.target_dir}")
    
    orchestrator = Orchestrator(args.target_dir)
    success = orchestrator.run()
    
    if success:
        print("\n✅ MISSION_COMPLETE")
        sys.exit(0)
    else:
        print("\n❌ MISSION_ECHOUEE")
        sys.exit(1)

if __name__ == "__main__":
    main()