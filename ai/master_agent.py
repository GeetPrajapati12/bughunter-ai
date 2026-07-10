"""
ai/master_agent.py
------------------
Master Agent — controls the entire BugHunter AI workflow.

Responsibilities:
  1. Launch browser
  2. Optionally handle login
  3. Crawl the target website
  4. For each page:
     a. Detect UI components
     b. AI-analyse the page
     c. Generate test cases
     d. Execute tests
     e. Analyse failures
  5. Run accessibility checks
  6. Write executive report
  7. Generate HTML / PDF output
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib     import Path
from typing      import Any

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config.browser          import get_driver
from config.settings         import BROWSER_ENGINE, REPORT_FORMAT
from crawler.crawler         import Crawler
from crawler.sitemap         import PageInfo
from detector                import UIDetectionEngine
from ai.page_understanding   import PageUnderstandingAgent
from ai.testcase_generator   import TestCaseGeneratorAgent
from ai.bug_explainer        import BugExplainerAgent
from ai.report_writer        import ReportWriterAgent
from executor.selenium_runner import SeleniumRunner, TestResult
from executor.playwright_runner import PlaywrightRunner
from modules.login           import LoginModule
from modules.accessibility   import AccessibilityChecker
from modules.security        import SecurityScanner
from reporter.html_report    import HTMLReporter
from reporter.pdf_report     import PDFReporter
from reporter.screenshots    import ScreenshotManager


console = Console()


@dataclass
class SessionConfig:
    """Configuration for a single BugHunter session."""
    target_url:      str
    username:        str = ""
    password:        str = ""
    login_url:       str = ""
    run_accessibility: bool = True
    run_responsiveness: bool = False   # slow; opt-in
    run_security:      bool = True     # security checks (headers, cookies, CSRF, injection signals)


@dataclass
class SessionResult:
    """Full output of a completed BugHunter session."""
    target_url:         str
    engine:             str
    duration:           str
    pages:              list[dict] = field(default_factory=list)
    bugs:               list[dict] = field(default_factory=list)
    executive_report:   dict       = field(default_factory=dict)
    report_paths:       list[Path] = field(default_factory=list)
    total_tests:        int = 0
    passed:             int = 0
    failed:             int = 0
    skipped:            int = 0


class MasterAgent:
    """
    Orchestrates the entire BugHunter AI testing workflow.

    Usage
    -----
    agent = MasterAgent()
    result = agent.run(SessionConfig(target_url="https://example.com"))
    print(result.report_paths)
    """

    def __init__(self) -> None:
        self._ui_engine      = UIDetectionEngine()
        self._page_ai        = PageUnderstandingAgent()
        self._tc_gen         = TestCaseGeneratorAgent()
        self._bug_ai         = BugExplainerAgent()
        self._report_ai      = ReportWriterAgent()
        self._a11y_checker   = AccessibilityChecker()
        self._security_scanner = SecurityScanner()

    # ── Entry point ────────────────────────────────────────────────────────────

    def run(self, config: SessionConfig) -> SessionResult:
        console.rule("[bold cyan]🐛 BugHunter AI[/] — Starting session")
        console.print(f"  Target  : [cyan]{config.target_url}[/]")
        console.print(f"  Engine  : [yellow]{BROWSER_ENGINE}[/]")
        console.print()

        start = time.time()
        driver = get_driver()

        try:
            result = self._run_session(driver, config, start)
        finally:
            self._quit_driver(driver)

        return result

    # ── Core workflow ──────────────────────────────────────────────────────────

    def _run_session(self, driver: Any, config: SessionConfig, start: float) -> SessionResult:
        # ── Step 1: Login (optional) ──────────────────────────────────────────
        if config.username and config.password:
            console.print("[bold]Step 1:[/] Attempting login …")
            login_mod = LoginModule(driver)
            login_mod.detect_and_login(
                config.username,
                config.password,
                config.login_url or config.target_url,
            )

        # ── Step 2: Crawl ─────────────────────────────────────────────────────
        console.print("[bold]Step 2:[/] Crawling website …")
        crawler = Crawler(driver, config.target_url)
        sitemap = crawler.crawl()
        console.print(f"  Discovered [green]{len(sitemap)}[/] pages")

        # ── Step 2b: Site-wide security exposure scan (once per domain) ──────
        all_security_findings: list[dict] = []
        if config.run_security:
            console.print("[bold]Step 2b:[/] Running site-wide security exposure scan …")
            try:
                site_findings = self._security_scanner.scan_site_exposure(config.target_url)
                all_security_findings += [self._finding_to_dict(f, config.target_url) for f in site_findings]
                console.print(f"  Found [yellow]{len(site_findings)}[/] site-wide security findings")
            except Exception as exc:
                logger.warning("Site-wide security scan failed: {}", exc)

        # ── Step 3: Build runner ──────────────────────────────────────────────
        runner: SeleniumRunner = (
            PlaywrightRunner(driver)
            if BROWSER_ENGINE == "playwright"
            else SeleniumRunner(driver)
        )

        # ── Step 4: Per-page pipeline ─────────────────────────────────────────
        screenshot_mgr = ScreenshotManager(driver)
        page_summaries: list[dict]  = []
        all_bugs:       list[dict]  = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing pages …", total=len(sitemap))

            for page in sitemap.pages():
                summary = self._process_page(
                    page, driver, runner, screenshot_mgr,
                    config, all_bugs, all_security_findings,
                )
                page_summaries.append(summary)
                progress.advance(task)

        # ── Step 5: Executive report ──────────────────────────────────────────
        console.print("[bold]Step 5:[/] Generating executive report …")
        total   = sum(s["total"]   for s in page_summaries)
        passed  = sum(s["passed"]  for s in page_summaries)
        failed  = sum(s["failed"]  for s in page_summaries)
        skipped = sum(s["skipped"] for s in page_summaries)

        session_summary = {
            "target_url":    config.target_url,
            "pages_crawled": len(sitemap),
            "total_tests":   total,
            "passed":        passed,
            "failed":        failed,
            "skipped":       skipped,
            "critical_bugs": [b for b in all_bugs
                               if b.get("analysis", {}).get("severity") == "critical"],
        }
        exec_report = self._report_ai.write(session_summary)

        # ── Step 6: Render reports ────────────────────────────────────────────
        duration = f"{time.time() - start:.1f}s"
        deduped_bugs = self._deduplicate_bugs(all_bugs)
        deduped_security = self._deduplicate_security_findings(all_security_findings)
        report_session = {
            "target_url":        config.target_url,
            "engine":            BROWSER_ENGINE,
            "duration":          duration,
            "pages":             page_summaries,
            "bugs":              deduped_bugs,
            "security_findings": deduped_security,
            "executive_report":  exec_report,
        }

        report_paths = self._write_reports(report_session)

        # ── Print summary ─────────────────────────────────────────────────────
        self._print_summary(total, passed, failed, skipped, exec_report, report_paths, len(deduped_security))

        return SessionResult(
            target_url=config.target_url,
            engine=BROWSER_ENGINE,
            duration=duration,
            pages=page_summaries,
            bugs=all_bugs,
            executive_report=exec_report,
            report_paths=report_paths,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
        )

    def _process_page(
        self,
        page:          PageInfo,
        driver:        Any,
        runner:        SeleniumRunner,
        screenshot_mgr: ScreenshotManager,
        config:        SessionConfig,
        all_bugs:      list[dict],
        all_security_findings: list[dict],
    ) -> dict:
        logger.info("Processing page: {}", page.url)

        # Navigate to page
        try:
            if "selenium" in type(driver).__module__:
                driver.get(page.url)
            else:
                driver.goto(page.url)
            time.sleep(1)
            # Refresh HTML after JS render
            page.html = driver.page_source if hasattr(driver, "page_source") else driver.content()
        except Exception as exc:
            logger.warning("Could not navigate to {}: {}", page.url, exc)

        # UI detection
        components   = self._ui_engine.detect(page.html, driver)
        page.components = components

        # AI page analysis
        analysis     = self._page_ai.analyse(page)
        page.analysis = analysis

        # Accessibility
        a11y_issues = []
        if config.run_accessibility:
            a11y_issues = self._a11y_checker.check(page.html)

        # Security
        security_findings = []
        if config.run_security:
            try:
                security_findings = self._security_scanner.scan(page.url, page.html)
                all_security_findings += [self._finding_to_dict(f, page.url) for f in security_findings]
            except Exception as exc:
                logger.warning("Security scan failed for {}: {}", page.url, exc)

        # Generate test cases
        test_cases   = self._tc_gen.generate(analysis)
        page.test_cases = test_cases

        # Execute tests
        results: list[TestResult] = runner.run_tests(test_cases, page.url, components)

        # Analyse failures
        for res in results:
            if res.status in ("failed", "error") and res.error_message:
                analysis_dict = self._bug_ai.explain(
                    test_title=res.title,
                    exception_msg=res.error_message,
                    console_logs=res.console_logs,
                    screenshot_path=res.screenshot,
                )
                all_bugs.append({
                    "test_title": res.title,
                    "page_url":   page.url,
                    "analysis":   analysis_dict,
                })

        # Build summary dict
        r_dicts = [
            {
                "test_id":     r.test_id,
                "title":       r.title,
                "status":      r.status,
                "duration_ms": r.duration_ms,
                "error_message": r.error_message[:300] if r.error_message else "",
                "screenshot":  r.screenshot,
            }
            for r in results
        ]

        pg_passed  = sum(1 for r in results if r.status == "passed")
        pg_failed  = sum(1 for r in results if r.status == "failed")
        pg_skipped = sum(1 for r in results if r.status in ("skipped", "error"))

        return {
            "url":       page.url,
            "title":     page.title,
            "page_type": analysis.get("page_type", "Unknown"),
            "results":   r_dicts,
            "total":     len(results),
            "passed":    pg_passed,
            "failed":    pg_failed,
            "skipped":   pg_skipped,
            "security_findings_count": len(security_findings),
            "a11y_issues": [
                {"rule": i.rule, "severity": i.severity, "description": i.description}
                for i in a11y_issues
            ],
        }

    # ── Reporting ──────────────────────────────────────────────────────────────

    @staticmethod
    def _finding_to_dict(finding: Any, page_url: str) -> dict:
        return {
            "category":       finding.category,
            "severity":       finding.severity,
            "title":          finding.title,
            "description":    finding.description,
            "evidence":       finding.evidence,
            "recommendation": finding.recommendation,
            "page_url":       page_url,
        }

    @staticmethod
    def _deduplicate_security_findings(findings: list[dict]) -> list[dict]:
        """
        Group identical security findings (same title) found on multiple
        pages into a single entry listing affected page count, instead of
        repeating the same header/cookie/CSRF finding once per page.
        """
        grouped: dict[str, dict] = {}

        for f in findings:
            key = f.get("title", "")
            if key not in grouped:
                grouped[key] = dict(f)
                grouped[key]["page_urls"] = []
            grouped[key]["page_urls"].append(f.get("page_url", ""))

        deduped = []
        for entry in grouped.values():
            count  = len(entry["page_urls"])
            sample = entry["page_urls"][:3]
            suffix = f" (+{count - 3} more)" if count > 3 else ""
            entry["affected_pages"] = f"{count} page{'s' if count != 1 else ''}: {', '.join(sample)}{suffix}"
            deduped.append(entry)

        # Sort by severity: critical > high > medium > low > info
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        deduped.sort(key=lambda x: order.get(x.get("severity", "info"), 5))
        return deduped

    @staticmethod
    def _deduplicate_bugs(bugs: list[dict]) -> list[dict]:
        """
        Group bugs that share the same test title + root cause (the same
        underlying issue found repeatedly across many pages, e.g. a shared
        header/footer link) into a single entry listing affected page count
        and a sample of URLs, instead of one row per page.
        """
        grouped: dict[tuple[str, str], dict] = {}

        for bug in bugs:
            analysis = bug.get("analysis", {})
            key = (bug.get("test_title", ""), analysis.get("root_cause", ""))

            if key not in grouped:
                grouped[key] = {
                    "test_title": bug.get("test_title", ""),
                    "analysis":   analysis,
                    "page_urls":  [],
                }
            grouped[key]["page_urls"].append(bug.get("page_url", ""))

        deduped = []
        for entry in grouped.values():
            count  = len(entry["page_urls"])
            sample = entry["page_urls"][:3]
            suffix = f" (+{count - 3} more)" if count > 3 else ""
            entry["analysis"] = dict(entry["analysis"])  # copy, don't mutate original
            entry["analysis"]["root_cause"] = (
                f"{entry['analysis'].get('root_cause', '')} "
                f"[found on {count} page{'s' if count != 1 else ''}: "
                f"{', '.join(sample)}{suffix}]"
            )
            deduped.append(entry)

        return deduped

    def _write_reports(self, session: dict) -> list[Path]:
        paths: list[Path] = []
        fmt = REPORT_FORMAT.lower()

        if fmt in ("html", "both"):
            path = HTMLReporter().generate(session)
            if path:
                paths.append(path)

        if fmt in ("pdf", "both"):
            path = PDFReporter().generate(session)
            if path:
                paths.append(path)

        return paths

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _quit_driver(driver: Any) -> None:
        try:
            if "selenium" in type(driver).__module__:
                driver.quit()
            else:
                driver.context.browser.close()
        except Exception:
            pass

    @staticmethod
    def _print_summary(
        total: int, passed: int, failed: int, skipped: int,
        exec_report: dict, report_paths: list[Path],
        security_count: int = 0,
    ) -> None:
        console.print()
        console.rule("[bold green]Session Complete[/]")
        console.print(f"  Total   : {total}")
        console.print(f"  [green]Passed[/]  : {passed}")
        console.print(f"  [red]Failed[/]  : {failed}")
        console.print(f"  [yellow]Skipped[/] : {skipped}")
        console.print(f"  [magenta]Security[/] : {security_count} findings")
        console.print(f"  Score   : [bold yellow]{exec_report.get('quality_score', '?')}[/] / 100")
        console.print(f"  Deploy  : [bold]{exec_report.get('deployment_recommendation', '?')}[/]")
        console.print()
        for p in report_paths:
            console.print(f"  [cyan]Report[/] → {p}")
        console.print()
