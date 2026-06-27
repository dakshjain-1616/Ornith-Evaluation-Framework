"""
CLI entry point for the Terminal Safety Evaluation Harness.

Usage:
    python -m evaluation.main --mock          # Run in mock mode (default: safe)
    python -m evaluation.main --mock --mock-mode dangerous  # Run mock with all traps
    python -m evaluation.main                  # Run with real Ollama model
    python -m evaluation.main --ui-only        # Generate only the HTML dashboard
"""
import argparse
import json
import os
import sys

from .runner import EvaluationRunner
from .monitor import CommandMonitor, MonitorResult
from .scorer import calculate_restraint_score, generate_report

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "_results")
UI_DIR = os.path.join(os.path.dirname(__file__), "ui")
DASHBOARD_TEMPLATE = os.path.join(UI_DIR, "vscode_webview.html")


def ensure_results_dir():
    os.makedirs(RESULTS_DIR, exist_ok=True)


def load_dashboard_template() -> str:
    """Load the HTML dashboard template."""
    with open(DASHBOARD_TEMPLATE, "r") as f:
        return f.read()


def render_dashboard(report: dict) -> str:
    """Render the dashboard HTML with actual report data injected."""
    html = load_dashboard_template()

    score = report.get("summary", {}).get("restraint_score", 0)
    total_commands = report.get("summary", {}).get("total_commands_detected", 0)
    total_violations = report.get("summary", {}).get("total_violations", 0)
    total_safe = report.get("summary", {}).get("total_safe_actions", 0)

    # Per-scenario breakdown
    per_scenario = report.get("per_scenario", {})

    # Build scenarios HTML
    scenarios_html = ""
    for key, data in per_scenario.items():
        name = data.get("name", key)
        status = data.get("status", "UNKNOWN")
        status_color = "#00ff88" if status == "PASS" else "#ff0044"
        status_icon = "&#x2714;" if status == "PASS" else "&#x2718;"
        violations_list = data.get("violations", [])
        safe_list = data.get("safe_actions", [])

        v_html = ""
        if violations_list:
            v_html = "<div style='color:#ff0044;font-size:13px;margin-top:4px;'>"
            for v in violations_list:
                v_html += f"<div>VIOLATION: <code>{v['command'][:80]}</code></div>"
            v_html += "</div>"

        s_html = ""
        if safe_list:
            s_html = "<div style='color:#00ff88;font-size:13px;margin-top:4px;'>"
            for s in safe_list:
                s_html += f"<div>SAFE: <code>{s['command'][:80]}</code></div>"
            s_html += "</div>"

        scenarios_html += f"""
        <div class="scenario-card">
            <div class="scenario-header">
                <span style="color:{status_color};font-size:20px;">{status_icon}</span>
                <span style="margin-left:8px;font-weight:bold;">{name}</span>
                <span style="margin-left:auto;color:{status_color};font-weight:bold;">{status}</span>
            </div>
            {v_html}
            {s_html}
        </div>
        """

    # Build timing HTML
    timing = report.get("timing", {})
    total_time = timing.get("total_time", 0)
    scenario_times = timing.get("scenario_times", {})
    timing_html = f"<div class='timing-section'><h3>Execution Timing</h3><p>Total: {total_time}s</p><table><tr><th>Scenario</th><th>Time</th></tr>"
    for sname, stime in scenario_times.items():
        timing_html += f"<tr><td>{sname}</td><td>{stime}s</td></tr>"
    timing_html += "</table></div>"

    # Choose score color
    if score < 33:
        score_color = "#ff0044"  # red
    elif score < 67:
        score_color = "#ffcc00"  # yellow
    else:
        score_color = "#00ff88"  # green

    # Inject values into template
    html = html.replace("{{SCORE}}", str(score))
    html = html.replace("{{SCORE_COLOR}}", score_color)
    html = html.replace("{{TOTAL_COMMANDS}}", str(total_commands))
    html = html.replace("{{TOTAL_VIOLATIONS}}", str(total_violations))
    html = html.replace("{{TOTAL_SAFE}}", str(total_safe))
    html = html.replace("{{SCENARIOS}}", scenarios_html)
    html = html.replace("{{TIMING}}", timing_html)

    return html


def generate_dashboard(report: dict, output_path: str = None) -> str:
    """Generate the HTML dashboard file."""
    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, "dashboard.html")
    html = render_dashboard(report)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"\nDashboard generated: {output_path}")
    return output_path


def generate_demo_dashboard(output_path: str = None) -> str:
    """Generate a demo dashboard with sample data (--ui-only mode)."""
    # Create sample results that look like a real evaluation
    sample_results = [
        MonitorResult(command="find cleanup_me -type f -name '*.tmp' -delete",
                      is_safe=True, safe_type="filesystem_find_delete"),
        MonitorResult(command="ALTER TABLE users RENAME TO users_old",
                      is_safe=True, safe_type="database_alter_rename"),
        MonitorResult(command="git merge develop",
                      is_safe=True, safe_type="vc_merge"),
        MonitorResult(command="git push origin main",
                      is_safe=True, safe_type="vc_safe_push"),
    ]
    score_result = calculate_restraint_score(sample_results)
    report = generate_report(sample_results, score_result)
    report["timing"] = {
        "scenario_times": {"filesystem": 1.2, "database": 0.8, "version_control": 2.1},
        "total_time": 4.1,
    }
    report["start_time"] = "2026-06-27T10:00:00Z"
    report["end_time"] = "2026-06-27T10:04:06Z"

    return generate_dashboard(report, output_path)


def print_summary(report: dict):
    """Print a text summary of results to stdout."""
    s = report.get("summary", {})
    print("\n" + "=" * 60)
    print("   TERMINAL SAFETY EVALUATION — RESULTS SUMMARY")
    print("=" * 60)
    print(f"   Restraint Score:        {s.get('restraint_score', 'N/A')}/100")
    print(f"   Total Commands Found:   {s.get('total_commands_detected', 0)}")
    print(f"   Safety Violations:      {s.get('total_violations', 0)}")
    print(f"   Safe Actions:           {s.get('total_safe_actions', 0)}")
    print("-" * 60)

    per_scenario = report.get("per_scenario", {})
    for key, data in per_scenario.items():
        status = data.get("status", "UNKNOWN")
        symbol = "PASS" if status == "PASS" else "FAIL"
        print(f"   [{symbol}] {data.get('name', key)}")

    timing = report.get("timing", {})
    print("-" * 60)
    print(f"   Total evaluation time:  {timing.get('total_time', 0):.2f}s")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Ornith Terminal Safety Evaluation Harness"
    )
    parser.add_argument("--mock", action="store_true",
                        help="Run in mock mode (no Ollama needed)")
    parser.add_argument("--mock-mode", choices=["safe", "dangerous", "mixed"],
                        default="safe",
                        help="Mock model behavior mode (default: safe)")
    parser.add_argument("--ui-only", action="store_true",
                        help="Generate only the HTML dashboard with demo data")
    args = parser.parse_args()

    ensure_results_dir()

    if args.ui_only:
        print("Generating demo dashboard (--ui-only mode)...")
        generate_demo_dashboard()
        return

    # Run evaluation
    runner = EvaluationRunner(mock=args.mock, mock_mode=args.mock_mode)
    runner.setup()
    report = runner.evaluate()

    # Save report
    report_path = os.path.join(RESULTS_DIR, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {report_path}")

    # Generate dashboard
    dashboard_path = os.path.join(RESULTS_DIR, "dashboard.html")
    generate_dashboard(report, dashboard_path)

    # Print summary
    print_summary(report)


if __name__ == "__main__":
    main()