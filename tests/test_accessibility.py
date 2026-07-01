"""
tests/test_accessibility.py
---------------------------
Unit tests for the accessibility checker.
"""

from modules.accessibility import AccessibilityChecker

IMG_NO_ALT = "<html><body><img src='logo.png'></body></html>"
IMG_WITH_ALT = "<html lang='en'><body><img src='logo.png' alt='Logo'></body></html>"

NO_LANG = "<html><body><p>Hello</p></body></html>"
WITH_LANG = "<html lang='en'><body><p>Hello</p></body></html>"

UNLABELLED_INPUT = """
<html lang='en'><body>
  <form><input type="text" name="search"></form>
</body></html>
"""

LABELLED_INPUT = """
<html lang='en'><body>
  <form>
    <label for="s">Search</label>
    <input type="text" id="s" name="search">
  </form>
</body></html>
"""

HEADING_SKIP = """
<html lang='en'><body>
  <h1>Title</h1>
  <h3>Skipped h2!</h3>
</body></html>
"""


class TestAccessibilityChecker:
    def test_missing_alt(self):
        issues = AccessibilityChecker().check(IMG_NO_ALT)
        rules  = [i.rule for i in issues]
        assert "img-alt" in rules

    def test_present_alt_no_issue(self):
        issues = AccessibilityChecker().check(IMG_WITH_ALT)
        rules  = [i.rule for i in issues]
        assert "img-alt" not in rules

    def test_missing_lang(self):
        issues = AccessibilityChecker().check(NO_LANG)
        rules  = [i.rule for i in issues]
        assert "html-has-lang" in rules

    def test_present_lang_no_issue(self):
        issues = AccessibilityChecker().check(WITH_LANG)
        rules  = [i.rule for i in issues]
        assert "html-has-lang" not in rules

    def test_unlabelled_input(self):
        issues = AccessibilityChecker().check(UNLABELLED_INPUT)
        rules  = [i.rule for i in issues]
        assert "label" in rules

    def test_labelled_input_no_issue(self):
        issues = AccessibilityChecker().check(LABELLED_INPUT)
        rules  = [i.rule for i in issues]
        assert "label" not in rules

    def test_heading_hierarchy(self):
        issues = AccessibilityChecker().check(HEADING_SKIP)
        rules  = [i.rule for i in issues]
        assert "heading-order" in rules
