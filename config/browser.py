"""
config/browser.py
-----------------
Browser factory.
Returns a configured Selenium WebDriver or Playwright Page based on
the BROWSER_ENGINE environment variable.

IMPORTANT: get_driver() reads BROWSER_ENGINE fresh from os.environ
at call time (not at import time) so that CLI --engine overrides
applied before import are correctly picked up.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger


def get_driver() -> Any:
    """
    Return a ready-to-use browser driver.

    Reads BROWSER_ENGINE from os.environ at call time so that
    CLI overrides (--engine playwright) are always respected,
    regardless of import order.
    """
    # Read fresh from env, not from the cached settings module value
    engine = os.environ.get("BROWSER_ENGINE", "selenium").lower().strip()

    logger.info("Browser engine requested: {}", engine)

    if engine == "selenium":
        return _build_selenium_driver()
    if engine == "playwright":
        return _build_playwright_page()
    raise ValueError(
        f"Unknown BROWSER_ENGINE: {engine!r}. Use 'selenium' or 'playwright'."
    )


# ── Selenium ──────────────────────────────────────────────────────────────────

def _build_selenium_driver() -> Any:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as exc:
        raise ImportError("Run: pip install selenium") from exc

    headless = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"
    width    = int(os.environ.get("BROWSER_WINDOW_WIDTH",  "1366"))
    height   = int(os.environ.get("BROWSER_WINDOW_HEIGHT", "768"))
    timeout  = int(os.environ.get("PAGE_LOAD_TIMEOUT",     "30"))
    wait     = int(os.environ.get("IMPLICIT_WAIT",         "5"))

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(timeout)
    driver.implicitly_wait(wait)
    driver.set_window_size(width, height)

    logger.info("Selenium Chrome driver initialised (headless={})", headless)
    return driver


# ── Playwright ────────────────────────────────────────────────────────────────

def _build_playwright_page() -> Any:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Run: pip install playwright && playwright install chromium"
        ) from exc

    headless = os.environ.get("BROWSER_HEADLESS", "true").lower() == "true"
    width    = int(os.environ.get("BROWSER_WINDOW_WIDTH",  "1366"))
    height   = int(os.environ.get("BROWSER_WINDOW_HEIGHT", "768"))
    timeout  = int(os.environ.get("PAGE_LOAD_TIMEOUT",     "30"))

    pw      = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(
        viewport={"width": width, "height": height}
    )
    page = context.new_page()
    page.set_default_timeout(timeout * 1000)

    logger.info("Playwright Chromium initialised (headless={})", headless)
    return page