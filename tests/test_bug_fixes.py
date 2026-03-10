"""
Verification tests for 6 bug fixes + Imagen label fix.
Uses Playwright against live servers: Flask (5000), Enterprise (8080), Studio (3000).
"""

import asyncio
import re
import httpx
from playwright.async_api import async_playwright

FLASK = "http://localhost:5000"
ENTERPRISE = "http://localhost:8080"
TEST_EMAIL = "test-verify@archon.ai"
TEST_PASS = "testpass123"

results = {}


async def register_test_user():
    """Register a test user via Flask API (idempotent)."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{FLASK}/api/auth/register",
                json={"email": TEST_EMAIL, "password": TEST_PASS, "name": "Test Verifier"},
                timeout=10,
            )
        except Exception:
            pass


async def enterprise_login(page):
    """Login to Enterprise app if redirected to /login."""
    await page.goto(ENTERPRISE, wait_until="networkidle", timeout=15000)
    if "/login" in page.url:
        await page.fill('input[type="email"], input[name="email"]', TEST_EMAIL)
        await page.fill('input[type="password"], input[name="password"]', TEST_PASS)
        await page.click('button[type="submit"]')
        # Wait for redirect away from /login (could be /dashboard, /projects, etc.)
        await page.wait_for_function("!window.location.pathname.includes('/login')", timeout=10000)
        await page.wait_for_load_state("networkidle")


async def test1_quality_recommendations(page):
    """Test 1 — Quality Recommendations section exists on Governance tab."""
    name = "Test 1 (Quality Recommendations)"
    try:
        await enterprise_login(page)
        # Navigate to Artifacts tab
        await page.click('text=Artifacts', timeout=5000)
        await page.wait_for_timeout(1000)
        # Click Governance sub-tab
        await page.click('text=Governance', timeout=5000)
        await page.wait_for_timeout(2000)
        # Scroll down to find Quality Recommendations (governance shows for current project)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        content = await page.content()
        has_title = "Quality Recommendations" in content
        has_subtitle = "Suggestions to improve" in content or "improve your next iteration" in content
        if has_title and has_subtitle:
            results[name] = "PASS"
        else:
            missing = []
            if not has_title:
                missing.append("'Quality Recommendations' not found")
            if not has_subtitle:
                missing.append("'Suggestions to improve your next iteration' not found")
            results[name] = f"FAIL — {'; '.join(missing)}"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def test2_imagen_images(page):
    """Test 2 — All Imagen asset images return HTTP 200."""
    name = "Test 2 (Imagen Images)"
    try:
        await page.goto(f"{FLASK}/api/preview/647/1", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)
        # Collect asset URLs from multiple sources: img src, CSS background-image, inline styles
        asset_urls = await page.evaluate("""() => {
            const urls = new Set();
            // Check img src attributes
            document.querySelectorAll('img').forEach(img => {
                if (img.src && img.src.includes('/api/assets/')) urls.add(img.src);
            });
            // Check computed background-image styles
            document.querySelectorAll('*').forEach(el => {
                const bg = getComputedStyle(el).backgroundImage;
                if (bg && bg !== 'none') {
                    const match = bg.match(/url\\(['"]?(http[^'"\\)]+\\/api\\/assets\\/[^'"\\)]+)/);
                    if (match) urls.add(match[1]);
                }
            });
            // Check inline style attributes in HTML
            const html = document.documentElement.outerHTML;
            const re = /(?:src|url)\\s*[=:(]\\s*['"]?(http[^'"\\s)]+\\/api\\/assets\\/[^'"\\s)]+)/g;
            let m;
            while ((m = re.exec(html)) !== null) urls.add(m[1]);
            // Also check relative asset URLs
            const re2 = /\\/api\\/assets\\/[^'"\\s)]+/g;
            while ((m = re2.exec(html)) !== null) urls.add(window.location.origin + m[0]);
            return [...urls];
        }""")
        if not asset_urls:
            results[name] = "FAIL — no /api/assets/ URLs found on page"
            return
        failures = []
        async with httpx.AsyncClient() as client:
            for url in asset_urls:
                resp = await client.head(url, timeout=10, follow_redirects=True)
                if resp.status_code != 200:
                    failures.append(f"{url} -> {resp.status_code}")
        if failures:
            results[name] = f"FAIL — {'; '.join(failures[:3])}"
        else:
            results[name] = f"PASS ({len(asset_urls)} asset(s) verified)"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def test3_double_nlu(browser):
    """Test 3 — Code check: /iterate skips NLU when provided_nlu_result is present."""
    name = "Test 3 (Double NLU)"
    try:
        import pathlib
        app_py = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app.py"
        code = app_py.read_text(encoding="utf-8")
        has_check = "provided_nlu_result" in code
        has_skip = "Using provided analysis" in code or "nlu_result = provided_nlu_result" in code
        if has_check and has_skip:
            results[name] = "PASS (code check)"
        else:
            results[name] = "FAIL — provided_nlu_result skip logic not found in app.py"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def test4_interactivity(page):
    """Test 4 — Clicking a button in preview produces a visible change."""
    name = "Test 4 (Interactivity)"
    try:
        await page.goto(f"{FLASK}/api/preview/647/1", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)
        # Strategy: try multiple interaction types and check for DOM changes
        changed = False
        # Approach 1: Click a filter pill (e.g. "Nike") — should toggle active class
        filter_btn = page.locator("button.filter-pill:not(.active)").first
        if await filter_btn.count() > 0:
            initial_active = await page.locator("button.filter-pill.active").count()
            initial_classes = await page.evaluate("() => [...document.querySelectorAll('.filter-pill')].map(b => b.className).join('|')")
            await filter_btn.click(timeout=3000)
            await page.wait_for_timeout(1000)
            after_classes = await page.evaluate("() => [...document.querySelectorAll('.filter-pill')].map(b => b.className).join('|')")
            if initial_classes != after_classes:
                changed = True
        # Approach 2: Click cart icon — should open cart sidebar
        if not changed:
            cart_btn = page.locator("button.cart-icon, [class*='cart-icon']").first
            if await cart_btn.count() > 0:
                initial_html = await page.content()
                await cart_btn.click(timeout=3000)
                await page.wait_for_timeout(1000)
                after_html = await page.content()
                if initial_html != after_html:
                    changed = True
        # Approach 3: Click any visible button and check for any DOM change
        if not changed:
            buttons = page.locator("button:visible")
            count = await buttons.count()
            for i in range(min(count, 5)):
                initial_html = await page.content()
                try:
                    await buttons.nth(i).click(timeout=3000)
                    await page.wait_for_timeout(1000)
                    after_html = await page.content()
                    if initial_html != after_html:
                        changed = True
                        break
                except Exception:
                    continue
        results[name] = "PASS" if changed else "FAIL — no visible DOM change after clicking buttons"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def test5_notification_sound(browser):
    """Test 5 — Code check: AudioContext resume and global sound listener."""
    name = "Test 5 (Notification Sound)"
    try:
        import pathlib
        base = pathlib.Path(__file__).resolve().parent.parent
        hook_file = base / "frontend" / "src" / "hooks" / "useNotificationSound.ts"
        shell_file = base / "frontend-studio" / "components" / "app-shell.tsx"
        hook_code = hook_file.read_text(encoding="utf-8")
        shell_code = shell_file.read_text(encoding="utf-8")
        has_resume = "ctx.resume()" in hook_code or "resume()" in hook_code
        has_sound = "playSuccess" in shell_code or "useNotificationSound" in shell_code
        if has_resume and has_sound:
            results[name] = "PASS (code check)"
        else:
            missing = []
            if not has_resume:
                missing.append("ctx.resume() not in useNotificationSound.ts")
            if not has_sound:
                missing.append("playSuccess/useNotificationSound not in app-shell.tsx")
            results[name] = f"FAIL — {'; '.join(missing)}"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def test6_authguard_expiry(page):
    """Test 6 — Removing token redirects to /login."""
    name = "Test 6 (AuthGuard Expiry)"
    try:
        await enterprise_login(page)
        await page.evaluate("localStorage.removeItem('archon_token')")
        await page.reload(wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(3000)
        if "/login" in page.url:
            results[name] = "PASS"
        else:
            results[name] = f"FAIL — URL is {page.url}, expected /login"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def test_bonus_imagen_label(page):
    """Bonus — Imagen 4.0 Ultra label on Governance tab."""
    name = "Bonus  (Imagen Label)"
    try:
        await enterprise_login(page)
        await page.click('text=Artifacts', timeout=5000)
        await page.wait_for_timeout(1000)
        await page.click('text=Governance', timeout=5000)
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        content = await page.content()
        # Backend outputs "Imagen 4.0 Ultra" but page may render "Imagen 4 Ultra"
        if "Imagen 4.0 Ultra" in content or "Imagen 4 Ultra" in content:
            results[name] = "PASS"
        elif "Imagen 3.0" in content or "Imagen 3" in content:
            results[name] = "FAIL — found old 'Imagen 3.0' label instead of 'Imagen 4.0 Ultra'"
        else:
            results[name] = "FAIL — neither Imagen label found on page"
    except Exception as e:
        results[name] = f"FAIL — {e}"


async def main():
    await register_test_user()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Code-check tests (no browser needed)
        await test3_double_nlu(browser)
        await test5_notification_sound(browser)

        # Browser tests — each gets a fresh page
        page1 = await context.new_page()
        await test1_quality_recommendations(page1)
        await page1.close()

        page2 = await context.new_page()
        await test2_imagen_images(page2)
        await page2.close()

        page4 = await context.new_page()
        await test4_interactivity(page4)
        await page4.close()

        page6 = await context.new_page()
        await test6_authguard_expiry(page6)
        await page6.close()

        page_bonus = await context.new_page()
        await test_bonus_imagen_label(page_bonus)
        await page_bonus.close()

        await browser.close()

    # Print results
    print("\n" + "=" * 45)
    print("=== BUG FIX VERIFICATION RESULTS ===")
    print("=" * 45)
    order = [
        "Test 1 (Quality Recommendations)",
        "Test 2 (Imagen Images)",
        "Test 3 (Double NLU)",
        "Test 4 (Interactivity)",
        "Test 5 (Notification Sound)",
        "Test 6 (AuthGuard Expiry)",
        "Bonus  (Imagen Label)",
    ]
    for key in order:
        status = results.get(key, "NOT RUN")
        print(f"{key + ':':40s} {status}")
    print("=" * 45)


if __name__ == "__main__":
    asyncio.run(main())
