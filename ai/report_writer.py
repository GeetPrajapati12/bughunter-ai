"""
ai/report_writer.py
-------------------
Report Writer Agent.
Generates an executive-level JSON summary of the entire test session.
"""

from __future__ import annotations

import json
import re

from loguru import logger

from ai.llm_client  import LLMClient
from config.prompts import executive_report_prompt


class ReportWriterAgent:
    """Use the configured LLM to write an executive summary of the test run."""

    def __init__(self) -> None:
        self._llm = LLMClient()

    def write(self, session_summary: dict) -> dict:
        if not self._llm.is_available():
            return self._fallback(session_summary)

        prompt = executive_report_prompt(json.dumps(session_summary, indent=2))

        try:
            raw     = self._llm.chat(prompt)
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
            "executive_summary":        f"Automated QA run completed. {passed}/{total} tests passed.",
            "major_risks":              [],
            "critical_bugs":            summary.get("critical_bugs", []),
            "recommendations":          ["Check AI_PROVIDER and API key in .env for full AI analysis."],
            "quality_score":            score,
            "deployment_recommendation":"Conditional Go" if score >= 70 else "No-Go",
            "deployment_rationale":     "Based on automated test pass rate.",
        }
