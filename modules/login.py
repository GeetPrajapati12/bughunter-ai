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

from ai.llm_client    import LLMClient
from config.prompts   import login_detection_prompt
from crawler.navigation import Navigator


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

        if not user_sel or not pass_sel:
            logger.warning("LoginModule: could not identify username/password selectors")
            return False

        self.navigator.type_text(user_sel, username)
        self.navigator.type_text(pass_sel, password)

        old_url = self.navigator.get_current_url()

        if submit_sel:
            self.navigator.click(submit_sel)
        else:
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.by   import By
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, pass_sel)
                el.send_keys(Keys.RETURN)
            except Exception:
                pass

        time.sleep(3)
        new_url = self.navigator.get_current_url()
        success = new_url != old_url

        if success:
            logger.info("LoginModule: login succeeded — redirected to {}", new_url)
        else:
            logger.warning("LoginModule: login may have failed — URL unchanged")

        return success

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
