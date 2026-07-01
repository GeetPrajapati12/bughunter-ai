"""
reporter/screenshots.py
-----------------------
Screenshot management utilities.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing  import Any

from loguru import logger

from config.settings import SCREENSHOTS_DIR


class ScreenshotManager:
    """
    Centralised screenshot capture and management.
    """

    def __init__(self, driver: Any) -> None:
        self.driver = driver

    def capture(self, name: str = "") -> str:
        """
        Take a screenshot and return the file path.
        """
        ts   = int(time.time() * 1000)
        slug = name.replace(" ", "_").replace("/", "_")[:50] if name else "screen"
        path = SCREENSHOTS_DIR / f"{slug}_{ts}.png"

        try:
            if "selenium" in type(self.driver).__module__:
                self.driver.save_screenshot(str(path))
            else:
                self.driver.screenshot(path=str(path))
            logger.debug("Screenshot: {}", path)
            return str(path)
        except Exception as exc:
            logger.warning("Screenshot failed: {}", exc)
            return ""

    def capture_full_page(self, name: str = "") -> str:
        """Full-page screenshot (Playwright only; falls back for Selenium)."""
        ts   = int(time.time() * 1000)
        slug = name[:50] if name else "fullpage"
        path = SCREENSHOTS_DIR / f"{slug}_full_{ts}.png"

        try:
            if "selenium" in type(self.driver).__module__:
                # Selenium: scroll and stitch not implemented; take viewport
                self.driver.save_screenshot(str(path))
            else:
                self.driver.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception as exc:
            logger.warning("Full-page screenshot failed: {}", exc)
            return ""
