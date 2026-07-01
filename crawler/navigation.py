"""
crawler/navigation.py
---------------------
Navigation helpers that abstract over Selenium / Playwright.
Provides safe wrappers for common actions: click, type, scroll, wait.
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger

from config.settings import ELEMENT_TIMEOUT


class Navigator:
    """
    Thin adapter over the active browser driver.
    Methods are engine-agnostic: they detect whether the driver is
    Selenium or Playwright and call the appropriate API.
    """

    def __init__(self, driver: Any) -> None:
        self.driver   = driver
        self._is_selenium = "selenium" in type(driver).__module__

    # ── Navigation ─────────────────────────────────────────────────────────────

    def goto(self, url: str) -> None:
        if self._is_selenium:
            self.driver.get(url)
        else:
            self.driver.goto(url, wait_until="networkidle")

    def refresh(self) -> None:
        if self._is_selenium:
            self.driver.refresh()
        else:
            self.driver.reload()

    def back(self) -> None:
        if self._is_selenium:
            self.driver.back()
        else:
            self.driver.go_back()

    # ── Element interaction ────────────────────────────────────────────────────

    def click(self, selector: str) -> bool:
        """Click an element by CSS selector. Returns True on success."""
        try:
            if self._is_selenium:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                el = WebDriverWait(self.driver, ELEMENT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                el.click()
            else:
                self.driver.click(selector, timeout=ELEMENT_TIMEOUT * 1000)
            return True
        except Exception as exc:
            logger.debug("click({}) failed: {}", selector, exc)
            return False

    def type_text(self, selector: str, text: str, clear_first: bool = True) -> bool:
        """Type text into an input element."""
        try:
            if self._is_selenium:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                el = WebDriverWait(self.driver, ELEMENT_TIMEOUT).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                if clear_first:
                    el.clear()
                el.send_keys(text)
            else:
                if clear_first:
                    self.driver.fill(selector, "")
                self.driver.type(selector, text)
            return True
        except Exception as exc:
            logger.debug("type_text({}) failed: {}", selector, exc)
            return False

    def select_option(self, selector: str, value: str) -> bool:
        """Select a <select> option by value."""
        try:
            if self._is_selenium:
                from selenium.webdriver.support.ui import Select
                from selenium.webdriver.common.by import By
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                Select(el).select_by_value(value)
            else:
                self.driver.select_option(selector, value)
            return True
        except Exception as exc:
            logger.debug("select_option({}) failed: {}", selector, exc)
            return False

    def scroll_to_bottom(self) -> None:
        if self._is_selenium:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            self.driver.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)

    def scroll_into_view(self, selector: str) -> None:
        if self._is_selenium:
            from selenium.webdriver.common.by import By
            el = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
        else:
            self.driver.evaluate(f"document.querySelector('{selector}').scrollIntoView(true);")

    # ── Information ────────────────────────────────────────────────────────────

    def get_current_url(self) -> str:
        if self._is_selenium:
            return self.driver.current_url
        return self.driver.url

    def get_page_source(self) -> str:
        if self._is_selenium:
            return self.driver.page_source
        return self.driver.content()

    def get_title(self) -> str:
        if self._is_selenium:
            return self.driver.title
        return self.driver.title()

    def get_console_logs(self) -> list[str]:
        try:
            if self._is_selenium:
                logs = self.driver.get_log("browser")
                return [f"[{l['level']}] {l['message']}" for l in logs]
        except Exception:
            pass
        return []

    # ── Screenshot ─────────────────────────────────────────────────────────────

    def screenshot(self, path: str) -> bool:
        try:
            if self._is_selenium:
                self.driver.save_screenshot(path)
            else:
                self.driver.screenshot(path=path)
            return True
        except Exception as exc:
            logger.warning("Screenshot failed: {}", exc)
            return False

    # ── Wait helpers ───────────────────────────────────────────────────────────

    def wait_for_url_change(self, old_url: str, timeout: int = 10) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if self.get_current_url() != old_url:
                return True
            time.sleep(0.3)
        return False

    def wait_seconds(self, seconds: float) -> None:
        time.sleep(seconds)
