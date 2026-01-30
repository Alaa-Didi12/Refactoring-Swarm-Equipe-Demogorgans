# test_analysis_fix.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialiser la sécurité d'abord
from src.tools import init_security
init_security("./sandbox")

# Créer un fichier Python de test dans sandbox
test_code = """
def hello():
    print("Hello")

def add(a, b):
    return a + b
"""

from src.tools import write_file
write_file("test_analysis.py", test_code, agent_name="Test")

# Tester analyze_project
from src.tools import analyze_project
result = analyze_project(".", agent_name="Test")
print(f"✅ Analyse projet réussie !")
print(f"   Fichiers trouvés: {result['total_files']}")
print(f"   Fichiers analysés: {len(result['files'])}")