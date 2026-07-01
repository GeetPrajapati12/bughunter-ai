"""
detector/tables.py
------------------
Detect HTML tables and data-grid elements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class TableInfo:
    selector:        str
    headers:         list[str]
    row_count:       int
    has_pagination:  bool
    has_sort:        bool
    has_filter:      bool
    is_data_grid:    bool   # True if it's a JS grid (ag-Grid, DataTables, etc.)


class TableDetector:
    """Detects native <table> and common JS data-grid components."""

    # JS grid class hints
    _GRID_CLASSES = (
        "ag-grid", "datatable", "data-table", "grid-js",
        "handsontable", "tabulator", "reacttable",
    )

    def detect(self, html: str) -> list[TableInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        for idx, table in enumerate(soup.find_all("table")):
            result.append(self._parse_table(table, idx))

        # Detect JS grids by class hint
        for div in soup.find_all("div"):
            classes = " ".join(div.get("class", [])).lower()
            if any(g in classes for g in self._GRID_CLASSES):
                result.append(TableInfo(
                    selector=f"div.{div['class'][0]}",
                    headers=[],
                    row_count=0,
                    has_pagination=True,
                    has_sort=True,
                    has_filter=True,
                    is_data_grid=True,
                ))

        logger.debug("TableDetector found {} tables/grids", len(result))
        return result

    def _parse_table(self, table: Any, idx: int) -> TableInfo:
        tbl_id = table.get("id", "")
        selector = f"#{tbl_id}" if tbl_id else f"table:nth-of-type({idx + 1})"

        # Headers from <th> in <thead> or first <tr>
        headers: list[str] = []
        thead = table.find("thead")
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all("th")]
        if not headers:
            first_row = table.find("tr")
            if first_row:
                headers = [th.get_text(strip=True) for th in first_row.find_all(["th", "td"])]

        tbody = table.find("tbody")
        rows  = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

        # Heuristics for pagination / sort / filter
        page_str = table.get_text().lower()
        has_sort   = bool(table.find(attrs={"data-sort": True})) or "sortable" in page_str
        has_filter = bool(table.find("input")) or "filter" in page_str
        page_parent = table.find_parent()
        has_pagination = (
            bool(page_parent and page_parent.find(attrs={"class": lambda c: c and "pag" in " ".join(c).lower()}))
        )

        return TableInfo(
            selector=selector,
            headers=headers,
            row_count=len(rows),
            has_pagination=has_pagination,
            has_sort=has_sort,
            has_filter=has_filter,
            is_data_grid=False,
        )
