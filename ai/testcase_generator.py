"""
ai/testcase_generator.py
------------------------
Test Planner Agent.
Takes a page analysis dict and returns a list of structured test case dicts.
"""

from __future__ import annotations

import json
import re

from loguru import logger

from ai.llm_client  import LLMClient
from config.prompts import test_case_generation_prompt


class TestCaseGeneratorAgent:
    """Generate exhaustive test cases for a page using the configured LLM."""

    def __init__(self) -> None:
        self._llm = LLMClient()

    def generate(self, page_analysis: dict) -> list[dict]:
        if not self._llm.is_available():
            logger.warning("LLM provider not configured — returning generic test cases")
            return self._generic_tests(page_analysis)

        prompt = test_case_generation_prompt(json.dumps(page_analysis, indent=2))

        try:
            raw        = self._llm.chat(prompt)
            test_cases = self._parse_json(raw)
            logger.info(
                "TestCaseGeneratorAgent: {} test cases for page '{}'",
                len(test_cases),
                page_analysis.get("page_name", "?"),
            )
            return test_cases

        except Exception as exc:
            logger.error("TestCaseGeneratorAgent failed: {}", exc)
            return self._generic_tests(page_analysis)

    @staticmethod
    def _parse_json(text: str) -> list[dict]:
        cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        result  = json.loads(cleaned)
        return result if isinstance(result, list) else result.get("test_cases", [])

    @staticmethod
    def _generic_tests(analysis: dict) -> list[dict]:
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
