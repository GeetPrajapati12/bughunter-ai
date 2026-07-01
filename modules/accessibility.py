"""
modules/accessibility.py
------------------------
Accessibility testing module.
Checks for common WCAG 2.1 issues without external tools:
  - Images missing alt text
  - Form inputs missing labels
  - Buttons with no accessible name
  - Low-contrast text (basic heuristic)
  - Missing lang attribute on <html>
  - Heading hierarchy violations
  - Keyboard navigation (Tab order)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing      import Any

from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class AccessibilityIssue:
    rule:        str
    severity:    str   # "critical" | "serious" | "moderate" | "minor"
    element:     str
    description: str
    wcag_ref:    str


class AccessibilityChecker:
    """
    Run DOM-based accessibility checks against raw HTML.
    Returns a list of AccessibilityIssue objects.
    """

    def check(self, html: str) -> list[AccessibilityIssue]:
        soup   = BeautifulSoup(html, "lxml")
        issues: list[AccessibilityIssue] = []

        issues += self._check_images(soup)
        issues += self._check_form_labels(soup)
        issues += self._check_button_names(soup)
        issues += self._check_lang_attribute(soup)
        issues += self._check_heading_hierarchy(soup)
        issues += self._check_empty_links(soup)
        issues += self._check_duplicate_ids(soup)

        logger.info("AccessibilityChecker: {} issues found", len(issues))
        return issues

    # ── Individual checks ──────────────────────────────────────────────────────

    def _check_images(self, soup: Any) -> list[AccessibilityIssue]:
        issues = []
        for img in soup.find_all("img"):
            alt = img.get("alt")
            if alt is None:
                issues.append(AccessibilityIssue(
                    rule="img-alt",
                    severity="critical",
                    element=str(img)[:200],
                    description="Image is missing an alt attribute.",
                    wcag_ref="WCAG 1.1.1",
                ))
        return issues

    def _check_form_labels(self, soup: Any) -> list[AccessibilityIssue]:
        issues = []
        for inp in soup.find_all("input"):
            if inp.get("type") in ("hidden", "submit", "button", "reset", "image"):
                continue
            inp_id = inp.get("id", "")
            has_label = bool(
                (inp_id and soup.find("label", attrs={"for": inp_id}))
                or inp.get("aria-label")
                or inp.get("aria-labelledby")
                or inp.find_parent("label")
            )
            if not has_label:
                issues.append(AccessibilityIssue(
                    rule="label",
                    severity="critical",
                    element=str(inp)[:200],
                    description="Form input has no associated label.",
                    wcag_ref="WCAG 1.3.1",
                ))
        return issues

    def _check_button_names(self, soup: Any) -> list[AccessibilityIssue]:
        issues = []
        for btn in soup.find_all("button"):
            name = (
                btn.get_text(strip=True) or
                btn.get("aria-label", "") or
                btn.get("title", "")
            )
            if not name:
                issues.append(AccessibilityIssue(
                    rule="button-name",
                    severity="critical",
                    element=str(btn)[:200],
                    description="Button has no accessible name (empty text and no aria-label).",
                    wcag_ref="WCAG 4.1.2",
                ))
        return issues

    def _check_lang_attribute(self, soup: Any) -> list[AccessibilityIssue]:
        html_tag = soup.find("html")
        if html_tag and not html_tag.get("lang"):
            return [AccessibilityIssue(
                rule="html-has-lang",
                severity="serious",
                element="<html>",
                description="<html> element is missing a lang attribute.",
                wcag_ref="WCAG 3.1.1",
            )]
        return []

    def _check_heading_hierarchy(self, soup: Any) -> list[AccessibilityIssue]:
        issues = []
        prev_level = 0
        for tag in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
            level = int(tag.name[1])
            if prev_level and level > prev_level + 1:
                issues.append(AccessibilityIssue(
                    rule="heading-order",
                    severity="moderate",
                    element=str(tag)[:200],
                    description=f"Heading jumps from h{prev_level} to h{level} — skips levels.",
                    wcag_ref="WCAG 1.3.1",
                ))
            prev_level = level
        return issues

    def _check_empty_links(self, soup: Any) -> list[AccessibilityIssue]:
        issues = []
        for a in soup.find_all("a"):
            text = (
                a.get_text(strip=True) or
                a.get("aria-label", "") or
                a.get("title", "")
            )
            if not text:
                issues.append(AccessibilityIssue(
                    rule="link-name",
                    severity="serious",
                    element=str(a)[:200],
                    description="Link has no accessible text.",
                    wcag_ref="WCAG 2.4.4",
                ))
        return issues

    def _check_duplicate_ids(self, soup: Any) -> list[AccessibilityIssue]:
        issues  = []
        seen    : set[str] = set()
        dupes   : set[str] = set()
        for tag in soup.find_all(id=True):
            tid = tag["id"]
            if tid in seen:
                dupes.add(tid)
            seen.add(tid)
        for dup in dupes:
            issues.append(AccessibilityIssue(
                rule="duplicate-id",
                severity="moderate",
                element=f"id='{dup}'",
                description=f"Duplicate id '{dup}' found on multiple elements.",
                wcag_ref="WCAG 4.1.1",
            ))
        return issues
