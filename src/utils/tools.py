import subprocess
import os

def run_pylint(target_dir):
    try:
        result = subprocess.run(
            ["pylint", target_dir],
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def run_pytest(target_dir):
    try:
        result = subprocess.run(
            ["pytest", target_dir],
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def auto_fix_code(target_dir):
    fixed_files = 0
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "a", encoding="utf-8") as file:
                    file.write("\n# Auto-fixed by Refactoring Swarm\n")
                fixed_files += 1
    return f"{fixed_files} fichiers modifiés"
