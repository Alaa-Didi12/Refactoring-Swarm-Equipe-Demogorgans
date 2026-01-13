from src.utils.logger import log_experiment, ActionType

class AuditorAgent:
    def __init__(self):
        # L'ingénieur prompt remplira ceci
        self.system_prompt = "[Job of alaa ]"
    
    def analyze(self, target_dir: str) -> dict:
        """
        Retourne un plan d'audit fictif.
        À implémenter par : ALAA aand SARAH
        """
        print(f"[Auditor] Analyse simulée de {target_dir}")
        
        log_experiment(
            agent_name="Auditor",
            model_used="gemini-2.0-flash",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": self.system_prompt,
                "output_response": "PLAN D'AUDIT SIMULÉ - À IMPLÉMENTER",
                "files_scanned": 0,
                "issues_found": 0
            },
            status="SUCCESS"
        )
        
        # Structure attendue par l'orchestrateur
        return {
            "files": [],
            "issues": [],
            "suggestions": []
        }