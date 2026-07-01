"""
ai/page_understanding.py
------------------------
Page Understanding Agent.
Sends page HTML + visible text to Claude and returns a structured
analysis of the page purpose, components, and recommended tests.
"""

from __future__ import annotations

import json
import re

import anthropic
from loguru import logger

from config.settings  import ANTHROPIC_API_KEY, AI_MODEL, AI_MAX_TOKENS
from config.prompts   import page_understanding_prompt
from crawler.sitemap  import PageInfo


class PageUnderstandingAgent:
    """
    Uses Claude to interpret a page's purpose and identify what
    should be tested.
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def analyse(self, page: PageInfo) -> dict:
        """
        Analyse a single page and populate page.analysis.

        Returns the analysis dict.
        """
        if not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set — skipping AI page analysis")
            return self._fallback_analysis(page)

        prompt = page_understanding_prompt(page.html, page.url, page.visible_text)

        try:
            response = self._client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text
            analysis = self._parse_json(raw_text)
            analysis["url"] = page.url
            page.analysis   = analysis
            logger.info("AI analysed page: {} (type={})", page.url, analysis.get("page_type", "?"))
            return analysis

        except Exception as exc:
            logger.error("PageUnderstandingAgent failed for {}: {}", page.url, exc)
            return self._fallback_analysis(page)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Strip markdown fences and parse JSON."""
        cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        return json.loads(cleaned)

    @staticmethod
    def _fallback_analysis(page: PageInfo) -> dict:
        return {
            "page_name": page.title or page.url,
            "page_type": "Unknown",
            "criticality": "medium",
            "url": page.url,
            "components": [],
            "primary_actions": [],
            "recommended_tests": ["Basic page load", "Link validation"],
            "security_tests": [],
            "accessibility_tests": [],
            "notes": "AI analysis unavailable — ANTHROPIC_API_KEY not set.",
        }
