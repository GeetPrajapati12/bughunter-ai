"""
modules/responsiveness.py
-------------------------
Responsive design testing module.
Resizes the browser to common viewports and checks for layout issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing      import Any

from loguru import logger

from crawler.navigation import Navigator


@dataclass
class ViewportResult:
    viewport:    str    # e.g. "Mobile 375×667"
    width:       int
    height:      int
    has_overflow: bool
    scroll_x:    bool
    issues:      list[str]


VIEWPORTS = [
    ("Mobile S",  320,  568),
    ("Mobile M",  375,  667),
    ("Mobile L",  425,  812),
    ("Tablet",    768, 1024),
    ("Laptop",   1366,  768),
    ("Desktop",  1920, 1080),
]


class ResponsivenessChecker:
    """
    Tests a page across common viewports and reports layout issues.
    """

    def __init__(self, driver: Any) -> None:
        self.driver    = driver
        self.navigator = Navigator(driver)
        self._is_selenium = "selenium" in type(driver).__module__

    def check(self, url: str) -> list[ViewportResult]:
        results: list[ViewportResult] = []
        for name, w, h in VIEWPORTS:
            result = self._check_viewport(url, name, w, h)
            results.append(result)
        return results

    def _check_viewport(self, url: str, name: str, w: int, h: int) -> ViewportResult:
        self._resize(w, h)
        self.navigator.goto(url)

        issues: list[str] = []
        has_overflow = False
        scroll_x     = False

        try:
            if self._is_selenium:
                overflow = self.driver.execute_script(
                    "return document.body.scrollWidth > window.innerWidth;"
                )
                scroll_x = bool(overflow)
                if scroll_x:
                    has_overflow = True
                    issues.append(f"Horizontal scroll detected at {w}px width")

                # Check if any element bleeds outside viewport
                bleed = self.driver.execute_script("""
                    const els = document.querySelectorAll('*');
                    for (let el of els) {
                        const r = el.getBoundingClientRect();
                        if (r.right > window.innerWidth + 5) return el.tagName + '.' + el.className;
                    }
                    return null;
                """)
                if bleed:
                    issues.append(f"Element bleeds outside viewport: {str(bleed)[:80]}")

        except Exception as exc:
            issues.append(f"Check error: {exc}")

        logger.debug("Responsiveness [{}x{}]: {} issues", w, h, len(issues))
        return ViewportResult(
            viewport=f"{name} {w}×{h}",
            width=w,
            height=h,
            has_overflow=has_overflow,
            scroll_x=scroll_x,
            issues=issues,
        )

    def _resize(self, w: int, h: int) -> None:
        if self._is_selenium:
            self.driver.set_window_size(w, h)
        else:
            self.driver.set_viewport_size({"width": w, "height": h})
