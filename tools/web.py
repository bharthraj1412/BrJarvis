# tools/web.py
from __future__ import annotations

_DDG_AVAILABLE = False
try:
    from ddgs import DDGS
    _DDG_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        _DDG_AVAILABLE = True
    except ImportError:
        _DDG_AVAILABLE = False

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_AVAILABLE = True
except Exception:
    _PLAYWRIGHT_AVAILABLE = False

async def web_search(query: str, max_results: int = 10) -> list[dict]:
    if not _DDG_AVAILABLE:
        return [{"error": "duckduckgo_search/ddgs is not available. Install with: pip install ddgs"}]
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))

async def fetch_page(url: str) -> str:
    """Fetch rendered HTML page using headless Chromium. Falls back to raw HTTP if playwright missing."""
    if not _PLAYWRIGHT_AVAILABLE:
        return f"[WARNING: Playwright not installed. Falling back to raw HTTP fetch.]\n{await fetch_raw(url)}"
        
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            text = await page.inner_text("body")
            await browser.close()
            return text
    except Exception as e:
        return f"Error fetching page: {e}"

async def fetch_raw(url: str) -> str:
    """Fetch raw page content via HTTP GET."""
    if not _HTTPX_AVAILABLE:
        # Fallback to urllib
        import urllib.request
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/37.5"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            return f"Error fetching URL: {e}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10, follow_redirects=True)
        return r.text
