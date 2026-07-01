"""
detector/calendar.py
--------------------
Detect date-picker / calendar widgets.
"""

from __future__ import annotations

from dataclasses import dataclass
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class CalendarInfo:
    selector:  str
    cal_type:  str   # "native-date" | "datepicker" | "calendar-widget"


class CalendarDetector:
    _HINTS = ("datepicker", "date-picker", "flatpickr", "pikaday", "datetimepicker", "calendar")

    def detect(self, html: str) -> list[CalendarInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        # Native <input type="date">
        for inp in soup.find_all("input", type="date"):
            result.append(CalendarInfo(selector="input[type='date']", cal_type="native-date"))

        for inp in soup.find_all("input", type="datetime-local"):
            result.append(CalendarInfo(selector="input[type='datetime-local']", cal_type="native-date"))

        # Custom pickers by class
        for tag in soup.find_all(True):
            cls = " ".join(tag.get("class", [])).lower()
            if any(h in cls for h in self._HINTS):
                result.append(CalendarInfo(
                    selector=f".{tag['class'][0]}" if tag.get("class") else tag.name,
                    cal_type="datepicker",
                ))

        logger.debug("CalendarDetector found {} date pickers", len(result))
        return result
