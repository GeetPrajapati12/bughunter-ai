"""
tests/test_detectors.py
-----------------------
Unit tests for the UI Detection Engine.
No browser required — all tests operate on static HTML strings.
"""

import pytest
from detector.buttons    import ButtonDetector
from detector.forms      import FormDetector
from detector.tables     import TableDetector
from detector.dropdowns  import DropdownDetector
from detector.searchbox  import SearchBoxDetector
from detector.pagination import PaginationDetector


# ── Sample HTML fixtures ───────────────────────────────────────────────────────

LOGIN_HTML = """
<html><body>
  <form id="login-form" action="/login" method="POST">
    <label for="email">Email</label>
    <input type="email" id="email" name="email" required placeholder="you@example.com">
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required>
    <button type="submit" id="login-btn">Sign In</button>
  </form>
</body></html>
"""

TABLE_HTML = """
<html><body>
  <table id="users-table">
    <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
    <tbody>
      <tr><td>Alice</td><td>alice@example.com</td><td>Admin</td></tr>
      <tr><td>Bob</td><td>bob@example.com</td><td>User</td></tr>
    </tbody>
  </table>
</body></html>
"""

SEARCH_HTML = """
<html><body>
  <div class="search-bar">
    <input type="search" id="q" name="q" placeholder="Search products…">
    <button type="submit">Go</button>
  </div>
</body></html>
"""

PAGINATION_HTML = """
<html><body>
  <nav class="pagination" aria-label="Pagination">
    <a href="?page=1">«</a>
    <a href="?page=1">1</a>
    <a href="?page=2">2</a>
    <a href="?page=3">3</a>
    <a href="?page=2">»</a>
  </nav>
</body></html>
"""

DROPDOWN_HTML = """
<html><body>
  <label for="country">Country</label>
  <select id="country" name="country">
    <option value="">Select…</option>
    <option value="us">United States</option>
    <option value="gb">United Kingdom</option>
    <option value="in">India</option>
  </select>
</body></html>
"""


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestButtonDetector:
    def test_detects_submit_button(self):
        detector = ButtonDetector()
        buttons  = detector.detect_from_html(LOGIN_HTML)
        assert len(buttons) >= 1
        assert any(b.btn_type == "submit" for b in buttons)

    def test_button_text(self):
        detector = ButtonDetector()
        buttons  = detector.detect_from_html(LOGIN_HTML)
        texts    = [b.text for b in buttons]
        assert any("Sign In" in t for t in texts)


class TestFormDetector:
    def test_detects_login_form(self):
        detector = FormDetector()
        forms    = detector.detect(LOGIN_HTML)
        assert len(forms) == 1
        assert forms[0].method == "POST"

    def test_field_count(self):
        detector = FormDetector()
        forms    = detector.detect(LOGIN_HTML)
        # email + password (submit button excluded)
        assert len(forms[0].fields) == 2

    def test_required_field(self):
        detector = FormDetector()
        forms    = detector.detect(LOGIN_HTML)
        required = [f for f in forms[0].fields if f.is_required]
        assert len(required) == 2

    def test_field_labels(self):
        detector = FormDetector()
        forms    = detector.detect(LOGIN_HTML)
        labels   = {f.label for f in forms[0].fields}
        assert "Email" in labels
        assert "Password" in labels


class TestTableDetector:
    def test_detects_table(self):
        detector = TableDetector()
        tables   = detector.detect(TABLE_HTML)
        assert len(tables) >= 1

    def test_headers(self):
        detector = TableDetector()
        tables   = detector.detect(TABLE_HTML)
        assert "Name"  in tables[0].headers
        assert "Email" in tables[0].headers
        assert "Role"  in tables[0].headers

    def test_row_count(self):
        detector = TableDetector()
        tables   = detector.detect(TABLE_HTML)
        assert tables[0].row_count == 2


class TestSearchBoxDetector:
    def test_detects_search(self):
        detector = SearchBoxDetector()
        boxes    = detector.detect(SEARCH_HTML)
        assert len(boxes) >= 1

    def test_placeholder(self):
        detector = SearchBoxDetector()
        boxes    = detector.detect(SEARCH_HTML)
        assert "Search" in boxes[0].placeholder

    def test_has_button(self):
        detector = SearchBoxDetector()
        boxes    = detector.detect(SEARCH_HTML)
        assert boxes[0].has_button is True


class TestPaginationDetector:
    def test_detects_pagination(self):
        detector = PaginationDetector()
        pags     = detector.detect(PAGINATION_HTML)
        assert len(pags) >= 1

    def test_has_prev_next(self):
        detector = PaginationDetector()
        pags     = detector.detect(PAGINATION_HTML)
        assert pags[0].has_prev is True
        assert pags[0].has_next is True


class TestDropdownDetector:
    def test_detects_select(self):
        detector = DropdownDetector()
        dds      = detector.detect(DROPDOWN_HTML)
        assert len(dds) >= 1

    def test_options(self):
        detector = DropdownDetector()
        dds      = detector.detect(DROPDOWN_HTML)
        assert len(dds[0].options) >= 3
