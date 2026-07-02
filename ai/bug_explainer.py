"""
ai/bug_explainer.py
-------------------
Bug Analyzer Agent.
Given a test failure, asks the configured LLM to explain root cause and severity.
"""

from __future__ import annotations

import json
import re

from loguru import logger

from ai.llm_client  import LLMClient
from config.prompts import failure_analysis_prompt


class BugExplainerAgent:
    """Use the configured LLM to interpret test failures."""

    def __init__(self) -> None:
        self._llm = LLMClient()

    def explain(
        self,
        test_title:      str,
        exception_msg:   str,
        html_snippet:    str = "",
        console_logs:    list[str] | None = None,
        screenshot_path: str = "",
    ) -> dict:
        if not self._llm.is_available():
            return self._fallback(test_title, exception_msg)

        screenshot_desc = f"Screenshot saved at: {screenshot_path}" if screenshot_path else "No screenshot."
        logs            = console_logs or []

        prompt = failure_analysis_prompt(
            test_title,
            exception_msg,
            screenshot_desc,
            html_snippet,
            logs,
        )

        try:
            raw     = self._llm.chat(prompt, max_tokens=1024)
            cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
            result  = json.loads(cleaned)
            logger.info(
                "BugExplainer: severity={} confidence={}%",
                result.get("severity", "?"),
                result.get("confidence_pct", "?"),
            )
            return result

        except Exception as exc:
            logger.error("BugExplainerAgent failed: {}", exc)
            return self._fallback(test_title, exception_msg)

    @staticmethod
    def _fallback(title: str, exc: str) -> dict:
        return {
            "root_cause":         exc,
            "affected_component": "unknown",
            "severity":           "medium",
            "possible_fix":       "Manual investigation required.",
            "is_app_bug":         True,
            "confidence_pct":     50,
            "additional_notes":   "AI analysis unavailable — check AI_PROVIDER and API key in .env",
        }
