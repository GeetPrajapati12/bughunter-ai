"""
config/prompts.py
-----------------
All AI prompt templates in one place.
Keeping prompts isolated means we can iterate on them without touching
execution logic.  Each function returns a fully-formed string ready to
send to the LLM.
"""

from __future__ import annotations


# ── Prompt 1 ─ Understand Page ────────────────────────────────────────────────

def page_understanding_prompt(html: str, url: str, visible_text: str) -> str:
    return f"""You are a Senior QA Engineer performing web application analysis.

Analyze the HTML and visible text from the page at URL: {url}

HTML (truncated to 8 000 chars):
{html[:8000]}

VISIBLE TEXT:
{visible_text[:3000]}

Determine:
1. What kind of page is this?
2. What is the primary business purpose?
3. What user actions are available?
4. What UI components exist?
5. What workflows should be tested?
6. What negative scenarios should be tested?
7. What security checks apply?
8. What accessibility checks apply?

Return ONLY valid JSON with this exact structure (no markdown fences):
{{
  "page_name": "",
  "page_type": "",
  "criticality": "high|medium|low",
  "url": "",
  "components": [],
  "primary_actions": [],
  "recommended_tests": [],
  "security_tests": [],
  "accessibility_tests": [],
  "notes": ""
}}"""


# ── Prompt 2 ─ Generate Test Cases ───────────────────────────────────────────

def test_case_generation_prompt(page_analysis: dict) -> str:
    return f"""You are an ISTQB Certified Senior QA Automation Engineer.

Given the following page analysis:
{page_analysis}

Generate exhaustive functional test cases covering:
- Positive paths (happy path)
- Negative paths (invalid inputs, boundary values)
- Validation (field validation, form constraints)
- Security (XSS, SQLi, CSRF where applicable)
- Accessibility (keyboard nav, ARIA, contrast)
- Responsive (mobile viewport behaviour)
- Edge cases specific to this page type

Return ONLY a valid JSON array (no markdown fences). Each element:
{{
  "id": "TC-001",
  "title": "Short descriptive title",
  "category": "functional|security|accessibility|negative|performance",
  "priority": "critical|high|medium|low",
  "preconditions": [],
  "steps": [],
  "expected_result": "",
  "component_target": ""
}}"""


# ── Prompt 3 ─ Analyze Failure ────────────────────────────────────────────────

def failure_analysis_prompt(
    test_title: str,
    exception_msg: str,
    screenshot_description: str,
    html_snippet: str,
    console_logs: list[str],
) -> str:
    return f"""You are a QA Lead performing root-cause analysis on a test failure.

Test Title: {test_title}

Exception:
{exception_msg}

Screenshot Description:
{screenshot_description}

Relevant HTML Snippet:
{html_snippet[:3000]}

Browser Console Logs:
{chr(10).join(console_logs[:20])}

Analyse the failure and return ONLY valid JSON (no markdown fences):
{{
  "root_cause": "",
  "affected_component": "",
  "severity": "critical|high|medium|low",
  "possible_fix": "",
  "is_app_bug": true,
  "confidence_pct": 85,
  "additional_notes": ""
}}"""


# ── Prompt 4 ─ Executive Report ───────────────────────────────────────────────

def executive_report_prompt(session_summary: dict) -> str:
    return f"""You are a QA Manager preparing an executive summary for engineering leadership.

Test Session Data:
{session_summary}

Write a concise professional executive summary covering:
1. Executive Summary (2–3 sentences)
2. Major Risks identified
3. Critical Bugs list with severity
4. Recommendations (prioritised)
5. Overall Quality Score (0–100)
6. Deployment Recommendation (Go / No-Go / Conditional Go)

Return ONLY valid JSON (no markdown fences):
{{
  "executive_summary": "",
  "major_risks": [],
  "critical_bugs": [],
  "recommendations": [],
  "quality_score": 0,
  "deployment_recommendation": "Go|No-Go|Conditional Go",
  "deployment_rationale": ""
}}"""


# ── Prompt 5 ─ Login Detection ────────────────────────────────────────────────

def login_detection_prompt(html: str) -> str:
    return f"""You are a web automation expert.

Examine the following HTML and determine whether this page contains a login form.

HTML:
{html[:5000]}

Return ONLY valid JSON (no markdown fences):
{{
  "has_login": true,
  "username_selector": "CSS selector or empty string",
  "password_selector": "CSS selector or empty string",
  "submit_selector": "CSS selector or empty string",
  "notes": ""
}}"""
