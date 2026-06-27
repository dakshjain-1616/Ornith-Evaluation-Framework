"""
Main entry point for Adaptive Skill Ceiling Evaluation.

Usage:
  python -m evaluation.skill_ceiling.main
  python -m evaluation.skill_ceiling.main --mock --mock-mode start_pass_then_fail
  python -m evaluation.skill_ceiling.main --ceiling-only
  python -m evaluation.skill_ceiling.main --model maxwell1500/ornith-35b:q4_K_M
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .skills_bank import SKILLS
from .sandbox import SkillSandbox
from .evaluator import SkillEvaluator
from .ollama_runner import OllamaStreamClient, MockStreamClient
from .binary_search import BinarySearchDriver


def generate_dashboard(result: dict, output_dir: str) -> str:
    """
    Generate a scifi-themed HTML dashboard with binary search trajectory.
    
    Args:
        result: The binary search result dict.
        output_dir: Directory to save the dashboard.
    
    Returns:
        Path to the generated HTML file.
    """
    output_path = Path(output_dir) / "dashboard.html"
    
    # Prepare data as JSON for embedding
    import json as _json
    
    # Build the trajectory data for the SVG chart
    rounds = result["total_rounds"]
    history = result["history"]
    ceiling = result["ceiling"]
    
    # Determine badge color
    if ceiling >= 5:
        badge_color = "#00ff88"
        badge_glow = "#00ff8844"
        badge_text = "EXCEPTIONAL"
    elif ceiling >= 3:
        badge_color = "#f0e000"
        badge_glow = "#f0e00044"
        badge_text = "INTERMEDIATE"
    else:
        badge_color = "#ff3366"
        badge_glow = "#ff336644"
        badge_text = "BEGINNER"
    
    # Build SVG trajectory points
    if rounds > 0:
        svg_width = max(600, rounds * 80)
        svg_height = 400
        margin = 50
        plot_w = svg_width - 2 * margin
        plot_h = svg_height - 2 * margin
        
        points_data = []
        for h in history:
            x = margin + (h["round"] - 1) * plot_w / max(rounds - 1, 1)
            y = margin + plot_h - (h["level"] - 1) * plot_h / 9
            color = "#00ff88" if h["pass"] else "#ff3366"
            points_data.append({"x": x, "y": y, "color": color, "level": h["level"], "round": h["round"], "pass": h["pass"]})
        
        # Build SVG polyline points string
        polyline_points = " ".join([f"{p['x']},{p['y']}" for p in points_data])
        
        # Build vertical gridlines
        gridlines_v = ""
        for i in range(1, 11):
            y = margin + plot_h - (i - 1) * plot_h / 9
            gridlines_v += f'<line x1="{margin}" y1="{y}" x2="{svg_width - margin}" y2="{y}" stroke="#1a2040" stroke-width="1" />'
            gridlines_v += f'<text x="{margin - 10}" y="{y + 4}" fill="#556688" font-size="12" text-anchor="end">L{i}</text>'
        
        # Build round labels on X axis
        x_labels = ""
        for h in history:
            x = margin + (h["round"] - 1) * plot_w / max(rounds - 1, 1)
            x_labels += f'<text x="{x}" y="{svg_height - 10}" fill="#556688" font-size="11" text-anchor="middle">R{h["round"]}</text>'
        
        # Build trajectory dots
        trajectory_dots = ""
        for p in points_data:
            trajectory_dots += f'<circle cx="{p["x"]}" cy="{p["y"]}" r="7" fill="{p["color"]}" stroke="#0a0e1a" stroke-width="2" />'
        
        trajectory_lines = f'<polyline points="{polyline_points}" fill="none" stroke="#00f0ff" stroke-width="2" stroke-dasharray="6,3" />'
    else:
        trajectory_lines = ""
        gridlines_v = ""
        x_labels = ""
        trajectory_dots = ""
        svg_width = 600
        svg_height = 400
    
    # Build table rows
    table_rows = ""
    for h in history:
        badge_s = "✅ PASS" if h["pass"] else "❌ FAIL"
        badge_cls = "badge-pass" if h["pass"] else "badge-fail"
        code_preview = h["code"].strip()[:80].replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")
        ttft_str = f"{h['ttft']:.3f}s" if h['ttft'] else "N/A"
        speed_str = f"{h['prompt_eval_speed']:.1f} t/s" if h.get('prompt_eval_speed') else "N/A"
        table_rows += f"""
            <tr>
                <td>{h['round']}</td>
                <td><span class="level-cell">L{h['level']}</span></td>
                <td><span class="badge {badge_cls}">{badge_s}</span></td>
                <td>{ttft_str}</td>
                <td>{speed_str}</td>
                <td class="code-preview">{code_preview}</td>
            </tr>"""
    
    # Stats
    avg_ttft = sum(h["ttft"] for h in history if h["ttft"]) / max(len([h for h in history if h["ttft"]]), 1)
    levels_tested = ", ".join([f"L{h['level']}" for h in history])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adaptive Skill Ceiling — Ornith</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        background: #0a0e1a;
        color: #c8d6e5;
        font-family: 'Courier New', 'Consolas', monospace;
        padding: 20px;
        min-height: 100vh;
    }}
    .container {{
        max-width: 1100px;
        margin: 0 auto;
    }}
    .header {{
        text-align: center;
        padding: 30px 0;
        border-bottom: 1px solid #1a2040;
        margin-bottom: 30px;
    }}
    .header h1 {{
        font-size: 2.2em;
        font-weight: 700;
        background: linear-gradient(135deg, #00f0ff, #ff00aa, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 240, 255, 0.3);
        letter-spacing: 2px;
    }}
    .header .subtitle {{
        color: #556688;
        font-size: 0.9em;
        margin-top: 8px;
    }}
    .ceiling-badge {{
        text-align: center;
        padding: 30px;
        margin: 20px 0 30px;
        border: 2px solid {badge_color};
        border-radius: 12px;
        background: linear-gradient(135deg, {badge_glow}, transparent);
        animation: glowPulse 2s ease-in-out infinite;
    }}
    @keyframes glowPulse {{
        0%, 100% {{ box-shadow: 0 0 20px {badge_glow}; }}
        50% {{ box-shadow: 0 0 40px {badge_color}88; }}
    }}
    .ceiling-badge .label {{
        font-size: 0.85em;
        color: #556688;
        letter-spacing: 3px;
        text-transform: uppercase;
    }}
    .ceiling-badge .level {{
        font-size: 3.5em;
        font-weight: 700;
        color: {badge_color};
        margin: 10px 0;
        text-shadow: 0 0 30px {badge_color}66;
    }}
    .ceiling-badge .tier {{
        font-size: 1.1em;
        color: {badge_color};
        letter-spacing: 5px;
        text-transform: uppercase;
    }}
    .chart-container {{
        background: #0d1225;
        border: 1px solid #1a2040;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }}
    .chart-container h2 {{
        color: #00f0ff;
        font-size: 1em;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 15px;
        border-bottom: 1px solid #1a2040;
        padding-bottom: 10px;
    }}
    .chart-container svg {{
        display: block;
        margin: 0 auto;
        max-width: 100%;
        height: auto;
    }}
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }}
    .stat-box {{
        background: #0d1225;
        border: 1px solid #1a2040;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }}
    .stat-box .value {{
        font-size: 1.8em;
        font-weight: 700;
        color: #00f0ff;
    }}
    .stat-box .label {{
        font-size: 0.75em;
        color: #556688;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }}
    .rounds-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 0.85em;
    }}
    .rounds-table th {{
        background: #0d1225;
        color: #00f0ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.75em;
        padding: 10px 12px;
        border-bottom: 2px solid #1a2040;
        text-align: left;
    }}
    .rounds-table td {{
        padding: 8px 12px;
        border-bottom: 1px solid #111833;
        color: #8899bb;
    }}
    .rounds-table tr:hover td {{
        background: rgba(0, 240, 255, 0.03);
    }}
    .badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: 600;
    }}
    .badge-pass {{
        background: rgba(0, 255, 136, 0.15);
        color: #00ff88;
        border: 1px solid rgba(0, 255, 136, 0.3);
    }}
    .badge-fail {{
        background: rgba(255, 51, 102, 0.15);
        color: #ff3366;
        border: 1px solid rgba(255, 51, 102, 0.3);
    }}
    .level-cell {{
        color: #ff00aa;
        font-weight: 600;
    }}
    .code-preview {{
        font-family: 'Courier New', monospace;
        font-size: 0.8em;
        color: #556688;
        max-width: 250px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    .footer {{
        text-align: center;
        padding: 20px;
        color: #334466;
        font-size: 0.8em;
        border-top: 1px solid #1a2040;
        margin-top: 30px;
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>⟡ ADAPTIVE SKILL CEILING — ORNITH ⟡</h1>
        <div class="subtitle">Binary Search Evaluation · 10 Difficulty Levels</div>
    </div>

    <div class="ceiling-badge">
        <div class="label">Verified Skill Ceiling</div>
        <div class="level">Level {ceiling}</div>
        <div class="tier">{badge_text}</div>
    </div>

    <div class="stats-grid">
        <div class="stat-box">
            <div class="value">{result['total_rounds']}</div>
            <div class="label">Total Rounds</div>
        </div>
        <div class="stat-box">
            <div class="value">{result['total_time']:.2f}s</div>
            <div class="label">Total Time</div>
        </div>
        <div class="stat-box">
            <div class="value">{avg_ttft:.3f}s</div>
            <div class="label">Avg TTFT</div>
        </div>
        <div class="stat-box">
            <div class="value">{levels_tested}</div>
            <div class="label">Levels Tested</div>
        </div>
    </div>

    <div class="chart-container">
        <h2>⟐ Binary Search Trajectory</h2>
        <svg viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">
            <!-- Grid -->
            {gridlines_v}
            <!-- Axis labels -->
            {x_labels}
            <!-- Trajectory line -->
            {trajectory_lines}
            <!-- Data points -->
            {trajectory_dots}
        </svg>
    </div>

    <div class="chart-container">
        <h2>⟐ Round Details</h2>
        <table class="rounds-table">
            <thead>
                <tr>
                    <th>Round</th>
                    <th>Level</th>
                    <th>Verdict</th>
                    <th>TTFT</th>
                    <th>Prompt Speed</th>
                    <th>Code Preview</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>

    <div class="footer">
        Adaptive Skill Ceiling Framework v1.0 · {time.strftime("%Y-%m-%d %H:%M UTC")}
    </div>
</div>
</body>
</html>"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Skill Ceiling Evaluation for Ornith-35B"
    )
    parser.add_argument("--mock", action="store_true",
                        help="Use mock client instead of real Ollama")
    parser.add_argument("--mock-mode", default="all_pass",
                        choices=["all_pass", "all_fail", "start_pass_then_fail"],
                        help="Mock mode for testing binary search")
    parser.add_argument("--ceiling-only", action="store_true",
                        help="Only print the numeric ceiling, no dashboard")
    parser.add_argument("--model", default="maxwell1500/ornith-35b:q4_K_M",
                        help="Ollama model name")
    
    args = parser.parse_args()
    
    # Initialize components
    evaluator = SkillEvaluator()
    
    if args.mock:
        client = MockStreamClient(mode=args.mock_mode)
        print(f"\n  Running in MOCK mode (mode={args.mock_mode})\n")
    else:
        client = OllamaStreamClient()
        print(f"\n  Running against Ollama model: {args.model}\n")
    
    # Run binary search
    driver = BinarySearchDriver()
    result = driver.run(evaluator, client, SKILLS)
    
    # Print summary
    summary = driver.get_summary(result)
    print(summary)
    
    # Save report.json
    results_dir = os.path.join(os.path.dirname(__file__), "_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Sanitize the report (remove full code strings to keep file small)
    report = {
        "ceiling": result["ceiling"],
        "total_rounds": result["total_rounds"],
        "total_time": result["total_time"],
        "results": result["results"],
        "history": [
            {
                "round": h["round"],
                "level": h["level"],
                "pass": h["pass"],
                "test_output_preview": h["test_output"][:200] if h["test_output"] else "",
                "ttft": h["ttft"],
                "prompt_eval_speed": h["prompt_eval_speed"],
                "eval_count": h["eval_count"],
                "eval_duration": h["eval_duration"],
            }
            for h in result["history"]
        ],
    }
    
    report_path = os.path.join(results_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {report_path}")
    
    # Generate dashboard
    if not args.ceiling_only:
        dashboard_path = generate_dashboard(result, results_dir)
        print(f"  Dashboard generated: {dashboard_path}")
    
    # Cleanup sandbox
    SkillSandbox.cleanup()
    
    print(f"\n  {'='*60}")
    print(f"  FINAL VERDICT: Skill Ceiling = Level {result['ceiling']}")
    print(f"  {'='*60}\n")
    
    return result


if __name__ == "__main__":
    main()