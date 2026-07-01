"""
detector/buttons.py
-------------------
Detect all button-like elements on a page using pure DOM inspection.
No hardcoded page-specific logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class ButtonInfo:
    selector:   str
    text:       str
    tag:        str
    btn_type:   str   # "submit" | "button" | "reset" | "link-button" | "icon"
    is_visible: bool
    is_enabled: bool
    aria_label: str


class ButtonDetector:
    """
    Detects button-like elements from HTML source.
    Works without a live driver; for live state (visible/enabled) pass the driver.
    """

    # CSS / aria roles that signal a clickable element
    _ROLE_SELECTORS = [
        "button",
        "input[type='submit']",
        "input[type='button']",
        "input[type='reset']",
        "[role='button']",
        "a.btn",
        "a.button",
        "[class*='btn']",
        "[class*='button']",
    ]

    def detect_from_html(self, html: str) -> list[ButtonInfo]:
        soup = BeautifulSoup(html, "lxml")
        results: list[ButtonInfo] = []
        seen_texts: set[str] = set()

        for tag in soup.find_all(["button", "input", "a"]):
            info = self._parse_tag(tag)
            if info is None:
                continue
            key = f"{info.tag}:{info.text}"
            if key not in seen_texts:
                seen_texts.add(key)
                results.append(info)

        logger.debug("ButtonDetector found {} buttons", len(results))
        return results

    def detect_from_driver(self, driver: Any) -> list[ButtonInfo]:
        """Use live driver for is_visible / is_enabled state."""
        try:
            if "selenium" in type(driver).__module__:
                return self._detect_selenium(driver)
        except Exception as exc:
            logger.warning("ButtonDetector driver-mode failed: {}", exc)
        # Fallback to HTML parse
        src = driver.page_source if hasattr(driver, "page_source") else driver.content()
        return self.detect_from_html(src)

    # ── Internals ──────────────────────────────────────────────────────────────

    def _parse_tag(self, tag: Any) -> ButtonInfo | None:
        tag_name = tag.name.lower()
        classes  = " ".join(tag.get("class", []))

        if tag_name == "button":
            btn_type = tag.get("type", "button")
        elif tag_name == "input":
            btn_type = tag.get("type", "")
            if btn_type not in ("submit", "button", "reset"):
                return None
        elif tag_name == "a":
            if not any(k in classes for k in ("btn", "button")):
                if tag.get("role") != "button":
                    return None
            btn_type = "link-button"
        else:
            return None

        text = (tag.get_text(strip=True) or tag.get("value", "") or
                tag.get("aria-label", "") or tag.get("title", ""))
        is_enabled = not (tag.get("disabled") is not None)

        # Build a simple CSS selector
        tag_id  = tag.get("id", "")
        selector = f"#{tag_id}" if tag_id else self._class_selector(tag_name, classes)

        return ButtonInfo(
            selector=selector,
            text=text[:120],
            tag=tag_name,
            btn_type=btn_type,
            is_visible=True,    # can't know from HTML alone
            is_enabled=is_enabled,
            aria_label=tag.get("aria-label", ""),
        )

    def _detect_selenium(self, driver: Any) -> list[ButtonInfo]:
        from selenium.webdriver.common.by import By
        results: list[ButtonInfo] = []
        css = ", ".join(self._ROLE_SELECTORS)
        elements = driver.find_elements(By.CSS_SELECTOR, css)
        for el in elements:
            try:
                results.append(ButtonInfo(
                    selector=self._selenium_selector(el),
                    text=(el.text or el.get_attribute("value") or
                          el.get_attribute("aria-label") or "")[:120],
                    tag=el.tag_name,
                    btn_type=el.get_attribute("type") or "button",
                    is_visible=el.is_displayed(),
                    is_enabled=el.is_enabled(),
                    aria_label=el.get_attribute("aria-label") or "",
                ))
            except Exception:
                continue
        return results

    @staticmethod
    def _class_selector(tag: str, classes: str) -> str:
        cls = classes.split()[0] if classes else ""
        return f"{tag}.{cls}" if cls else tag

    @staticmethod
    def _selenium_selector(el: Any) -> str:
        try:
            el_id = el.get_attribute("id")
            if el_id:
                return f"#{el_id}"
            cls = el.get_attribute("class") or ""
            first_cls = cls.split()[0] if cls else ""
            return f"{el.tag_name}.{first_cls}" if first_cls else el.tag_name
        except Exception:
            return el.tag_name
