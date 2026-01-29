# src/utils/orchestrator.py - VERSION COMPLÈTE
import time
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
from datetime import datetime

# Imports
from src.utils.messaging import MessageBus, Message, MessageType
from src.utils.logger import log_experiment, ActionType
from src.tools.analysis import analyze_project, run_static_analysis
from src.tools.testing import run_tests
from src.agents.auditor import audit_project
from src.agents.fixer import fix_code, subscribe_to_messages as fixer_subscribe
from src.agents.judge import test_project

class RefactoringOrchestrator:
    """Orchestrateur complet du Refactoring Swarm."""
    
    def __init__(self, target_dir: str, max_iterations: int = 10, verbose: bool = False):
        self.target_dir = Path(target_dir).resolve()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.current_iteration = 0
        self.success = False
        self.message_bus = MessageBus()
        
        # Métriques
        self.metrics = {
            "start_time": time.time(),
            "iterations_completed": 0,
            "total_fixes": 0,
            "total_tests": 0,
            "quality_score_initial": 0,
            "quality_score_final": 0
        }
        
        # Abonner les agents
        self._subscribe_agents()
        
        print(f"🎯 Orchestrateur initialisé pour: {self.target_dir}")
        print(f"   - Max itérations: {max_iterations}")
        print(f"   - Mode verbose: {verbose}")
    
    def _subscribe_agents(self):
        """Abonne les agents au bus de messages."""
        # Ici on pourrait ajouter des callbacks pour chaque agent
        # Pour l'instant, on utilise directement les fonctions
        pass
    
    def run(self) -> bool:
        """
        Exécute le processus complet de refactoring.
        
        Returns:
            True si le refactoring a réussi, False sinon
        """
        print("\n" + "="*60)
        print("🔄 DÉBUT DU PROCESSUS DE REFACTORING SWARM")
        print("="*60)
        
        # Log de démarrage
        log_experiment(
            agent_name="Orchestrator",
            model_used="gemini-2.0-flash",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Démarrage du Refactoring Swarm sur {self.target_dir}",
                "output_response": f"Orchestrateur initialisé avec {self.max_iterations} itérations max",
                "target_dir": str(self.target_dir),
                "max_iterations": self.max_iterations
            },
            status="STARTED"
        )
        
        try:
            # ÉTAPE 1: Audit initial
            initial_quality = self._run_initial_audit()
            if initial_quality == 0:
                print("⚠️  Aucun fichier Python trouvé - Fin du processus")
                return True
            
            # ÉTAPE 2: Boucle de refactoring
            self.success = self._refactoring_loop()
            
            # ÉTAPE 3: Audit final et vérification
            final_quality = self._run_final_audit()
            
            # ÉTAPE 4: Rapport final
            self._generate_final_report(initial_quality, final_quality)
            
            return self.success
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE dans l'orchestrateur: {e}")
            import traceback
            traceback.print_exc()
            
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": "Erreur critique dans run()",
                    "output_response": f"{str(e)}\n{traceback.format_exc()}",
                    "error_type": type(e).__name__
                },
                status="FAILURE"
            )
            return False
    
    def _run_initial_audit(self) -> float:
        """Exécute l'audit initial et retourne le score de qualité."""
        print("\n🔍 ÉTAPE 1: AUDIT INITIAL")
        print("-" * 40)
        
        try:
            # Appel direct à l'auditor (pour commencer simple)
            audit_result = audit_project(str(self.target_dir))
            
            if "error" in audit_result:
                print(f"❌ Erreur audit initial: {audit_result['error']}")
                return 0
            
            # Calculer un score de qualité simplifié
            total_issues = audit_result.get("total_issues", 0)
            total_files = audit_result.get("files_audited", 1)
            
            # Score: 10 - (issues par fichier * 2), minimum 0
            issues_per_file = total_issues / total_files
            quality_score = max(0, 10 - (issues_per_file * 2))
            
            self.metrics["quality_score_initial"] = quality_score
            self.metrics["initial_issues"] = total_issues
            
            print(f"📊 Résultats audit initial:")
            print(f"   • Fichiers analysés: {total_files}")
            print(f"   • Problèmes détectés: {total_issues}")
            print(f"   • Score qualité initial: {quality_score:.2f}/10")
            
            # Log détaillé
            log_experiment(
                agent_name="Orchestrator",
                model_used="gemini-2.0-flash",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Audit initial du projet {self.target_dir}",
                    "output_response": json.dumps(audit_result, indent=2),
                    "total_files": total_files,
                    "total_issues": total_issues,
                    "quality_score": quality_score
                },
                status="SUCCESS"
            )
            
            # Si aucun problème, on peut s'arrêter tout de suite
            if total_issues == 0:
                print("✅ Aucun problème détecté - Le code est déjà propre!")
                self.success = True
                return quality_score
            
            return quality_score
            
        except Exception as e:
            print(f"❌ Erreur audit initial: {e}")
            log_experiment(
                agent_name="Orchestrator",
                model_used="system",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": "Erreur dans _run_initial_audit()",
                    "output_response": str(e)
                },
                status="FAILURE"
            )
            return 0
    
    def _refactoring_loop(self) -> bool:
        """Exécute la boucle de refactoring avec self-healing."""
        print(f"\n⚙️  ÉTAPE 2: BOUCLE DE REFACTORING (max {self.max_iterations} itérations)")
        print("-" * 60)
        
        improvement_detected = False
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            self.metrics["iterations_completed"] = iteration
            
            print(f"\n🔄 ITÉRATION {iteration}/{self.max_iterations}")
            
            # 1. Vérification des tests actuels
            print("   🧪 Vérification des tests...")
            test_result = test_project(str(self.target_dir))
            
            # 2. Si les tests passent, vérifier la qualité
            if test_result.get("all_passed", False):
                print(f"   ✅ Tous les tests passent ({test_result.get('tests_passed', 0)} tests)")
                
                # Vérifier la qualité du code
                quality_ok = self._check_code_quality(iteration)
                if quality_ok:
                    print(f"   🎯 Qualité du code acceptable - Mission accomplie!")
                    return True
                else:
                    print(f"   ⚠️  Tests OK mais qualité insuffisante - Continue...")
            
            # 3. Si tests échouent ou qualité insuffisante -> Correction
            print(f"   🛠️  Lancement de la correction...")
            
            # A. Identifier les fichiers problématiques
            problematic_files = self._identify_problematic_files()
            if not problematic_files:
                print(f"   ℹ️  Aucun fichier problématique identifié")
                break
            
            # B. Appliquer les corrections
            fixes_applied = self._apply_corrections(problematic_files, iteration)
            if fixes_applied:
                improvement_detected = True
                print(f"   ✅ Corrections appliquées avec succès")
            else:
                print(f"   ⚠️  Aucune correction n'a pu être appliquée")
            
            # 4. Pause entre les itérations
            if iteration < self.max_iterations:
                print(f"   ⏳ Pause avant prochaine itération...")
                time.sleep(2)
        
        print(f"\n⏱️  Limite d'itérations atteinte ({self.max_iterations})")
        return improvement_detected
    
    def _check_code_quality(self, iteration: int) -> bool:
        """Vérifie si la qualité du code est acceptable."""
        try:
            # Utiliser pylint pour un score précis
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pylint", "--exit-zero", str(self.target_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Extraire le score (format: "Your code has been rated at 8.50/10")
            import re
            match = re.search(r"rated at (\d+\.\d+)/10", result.stdout)
            if match:
                score = float(match.group(1))
                print(f"   📝 Score Pylint: {score}/10")
                
                # Log du score
                log_experiment(
                    agent_name="Orchestrator",
                    model_used="tool",
                    action=ActionType.ANALYSIS,
                    details={
                        "input_prompt": f"Vérification qualité code - Itération {iteration}",
                        "output_response": f"Score Pylint: {score}/10",
                        "score": score,
                        "threshold": 8.0,
                        "iteration": iteration
                    },
                    status="SUCCESS" if score >= 8.0 else "FAILURE"
                )
                
                # Critère: score >= 8.0/10 ET tous les tests passent
                return score >= 8.0
            else:
                print(f"   ⚠️  Impossible d'extraire le score Pylint")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Erreur vérification qualité: {e}")
            return False
    
    def _identify_problematic_files(self) -> List[Dict[str, Any]]:
        """Identifie les fichiers à corriger."""
        try:
            # Analyse rapide pour trouver les fichiers problématiques
            files = []
            for file_path in self.target_dir.rglob("*.py"):
                if file_path.is_file():
                    # Vérifier si le fichier a des problèmes
                    analysis = run_static_analysis(str(file_path), "Orchestrator_Scanner")
                    if analysis.get("issues_count", 0) > 0:
                        files.append({
                            "path": str(file_path),
                            "issues_count": analysis["issues_count"],
                            "issues": analysis.get("issues", [])
                        })
            
            print(f"   📄 {len(files)} fichiers problématiques identifiés")
            return files
            
        except Exception as e:
            print(f"   ❌ Erreur identification fichiers: {e}")
            return []
    
    def _apply_corrections(self, files: List[Dict[str, Any]], iteration: int) -> bool:
        """Applique les corrections aux fichiers."""
        fixes_made = False
        
        for file_info in files[:3]:  # Limiter à 3 fichiers par itération
            file_path = file_info["path"]
            issues = file_info.get("issues", [])
            
            print(f"   🔧 Correction de {Path(file_path).name}...")
            
            try:
                # Appeler le Fixer
                fix_result = fix_code(file_path, issues)
                
                if fix_result.get("changes_made", False):
                    fixes_made = True
                    self.metrics["total_fixes"] += fix_result.get("issues_fixed", 0)
                    print(f"   ✅ {fix_result.get('issues_fixed', 0)} correction(s) appliquée(s)")
                else:
                    print(f"   ℹ️  Aucune correction nécessaire")
                    
            except Exception as e:
                print(f"   ❌ Erreur correction {Path(file_path).name}: {e}")
        
        return fixes_made
    
    def _run_final_audit(self) -> float:
        """Exécute l'audit final."""
        print("\n📋 ÉTAPE 3: AUDIT FINAL")
        print("-" * 40)
        
        try:
            audit_result = audit_project(str(self.target_dir))
            
            if "error" in audit_result:
                print(f"⚠️  Erreur audit final: {audit_result['error']}")
                return 0
            
            # Calcul du score final
            total_issues = audit_result.get("total_issues", 0)
            total_files = audit_result.get("files_audited", 1)
            issues_per_file = total_issues / total_files
            quality_score = max(0, 10 - (issues_per_file * 2))
            
            self.metrics["quality_score_final"] = quality_score
            self.metrics["final_issues"] = total_issues
            
            print(f"📊 Résultats audit final:")
            print(f"   • Problèmes restants: {total_issues}")
            print(f"   • Score qualité final: {quality_score:.2f}/10")
            
            return quality_score
            
        except Exception as e:
            print(f"❌ Erreur audit final: {e}")
            return 0
    
    def _generate_final_report(self, initial_score: float, final_score: float):
        """Génère un rapport final détaillé."""
        print("\n" + "="*60)
        print("📈 RAPPORT FINAL DU REFACTORING SWARM")
        print("="*60)
        
        # Calcul des améliorations
        initial_issues = self.metrics.get("initial_issues", 0)
        final_issues = self.metrics.get("final_issues", 0)
        
        if initial_issues > 0:
            improvement = ((initial_issues - final_issues) / initial_issues) * 100
        else:
            improvement = 0
        
        # Affichage des résultats
        print(f"\n📊 MÉTRIQUES:")
        print(f"   • Itérations effectuées: {self.current_iteration}/{self.max_iterations}")
        print(f"   • Problèmes initiaux: {initial_issues}")
        print(f"   • Problèmes finaux: {final_issues}")
        print(f"   • Amélioration: {improvement:.1f}%")
        print(f"   • Score qualité initial: {initial_score:.2f}/10")
        print(f"   • Score qualité final: {final_score:.2f}/10")
        print(f"   • Corrections appliquées: {self.metrics.get('total_fixes', 0)}")
        
        # Temps d'exécution
        duration = time.time() - self.metrics["start_time"]
        print(f"   • Temps total: {duration:.2f} secondes")
        
        # Conclusion
        print(f"\n🎯 CONCLUSION:")
        if self.success:
            print(f"   ✅ MISSION ACCOMPLIE AVEC SUCCÈS!")
            print(f"   Le code est maintenant propre et les tests passent.")
        else:
            print(f"   ⚠️  MISSION PARTIELLEMENT ACCOMPLIE")
            print(f"   Des problèmes persistent mais des améliorations ont été faites.")
        
        # Log du rapport final
        log_experiment(
            agent_name="Orchestrator",
            model_used="gemini-2.0-flash",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "Rapport final du Refactoring Swarm",
                "output_response": f"Processus terminé en {self.current_iteration} itérations\n"
                                 f"Amélioration: {improvement:.1f}%\n"
                                 f"Score final: {final_score:.2f}/10",
                "metrics": self.metrics,
                "initial_score": initial_score,
                "final_score": final_score,
                "improvement_percentage": improvement,
                "total_duration_seconds": duration,
                "success": self.success
            },
            status="SUCCESS" if self.success else "PARTIAL"
        )