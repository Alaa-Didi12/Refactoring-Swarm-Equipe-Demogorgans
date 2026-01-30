"""
File operations toolkit with sandbox security.
Provides safe file reading/writing operations for agents.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional


class SandboxViolationError(Exception):
    """Raised when an operation attempts to escape the sandbox."""
    pass


class FileOperations:
    """Secure file operations with sandbox enforcement."""
    
    def __init__(self, sandbox_root: str):
        """
        Initialize file operations with a sandbox root.
        
        Args:
            sandbox_root: Root directory for all file operations
        """
        self.sandbox_root = Path(sandbox_root).resolve()
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
    
    def _validate_path(self, filepath: str) -> Path:
        """
        Validate that a path is within the sandbox.
        
        Args:
            filepath: Path to validate
            
        Returns:
            Resolved absolute path
            
        Raises:
            SandboxViolationError: If path escapes sandbox
        """
        full_path = (self.sandbox_root / filepath).resolve()
        
        try:
            full_path.relative_to(self.sandbox_root)
        except ValueError:
            raise SandboxViolationError(
                f"Path '{filepath}' attempts to escape sandbox '{self.sandbox_root}'"
            )
        
        return full_path
    
    def read_file(self, filepath: str) -> str:
        """
        Safely read a file from the sandbox.
        
        Args:
            filepath: Relative path within sandbox
            
        Returns:
            File contents as string
        """
        full_path = self._validate_path(filepath)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, filepath: str, content: str) -> None:
        """
        Safely write a file to the sandbox.
        
        Args:
            filepath: Relative path within sandbox
            content: Content to write
        """
        full_path = self._validate_path(filepath)
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def list_python_files(self, directory: str = ".") -> List[str]:
        """
        List all Python files in a directory.
        
        Args:
            directory: Directory to search (relative to sandbox)
            
        Returns:
            List of Python file paths
        """
        full_path = self._validate_path(directory)
        
        python_files = []
        for root, _, files in os.walk(full_path):
            for file in files:
                if file.endswith('.py'):
                    # Get relative path from sandbox root
                    abs_file_path = Path(root) / file
                    rel_path = abs_file_path.relative_to(self.sandbox_root)
                    python_files.append(str(rel_path))
        
        return python_files
    
    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists in the sandbox."""
        try:
            full_path = self._validate_path(filepath)
            return full_path.exists()
        except SandboxViolationError:
            return False
    
    def copy_to_sandbox(self, source_dir: str) -> None:
        """
        Copy files from external directory to sandbox.
        
        Args:
            source_dir: External directory to copy from
        """
        source_path = Path(source_dir).resolve()
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        # Copy all files
        for item in source_path.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(source_path)
                dest_path = self.sandbox_root / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
    
    def get_file_info(self, filepath: str) -> dict:
        """Get information about a file."""
        full_path = self._validate_path(filepath)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        stat = full_path.stat()
        
        return {
            "path": str(filepath),
            "size": stat.st_size,
            "lines": len(self.read_file(filepath).splitlines()),
            "exists": True
        }