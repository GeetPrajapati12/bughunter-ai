"""
detector/uploads.py
-------------------
Detect file upload inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class UploadInfo:
    selector: str
    accept:   str   # accepted MIME types / extensions
    multiple: bool


class UploadDetector:
    def detect(self, html: str) -> list[UploadInfo]:
        soup   = BeautifulSoup(html, "lxml")
        result = []

        for inp in soup.find_all("input", type="file"):
            inp_id   = inp.get("id", "")
            selector = f"#{inp_id}" if inp_id else "input[type='file']"
            result.append(UploadInfo(
                selector=selector,
                accept=inp.get("accept", "*"),
                multiple=inp.has_attr("multiple"),
            ))

        logger.debug("UploadDetector found {} file inputs", len(result))
        return result
