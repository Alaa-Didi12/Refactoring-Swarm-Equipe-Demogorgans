from src.utils.logger import log_experiment, ActionType

class FixerAgent:
    def __init__(self):
        # alaa here aussi
        self.system_prompt = "[job de alaa]"
    
    def fix(self, target_dir: str, audit_plan: dict) -> bool:
        """
        Simule une correction.
        À implémenter par : ALAA aand SARAH
        """
        print(f"[Fixer] Correction simulée dans {target_dir}")
        
        log_experiment(
            agent_name="Fixer",
            model_used="gemini-2.0-flash",
            action=ActionType.FIX,
            details={
                "input_prompt": self.system_prompt,
                "output_response": "CORRECTION SIMULÉE - À IMPLÉMENTER",
                "plan_received": audit_plan
            },
            status="SUCCESS"
        )
        
        return True  # Toujours vrai en simulation