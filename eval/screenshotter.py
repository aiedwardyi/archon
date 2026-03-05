"""
Playwright Python — navigate to preview URL, take full-page and viewport screenshots.
"""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Screenshotter:
    def __init__(self, viewport_width: int = 1440, viewport_height: int = 900):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    async def capture(
        self,
        url: str,
        output_path: Path,
        wait_seconds: float = 3.0,
        full_page: bool = True,
    ) -> Path:
        """Navigate to URL and take a screenshot.

        Args:
            url: The page URL to screenshot.
            output_path: Where to save the PNG.
            wait_seconds: Extra wait time after load for animations/charts.
            full_page: If True, captures full scrollable page. If False, viewport only.

        Returns:
            The output_path where the screenshot was saved.
        """
        from playwright.async_api import async_playwright

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": self.viewport_width, "height": self.viewport_height},
                device_scale_factor=2,  # Retina quality
            )
            page = await context.new_page()

            logger.info(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                logger.warning(f"Navigation timeout/error (proceeding anyway): {e}")

            # Wait for animations, chart rendering, image loading
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            # Take the screenshot
            await page.screenshot(path=str(output_path), full_page=full_page, type="png")
            logger.info(f"Screenshot saved: {output_path}")

            await browser.close()

        return output_path

    async def capture_both(
        self,
        url: str,
        output_dir: Path,
        wait_seconds: float = 3.0,
    ) -> dict[str, Path]:
        """Capture both a full-page and viewport-only screenshot.

        Returns dict with 'full_page' and 'viewport' keys.
        """
        from playwright.async_api import async_playwright

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        full_path = output_dir / "screenshot_full.png"
        viewport_path = output_dir / "screenshot.png"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": self.viewport_width, "height": self.viewport_height},
                device_scale_factor=2,
            )
            page = await context.new_page()

            logger.info(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                logger.warning(f"Navigation timeout/error (proceeding anyway): {e}")

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            # Viewport screenshot (above the fold)
            await page.screenshot(path=str(viewport_path), full_page=False, type="png")
            logger.info(f"Viewport screenshot saved: {viewport_path}")

            # Full page screenshot — clip height to avoid decompression bomb issues
            # At 2x device scale, max 7900px on API side means ~3950 CSS px max useful height
            # Cap at 15000 CSS px to cover most pages while avoiding 100k+ pixel screenshots
            page_height = await page.evaluate("document.documentElement.scrollHeight")
            max_css_height = 15000
            if page_height > max_css_height:
                logger.info(f"Page height {page_height}px exceeds {max_css_height}px — clipping full-page screenshot")
                await page.screenshot(
                    path=str(full_path),
                    full_page=False,
                    type="png",
                    clip={"x": 0, "y": 0, "width": self.viewport_width, "height": max_css_height},
                )
            else:
                await page.screenshot(path=str(full_path), full_page=True, type="png")
            logger.info(f"Full-page screenshot saved: {full_path}")

            await browser.close()

        return {"viewport": viewport_path, "full_page": full_path}


def capture_sync(url: str, output_path: Path, **kwargs) -> Path:
    """Synchronous wrapper around Screenshotter.capture."""
    s = Screenshotter(
        viewport_width=kwargs.pop("viewport_width", 1440),
        viewport_height=kwargs.pop("viewport_height", 900),
    )
    return asyncio.run(s.capture(url, output_path, **kwargs))
