# scraper.py
import hashlib
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

async def fetch_url_text(url: str, timeout: int = 20) -> str:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.text

def make_hash(title: str, link: str) -> str:
    combined = (title or "") + "|" + (link or "")
    return hashlib.sha256(combined.strip().encode("utf-8")).hexdigest()

async def parse_rss_or_atom(url: str) -> List[Dict]:
    try:
        html = await fetch_url_text(url)
    except Exception as e:
        print(f"[scraper] failed fetch {url}: {e}")
        return []
    soup = BeautifulSoup(html, "lxml")
    items = soup.find_all(["item", "entry"])
    results = []
    for it in items:
        title_tag = it.find("title")
        link_tag = it.find("link")
        title = title_tag.get_text(strip=True) if title_tag else None
        link = None
        if link_tag:
            link = link_tag.get("href") or link_tag.get_text(strip=True)
        if not link:
            g = it.find("guid")
            if g:
                link = g.get_text(strip=True)
        summary_tag = it.find("description") or it.find("summary") or it.find("content")
        summary = summary_tag.get_text(strip=True) if summary_tag else None
        posted_date = None
        pub = it.find("pubdate") or it.find("published") or it.find("updated")
        if pub:
            posted_date = pub.get_text(strip=True)
        if title and link:
            results.append({
                "title": title,
                "link": link,
                "summary": summary,
                "posted_date": posted_date,
            })
    return results

async def parse_generic_list_page(url: str, item_selector: str = "a", base_url: Optional[str] = None) -> List[Dict]:
    try:
        html = await fetch_url_text(url)
    except Exception as e:
        print(f"[scraper] failed fetch {url}: {e}")
        return []
    soup = BeautifulSoup(html, "lxml")
    results = []
    elements = soup.select(item_selector)
    for el in elements:
        title = None
        link = None
        if el.name == "a":
            title = el.get_text(strip=True)
            link = el.get("href")
        else:
            a = el.find("a")
            if a:
                title = a.get_text(strip=True)
                link = a.get("href")
        if not title or not link:
            continue
        if base_url and link.startswith("/"):
            link = base_url.rstrip("/") + link
        results.append({
            "title": title,
            "link": link,
            "summary": None,
            "posted_date": None,
        })
    return results

# Add the actual sites you want to monitor below (RSS preferred when available).
SITES = [
    # Example RSS site - replace with real feeds or pages you want
    # {"name": "UPSC RSS", "url": "https://upsc.gov.in/rss", "parser": parse_rss_or_atom},
    # Example generic HTML page (edit selector)
    # {"name": "Example Careers", "url": "https://example.com/careers", "parser": parse_generic_list_page, "parser_kwargs": {"item_selector": ".career-item a", "base_url": "https://example.com"}},
]

async def run_all_sites(sites=None) -> List[Dict]:
    if sites is None:
        sites = SITES
    results = []
    for site in sites:
        parser = site["parser"]
        url = site["url"]
        kwargs = site.get("parser_kwargs", {})
        try:
            parsed = await parser(url, **kwargs) if callable(parser) else []
            for item in parsed:
                item["organization"] = site.get("name")
                item["hash"] = make_hash(item.get("title", ""), item.get("link", ""))
                item["discovered_at"] = datetime.utcnow().isoformat()
                results.append(item)
        except Exception as e:
            print(f"[scraper] error scraping {url}: {e}")
            continue
    return results
