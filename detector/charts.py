"""
detector/charts.py
------------------
Detect chart and visualisation components.
"""

from __future__ import annotations

from dataclasses import dataclass
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class ChartInfo:
    selector:    str
    chart_type:  str   # "svg-chart" | "canvas-chart" | "highcharts" | "chartjs" | "d3"


class ChartDetector:
    _LIB_HINTS = {
        "highcharts": "highcharts",
        "chartjs":    "chart-js",
        "recharts":   "recharts",
        "apexcharts": "apexcharts",
        "d3":         "d3",
        "echarts":    "echarts",
    }

    def detect(self, html: str) -> list[ChartInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        for canvas in soup.find_all("canvas"):
            cls = " ".join(canvas.get("class", []))
            result.append(ChartInfo(selector="canvas", chart_type="canvas-chart"))

        for svg in soup.find_all("svg"):
            cls = " ".join(svg.get("class", [])).lower()
            chart_type = "svg-chart"
            for lib, label in self._LIB_HINTS.items():
                if lib in cls or lib in html[:3000].lower():
                    chart_type = label
                    break
            result.append(ChartInfo(selector="svg", chart_type=chart_type))

        logger.debug("ChartDetector found {} charts", len(result))
        return result
