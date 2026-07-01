"""
ai/testcase_generator.py
------------------------
Test Planner Agent.
Takes a page analysis dict and returns a list of structured test case dicts.
"""

from __future__ import annotations

import json
import re

import anthropic
from loguru import logger

from config.settings import ANTHROPIC_API_KEY, AI_MODEL, AI_MAX_TOKENS
from config.prompts  import test_case_generation_prompt


class TestCaseGeneratorAgent:
    """Generate exhaustive test cases for a page using Claude."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate(self, page_analysis: dict) -> list[dict]:
        """
        Return a list of test case dicts for the given page analysis.
        """
        if not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set — returning generic test cases")
            return self._generic_tests(page_analysis)

        prompt = test_case_generation_prompt(json.dumps(page_analysis, indent=2))

        try:
            response = self._client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text   = response.content[0].text
            test_cases = self._parse_json(raw_text)

            logger.info(
                "TestCaseGeneratorAgent: {} test cases for page '{}'",
                len(test_cases),
                page_analysis.get("page_name", "?"),
            )
            return test_cases

        except Exception as exc:
            logger.error("TestCaseGeneratorAgent failed: {}", exc)
            return self._generic_tests(page_analysis)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> list[dict]:
        cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        result  = json.loads(cleaned)
        return result if isinstance(result, list) else result.get("test_cases", [])

    @staticmethod
    def _generic_tests(analysis: dict) -> list[dict]:
        """Minimal fallback test cases that apply to any page."""
        return [
            {
                "id": "TC-GENERIC-001",
                "title": "Verify page loads successfully",
                "category": "functional",
                "priority": "critical",
                "preconditions": [],
                "steps": ["Navigate to page URL"],
                "expected_result": "Page loads with HTTP 200, no console errors",
                "component_target": "page",
            },
            {
                "id": "TC-GENERIC-002",
                "title": "Verify all links are not broken",
                "category": "functional",
                "priority": "high",
                "preconditions": [],
                "steps": ["Collect all <a> tags", "Check each href returns 2xx"],
                "expected_result": "No 404 or 5xx responses",
                "component_target": "links",
            },
            {
                "id": "TC-GENERIC-003",
                "title": "Check page title is not empty",
                "category": "functional",
                "priority": "medium",
                "preconditions": [],
                "steps": ["Inspect <title> tag"],
                "expected_result": "Title is set and descriptive",
                "component_target": "page",
            },
        ]
