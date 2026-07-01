"""
detector/pagination.py
----------------------
Detect pagination controls on a page.
"""

from __future__ import annotations

from dataclasses import dataclass
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class PaginationInfo:
    selector:      str
    has_prev:      bool
    has_next:      bool
    page_numbers:  list[str]
    is_infinite:   bool   # infinite scroll pattern


class PaginationDetector:
    _PAG_CLASSES = ("pagination", "pager", "paginator", "page-nav")

    def detect(self, html: str) -> list[PaginationInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        for tag in soup.find_all(["nav", "ul", "div"]):
            classes = " ".join(tag.get("class", [])).lower()
            if not any(p in classes for p in self._PAG_CLASSES):
                aria = (tag.get("aria-label") or "").lower()
                if "pagination" not in aria:
                    continue

            links = tag.find_all("a")
            texts = [a.get_text(strip=True).lower() for a in links]

            has_prev = any(t in ("prev", "previous", "‹", "«", "<") for t in texts)
            has_next = any(t in ("next", "›", "»", ">")              for t in texts)
            nums     = [t for t in texts if t.isdigit()]

            cls = tag.get("class", ["pagination"])
            result.append(PaginationInfo(
                selector=f".{cls[0]}",
                has_prev=has_prev,
                has_next=has_next,
                page_numbers=nums,
                is_infinite=False,
            ))

        logger.debug("PaginationDetector found {} pagination controls", len(result))
        return result
