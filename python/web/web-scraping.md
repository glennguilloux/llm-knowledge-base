---
id: "python-web-web-scraping"
title: "Web Scraping with BeautifulSoup and Playwright"
language: "python"
category: "web"
tags: ["scraping", "beautifulsoup", "playwright", "html", "parsing", "automation"]
version: "3.10+"
retrieval_hint: "web scraping beautifulsoup playwright HTML parsing automation extraction"
last_verified: "2026-05-22"
confidence: "high"
---

# Web Scraping with BeautifulSoup and Playwright

## When to Use
- Extracting data from websites that don't have APIs
- Automating form submissions and navigation
- Parsing HTML/XML documents
- Scraping JavaScript-rendered pages (Playwright)

## Standard Pattern

```python
import httpx
from bs4 import BeautifulSoup


# --- Basic HTML scraping ---
def scrape_articles(url: str) -> list[dict[str, str]]:
    """Scrape article titles and links from a page."""
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for article in soup.select("article"):
        title_tag = article.select_one("h2 a")
        if title_tag:
            articles.append({
                "title": title_tag.get_text(strip=True),
                "url": title_tag.get("href", ""),
            })

    return articles


# --- Scraping with CSS selectors ---
def scrape_table_data(url: str) -> list[dict[str, str]]:
    """Extract data from an HTML table."""
    response = httpx.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.select_one("table.data")

    if not table:
        return []

    headers = [th.get_text(strip=True) for th in table.select("thead th")]
    rows = []
    for tr in table.select("tbody tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        rows.append(dict(zip(headers, cells)))

    return rows


# --- Playwright for JavaScript-rendered pages ---
async def scrape_dynamic_page(url: str) -> str:
    """Scrape a page that requires JavaScript to render."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        # Wait for specific element to appear
        await page.wait_for_selector(".content-loaded")

        content = await page.content()
        await browser.close()

        return content


# --- Playwright: form submission ---
async def submit_form(url: str, username: str, password: str) -> str:
    """Fill and submit a login form."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        await page.fill('input[name="username"]', username)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"]')

        # Wait for navigation after form submission
        await page.wait_for_load_state("networkidle")

        content = await page.content()
        await browser.close()
        return content


# --- Rate-limited scraping ---
async def scrape_multiple_pages(base_url: str, pages: int) -> list[dict]:
    """Scrape multiple pages with rate limiting."""
    import asyncio

    results = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for page_num in range(1, pages + 1):
            url = f"{base_url}?page={page_num}"
            response = await client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.select(".item"):
                results.append({
                    "title": item.select_one(".title").get_text(strip=True),
                    "page": page_num,
                })

            # Rate limiting
            await asyncio.sleep(1.0)

    return results
```

## Common Mistakes

```python
# WRONG: No rate limiting (gets blocked)
for url in urls:
    response = httpx.get(url)  # Hammering the server

# CORRECT: Add delays between requests
import asyncio
for url in urls:
    response = httpx.get(url, timeout=15)
    await asyncio.sleep(1.0)  # Be polite

# WRONG: Using regex to parse HTML
import re
titles = re.findall(r"<h2>(.*?)</h2>", html)  # Breaks on nested tags

# CORRECT: Use BeautifulSoup for HTML parsing
soup = BeautifulSoup(html, "html.parser")
titles = [h2.get_text() for h2 in soup.select("h2")]

# WRONG: Not handling missing elements
title = soup.select_one("h1").get_text()  # AttributeError if h1 missing

# CORRECT: Check for None
h1 = soup.select_one("h1")
title = h1.get_text(strip=True) if h1 else "No title"

# WRONG: Ignoring robots.txt
response = httpx.get("https://example.com/admin")  # May violate ToS

# CORRECT: Check robots.txt first
# Use urllib.robotparser to check allowed paths
```

## Gotchas
- BeautifulSoup's `select()` uses CSS selectors; `find()` uses tag names and attributes
- Playwright requires a browser binary — run `playwright install` first
- `httpx` follows redirects by default with `follow_redirects=True`; `requests` follows them automatically
- JavaScript-rendered content won't appear with simple HTTP requests — use Playwright for SPAs
- Many sites block scrapers — use appropriate User-Agent headers and rate limiting
- `soup.get_text()` concatenates all text; use `separator=" "` for readable output
- Always check a site's Terms of Service and robots.txt before scraping

## Related
- python/web/requests/basics.md
- python/stdlib/httpx.md
- python/stdlib/regex.md
