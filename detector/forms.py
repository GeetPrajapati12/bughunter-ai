"""
detector/forms.py
-----------------
Detect <form> elements and their fields on any page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class FieldInfo:
    name:        str
    field_type:  str   # text | email | password | checkbox | radio | select | textarea | file | hidden
    selector:    str
    label:       str
    is_required: bool
    placeholder: str
    options:     list[str] = field(default_factory=list)   # for <select>


@dataclass
class FormInfo:
    action:    str
    method:    str
    selector:  str
    fields:    list[FieldInfo] = field(default_factory=list)
    has_csrf:  bool = False


class FormDetector:
    """Parses HTML to identify forms and their fields."""

    def detect(self, html: str) -> list[FormInfo]:
        soup  = BeautifulSoup(html, "lxml")
        forms = soup.find_all("form")
        result: list[FormInfo] = []

        for idx, form in enumerate(forms):
            form_id  = form.get("id", "")
            selector = f"#{form_id}" if form_id else f"form:nth-of-type({idx + 1})"

            fields   = self._parse_fields(form)
            has_csrf = any(
                f.name in ("csrf_token", "_token", "csrfmiddlewaretoken")
                for f in fields
            )

            result.append(FormInfo(
                action=form.get("action", ""),
                method=form.get("method", "GET").upper(),
                selector=selector,
                fields=[f for f in fields if f.field_type != "hidden"],
                has_csrf=has_csrf,
            ))

        logger.debug("FormDetector found {} forms", len(result))
        return result

    def _parse_fields(self, form: Any) -> list[FieldInfo]:
        fields: list[FieldInfo] = []

        # <input> elements
        for inp in form.find_all("input"):
            ftype = (inp.get("type") or "text").lower()
            if ftype == "submit":
                continue
            fields.append(FieldInfo(
                name=inp.get("name", inp.get("id", "")),
                field_type=ftype,
                selector=self._best_selector(inp),
                label=self._find_label(form, inp),
                is_required=inp.has_attr("required"),
                placeholder=inp.get("placeholder", ""),
            ))

        # <textarea> elements
        for ta in form.find_all("textarea"):
            fields.append(FieldInfo(
                name=ta.get("name", ta.get("id", "")),
                field_type="textarea",
                selector=self._best_selector(ta),
                label=self._find_label(form, ta),
                is_required=ta.has_attr("required"),
                placeholder=ta.get("placeholder", ""),
            ))

        # <select> elements
        for sel in form.find_all("select"):
            options = [o.get_text(strip=True) for o in sel.find_all("option")]
            fields.append(FieldInfo(
                name=sel.get("name", sel.get("id", "")),
                field_type="select",
                selector=self._best_selector(sel),
                label=self._find_label(form, sel),
                is_required=sel.has_attr("required"),
                placeholder="",
                options=options,
            ))

        return fields

    @staticmethod
    def _best_selector(tag: Any) -> str:
        if tag.get("id"):
            return f"#{tag['id']}"
        if tag.get("name"):
            return f"[name='{tag['name']}']"
        return tag.name

    @staticmethod
    def _find_label(form: Any, field: Any) -> str:
        field_id = field.get("id", "")
        if field_id:
            lbl = form.find("label", attrs={"for": field_id})
            if lbl:
                return lbl.get_text(strip=True)
        # Implicit label (field is child of label)
        parent = field.find_parent("label")
        if parent:
            return parent.get_text(strip=True)
        return ""
