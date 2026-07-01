"""
crawler/sitemap.py
------------------
Lightweight data classes that represent the discovered site structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class PageInfo:
    """All data collected about a single crawled page."""
    url:          str
    title:        str
    html:         str
    visible_text: str
    links:        list[str]
    depth:        int
    analysis:     dict  = field(default_factory=dict)   # filled by AI
    test_cases:   list  = field(default_factory=list)   # filled by AI
    components:   dict  = field(default_factory=dict)   # filled by detector


class SiteMap:
    """
    Ordered collection of PageInfo objects with fast URL lookup.
    """

    def __init__(self) -> None:
        self._pages:    list[PageInfo]       = []
        self._url_index: dict[str, PageInfo] = {}

    def add(self, page: PageInfo) -> None:
        if page.url not in self._url_index:
            self._pages.append(page)
            self._url_index[page.url] = page

    def get(self, url: str) -> PageInfo | None:
        return self._url_index.get(url)

    def pages(self) -> Iterator[PageInfo]:
        yield from self._pages

    def urls(self) -> list[str]:
        return [p.url for p in self._pages]

    def __len__(self) -> int:
        return len(self._pages)

    def __repr__(self) -> str:
        return f"SiteMap(pages={len(self._pages)})"
