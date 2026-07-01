"""
ai/report_writer.py
-------------------
Report Writer Agent.
Generates an executive-level JSON summary of the entire test session,
which the HTML/PDF reporters then render.
"""

from __future__ import annotations

import json
import re

import anthropic
from loguru import logger

from config.settings import ANTHROPIC_API_KEY, AI_MODEL, AI_MAX_TOKENS
from config.prompts  import executive_report_prompt


class ReportWriterAgent:
    """Use Claude to write an executive summary of the test run."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def write(self, session_summary: dict) -> dict:
        """
        Given a session_summary dict (pages tested, pass/fail counts, bug list),
        return an executive report dict.
        """
        if not ANTHROPIC_API_KEY:
            return self._fallback(session_summary)

        prompt = executive_report_prompt(json.dumps(session_summary, indent=2))

        try:
            response = self._client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            raw     = response.content[0].text
            cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
            report  = json.loads(cleaned)
            logger.info(
                "ReportWriterAgent: score={} recommendation={}",
                report.get("quality_score"),
                report.get("deployment_recommendation"),
            )
            return report

        except Exception as exc:
            logger.error("ReportWriterAgent failed: {}", exc)
            return self._fallback(session_summary)

    @staticmethod
    def _fallback(summary: dict) -> dict:
        total  = summary.get("total_tests", 0)
        passed = summary.get("passed",      0)
        score  = int((passed / total * 100)) if total else 0
        return {
            "executive_summary": f"Automated QA run completed. {passed}/{total} tests passed.",
            "major_risks": [],
            "critical_bugs": summary.get("critical_bugs", []),
            "recommendations": ["Review failed test cases manually."],
            "quality_score": score,
            "deployment_recommendation": "Conditional Go" if score >= 70 else "No-Go",
            "deployment_rationale": "Based on automated test pass rate.",
        }
