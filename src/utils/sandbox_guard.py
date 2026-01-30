# src/utils/sandbox_guard.py
import os

def ensure_in_sandbox(path):
    if "sandbox" not in os.path.abspath(path):
        raise PermissionError("Écriture hors sandbox interdite")
