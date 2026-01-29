# src/utils/orchestrator.py
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Imports des outils du Toolsmith
from src.tools.file_ops import list_files, read_file
from src.tools.analysis import analyze_project, run_static_analysis
from src.tools.testing import run_tests
from src.utils.logger import log_experiment, ActionType

class RefactoringOrchestrator:
    """Orchestrateur principal du Refactoring Swarm."""
    
    def __init__(self, target_dir: str, max_iterations: int = 10, verbose: bool = False):
        """
        Args:
            target_dir: Dossier contenant le code à refactoriser
            max_iterations: Nombre maximum d'itérations de correction
            verbose: Mode verbeux pour le débogage
        """
        self.target_dir = Path(target_dir).resolve()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.current_iteration = 0
        self.status_history = []
        
        print(f"🎯 Orchestrateur initialisé pour: {self.target_dir}")
    
    def run(self) -> bool:
        """
        Exécute le processus complet de refactoring.
        
        Returns:
            True si le refactoring a réussi, False sinon
        """
        print("\n" + "="*60)
        print("🔄 DÉBUT DU PROCESSUS DE REFACTORING")
        print("="*60)
        
        try:
            # Étape 1: Audit initial
            print("\n🔍 ÉTAPE 1: AUDIT INITIAL")
            initial_analysis = self._run_audit()
            
            if not initial_analysis.get("success", False):
                print("❌ Échec de l'audit initial")
                return False
            
            # Étape 2: Boucle de refactoring
            print("\n⚙️  ÉTAPE 2: BOUCLE DE REFACTORING")
            success = self._refactoring_loop()
            
            # Étape 3: Audit final
            print("\n📋 ÉTAPE 3: AUDIT FINAL")
            final_analysis = self._run_audit()
            
            # Log de synthèse
            self._log_summary(initial_analysis, final_analysis)
            
            return success
            
        except Exception as e:
            print(f"❌ Erreur dans le processus principal: {e}")
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": "Erreur dans run()",
                    "output_response": str(e),
                    "error_type": type(e).__name__
                },
                status="FAILURE"
            )
            return False
    
    def _run_audit(self) -> Dict[str, Any]:
        """
        Exécute l'audit du projet.
        
        Returns:
            Résultats de l'analyse
        """
        try:
            print(f"  📊 Analyse du projet: {self.target_dir}")
            
            # Utiliser l'outil d'analyse du Toolsmith
            analysis = analyze_project(str(self.target_dir), "Orchestrator_Audit")
            
            # Calculer le score de qualité
            total_issues = analysis.get("summary", {}).get("total_issues", 0)
            total_files = analysis.get("total_files", 0)
            
            print(f"  📁 Fichiers analysés: {total_files}")
            print(f"  ⚠️  Problèmes détectés: {total_issues}")
            
            # Log de l'audit
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Audit du projet {self.target_dir}",
                    "output_response": f"Analyse complète: {total_files} fichiers, {total_issues} problèmes",
                    "analysis_result": analysis,
                    "total_files": total_files,
                    "total_issues": total_issues
                },
                status="SUCCESS"
            )
            
            return {
                "success": True,
                "analysis": analysis,
                "total_files": total_files,
                "total_issues": total_issues,
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"  ❌ Erreur lors de l'audit: {e}")
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": "Erreur dans _run_audit()",
                    "output_response": str(e)
                },
                status="FAILURE"
            )
            return {"success": False, "error": str(e)}
    
    def _refactoring_loop(self) -> bool:
        """
        Exécute la boucle de refactoring avec self-healing.
        
        Returns:
            True si au moins une amélioration a été faite
        """
        print(f"  🔄 Lancement de la boucle de refactoring (max {self.max_iterations} itérations)")
        
        improvements_made = False
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            
            print(f"\n  🔁 ITÉRATION {iteration}/{self.max_iterations}")
            
            # Vérifier si les tests passent déjà
            print("  🧪 Vérification des tests en cours...")
            test_result = run_tests(str(self.target_dir), f"Orchestrator_Iteration_{iteration}")
            
            if test_result.get("success", False):
                print(f"  ✅ Tous les tests passent! (Itération {iteration})")
                
                # Vérifier la qualité du code
                print("  📝 Vérification de la qualité du code...")
                code_quality = self._check_code_quality()
                
                if code_quality.get("acceptable", False):
                    print(f"  🎯 Qualité du code acceptable - Arrêt de la boucle")
                    return improvements_made or True
                else:
                    print(f"  ⚠️  Tests OK mais qualité du code insuffisante, continuation...")
            
            # Si les tests échouent ou qualité insuffisante, lancer la correction
            print("  🛠️  Lancement de la correction...")
            correction_success = self._trigger_fixer(iteration, test_result)
            
            if correction_success:
                improvements_made = True
                print(f"  ✅ Correction appliquée avec succès")
            else:
                print(f"  ⚠️  Aucune correction appliquée ou erreur")
            
            # Petite pause pour éviter les boucles trop rapides
            time.sleep(1)
        
        print(f"  ⏰ Limite d'itérations atteinte ({self.max_iterations})")
        return improvements_made
    
    def _check_code_quality(self) -> Dict[str, Any]:
        """
        Vérifie la qualité globale du code.
        
        Returns:
            Dict avec les résultats de qualité
        """
        try:
            # Analyser un fichier représentatif
            python_files = list_files(str(self.target_dir), ".py", "Orchestrator_Quality_Check")
            
            if not python_files:
                return {"acceptable": True, "reason": "Aucun fichier Python"}
            
            # Prendre le premier fichier comme échantillon
            sample_file = python_files[0]
            analysis = run_static_analysis(sample_file, "Orchestrator_Quality_Sample")
            
            issues_count = analysis.get("issues_count", 0)
            acceptable = issues_count < 5  # Seuil arbitraire
            
            return {
                "acceptable": acceptable,
                "sample_file": sample_file,
                "issues_count": issues_count,
                "threshold": 5
            }
            
        except Exception as e:
            print(f"  ❌ Erreur vérification qualité: {e}")
            return {"acceptable": False, "error": str(e)}
    
    def _trigger_fixer(self, iteration: int, test_result: Dict[str, Any]) -> bool:
        """
        Déclenche le processus de correction.
        
        Args:
            iteration: Numéro d'itération
            test_result: Résultats des tests
            
        Returns:
            True si une correction a été appliquée
        """
        try:
            # ICI: Tu devras intégrer l'agent Fixer quand il sera développé
            # Pour l'instant, on simule une correction
            
            print(f"  🤖 [SIMULATION] Appel de l'agent Fixer pour itération {iteration}")
            
            # Log de l'appel au fixer
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.FIX,
                details={
                    "input_prompt": f"Déclenchement du Fixer - Itération {iteration}",
                    "output_response": f"Tests: {'SUCCESS' if test_result.get('success') else 'FAILURE'}",
                    "iteration": iteration,
                    "test_result": test_result,
                    "status": "TRIGGERED"
                },
                status="INFO"
            )
            
            # Simulation: Pour l'instant, retourne True pour continuer
            # À remplacer par l'appel réel à l'agent Fixer
            return True
            
        except Exception as e:
            print(f"  ❌ Erreur déclenchement fixer: {e}")
            return False
    
    def _log_summary(self, initial: Dict[str, Any], final: Dict[str, Any]) -> None:
        """
        Log un résumé du processus.
        
        Args:
            initial: Audit initial
            final: Audit final
        """
        print("\n" + "="*60)
        print("📈 RÉSUMÉ DU PROCESSUS")
        print("="*60)
        
        initial_issues = initial.get("total_issues", 0)
        final_issues = final.get("total_issues", 0)
        
        print(f"  • Itérations effectuées: {self.current_iteration}/{self.max_iterations}")
        print(f"  • Problèmes initiaux: {initial_issues}")
        print(f"  • Problèmes finaux: {final_issues}")
        
        if final_issues < initial_issues:
            improvement = ((initial_issues - final_issues) / max(initial_issues, 1)) * 100
            print(f"  📈 Amélioration: {improvement:.1f}% de réduction des problèmes")
        else:
            print(f"  ⚠️  Aucune amélioration détectée")
        
        # Log du résumé
        log_experiment(
            agent_name="Orchestrator",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "Résumé final du refactoring",
                "output_response": f"Processus terminé en {self.current_iteration} itérations",
                "initial_analysis": initial,
                "final_analysis": final,
                "iterations": self.current_iteration,
                "max_iterations": self.max_iterations,
                "improvement_percentage": (
                    ((initial_issues - final_issues) / max(initial_issues, 1)) * 100
                    if initial_issues > 0 else 0
                )
            },
            status="SUMMARY"
        )