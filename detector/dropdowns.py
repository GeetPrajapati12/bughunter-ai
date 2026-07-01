"""
detector/dropdowns.py
---------------------
Detect <select> and custom JS dropdown components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class DropdownInfo:
    selector: str
    label:    str
    options:  list[str] = field(default_factory=list)
    is_multi: bool = False
    is_custom: bool = False   # JS-rendered dropdown


class DropdownDetector:
    _CUSTOM_CLASSES = ("select2", "chosen", "selectize", "multiselect", "dropdown-menu")

    def detect(self, html: str) -> list[DropdownInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        # Native selects
        for sel in soup.find_all("select"):
            sel_id   = sel.get("id", sel.get("name", "select"))
            selector = f"#{sel_id}" if sel.get("id") else f"[name='{sel_id}']"
            label    = ""
            if sel.get("id"):
                lbl = soup.find("label", attrs={"for": sel["id"]})
                label = lbl.get_text(strip=True) if lbl else ""

            result.append(DropdownInfo(
                selector=selector,
                label=label,
                options=[o.get_text(strip=True) for o in sel.find_all("option")],
                is_multi=sel.has_attr("multiple"),
                is_custom=False,
            ))

        # Custom dropdowns
        for div in soup.find_all(["div", "ul"]):
            classes = " ".join(div.get("class", [])).lower()
            if any(c in classes for c in self._CUSTOM_CLASSES):
                result.append(DropdownInfo(
                    selector=f".{div['class'][0]}",
                    label="",
                    is_custom=True,
                ))

        logger.debug("DropdownDetector found {} dropdowns", len(result))
        return result
