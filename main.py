#!/usr/bin/env python3
"""
main.py
-------
BugHunter AI — Universal AI-Powered Web Testing Agent

Usage
-----
    # Basic usage
    python main.py --url https://example.com

    # With authentication
    python main.py --url https://app.example.com --username admin --password secret

    # Choose report format
    python main.py --url https://example.com --report both

    # Use Playwright instead of Selenium
    python main.py --url https://example.com --engine playwright

    # Limit crawl depth and pages
    python main.py --url https://example.com --max-pages 10 --max-depth 2
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from loguru import logger
from rich.console import Console

# ── Configure logging before any module imports ────────────────────────────────
from config.settings import LOG_FILE, LOG_LEVEL

logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    colorize=True,
)
logger.add(
    str(LOG_FILE),
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{line} | {message}",
)

from ai.master_agent import MasterAgent, SessionConfig  # noqa: E402

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bughunter-ai",
        description="🐛 BugHunter AI — Universal AI-Powered Web Testing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url", "-u",
        required=True,
        help="Target website URL (e.g. https://example.com)",
    )
    parser.add_argument(
        "--username",
        default="",
        help="Login username (optional)",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Login password (optional)",
    )
    parser.add_argument(
        "--login-url",
        default="",
        help="Login page URL if different from --url",
    )
    parser.add_argument(
        "--engine",
        choices=["selenium", "playwright"],
        default=None,
        help="Browser engine (default: from .env / settings)",
    )
    parser.add_argument(
        "--report",
        choices=["html", "pdf", "both"],
        default=None,
        help="Report format (default: html)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to crawl",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum crawl depth",
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run browser in headless mode (default: true)",
    )
    parser.add_argument(
        "--no-accessibility",
        action="store_true",
        help="Skip accessibility checks",
    )
    parser.add_argument(
        "--no-security",
        action="store_true",
        help="Skip security checks (headers, cookies, CSRF, injection signals, exposed files)",
    )
    return parser.parse_args()


def apply_cli_overrides(args: argparse.Namespace) -> None:
    """Override settings from CLI flags."""
    import config.settings as s

    if args.engine:
        s.BROWSER_ENGINE = args.engine
        os.environ["BROWSER_ENGINE"] = args.engine

    if args.report:
        s.REPORT_FORMAT = args.report
        os.environ["REPORT_FORMAT"] = args.report

    if args.max_pages is not None:
        s.MAX_PAGES = args.max_pages

    if args.max_depth is not None:
        s.MAX_DEPTH = args.max_depth

    if args.headless is not None:
        s.BROWSER_HEADLESS = args.headless


def main() -> int:
    args = parse_args()
    apply_cli_overrides(args)

    config = SessionConfig(
        target_url=args.url,
        username=args.username,
        password=args.password,
        login_url=args.login_url,
        run_accessibility=not args.no_accessibility,
        run_security=not args.no_security,
    )

    try:
        agent  = MasterAgent()
        result = agent.run(config)
        return 0 if result.failed == 0 else 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/]")
        return 130
    except Exception as exc:
        logger.exception("Fatal error: {}", exc)
        console.print(f"[red]Fatal error:[/] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
