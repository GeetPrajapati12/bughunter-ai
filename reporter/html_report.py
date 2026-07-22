"""
reporter/html_report.py
-----------------------
HTML Report Generator.
Renders a professional, self-contained HTML report from the session data.
All CSS is inlined — the report is a single portable file.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib  import Path

from jinja2  import Template
from loguru  import logger

from config.settings import REPORTS_DIR


# ── Jinja2 template ────────────────────────────────────────────────────────────

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BugHunter AI — Test Report</title>
<style>
  :root {
    --pass:   #22c55e; --fail: #ef4444; --skip: #f59e0b;
    --err:    #8b5cf6; --bg: #0f172a;   --card: #1e293b;
    --border: #334155; --text: #e2e8f0; --muted: #94a3b8;
    --accent: #38bdf8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }
  header { background: var(--card); border-bottom: 2px solid var(--accent); padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; }
  header h1 { font-size: 24px; color: var(--accent); font-weight: 700; }
  header .meta { color: var(--muted); font-size: 12px; text-align: right; line-height: 1.7; }
  .container { max-width: 1400px; margin: 0 auto; padding: 24px 32px; }
  .scorecard { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .score-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; text-align: center; }
  .score-card .value { font-size: 36px; font-weight: 800; }
  .score-card .label { color: var(--muted); font-size: 12px; margin-top: 4px; text-transform: uppercase; letter-spacing: .05em; }
  .score-card.pass .value { color: var(--pass); }
  .score-card.fail .value { color: var(--fail); }
  .score-card.total .value { color: var(--accent); }
  .score-card.score-val .value { color: #fbbf24; }
  section { margin-bottom: 40px; }
  section h2 { font-size: 18px; font-weight: 600; border-left: 4px solid var(--accent); padding-left: 12px; margin-bottom: 16px; }
  .exec-box { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; line-height: 1.7; }
  .exec-box .rec { padding: 8px 0; border-bottom: 1px solid var(--border); }
  .exec-box .rec:last-child { border-bottom: none; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
  .badge.passed  { background: #166534; color: var(--pass); }
  .badge.failed  { background: #7f1d1d; color: var(--fail); }
  .badge.skipped { background: #78350f; color: var(--skip); }
  .badge.error   { background: #4c1d95; color: #c4b5fd; }
  .badge.critical { background: #7f1d1d; color: #fca5a5; }
  .badge.high    { background: #78350f; color: #fdba74; }
  .badge.medium  { background: #374151; color: #d1d5db; }
  .badge.low     { background: #1e3a5f; color: #7dd3fc; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { background: #0f172a; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; }
  tr:hover td { background: rgba(255,255,255,.03); }
  .page-section { background: var(--card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 16px; overflow: hidden; }
  .page-header { padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
  .page-url { color: var(--accent); font-size: 13px; word-break: break-all; }
  .page-stats { color: var(--muted); font-size: 12px; white-space: nowrap; margin-left: 16px; }
  .screenshot { max-width: 300px; border-radius: 6px; margin-top: 6px; border: 1px solid var(--border); }
  footer { text-align: center; color: var(--muted); font-size: 12px; padding: 24px; border-top: 1px solid var(--border); }
  .deploy-go   { color: var(--pass); font-weight: 700; font-size: 18px; }
  .deploy-nogo { color: var(--fail); font-weight: 700; font-size: 18px; }
  .deploy-cond { color: var(--skip); font-weight: 700; font-size: 18px; }
</style>
</head>
<body>

<header>
  <div>
    <h1>🐛 BugHunter AI — Test Report</h1>
    <div style="color:var(--muted);margin-top:4px;font-size:13px;">{{ target_url }}</div>
  </div>
  <div class="meta">
    Generated: {{ generated_at }}<br>
    Engine: {{ engine }}<br>
    Duration: {{ duration }}
  </div>
</header>

<div class="container">

  <!-- Scorecard -->
  <div class="scorecard">
    <div class="score-card total">  <div class="value">{{ total_tests }}</div>  <div class="label">Total Tests</div></div>
    <div class="score-card pass">   <div class="value">{{ passed }}</div>        <div class="label">Passed</div></div>
    <div class="score-card fail">   <div class="value">{{ failed }}</div>        <div class="label">Failed</div></div>
    <div class="score-card">        <div class="value" style="color:var(--skip)">{{ skipped }}</div><div class="label">Skipped</div></div>
    <div class="score-card">        <div class="value" style="color:var(--muted)">{{ pages_crawled }}</div><div class="label">Pages</div></div>
    <div class="score-card">        <div class="value" style="color:#f472b6">{{ security_findings|length }}</div><div class="label">Security Findings</div></div>
    <div class="score-card score-val"><div class="value">{{ quality_score }}</div><div class="label">Quality Score</div></div>
  </div>

  <!-- Deployment Recommendation -->
  <section>
    <h2>Deployment Recommendation</h2>
    <div class="exec-box">
      <div class="deploy-{{ deploy_class }}">{{ deployment_recommendation }}</div>
      <p style="margin-top:10px;color:var(--muted);">{{ deployment_rationale }}</p>
    </div>
  </section>

  <!-- Executive Summary -->
  <section>
    <h2>Executive Summary</h2>
    <div class="exec-box">
      <p>{{ executive_summary }}</p>
      {% if recommendations %}
      <div style="margin-top:16px;"><strong>Recommendations</strong></div>
      {% for rec in recommendations %}
      <div class="rec">{{ loop.index }}. {{ rec }}</div>
      {% endfor %}
      {% endif %}
    </div>
  </section>

  <!-- Bugs -->
  {% if bugs %}
  <section>
    <h2>Bugs Found ({{ bugs|length }})</h2>
    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden">
    <table>
      <thead><tr><th>#</th><th>Test</th><th>Severity</th><th>Root Cause</th><th>Fix</th><th>Confidence</th></tr></thead>
      <tbody>
      {% for bug in bugs %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ bug.test_title }}</td>
        <td><span class="badge {{ bug.analysis.severity }}">{{ bug.analysis.severity }}</span></td>
        <td>{{ bug.analysis.root_cause }}</td>
        <td>{{ bug.analysis.possible_fix }}</td>
        <td>{{ bug.analysis.confidence_pct }}%</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </section>
  {% endif %}

  <!-- Security Findings -->
  {% if security_findings %}
  <section>
    <h2>🔒 Security Findings ({{ security_findings|length }})</h2>
    <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden">
    <table>
      <thead><tr><th>#</th><th>Severity</th><th>Category</th><th>Finding</th><th>Description</th><th>Recommendation</th><th>Affected</th></tr></thead>
      <tbody>
      {% for finding in security_findings %}
      <tr>
        <td>{{ loop.index }}</td>
        <td><span class="badge {{ finding.severity }}">{{ finding.severity }}</span></td>
        <td>{{ finding.category }}</td>
        <td>{{ finding.title }}</td>
        <td>{{ finding.description }}</td>
        <td>{{ finding.recommendation }}</td>
        <td style="font-size:11px;color:var(--muted);">{{ finding.affected_pages }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    <p style="margin-top:10px;color:var(--muted);font-size:12px;">
      ⚠️ These are automated signals intended to guide manual investigation by a security
      professional — they are not confirmed exploits. Only test websites you own or have
      explicit written authorization to assess.
    </p>
  </section>
  {% endif %}

  <!-- Page Results -->
  <section>
    <h2>Page Results</h2>
    {% for page in pages %}
    <div class="page-section">
      <div class="page-header">
        <span class="page-url">{{ page.url }}</span>
        <span class="page-stats">
          ✓ {{ page.passed }} / ✗ {{ page.failed }} / — {{ page.skipped }} | {{ page.page_type }}
        </span>
      </div>
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Duration</th><th>Error / Evidence</th></tr></thead>
        <tbody>
        {% for r in page.results %}
        <tr>
          <td>{{ r.test_id }}</td>
          <td>{{ r.title }}</td>
          <td><span class="badge {{ r.status }}">{{ r.status }}</span></td>
          <td>{{ r.duration_ms }}ms</td>
          <td>
            {{ r.error_message[:200] if r.error_message else "" }}
            {% if r.screenshot %}
            <br><img class="screenshot" src="{{ r.screenshot }}" alt="screenshot">
            {% endif %}
          </td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    {% endfor %}
  </section>

</div>

<footer>BugHunter AI &bull; {{ generated_at }} &bull; Powered by Geet Prajapati</footer>
</body>
</html>
"""


class HTMLReporter:
    """Renders a self-contained HTML report for a test session."""

    def generate(self, session: dict) -> Path:
        """
        Parameters
        ----------
        session:
            Dict produced by the MasterAgent containing all results.

        Returns
        -------
        Path to the generated HTML file.
        """
        now       = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        out_path  = REPORTS_DIR / f"bughunter_report_{timestamp}.html"

        # Compute totals
        all_results = []
        for p in session.get("pages", []):
            all_results += p.get("results", [])

        total   = len(all_results)
        passed  = sum(1 for r in all_results if r.get("status") == "passed")
        failed  = sum(1 for r in all_results if r.get("status") == "failed")
        skipped = sum(1 for r in all_results if r.get("status") == "skipped")

        exec_report = session.get("executive_report", {})
        quality_score = exec_report.get("quality_score", 0)
        deploy = exec_report.get("deployment_recommendation", "Conditional Go")
        deploy_class = {"Go": "go", "No-Go": "nogo"}.get(deploy, "cond")

        ctx = {
            "target_url":               session.get("target_url", ""),
            "generated_at":             now.strftime("%Y-%m-%d %H:%M:%S"),
            "engine":                   session.get("engine", "selenium"),
            "duration":                 session.get("duration", ""),
            "total_tests":              total,
            "passed":                   passed,
            "failed":                   failed,
            "skipped":                  skipped,
            "pages_crawled":            len(session.get("pages", [])),
            "quality_score":            quality_score,
            "deployment_recommendation":deploy,
            "deployment_rationale":     exec_report.get("deployment_rationale", ""),
            "deploy_class":             deploy_class,
            "executive_summary":        exec_report.get("executive_summary", ""),
            "recommendations":          exec_report.get("recommendations", []),
            "bugs":                     session.get("bugs", []),
            "security_findings":        session.get("security_findings", []),
            "pages":                    session.get("pages", []),
        }

        html = Template(_TEMPLATE).render(**ctx)
        out_path.write_text(html, encoding="utf-8")
        logger.info("HTML report written: {}", out_path)
        return out_path
