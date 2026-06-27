"""
Binary Search Driver — Finds the highest skill level Ornith can pass.

Uses binary search over levels 1-15, starting at level 8, to efficiently
isolate the skill ceiling where generated code fails unit tests.
"""

import time
from .skills_bank import SKILLS
from .sandbox import SkillSandbox
from .ollama_runner import MockStreamClient


class BinarySearchDriver:
    """
    Orchestrates binary search to find the skill ceiling.

    Algorithm:
      low=1, high=15, current=start_level (default 8)
      On PASS: low = current + 1
      On FAIL: high = current - 1
      Continue until low > high
      Ceiling = high (last passing level, or 0 if none passed)
    """

    def __init__(self, start_level: int = 8, min_level: int = 1, max_level: int = 15):
        self.start_level = start_level
        self.min_level = min_level
        self.max_level = max_level

    def run(self, evaluator, client, skills_bank: dict = None) -> dict:
        """
        Run binary search to find the skill ceiling.

        Args:
            evaluator: SkillEvaluator instance.
            client: OllamaStreamClient or MockStreamClient instance.
            skills_bank: Dict of skill definitions (default: SKILLS from skills_bank).

        Returns:
            dict with keys:
              - ceiling: int (highest passing level, 0 if none)
              - results: dict {level: 'pass'|'fail'}
              - history: list of round dicts
              - total_rounds: int
              - total_time: float (seconds)
        """
        if skills_bank is None:
            from .skills_bank import SKILLS
            skills_bank = SKILLS

        low = self.min_level
        high = self.max_level
        current = self.start_level
        results = {}
        history = []
        start_time = time.monotonic()

        print(f"\n{'='*60}")
        print(f"  ADAPTIVE SKILL CEILING — BINARY SEARCH")
        print(f"{'='*60}")
        print(f"  Range: L{low} - L{high}  |  Start: L{current}")
        print(f"{'='*60}\n")

        while low <= high:
            task = skills_bank[current]
            print(f"  [Round {len(history)+1}] Testing Level {current}: {task['name']}")
            print(f"  {'─'*50}")

            # Provision sandbox
            sandbox_paths = SkillSandbox.provision(current)

            # Generate code
            round_start = time.monotonic()
            try:
                code = client.generate(task["prompt"], current)
            except Exception as e:
                print(f"  ❌ Generation error: {e}")
                code = ""

            gen_time = time.monotonic() - round_start
            print(f"     Generation: {gen_time:.2f}s")

            # Evaluate
            try:
                result = evaluator.evaluate(current, code)
            except Exception as e:
                print(f"  ❌ Evaluation error: {e}")
                result = {"pass": False, "output": str(e), "exit_code": -1}

            verdict = "✅ PASS" if result["pass"] else "❌ FAIL"
            print(f"     Verdict: {verdict}")
            print(f"     TTFT: {client.ttft:.3f}s | Prompt speed: {client.prompt_eval_speed:.1f} tok/s")

            # Code preview
            code_preview = code.strip()[:80].replace('\n', ' ')
            if code_preview:
                print(f"     Code: {code_preview}...")

            # Record history
            history.append({
                "round": len(history) + 1,
                "level": current,
                "pass": result["pass"],
                "code": code,
                "test_output": result["output"],
                "ttft": getattr(client, "ttft", 0),
                "prompt_eval_speed": getattr(client, "prompt_eval_speed", 0),
                "eval_count": getattr(client, "eval_count", 0),
                "eval_duration": getattr(client, "eval_duration", 0),
                "gen_time": gen_time,
            })

            # Binary search update
            if result["pass"]:
                results[current] = "pass"
                low = current + 1
            else:
                results[current] = "fail"
                high = current - 1

            if low <= high:
                current = (low + high) // 2
                print(f"     Next: L{current}  (low={low}, high={high})\n")
            else:
                print(f"     Search complete (low={low}, high={high})\n")

        total_time = time.monotonic() - start_time

        # Ceiling is the highest passing level
        ceiling = 0
        for level in sorted(results.keys()):
            if results[level] == "pass":
                ceiling = level

        return {
            "ceiling": ceiling,
            "results": results,
            "history": history,
            "total_rounds": len(history),
            "total_time": total_time,
        }

    def run_mock(self, evaluator, mock_mode: str = "all_pass",
                 level_overrides: dict = None) -> dict:
        """
        Run binary search with mock client (no real model needed).

        Args:
            evaluator: SkillEvaluator instance.
            mock_mode: One of 'all_pass', 'all_fail', 'start_pass_then_fail'.
            level_overrides: Optional dict of per-level overrides.

        Returns:
            Same result dict as run().
        """
        client = MockStreamClient(mode=mock_mode, level_overrides=level_overrides)
        return self.run(evaluator, client)

    @staticmethod
    def get_summary(result: dict) -> str:
        """Format the binary search results into a readable summary string."""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("  ADAPTIVE SKILL CEILING — RESULTS SUMMARY")
        lines.append("=" * 60)

        ceiling = result["ceiling"]
        if ceiling >= 5:
            color = "🟢"
        elif ceiling >= 3:
            color = "🟡"
        else:
            color = "🔴"

        lines.append(f"\n  {color} VERIFIED SKILL CEILING: Level {ceiling}")
        lines.append(f"  {'─' * 40}")
        lines.append(f"  Total Rounds:  {result['total_rounds']}")
        lines.append(f"  Total Time:    {result['total_time']:.2f}s")

        # Per-level results
        lines.append(f"\n  {'Level':>6}  {'Result':>6}")
        lines.append(f"  {'─'*6}  {'─'*6}")
        for level in sorted(result["results"].keys()):
            r = result["results"][level]
            symbol = "✅" if r == "pass" else "❌"
            lines.append(f"  {symbol}  L{level:<4}  {r.upper()}")

        # Round-by-round trajectory
        lines.append(f"\n  Binary Search Trajectory:")
        for h in result["history"]:
            symbol = "✅" if h["pass"] else "❌"
            lines.append(f"    Round {h['round']}: L{h['level']} {symbol}")

        lines.append("=" * 60 + "\n")
        return "\n".join(lines)