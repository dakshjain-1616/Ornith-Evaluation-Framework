"""
Evaluator — Runs pytest against generated code in isolated sandbox.

SkillEvaluator writes the model-generated code into the sandbox task_template.py,
installs any required dependencies, and runs pytest.
"""

import os
import sys
import subprocess
import importlib
import traceback
from pathlib import Path

from .skills_bank import SKILLS
from .sandbox import SkillSandbox


class SkillEvaluator:
    """
    Evaluates model-generated code by writing it into a sandbox and running tests.
    """

    def __init__(self):
        self._deps_installed = set()  # Track which levels have deps installed

    def evaluate(self, level: int, code: str) -> dict:
        """
        Evaluate model-generated code for a given skill level.

        Steps:
        1. Ensure sandbox exists
        2. Write code into task_template.py (replacing the placeholder pass)
        3. Install dependencies (once per level)
        4. Run pytest in the sandbox directory
        5. Return pass/fail result

        Args:
            level: Skill level (1-10).
            code: Model-generated code string.

        Returns:
            dict with keys: pass (bool), output (str), exit_code (int)
        """
        task = SKILLS[level]
        sandbox_paths = SkillSandbox.provision(level)
        task_dir = sandbox_paths["task_dir"]
        template_path = sandbox_paths["template_path"]

        # Write the generated code into the template file
        # The code replaces the entire file content (it contains the full function)
        with open(template_path, "w") as f:
            f.write(code)

        # Install dependencies if needed
        self._install_deps(level)

        # Run pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_task.py", "-v", "--tb=short"],
            cwd=task_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + "\n" + result.stderr
        passed = result.returncode == 0

        return {
            "pass": passed,
            "output": output.strip(),
            "exit_code": result.returncode,
        }

    def _install_deps(self, level: int) -> None:
        """Install pip dependencies for a level (only once)."""
        if level in self._deps_installed:
            return

        task = SKILLS[level]
        reqs = task.get("requirements", [])
        if not reqs:
            self._deps_installed.add(level)
            return

        print(f"  Installing deps for level {level}: {' '.join(reqs)}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q"] + reqs,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"  Warning: pip install for level {level}: {result.stderr.strip()}")
        self._deps_installed.add(level)

    def evaluate_with_code_template(self, level: int, code: str) -> dict:
        """
        Alternative: Write code that REPLACES the function body in the template.
        This is useful when the model only generates the function body, not the full file.

        The code is inserted into the template by replacing the first `pass` statement.
        """
        task = SKILLS[level]
        sandbox_paths = SkillSandbox.provision(level)
        template_path = sandbox_paths["template_path"]

        # Write the code into the template file, preserving imports
        with open(template_path, "r") as f:
            template_content = f.read()

        # Replace the first `pass` (placeholder) with the generated code
        # Use 4-space indented pass to avoid replacing 'pass' in strings
        if "    pass" in template_content and code.strip():
            modified = template_content.replace("    pass", code, 1)
            with open(template_path, "w") as f:
                f.write(modified)
        else:
            # Fallback: just write code directly
            with open(template_path, "w") as f:
                f.write(code)

        self._install_deps(level)

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_task.py", "-v", "--tb=short"],
            cwd=sandbox_paths["task_dir"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + "\n" + result.stderr
        passed = result.returncode == 0

        return {
            "pass": passed,
            "output": output.strip(),
            "exit_code": result.returncode,
        }