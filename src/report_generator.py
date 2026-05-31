"""EvalForge HTML report generator with Chart.js visualization."""

import json
from pathlib import Path
from datetime import datetime


def generate_html_report(results: list[dict], output_path: str = "report.html"):
    labels = [r.get("name", f"Test {i}") for i, r in enumerate(results)]
    scores = [r.get("score", 0) for r in results]
    statuses = ["pass" if s >= 0.7 else "fail" for s in scores]

    pass_count = statuses.count("pass")
    fail_count = statuses.count("fail")

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>EvalForge Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 24px; }}
    .summary {{ display: flex; gap: 24px; margin-bottom: 32px; }}
    .card {{ background: #f1f5f9; padding: 16px 24px; border-radius: 8px; flex: 1; }}
    .pass {{ color: #16a34a; }} .fail {{ color: #dc2626; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ background: #f8fafc; }}
  </style>
</head>
<body>
  <h1>EvalForge Report</h1>
  <p>Generated: {datetime.now().isoformat()}</p>
  <div class="summary">
    <div class="card"><h2>{pass_count}</h2><p class="pass">Passed</p></div>
    <div class="card"><h2>{fail_count}</h2><p class="fail">Failed</p></div>
    <div class="card"><h2>{len(results)}</h2><p>Total</p></div>
  </div>
  <canvas id="scoreChart"></canvas>
  <table>
    <tr><th>Test</th><th>Score</th><th>Status</th><th>Reason</th></tr>
    {"".join(f"<tr><td>{l}</td><td>{s:.2f}</td><td class='{st}'>{st.upper()}</td><td>{r.get('reason', '')}</td></tr>"
             for l, s, st, r in zip(labels, scores, statuses, results))}
  </table>
  <script>
    new Chart(document.getElementById('scoreChart'), {{
      type: 'bar',
      data: {{
        labels: {json.dumps(labels)},
        datasets: [{{ label: 'Score', data: {json.dumps(scores)}, backgroundColor: {json.dumps(['#16a34a' if s == 'pass' else '#dc2626' for s in statuses])} }}]
      }},
      options: {{ scales: {{ y: {{ beginAtZero: true, max: 1 }} }} }}
    }});
  </script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    return output_path
