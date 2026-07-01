"""
detector/searchbox.py
---------------------
Detect search input boxes on a page.
"""

from __future__ import annotations

from dataclasses import dataclass
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class SearchBoxInfo:
    selector:    str
    placeholder: str
    has_button:  bool


class SearchBoxDetector:
    _SEARCH_ATTRS = {"type": "search"}
    _SEARCH_HINTS = ("search", "query", "q", "find", "keyword")

    def detect(self, html: str) -> list[SearchBoxInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        for inp in soup.find_all("input"):
            itype = (inp.get("type") or "text").lower()
            iname = (inp.get("name") or inp.get("id") or inp.get("placeholder") or "").lower()

            if itype == "search" or any(h in iname for h in self._SEARCH_HINTS):
                inp_id   = inp.get("id", "")
                selector = f"#{inp_id}" if inp_id else (
                    f"[name='{inp.get('name')}']" if inp.get("name") else "input[type='search']"
                )
                # Check for adjacent button
                parent    = inp.find_parent()
                has_btn   = bool(parent and parent.find(["button", "input"], type="submit")) if parent else False

                result.append(SearchBoxInfo(
                    selector=selector,
                    placeholder=inp.get("placeholder", ""),
                    has_button=has_btn,
                ))

        logger.debug("SearchBoxDetector found {} search boxes", len(result))
        return result
