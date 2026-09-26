"""
config/settings.py
------------------
Central configuration for BugHunter AI.
All tunable parameters live here; nothing else imports os.environ directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Project root ──────────────────────────────────────────────────────────────
ROOT_DIR: Path = Path(__file__).resolve().parent.parent

# ── Output directories ────────────────────────────────────────────────────────
REPORTS_DIR:     Path = ROOT_DIR / "reports"
SCREENSHOTS_DIR: Path = ROOT_DIR / "screenshots"
LOGS_DIR:        Path = ROOT_DIR / "logs"
CACHE_DIR:       Path = ROOT_DIR / "cache"
BASELINE_DIR:    Path = ROOT_DIR / "baselines"
VISUAL_DIFF_DIR: Path = ROOT_DIR / "visual_diffs"

for _d in (REPORTS_DIR, SCREENSHOTS_DIR, LOGS_DIR, CACHE_DIR, BASELINE_DIR, VISUAL_DIFF_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── AI Provider ───────────────────────────────────────────────────────────────
# Options: anthropic | openai | gemini | groq | ollama | omniroute
AI_PROVIDER:    str   = os.getenv("AI_PROVIDER",    "anthropic")
AI_MODEL:       str   = os.getenv("AI_MODEL",       "claude-sonnet-4-6")
AI_MAX_TOKENS:  int   = int(os.getenv("AI_MAX_TOKENS", "4096"))
AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.2"))

# ── API Keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY:    str = os.getenv("OPENAI_API_KEY",    "")
GEMINI_API_KEY:    str = os.getenv("GEMINI_API_KEY",    "")
GROQ_API_KEY:      str = os.getenv("GROQ_API_KEY",      "")
OLLAMA_BASE_URL:   str = os.getenv("OLLAMA_BASE_URL",   "http://localhost:11434")

# ── OmniRoute ─────────────────────────────────────────────────────────────────
# OmniRoute is a free self-hosted AI gateway giving access to 231+ providers.
# Install: npm install -g omniroute && omniroute
# GitHub:  https://github.com/diegosouzapw/OmniRoute
# The API key is optional for free models — leave blank to use free tier.
OMNIROUTE_API_KEY:  str = os.getenv("OMNIROUTE_API_KEY",  "")
OMNIROUTE_BASE_URL: str = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")

# ── Browser ───────────────────────────────────────────────────────────────────
BROWSER_HEADLESS:      bool  = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_ENGINE:        str   = os.getenv("BROWSER_ENGINE", "selenium")
BROWSER_WINDOW_WIDTH:  int   = int(os.getenv("BROWSER_WINDOW_WIDTH",  "1366"))
BROWSER_WINDOW_HEIGHT: int   = int(os.getenv("BROWSER_WINDOW_HEIGHT", "768"))
PAGE_LOAD_TIMEOUT:     int   = int(os.getenv("PAGE_LOAD_TIMEOUT",     "30"))
IMPLICIT_WAIT:         int   = int(os.getenv("IMPLICIT_WAIT",         "5"))
ELEMENT_TIMEOUT:       int   = int(os.getenv("ELEMENT_TIMEOUT",       "10"))

# ── Crawler ───────────────────────────────────────────────────────────────────
MAX_PAGES:           int   = int(os.getenv("MAX_PAGES",           "50"))
MAX_DEPTH:           int   = int(os.getenv("MAX_DEPTH",           "3"))
CRAWL_DELAY_SECONDS: float = float(os.getenv("CRAWL_DELAY_SECONDS", "1.0"))
RESPECT_ROBOTS_TXT:  bool  = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"

# ── Visual Regression ─────────────────────────────────────────────────────────
VISUAL_THRESHOLD: float = float(os.getenv("VISUAL_THRESHOLD", "0.1"))

# ── Reporting ─────────────────────────────────────────────────────────────────
REPORT_FORMAT:      str  = os.getenv("REPORT_FORMAT", "html")
CAPTURE_VIDEO:      bool = os.getenv("CAPTURE_VIDEO", "false").lower() == "true"
SCREENSHOT_ON_FAIL: bool = os.getenv("SCREENSHOT_ON_FAIL", "true").lower() == "true"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str  = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE:  Path = LOGS_DIR / "bughunter.log"
