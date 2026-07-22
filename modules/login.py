"""
modules/login.py
----------------
Generic login module.
Detects login forms using the configured LLM, then attempts authentication.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from loguru import logger

from ai.llm_client       import LLMClient
from config.prompts      import login_detection_prompt
from crawler.navigation  import Navigator


class LoginModule:
    """
    Handles authentication for websites that require login.
    Uses the configured LLM to locate the login form regardless of HTML structure.
    """

    def __init__(self, driver: Any) -> None:
        self.driver    = driver
        self.navigator = Navigator(driver)
        self._llm      = LLMClient()

    def detect_and_login(
        self,
        username: str,
        password: str,
        url:      str | None = None,
    ) -> bool:
        if url:
            self.navigator.goto(url)
            time.sleep(2)

        html      = self.navigator.get_page_source()
        selectors = self._detect_login_form(html)

        if not selectors.get("has_login"):
            logger.info("LoginModule: no login form detected on this page")
            return False

        user_sel   = selectors.get("username_selector", "")
        pass_sel   = selectors.get("password_selector", "")
        submit_sel = selectors.get("submit_selector",  "")

        logger.debug(
            "LoginModule: detected selectors — username='{}' password='{}' submit='{}'",
            user_sel, pass_sel, submit_sel,
        )

        if not user_sel or not pass_sel:
            logger.warning("LoginModule: could not identify username/password selectors")
            return False

        typed_user = self.navigator.type_text(user_sel, username)
        typed_pass = self.navigator.type_text(pass_sel, password)

        if not typed_user or not typed_pass:
            logger.warning(
                "LoginModule: failed to type into detected fields (user_ok={}, pass_ok={}). "
                "Selectors may not match live DOM.",
                typed_user, typed_pass,
            )
            return False

        old_url = self.navigator.get_current_url()

        submitted = False
        if submit_sel:
            submitted = self.navigator.click(submit_sel)
            if not submitted:
                logger.warning("LoginModule: click on submit selector '{}' failed", submit_sel)

        if not submitted:
            # Fallback: press Enter in the password field (engine-agnostic)
            submitted = self._press_enter(pass_sel)

        if not submitted:
            logger.warning("LoginModule: could not submit the login form by any method")
            return False

        # Wait for either a URL change or the page to settle (SPA-safe).
        # Selenium and Playwright redirect at different speeds, so poll
        # instead of a single fixed sleep.
        success = self.navigator.wait_for_url_change(old_url, timeout=10)

        if not success:
            # Some SPAs update content without changing the URL at all
            # (e.g. client-side routing that keeps the same path briefly,
            # or a dashboard that loads via AJAX after login). Give it a
            # bit more time and re-check once more before giving up.
            time.sleep(2)
            new_url = self.navigator.get_current_url()
            success = new_url != old_url

        new_url = self.navigator.get_current_url()

        if success:
            logger.info("LoginModule: login succeeded — redirected to {}", new_url)
        else:
            logger.warning(
                "LoginModule: login may have failed — URL unchanged ({}). "
                "Check whether the submit selector actually triggers the login "
                "action, or whether this app shows an inline error instead of "
                "redirecting.",
                new_url,
            )

        return success

    # ── Internals ──────────────────────────────────────────────────────────────

    def _press_enter(self, field_selector: str) -> bool:
        """
        Press Enter in the given field. Works for both Selenium and
        Playwright drivers via the Navigator abstraction — does not
        assume a specific engine.
        """
        try:
            if "selenium" in type(self.driver).__module__:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.by   import By
                el = self.driver.find_element(By.CSS_SELECTOR, field_selector)
                el.send_keys(Keys.RETURN)
                return True
            else:
                # Playwright
                self.driver.press(field_selector, "Enter")
                return True
        except Exception as exc:
            logger.debug("LoginModule: _press_enter failed for '{}': {}", field_selector, exc)
            return False

    def _detect_login_form(self, html: str) -> dict:
        if self._llm.is_available():
            try:
                prompt  = login_detection_prompt(html)
                raw     = self._llm.chat(prompt, max_tokens=512)
                cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
                return json.loads(cleaned)
            except Exception as exc:
                logger.warning("AI login detection failed: {} — falling back to heuristics", exc)

        return self._heuristic_detect(html)

    @staticmethod
    def _heuristic_detect(html: str) -> dict:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        pwd_input = soup.find("input", type="password")
        if not pwd_input:
            return {"has_login": False}

        form = pwd_input.find_parent("form")
        if not form:
            return {"has_login": False}

        user_input = (
            form.find("input", type="email") or
            form.find("input", type="text")
        )
        submit_btn = (
            form.find("input", type="submit") or
            form.find("button", type="submit") or
            form.find("button")
        )

        def selector(tag: Any) -> str:
            if not tag:
                return ""
            if tag.get("id"):
                return f"#{tag['id']}"
            if tag.get("name"):
                return f"[name='{tag['name']}']"
            return tag.name

        return {
            "has_login":         True,
            "username_selector": selector(user_input),
            "password_selector": selector(pwd_input),
            "submit_selector":   selector(submit_btn),
        }