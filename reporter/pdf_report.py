"""
reporter/pdf_report.py
----------------------
PDF Report Generator.
Converts the HTML report to PDF using WeasyPrint (if installed),
or prints instructions to use a browser's print-to-PDF if not.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from config.settings      import REPORTS_DIR
from reporter.html_report import HTMLReporter


class PDFReporter:
    """Generate a PDF report from session data."""

    def generate(self, session: dict) -> Path | None:
        # First produce HTML
        html_reporter = HTMLReporter()
        html_path     = html_reporter.generate(session)

        pdf_path = html_path.with_suffix(".pdf")

        try:
            from weasyprint import HTML  # type: ignore
            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            logger.info("PDF report written: {}", pdf_path)
            return pdf_path
        except ImportError:
            logger.warning(
                "WeasyPrint not installed — PDF generation skipped. "
                "Install with: pip install weasyprint\n"
                "Alternatively open the HTML report in a browser and print to PDF.\n"
                "HTML report: {}",
                html_path,
            )
            return None
        except Exception as exc:
            logger.error("PDF generation failed: {}", exc)
            return None
