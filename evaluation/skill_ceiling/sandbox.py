"""
Sandbox — Isolated environment for running skill level tests.

SkillSandbox creates temporary directories under /tmp/skill_ceiling/L{N}/
with the task template, test file, and requirements for pytest execution.
"""

import os
import shutil
from pathlib import Path

from .skills_bank import SKILLS


SANDBOX_ROOT = Path("/tmp/skill_ceiling")


class SkillSandbox:
    """Manages temporary sandbox directories for testing skill levels."""

    @staticmethod
    def provision(level: int) -> dict:
        """
        Create a sandbox directory for a given skill level.

        Args:
            level: The skill level (1-10).

        Returns:
            dict with paths: task_dir, template_path, test_path, requirements_path
        """
        task = SKILLS[level]
        task_dir = SANDBOX_ROOT / f"L{level}"
        task_dir.mkdir(parents=True, exist_ok=True)

        template_path = task_dir / "task_template.py"
        test_path = task_dir / "test_task.py"
        requirements_path = task_dir / "requirements.txt"

        # Write boilerplate
        template_path.write_text(task["boilerplate"])

        # Write test code (strip leading whitespace for proper formatting)
        test_code = task["test_code"]
        if test_code.startswith("\n"):
            test_code = test_code[1:]
        test_path.write_text(test_code)

        # Write requirements
        reqs = task.get("requirements", [])
        if reqs:
            requirements_path.write_text(" ".join(reqs))
        else:
            requirements_path.write_text("")

        return {
            "task_dir": str(task_dir),
            "template_path": str(template_path),
            "test_path": str(test_path),
            "requirements_path": str(requirements_path),
        }

    @staticmethod
    def provision_all() -> list[dict]:
        """
        Create sandboxes for all 10 levels at once.

        Returns:
            List of path dicts for each level.
        """
        paths = []
        for level in sorted(SKILLS.keys()):
            paths.append(SkillSandbox.provision(level))
        return paths

    @staticmethod
    def cleanup() -> None:
        """Remove the entire /tmp/skill_ceiling/ directory."""
        if SANDBOX_ROOT.exists():
            shutil.rmtree(str(SANDBOX_ROOT))

    @staticmethod
    def get_sandbox_path(level: int) -> str:
        """Get the sandbox directory path for a level."""
        return str(SANDBOX_ROOT / f"L{level}")