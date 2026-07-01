"""
ai/bug_explainer.py
-------------------
Bug Analyzer Agent.
Given a test failure (exception, screenshot path, HTML snippet, console logs),
asks Claude to explain the root cause and severity.
"""

from __future__ import annotations

import json
import re

import anthropic
from loguru import logger

from config.settings import ANTHROPIC_API_KEY, AI_MODEL, AI_MAX_TOKENS
from config.prompts  import failure_analysis_prompt


class BugExplainerAgent:
    """Use Claude to interpret test failures."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def explain(
        self,
        test_title:    str,
        exception_msg: str,
        html_snippet:  str = "",
        console_logs:  list[str] | None = None,
        screenshot_path: str = "",
    ) -> dict:
        """
        Return a structured bug analysis dict.
        """
        screenshot_desc = f"Screenshot saved at: {screenshot_path}" if screenshot_path else "No screenshot available."
        logs            = console_logs or []

        if not ANTHROPIC_API_KEY:
            return self._fallback(test_title, exception_msg)

        prompt = failure_analysis_prompt(
            test_title,
            exception_msg,
            screenshot_desc,
            html_snippet,
            logs,
        )

        try:
            response = self._client.messages.create(
                model=AI_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw     = response.content[0].text
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
            "root_cause": exc,
            "affected_component": "unknown",
            "severity": "medium",
            "possible_fix": "Manual investigation required.",
            "is_app_bug": True,
            "confidence_pct": 50,
            "additional_notes": "AI analysis unavailable.",
        }
