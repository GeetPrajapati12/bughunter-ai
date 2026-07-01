"""
crawler/crawler.py
------------------
Universal web crawler.
Visits pages using the active browser driver, collects URLs, extracts
HTML and visible text, and hands pages off to the UI detection engine.
No page-specific logic lives here.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Iterator
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from loguru import logger

from config.settings import (
    CRAWL_DELAY_SECONDS,
    MAX_DEPTH,
    MAX_PAGES,
)
from crawler.sitemap import PageInfo, SiteMap


class Crawler:
    """
    BFS crawler that stays within the target origin.

    Parameters
    ----------
    driver:
        A Selenium WebDriver or Playwright Page instance.
    base_url:
        The seed URL supplied by the user.
    """

    def __init__(self, driver: object, base_url: str) -> None:
        self.driver   = driver
        self.base_url = base_url.rstrip("/")
        self.origin   = self._get_origin(base_url)
        self.sitemap  = SiteMap()

        self._visited: set[str]    = set()
        self._queue:   deque[tuple[str, int]] = deque([(self.base_url, 0)])

    # ── Public API ─────────────────────────────────────────────────────────────

    def crawl(self) -> SiteMap:
        """
        Crawl up to MAX_PAGES pages and return the populated SiteMap.
        """
        logger.info("Starting crawl — seed={} max_pages={} max_depth={}",
                    self.base_url, MAX_PAGES, MAX_DEPTH)

        while self._queue and len(self._visited) < MAX_PAGES:
            url, depth = self._queue.popleft()

            if url in self._visited or depth > MAX_DEPTH:
                continue

            page_info = self._visit(url, depth)
            if page_info is None:
                continue

            self._visited.add(url)
            self.sitemap.add(page_info)

            for link in page_info.links:
                if link not in self._visited:
                    self._queue.append((link, depth + 1))

            time.sleep(CRAWL_DELAY_SECONDS)

        logger.info("Crawl complete — {} pages discovered", len(self.sitemap))
        return self.sitemap

    def pages(self) -> Iterator[PageInfo]:
        """Iterate over already-crawled pages."""
        yield from self.sitemap.pages()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _visit(self, url: str, depth: int) -> PageInfo | None:
        try:
            logger.debug("Visiting [depth={}] {}", depth, url)
            self._navigate(url)
            html         = self._get_page_source()
            visible_text = self._get_visible_text(html)
            title        = self._get_title()
            links        = list(self._extract_links(html, url))
            return PageInfo(
                url=url,
                title=title,
                html=html,
                visible_text=visible_text,
                links=links,
                depth=depth,
            )
        except Exception as exc:
            logger.warning("Failed to visit {}: {}", url, exc)
            return None

    def _navigate(self, url: str) -> None:
        engine = type(self.driver).__module__
        if "selenium" in engine:
            self.driver.get(url)  # type: ignore[attr-defined]
        else:
            self.driver.goto(url)  # type: ignore[attr-defined]

    def _get_page_source(self) -> str:
        engine = type(self.driver).__module__
        if "selenium" in engine:
            return self.driver.page_source  # type: ignore[attr-defined]
        return self.driver.content()  # type: ignore[attr-defined]

    def _get_title(self) -> str:
        try:
            engine = type(self.driver).__module__
            if "selenium" in engine:
                return self.driver.title  # type: ignore[attr-defined]
            return self.driver.title()  # type: ignore[attr-defined]
        except Exception:
            return ""

    def _get_visible_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "meta", "link", "noscript"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())[:5000]

    def _extract_links(self, html: str, base: str) -> Iterator[str]:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full = urljoin(base, href).split("#")[0].rstrip("/")
            if self._is_same_origin(full):
                yield full

    @staticmethod
    def _get_origin(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _is_same_origin(self, url: str) -> bool:
        return url.startswith(self.origin)
