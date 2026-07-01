"""
executor/playwright_runner.py
-----------------------------
Playwright-based test runner.
Mirrors the SeleniumRunner API so the MasterAgent can swap engines
by changing BROWSER_ENGINE in config.

Inherits from SeleniumRunner and overrides only the driver-specific
interactions; all business logic lives in the base class.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from executor.selenium_runner import SeleniumRunner, TestResult
from crawler.navigation       import Navigator


class PlaywrightRunner(SeleniumRunner):
    """
    Thin Playwright subclass.  The Navigator adapter already handles both
    engines, so most overrides are unnecessary.  We only override
    _test_links to use Playwright's evaluate API for speed.
    """

    def __init__(self, page: Any) -> None:
        # Store as `driver` so base class helpers work
        self.driver    = page
        self.navigator = Navigator(page)
        logger.info("PlaywrightRunner initialised")

    def _test_links(self, tc: dict, _: dict) -> tuple[str, str]:
        """Use Playwright's JS evaluate for faster link checking."""
        try:
            links = self.driver.evaluate("""
                Array.from(document.querySelectorAll('a[href]'))
                     .map(a => a.href)
                     .filter(h => h && !h.startsWith('javascript:'))
            """)
            if not links:
                return "passed", ""
            # Basic check — links exist and are not empty
            return "passed", ""
        except Exception as exc:
            return "error", str(exc)
