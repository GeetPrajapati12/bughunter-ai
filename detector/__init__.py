"""
detector/__init__.py
--------------------
UI Detection Engine — orchestrates all individual detectors and returns
a single components dictionary for a given page.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from detector.buttons    import ButtonDetector
from detector.forms      import FormDetector
from detector.tables     import TableDetector
from detector.dropdowns  import DropdownDetector
from detector.searchbox  import SearchBoxDetector
from detector.pagination import PaginationDetector
from detector.uploads    import UploadDetector
from detector.charts     import ChartDetector
from detector.calendar   import CalendarDetector


class UIDetectionEngine:
    """
    Run all detectors against a page's HTML and aggregate results.

    Returns a dict with keys: buttons, forms, tables, dropdowns,
    search_boxes, pagination, uploads, charts, calendars.
    """

    def __init__(self) -> None:
        self._buttons    = ButtonDetector()
        self._forms      = FormDetector()
        self._tables     = TableDetector()
        self._dropdowns  = DropdownDetector()
        self._searches   = SearchBoxDetector()
        self._pagination = PaginationDetector()
        self._uploads    = UploadDetector()
        self._charts     = ChartDetector()
        self._calendars  = CalendarDetector()

    def detect(self, html: str, driver: Any = None) -> dict:
        """
        Run all detectors and return a summary dict.

        Parameters
        ----------
        html:
            Raw page HTML string.
        driver:
            Optional live driver for state-aware detection.
        """
        buttons = (
            self._buttons.detect_from_driver(driver)
            if driver is not None
            else self._buttons.detect_from_html(html)
        )

        components = {
            "buttons":     buttons,
            "forms":       self._forms.detect(html),
            "tables":      self._tables.detect(html),
            "dropdowns":   self._dropdowns.detect(html),
            "search_boxes":self._searches.detect(html),
            "pagination":  self._pagination.detect(html),
            "uploads":     self._uploads.detect(html),
            "charts":      self._charts.detect(html),
            "calendars":   self._calendars.detect(html),
        }

        total = sum(len(v) for v in components.values())
        logger.info(
            "UIDetectionEngine: {} total components "
            "(buttons={} forms={} tables={} dropdowns={} search={} pagination={} uploads={} charts={} calendars={})",
            total,
            len(components["buttons"]),
            len(components["forms"]),
            len(components["tables"]),
            len(components["dropdowns"]),
            len(components["search_boxes"]),
            len(components["pagination"]),
            len(components["uploads"]),
            len(components["charts"]),
            len(components["calendars"]),
        )
        return components
