from src.agents.auditor import AuditorAgent
from src.agents.fixer import FixerAgent
from src.agents.judge import JudgeAgent
from src.utils.logger import log_experiment, ActionType


#remarque: ceci est  une version un peu simplifiee ,je reglerai les details plus tard demogorgans 
class Orchestrator:
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.max_iterations = 3
        self.auditor = AuditorAgent()
        self.fixer = FixerAgent()
        self.judge = JudgeAgent()
    
    def run(self) -> bool:
        """
        Boucle principale orchestrant les 3 agents.
        Retourne True si tous les tests passent, sinon False.
        """
        print(f" Orchestrateur démarré sur {self.target_dir}")
        
        log_experiment(
            agent_name="Orchestrator",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lancement du swarm sur {self.target_dir}",
                "output_response": f"Boucle configurée avec max {self.max_iterations} itérations"
            },
            status="STARTED"
        )
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n🔄 Itération {iteration}/{self.max_iterations}")
            
            # 1_AUDIT
            plan = self.auditor.analyze(self.target_dir)
            print(f"    Plan généré: {len(plan.get('issues', []))} problèmes")
            
            # 2_CORRECTION
            fixed = self.fixer.fix(self.target_dir, plan)
            print(f"    Correction appliquée: {fixed}")
            
            # 3_VALIDATION
            tests_ok = self.judge.test(self.target_dir)
            print(f"    Tests passés: {tests_ok}")
            
            if tests_ok:
                print("\n SUCCÈeeeeeS : Tous les tests sont passés.")
                return True
        
        print("\n ÉCHEeeeeC!! : Maximum d'itérations atteint sans succès.")
        return False