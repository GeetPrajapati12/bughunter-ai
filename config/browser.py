"""
config/browser.py
-----------------
Browser factory.  Returns a configured Selenium WebDriver (or a
Playwright Browser object) based on the active BROWSER_ENGINE setting.

The rest of the codebase imports `get_driver()` and never touches
WebDriver or Playwright APIs directly — this keeps the runner swappable.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config.settings import (
    BROWSER_ENGINE,
    BROWSER_HEADLESS,
    BROWSER_WINDOW_WIDTH,
    BROWSER_WINDOW_HEIGHT,
    PAGE_LOAD_TIMEOUT,
    IMPLICIT_WAIT,
)


def get_driver() -> Any:
    """
    Return a ready-to-use browser driver/page object.

    Returns a ``selenium.webdriver.Chrome`` instance when BROWSER_ENGINE
    is ``"selenium"`` and a ``playwright.sync_api.Page`` when it is
    ``"playwright"``.
    """
    engine = BROWSER_ENGINE.lower()
    if engine == "selenium":
        return _build_selenium_driver()
    if engine == "playwright":
        return _build_playwright_page()
    raise ValueError(f"Unknown BROWSER_ENGINE: {engine!r}. Use 'selenium' or 'playwright'.")


# ── Selenium ──────────────────────────────────────────────────────────────────

def _build_selenium_driver() -> Any:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
    except ImportError as exc:
        raise ImportError("selenium is not installed. Run: pip install selenium") from exc

    options = Options()
    if BROWSER_HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument(f"--window-size={BROWSER_WINDOW_WIDTH},{BROWSER_WINDOW_HEIGHT}")
    options.add_argument("--log-level=3")

    # Suppress driver logging noise
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(IMPLICIT_WAIT)
    driver.set_window_size(BROWSER_WINDOW_WIDTH, BROWSER_WINDOW_HEIGHT)

    logger.info("Selenium Chrome driver initialised (headless={})", BROWSER_HEADLESS)
    return driver


# ── Playwright ────────────────────────────────────────────────────────────────

def _build_playwright_page() -> Any:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "playwright is not installed. Run: pip install playwright && playwright install"
        ) from exc

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=BROWSER_HEADLESS)
    context = browser.new_context(
        viewport={"width": BROWSER_WINDOW_WIDTH, "height": BROWSER_WINDOW_HEIGHT}
    )
    page = context.new_page()
    page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)

    logger.info("Playwright Chromium browser initialised (headless={})", BROWSER_HEADLESS)
    return page
