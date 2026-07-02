"""
ai/page_understanding.py
------------------------
Page Understanding Agent.
Sends page HTML + visible text to the active LLM provider and returns
a structured analysis of the page purpose, components, and recommended tests.
"""

from __future__ import annotations

import json
import re

from loguru import logger

from ai.llm_client   import LLMClient
from config.prompts  import page_understanding_prompt
from crawler.sitemap import PageInfo


class PageUnderstandingAgent:
    """Uses the configured LLM to interpret a page's purpose and test needs."""

    def __init__(self) -> None:
        self._llm = LLMClient()

    def analyse(self, page: PageInfo) -> dict:
        if not self._llm.is_available():
            logger.warning("LLM provider not configured — skipping AI page analysis")
            return self._fallback_analysis(page)

        prompt = page_understanding_prompt(page.html, page.url, page.visible_text)

        try:
            raw      = self._llm.chat(prompt)
            analysis = self._parse_json(raw)
            analysis["url"] = page.url
            page.analysis   = analysis
            logger.info("AI analysed page: {} (type={})", page.url, analysis.get("page_type", "?"))
            return analysis

        except Exception as exc:
            logger.error("PageUnderstandingAgent failed for {}: {}", page.url, exc)
            return self._fallback_analysis(page)

    @staticmethod
    def _parse_json(text: str) -> dict:
        cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        return json.loads(cleaned)

    @staticmethod
    def _fallback_analysis(page: PageInfo) -> dict:
        return {
            "page_name":          page.title or page.url,
            "page_type":          "Unknown",
            "criticality":        "medium",
            "url":                page.url,
            "components":         [],
            "primary_actions":    [],
            "recommended_tests":  ["Basic page load", "Link validation"],
            "security_tests":     [],
            "accessibility_tests":[],
            "notes":              "AI analysis unavailable — check AI_PROVIDER and API key in .env",
        }
