from src.utils.logger import log_experiment, ActionType

class JudgeAgent:
    def __init__(self):
        # L'ingénieur prompt remplira ceci
        self.system_prompt = "[job of alaa]"
    
    def test(self, target_dir: str) -> bool:
        """
        Simule l'exécution de tests.
        À implémenter par : ALAA + Yasmine
        """
        print(f"[Judge] Test simulé dans {target_dir}")
        
        log_experiment(
            agent_name="Judge",
            model_used="system",
            action=ActionType.GENERATION,
            details={
                "input_prompt": self.system_prompt,
                "output_response": "TESTS SIMULÉS - À IMPLÉMENTER",
                "tests_passed": True
            },
            status="SUCCESS"
        )
        
        return True  # Toujours vrai en simulation