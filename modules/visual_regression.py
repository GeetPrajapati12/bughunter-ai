"""
modules/visual_regression.py
-----------------------------
Visual Regression Testing Module for BugHunter AI.

How it works:
  1. First run  — captures a baseline screenshot for every page and saves
                  it to baselines/<slug>.png. Nothing to compare yet.
  2. Next runs  — captures a new screenshot, compares it pixel-by-pixel
                  against the baseline, generates a highlighted diff image,
                  and reports the percentage of pixels that changed.

Key design decisions:
  - Uses Pillow (PIL) only — no external binary dependencies like ImageMagick.
  - Changed pixels are highlighted in red on the diff image so differences
    are immediately obvious when you open the report.
  - A configurable threshold (default 0.1%) avoids noise from anti-aliasing
    and minor rendering differences flagging as failures.
  - Baselines are stored per URL slug so they survive across runs and
    can be committed to git as a source of truth.
  - Calling `approve_baseline(url)` replaces the stored baseline with the
    current screenshot — useful after intentional UI changes.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from pathlib     import Path
from typing      import Any

from loguru import logger


@dataclass
class VisualResult:
    url:              str
    status:           str       # "baseline_created" | "passed" | "failed" | "error"
    diff_percent:     float     # % of pixels that changed (0.0 if no diff)
    baseline_path:    str = ""
    current_path:     str = ""
    diff_path:        str = ""  # red-highlighted diff image
    changed_pixels:   int = 0
    total_pixels:     int = 0
    message:          str = ""


class VisualRegressionTester:
    """
    Captures full-page screenshots and compares them against stored baselines.

    Parameters
    ----------
    driver:
        Active Selenium WebDriver or Playwright Page.
    baseline_dir:
        Directory where baseline screenshots are stored between runs.
    diff_dir:
        Directory where diff images for the current run are saved.
    threshold_pct:
        Maximum allowed pixel change percentage before a page is flagged
        as a visual regression. Default: 0.1 (0.1%).
    """

    def __init__(
        self,
        driver:        Any,
        baseline_dir:  Path,
        diff_dir:      Path,
        threshold_pct: float = 0.1,
    ) -> None:
        self.driver        = driver
        self.baseline_dir  = baseline_dir
        self.diff_dir      = diff_dir
        self.threshold_pct = threshold_pct
        self._is_selenium  = "selenium" in type(driver).__module__

        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.diff_dir.mkdir(parents=True, exist_ok=True)

        self._check_pillow()

    # ── Public API ─────────────────────────────────────────────────────────────

    def check(self, url: str) -> VisualResult:
        """
        Run a visual regression check for a single page URL.
        Returns a VisualResult describing what happened.
        """
        slug          = self._url_to_slug(url)
        baseline_path = self.baseline_dir / f"{slug}_baseline.png"
        current_path  = self.diff_dir     / f"{slug}_current_{int(time.time())}.png"

        # Capture current screenshot
        captured = self._capture(str(current_path))
        if not captured:
            return VisualResult(
                url=url,
                status="error",
                diff_percent=0.0,
                message="Failed to capture screenshot.",
            )

        # No baseline yet — save current as baseline
        if not baseline_path.exists():
            import shutil
            shutil.copy(str(current_path), str(baseline_path))
            logger.info("Visual baseline created for: {}", url)
            return VisualResult(
                url=url,
                status="baseline_created",
                diff_percent=0.0,
                baseline_path=str(baseline_path),
                current_path=str(current_path),
                message="Baseline created. Run again to start comparing.",
            )

        # Compare against baseline
        return self._compare(url, baseline_path, current_path, slug)

    def approve_baseline(self, url: str) -> bool:
        """
        Replace the stored baseline with the latest current screenshot.
        Call this after intentional UI changes to update the reference.
        Returns True if a current screenshot was found and approved.
        """
        slug         = self._url_to_slug(url)
        baseline_path = self.baseline_dir / f"{slug}_baseline.png"

        # Find the most recent current screenshot in diff_dir
        candidates = sorted(
            self.diff_dir.glob(f"{slug}_current_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not candidates:
            logger.warning("approve_baseline: no current screenshot found for {}", url)
            return False

        import shutil
        shutil.copy(str(candidates[0]), str(baseline_path))
        logger.info("Visual baseline approved/updated for: {}", url)
        return True

    def get_baseline_path(self, url: str) -> Path | None:
        """Return the baseline path for a URL if one exists."""
        slug = self._url_to_slug(url)
        path = self.baseline_dir / f"{slug}_baseline.png"
        return path if path.exists() else None

    # ── Screenshot ─────────────────────────────────────────────────────────────

    def _capture(self, path: str) -> bool:
        """Capture a full-page screenshot to `path`."""
        try:
            if self._is_selenium:
                # Selenium: expand the window to full page height then screenshot
                total_height = self.driver.execute_script(
                    "return Math.max(document.body.scrollHeight, "
                    "document.documentElement.scrollHeight);"
                )
                self.driver.set_window_size(1366, max(total_height, 768))
                time.sleep(0.5)
                self.driver.save_screenshot(path)
                # Restore normal size
                self.driver.set_window_size(1366, 768)
            else:
                # Playwright: native full-page screenshot
                self.driver.screenshot(path=path, full_page=True)
            return True
        except Exception as exc:
            logger.warning("Visual screenshot failed: {}", exc)
            return False

    # ── Comparison ─────────────────────────────────────────────────────────────

    def _compare(
        self,
        url:           str,
        baseline_path: Path,
        current_path:  Path,
        slug:          str,
    ) -> VisualResult:
        try:
            from PIL import Image, ImageChops, ImageDraw
        except ImportError:
            return VisualResult(
                url=url,
                status="error",
                diff_percent=0.0,
                message="Pillow not installed. Run: pip install Pillow",
            )

        try:
            baseline_img = Image.open(baseline_path).convert("RGB")
            current_img  = Image.open(current_path).convert("RGB")

            # Resize to same dimensions if they differ
            # (can happen if the page grew or shrank between runs)
            if baseline_img.size != current_img.size:
                logger.debug(
                    "Visual: size mismatch for {} — baseline={} current={}, resizing current",
                    url, baseline_img.size, current_img.size,
                )
                current_img = current_img.resize(baseline_img.size, Image.LANCZOS)

            total_pixels   = baseline_img.width * baseline_img.height
            diff_img_raw   = ImageChops.difference(baseline_img, current_img)

            # Count changed pixels — a pixel is "changed" if any channel differs
            # by more than a small tolerance (avoids font-rendering noise)
            changed_pixels = self._count_changed_pixels(diff_img_raw, tolerance=10)
            diff_pct       = (changed_pixels / total_pixels) * 100 if total_pixels else 0.0

            # Generate highlighted diff image
            diff_path = self.diff_dir / f"{slug}_diff_{int(time.time())}.png"
            self._generate_diff_image(baseline_img, current_img, diff_img_raw, diff_path, tolerance=10)

            status = "failed" if diff_pct > self.threshold_pct else "passed"

            if status == "failed":
                logger.warning(
                    "Visual regression detected on {} — {:.2f}% pixels changed ({} px)",
                    url, diff_pct, changed_pixels,
                )
            else:
                logger.info(
                    "Visual check passed for {} — {:.2f}% pixels changed",
                    url, diff_pct,
                )

            return VisualResult(
                url=url,
                status=status,
                diff_percent=round(diff_pct, 4),
                baseline_path=str(baseline_path),
                current_path=str(current_path),
                diff_path=str(diff_path),
                changed_pixels=changed_pixels,
                total_pixels=total_pixels,
                message=(
                    f"{diff_pct:.2f}% of pixels changed ({changed_pixels:,} / {total_pixels:,}). "
                    f"Threshold: {self.threshold_pct}%."
                ),
            )

        except Exception as exc:
            logger.error("Visual comparison failed for {}: {}", url, exc)
            return VisualResult(
                url=url,
                status="error",
                diff_percent=0.0,
                message=str(exc),
            )

    # ── Diff image generation ──────────────────────────────────────────────────

    @staticmethod
    def _count_changed_pixels(diff_img: Any, tolerance: int = 10) -> int:
        """
        Count pixels where any RGB channel changed by more than `tolerance`.
        """
        import numpy as np
        arr = np.array(diff_img)
        # Changed if any channel exceeds tolerance
        mask = (arr > tolerance).any(axis=2)
        return int(mask.sum())

    @staticmethod
    def _generate_diff_image(
        baseline:  Any,
        current:   Any,
        diff_raw:  Any,
        out_path:  Path,
        tolerance: int = 10,
    ) -> None:
        """
        Generate a side-by-side comparison image:
          left  = baseline
          right = current (with changed pixels highlighted in red)
        """
        from PIL import Image, ImageDraw
        import numpy as np

        arr      = np.array(diff_raw)
        mask     = (arr > tolerance).any(axis=2)

        # Overlay red highlight on the current image where pixels changed
        highlighted = current.copy()
        h_arr       = np.array(highlighted)
        h_arr[mask] = [255, 0, 0]   # red
        highlighted = Image.fromarray(h_arr.astype("uint8"))

        # Side-by-side: baseline | highlighted current
        w, h    = baseline.size
        canvas  = Image.new("RGB", (w * 2 + 10, h + 40), color=(30, 30, 30))
        draw    = ImageDraw.Draw(canvas)

        # Labels
        draw.rectangle([0, 0, w * 2 + 10, 30], fill=(20, 20, 20))
        draw.text((10,  8), "BASELINE",          fill=(180, 180, 180))
        draw.text((w + 20, 8), "CURRENT (red = changed)", fill=(255, 100, 100))

        canvas.paste(baseline,    (0,       30))
        canvas.paste(highlighted, (w + 10,  30))
        canvas.save(str(out_path))

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _url_to_slug(url: str) -> str:
        """Convert a URL to a safe filename slug."""
        # Use URL hash for uniqueness + readable path suffix
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        readable = re.sub(r"https?://", "", url)
        readable = re.sub(r"[^\w\-]", "_", readable)[:50]
        return f"{readable}_{url_hash}"

    @staticmethod
    def _check_pillow() -> None:
        try:
            import PIL   # noqa: F401
            import numpy # noqa: F401
        except ImportError:
            logger.warning(
                "Visual regression requires Pillow and numpy. "
                "Run: pip install Pillow numpy"
            )