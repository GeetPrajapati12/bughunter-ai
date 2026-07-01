"""
executor/selenium_runner.py
---------------------------
Generic Selenium test runner.
Executes test case dicts produced by the TestCaseGeneratorAgent against
a live browser.  All actions are component-generic — no hardcoded selectors
or page-specific logic.
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from pathlib     import Path
from typing      import Any

from loguru import logger

from config.settings  import SCREENSHOTS_DIR, SCREENSHOT_ON_FAIL, ELEMENT_TIMEOUT
from crawler.navigation import Navigator


@dataclass
class TestResult:
    test_id:       str
    title:         str
    status:        str     # "passed" | "failed" | "skipped" | "error"
    duration_ms:   int
    error_message: str = ""
    screenshot:    str = ""
    console_logs:  list[str] = field(default_factory=list)
    html_snippet:  str = ""


class SeleniumRunner:
    """
    Executes a list of test case dicts against a Selenium WebDriver.

    Each test case must have at minimum: id, title, steps, expected_result.
    The runner interprets the 'component_target' field to decide which
    generic test routine to call.
    """

    # Map component_target → handler method name
    _HANDLERS: dict[str, str] = {
        "page":       "_test_page_load",
        "links":      "_test_links",
        "button":     "_test_button",
        "buttons":    "_test_button",
        "form":       "_test_form",
        "forms":      "_test_form",
        "search":     "_test_search",
        "search_box": "_test_search",
        "table":      "_test_table",
        "dropdown":   "_test_dropdown",
        "upload":     "_test_upload",
        "pagination": "_test_pagination",
    }

    def __init__(self, driver: Any) -> None:
        self.driver    = driver
        self.navigator = Navigator(driver)

    def run_tests(
        self,
        test_cases: list[dict],
        page_url:   str,
        components: dict,
    ) -> list[TestResult]:
        """
        Run all test cases for a page and return results.
        """
        results: list[TestResult] = []
        for tc in test_cases:
            result = self._run_one(tc, page_url, components)
            results.append(result)
            status_icon = "✓" if result.status == "passed" else "✗"
            logger.info("{} [{}] {}", status_icon, tc.get("id", "?"), tc.get("title", "?"))
        return results

    # ── Core execution ─────────────────────────────────────────────────────────

    def _run_one(self, tc: dict, page_url: str, components: dict) -> TestResult:
        tc_id    = tc.get("id",       "TC-?")
        title    = tc.get("title",    "Untitled")
        target   = tc.get("component_target", "page").lower()
        start_ms = int(time.time() * 1000)

        try:
            # Always navigate to the page fresh
            self.navigator.goto(page_url)
            time.sleep(1)

            handler_name = self._HANDLERS.get(target, "_test_generic")
            handler      = getattr(self, handler_name, self._test_generic)
            status, msg  = handler(tc, components)

        except Exception as exc:
            status = "error"
            msg    = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-500:]}"

        end_ms   = int(time.time() * 1000)
        duration = end_ms - start_ms

        screenshot = ""
        if status in ("failed", "error") and SCREENSHOT_ON_FAIL:
            screenshot = self._capture_screenshot(tc_id)

        console_logs = self.navigator.get_console_logs()

        return TestResult(
            test_id=tc_id,
            title=title,
            status=status,
            duration_ms=duration,
            error_message=msg,
            screenshot=screenshot,
            console_logs=console_logs,
        )

    # ── Generic test handlers ──────────────────────────────────────────────────

    def _test_page_load(self, tc: dict, _: dict) -> tuple[str, str]:
        title = self.navigator.get_title()
        url   = self.navigator.get_current_url()
        if not url or "error" in url.lower():
            return "failed", f"Unexpected URL: {url}"
        return "passed", ""

    def _test_links(self, tc: dict, _: dict) -> tuple[str, str]:
        """
        Check that <a> tags intended for navigation have a usable destination.

        Many modern admin panels (Vue/React SPA routers, Laravel + Livewire,
        etc.) implement navigation via JS click handlers rather than a real
        href, often using href="#" or no href at all alongside an onclick
        handler or a data-* routing attribute. These are NOT broken links —
        they are working navigation, just not server-rendered. We only flag
        an anchor as broken when it has real link text/aria-label intended
        for navigation AND has no href, no onclick, and no other JS hook
        (data-href, data-url, data-target, ng-click, @click, v-on, etc.)
        that would indicate it's deliberately handled in code.
        """
        from selenium.webdriver.common.by import By
        links = self.driver.find_elements(By.TAG_NAME, "a")

        # Attributes that indicate the link is intentionally JS-driven,
        # not a dead/forgotten href.
        js_hook_attrs = (
            "onclick", "data-href", "data-url", "data-target", "data-action",
            "data-route", "ng-click", "v-on:click", "@click",
        )

        broken: list[str] = []
        seen:   set[str]  = set()

        for link in links[:80]:
            try:
                href       = (link.get_attribute("href") or "").strip()
                role       = (link.get_attribute("role") or "").lower()
                text       = link.text.strip()
                aria_label = (link.get_attribute("aria-label") or "").strip()
                label      = text or aria_label

                if role == "button":
                    continue   # explicit JS action, not navigation

                has_js_hook = any(link.get_attribute(attr) for attr in js_hook_attrs)
                if has_js_hook:
                    continue   # link is deliberately handled by application code

                if not label:
                    continue   # icon-only / decorative, can't meaningfully report

                is_dead = (
                    href == "" or
                    href in ("#", "javascript:void(0)", "javascript:;")
                )

                if is_dead and label not in seen:
                    seen.add(label)
                    broken.append(label)

            except Exception:
                continue

        if broken:
            unique = sorted(set(broken))
            return "failed", f"Navigation links with missing/dead href: {unique}"
        return "passed", ""

    def _test_button(self, tc: dict, components: dict) -> tuple[str, str]:
        buttons = components.get("buttons", [])
        if not buttons:
            return "skipped", "No buttons detected on page"
        btn = buttons[0]
        clicked = self.navigator.click(btn.selector)
        if not clicked:
            return "failed", f"Could not click button: {btn.selector} ({btn.text})"
        time.sleep(0.5)
        return "passed", ""

    def _test_form(self, tc: dict, components: dict) -> tuple[str, str]:
        forms = components.get("forms", [])
        if not forms:
            return "skipped", "No forms detected on page"

        form  = forms[0]
        errors: list[str] = []
        for field in form.fields:
            ftype = field.field_type
            if ftype in ("text", "email", "search"):
                ok = self.navigator.type_text(field.selector, "test_input")
                if not ok:
                    errors.append(f"Could not type in {field.selector}")
            elif ftype == "select":
                if field.options:
                    self.navigator.select_option(field.selector, field.options[0])

        if errors:
            return "failed", "; ".join(errors)
        return "passed", ""

    def _test_search(self, tc: dict, components: dict) -> tuple[str, str]:
        boxes = components.get("search_boxes", [])
        if not boxes:
            return "skipped", "No search box detected"
        box = boxes[0]
        ok  = self.navigator.type_text(box.selector, "test")
        if not ok:
            return "failed", f"Could not type into search box: {box.selector}"
        if box.has_button:
            # Try to submit
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.by   import By
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, box.selector)
                el.send_keys(Keys.RETURN)
            except Exception:
                pass
        return "passed", ""

    def _test_table(self, tc: dict, components: dict) -> tuple[str, str]:
        tables = components.get("tables", [])
        if not tables:
            return "skipped", "No table detected"
        tbl = tables[0]
        if tbl.row_count == 0 and not tbl.is_data_grid:
            return "failed", "Table has no rows"
        return "passed", ""

    def _test_dropdown(self, tc: dict, components: dict) -> tuple[str, str]:
        dropdowns = components.get("dropdowns", [])
        if not dropdowns:
            return "skipped", "No dropdowns detected"
        dd = dropdowns[0]
        if not dd.is_custom and dd.options:
            ok = self.navigator.select_option(dd.selector, dd.options[0])
            if not ok:
                return "failed", f"Could not select option in {dd.selector}"
        return "passed", ""

    def _test_upload(self, tc: dict, components: dict) -> tuple[str, str]:
        uploads = components.get("uploads", [])
        if not uploads:
            return "skipped", "No file upload detected"
        return "passed", "Upload input detected (file interaction skipped in generic runner)"

    def _test_pagination(self, tc: dict, components: dict) -> tuple[str, str]:
        pags = components.get("pagination", [])
        if not pags:
            return "skipped", "No pagination detected"
        pag = pags[0]
        if pag.has_next:
            clicked = self.navigator.click(f"{pag.selector} [aria-label='Next'], {pag.selector} a:last-child")
            if not clicked:
                return "failed", "Could not click Next page"
        return "passed", ""

    def _test_generic(self, tc: dict, _: dict) -> tuple[str, str]:
        """Fallback: just verify the page is reachable."""
        url = self.navigator.get_current_url()
        return ("passed", "") if url else ("failed", "Page URL empty")

    # ── Screenshot ─────────────────────────────────────────────────────────────

    def _capture_screenshot(self, tc_id: str) -> str:
        path = str(SCREENSHOTS_DIR / f"{tc_id}_{int(time.time())}.png")
        self.navigator.screenshot(path)
        return path
