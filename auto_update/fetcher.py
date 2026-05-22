"""
News fetcher module: RSS feeds + web search.
Synced with Indonesia version: date validation, link validation, geographic filtering.
"""
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional

import feedparser
import requests
from dateutil import parser as date_parser

from config import (
    DATA_DIR,
    EXCLUDE_KEYWORDS,
    GLOBAL_KEYWORDS,
    REGIONAL_SOURCES,
    RSS_FEEDS,
    SEARCH_QUERIES,
    SERPAPI_KEY,
    THAILAND_GEO_KEYWORDS,
    WORD_BOUNDARY_KEYWORDS,
)

logger = logging.getLogger(__name__)

# Sources that aggregate/republish content — dates may not be original
AGGREGATOR_SOURCES = ["MSN", "msn.com", "TradingView", "tradingview.com",
                      "Yahoo", "yahoo.com"]

_MONTH_NAMES = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    # Thai
    "มกราคม": "01", "กุมภาพันธ์": "02", "มีนาคม": "03", "เมษายน": "04",
    "พฤษภาคม": "05", "มิถุนายน": "06", "กรกฎาคม": "07", "สิงหาคม": "08",
    "กันยายน": "09", "ตุลาคม": "10", "พฤศจิกายน": "11", "ธันวาคม": "12",
}


def _is_old_event_article(title: str, url: str) -> bool:
    """Detect articles about pre-2026 events based on title/URL patterns."""
    combined = (title + " " + url).lower()
    for month_name in _MONTH_NAMES:
        for pat in [
            rf"(?:in|on|per|dated?)\s+{month_name}\s+(\d{{4}})",
            rf"{month_name}[-\s]+(\d{{4}})",
        ]:
            m = re.search(pat, combined)
            if m:
                year = int(m.group(1))
                if year < 2026:
                    has_in_url = any(
                        mn in url.lower() for mn in _MONTH_NAMES
                    ) and str(year) in url
                    if has_in_url:
                        return True
    return False


def _is_aggregator_source(source: str) -> bool:
    src_lower = source.lower()
    return any(agg.lower() in src_lower for agg in AGGREGATOR_SOURCES)


def _extract_pub_date_from_page(url: str) -> str | None:
    """Fetch a page and extract the real publication date from meta tags."""
    if not url or "google.com/search" in url:
        return None
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html",
            },
            timeout=10,
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            return None
        html = resp.text[:20000]

        for pattern in [
            r'property="article:published_time"\s+content="([^"]+)"',
            r'property="og:article:published_time"\s+content="([^"]+)"',
            r'content="([^"]+)"\s+property="article:published_time"',
            r'name="publish[_-]?date"\s+content="([^"]+)"',
            r'name="date"\s+content="([^"]+)"',
            r'name="DC\.date"\s+content="([^"]+)"',
            r'name="article\.published"\s+content="([^"]+)"',
            r'"datePublished"\s*:\s*"([^"]+)"',
            r'"publishedDate"\s*:\s*"([^"]+)"',
            r'"date_published"\s*:\s*"([^"]+)"',
            r'itemprop="datePublished"\s+content="([^"]+)"',
            r'content="([^"]+)"\s+itemprop="datePublished"',
            r'class="published"[^>]*datetime="([^"]+)"',
            r'data-publishdate="([^"]+)"',
        ]:
            m = re.search(pattern, html)
            if m:
                raw = m.group(1)
                try:
                    dt = date_parser.parse(raw)
                    return dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    continue

        final_url = resp.url
        url_date = _extract_date_from_url(final_url)
        if url_date:
            return url_date

    except Exception as e:
        logger.debug(f"Failed to extract date from {url[:60]}: {e}")
    return None


def _resolve_google_news_url(gn_url: str, skip_decode: bool = False) -> str:
    """Resolve a Google News RSS redirect URL to the actual article URL.
    If skip_decode=True, returns a Google Search fallback instead of slow decoding."""
    if "news.google.com" not in gn_url:
        return gn_url
    if skip_decode:
        return gn_url
    try:
        from googlenewsdecoder import new_decoderv1
        decoded = new_decoderv1(gn_url, interval=5)
        if decoded.get("status") and decoded.get("decoded_url"):
            return decoded["decoded_url"]
    except Exception:
        pass
    try:
        resp = requests.head(gn_url, allow_redirects=True, timeout=8,
                             headers={"User-Agent": "Mozilla/5.0"})
        final = resp.url
        if final and "news.google.com" not in final:
            return final
    except Exception:
        pass
    return gn_url


def _resolve_url_fast(gn_url: str) -> str | None:
    """Fast URL resolution via HEAD redirect (no googlenewsdecoder)."""
    if "news.google.com" not in gn_url:
        return gn_url
    try:
        resp = requests.head(
            gn_url, allow_redirects=True, timeout=5,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        final = resp.url
        if final and "news.google.com" not in final and "consent.google" not in final:
            return final
    except Exception:
        pass
    return None


def _extract_date_from_url(url: str) -> str | None:
    """Extract YYYY-MM-DD from a URL path like /2026/05/10/article."""
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def _url_date_conflicts(url: str, pub_date_str: str) -> bool:
    """Return True if URL path contains a year that conflicts with published date."""
    if not url or not pub_date_str:
        return False
    url_years = re.findall(r"/(\d{4})/", url)
    if not url_years:
        return False
    try:
        pub_year = int(pub_date_str[:4])
    except (ValueError, IndexError):
        return False
    for y_str in url_years:
        y = int(y_str)
        if y < 2026 and abs(pub_year - y) > 1:
            logger.warning(
                f"URL date conflict: URL year {y} vs published {pub_date_str} "
                f"for {url[:80]}"
            )
            return True
    return False


_URL_CHECK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _validate_url(url: str) -> bool:
    """Quick check that a URL is reachable."""
    if not url or "google.com/search" in url:
        return True
    try:
        resp = requests.head(url, headers=_URL_CHECK_HEADERS, timeout=8,
                             allow_redirects=True)
        if resp.status_code in (404, 410):
            return False
        if resp.status_code >= 500:
            return False
        return True
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return True


def _url_with_fallback(url: str, title: str, source: str) -> str:
    """Return url if valid, else Google Search fallback."""
    if _validate_url(url):
        return url
    from urllib.parse import quote
    search_q = f'"{title}" {source}'.strip()
    fallback = f"https://www.google.com/search?q={quote(search_q)}"
    logger.info(f"URL replaced with Google Search fallback: {title[:50]}")
    return fallback


class NewsItem:
    """Represents a single news article."""

    def __init__(
        self,
        title: str,
        url: str,
        summary: str,
        source: str,
        published: Optional[str] = None,
        sections: Optional[list] = None,
        summary_zh: str = "",
        is_major: bool = False,
    ):
        self.title = title
        self.url = url
        self.summary = summary
        self.source = source
        self.published = published
        self.sections = sections or []
        self.summary_zh = summary_zh
        self.is_major = is_major

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "source": self.source,
            "published": self.published,
            "sections": self.sections,
            "summary_zh": self.summary_zh,
            "is_major": self.is_major,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


def _is_relevant(title: str, summary: str, source: str = "") -> bool:
    """Check if article is relevant to Thailand fintech."""
    text = (title + " " + summary).lower()
    for ex in EXCLUDE_KEYWORDS:
        if ex.lower() in text:
            return False
    if "papaya" in text and "paypaya" not in text:
        return False

    # Word-boundary matching for short keywords
    match_count = 0
    for kw in GLOBAL_KEYWORDS:
        kw_lower = kw.lower()
        if kw in WORD_BOUNDARY_KEYWORDS:
            if re.search(rf'\b{re.escape(kw_lower)}\b', text):
                match_count += 1
        else:
            if kw_lower in text:
                match_count += 1

    if match_count < 1:
        return False

    # All articles must contain at least one Thailand geographic keyword
    all_text = text.lower()
    has_geo = any(gk.lower() in all_text for gk in THAILAND_GEO_KEYWORDS)
    if not has_geo:
        logger.debug(f"Filtered (no TH geo): {title[:50]}")
        return False

    return True


def fetch_rss_feeds(max_age_days: int = 14) -> list[NewsItem]:
    """Fetch news from configured RSS feeds."""
    items = []
    cutoff = datetime.now() - timedelta(days=max_age_days)

    for feed_config in RSS_FEEDS:
        try:
            logger.info(f"Fetching RSS: {feed_config['name']}...")
            feed = feedparser.parse(feed_config["url"])

            for entry in feed.entries[:20]:
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

                if not pub_date or pub_date.year < 2026:
                    continue
                if pub_date < cutoff:
                    continue

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                if "<" in summary:
                    from bs4 import BeautifulSoup
                    summary = BeautifulSoup(summary, "html.parser").get_text()
                summary = summary[:500]

                if not _is_relevant(title, summary, source=feed_config["name"]):
                    continue

                if _is_old_event_article(title, link):
                    logger.info(f"Skip old event article: {title[:50]}")
                    continue

                actual_link = _resolve_google_news_url(link)
                url_date = _extract_date_from_url(actual_link)
                pub_str = pub_date.strftime("%Y-%m-%d") if pub_date else None
                if url_date:
                    url_year = int(url_date[:4])
                    if url_year < 2026:
                        logger.info(f"Skip old article (url_date={url_date}): {title[:50]}")
                        continue
                    if url_date != pub_str:
                        pub_str = url_date

                if _is_aggregator_source(feed_config["name"]):
                    real_date = _extract_pub_date_from_page(actual_link or link)
                    if real_date:
                        real_year = int(real_date[:4])
                        if real_year < 2026:
                            logger.info(f"Skip aggregator old (real={real_date}): {title[:50]}")
                            continue
                        if real_date != pub_str:
                            pub_str = real_date

                if _url_date_conflicts(actual_link, pub_str):
                    continue

                final_url = actual_link if actual_link != link else link
                final_url = _url_with_fallback(final_url, title, feed_config["name"])

                item = NewsItem(
                    title=title,
                    url=final_url,
                    summary=summary,
                    source=feed_config["name"],
                    published=pub_str,
                )
                items.append(item)

        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {feed_config['name']}: {e}")

    logger.info(f"RSS: fetched {len(items)} relevant articles")
    return items


def search_web(queries: Optional[list] = None) -> list[NewsItem]:
    """Search for news using SerpAPI or Google News RSS fallback."""
    queries = queries or SEARCH_QUERIES
    items = []

    if SERPAPI_KEY:
        items = _search_serpapi(queries)
    else:
        items = _search_google_news_rss(queries)

    logger.info(f"Web search: fetched {len(items)} relevant articles")
    return items


def _search_serpapi(queries: list) -> list[NewsItem]:
    """Use SerpAPI for Google search results."""
    items = []
    seen_urls = set()

    for query in queries:
        try:
            resp = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": SERPAPI_KEY,
                    "engine": "google_news",
                    "gl": "th",
                    "hl": "en",
                },
                timeout=15,
            )
            data = resp.json()

            for result in data.get("news_results", [])[:5]:
                url = result.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                if "date" not in result:
                    continue
                try:
                    parsed_pub = date_parser.parse(result["date"])
                except (ValueError, TypeError):
                    continue
                if parsed_pub.year < 2026:
                    continue
                pub_date = parsed_pub.strftime("%Y-%m-%d")

                title_text = result.get("title", "")
                snippet = result.get("snippet", "")
                if not _is_relevant(title_text, snippet):
                    continue
                if _is_old_event_article(title_text, url):
                    continue
                if _url_date_conflicts(url, pub_date):
                    continue

                final_url = _url_with_fallback(url, title_text, result.get("source", {}).get("name", "Web"))
                item = NewsItem(
                    title=title_text,
                    url=final_url,
                    summary=snippet,
                    source=result.get("source", {}).get("name", "Web"),
                    published=pub_date,
                )
                items.append(item)

            time.sleep(1)

        except Exception as e:
            logger.warning(f"SerpAPI search failed for '{query}': {e}")

    return items


def _search_google_news_rss(queries: list) -> list[NewsItem]:
    """Fallback: use Google News RSS (free, no API key needed).
    Skips slow URL decoding during search — uses Google Search fallback URLs."""
    items = []
    seen_urls = set()

    for query in queries:
        try:
            from urllib.parse import quote
            encoded_query = quote(query + " Thailand")
            rss_url = (
                f"https://news.google.com/rss/search?q={encoded_query}&hl=en&gl=TH&ceid=TH:en"
            )
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:10]:
                gn_url = entry.get("link", "")
                if gn_url in seen_urls:
                    continue
                seen_urls.add(gn_url)

                if not (hasattr(entry, "published_parsed") and entry.published_parsed):
                    continue
                parsed_pub = datetime(*entry.published_parsed[:6])
                if parsed_pub.year < 2026:
                    continue
                pub_date = parsed_pub.strftime("%Y-%m-%d")

                raw_summary = entry.get("summary", "").strip()
                if "<" in raw_summary:
                    from bs4 import BeautifulSoup
                    raw_summary = BeautifulSoup(raw_summary, "html.parser").get_text()
                raw_summary = raw_summary[:500]

                title_text = entry.get("title", "").strip()
                gn_source = entry.get("source", {}).get("title", "Google News")
                if not _is_relevant(title_text, raw_summary, source=gn_source):
                    continue

                if _is_old_event_article(title_text, gn_url):
                    logger.info(f"Skip old event article: {title_text[:50]}")
                    continue

                # Try fast HEAD redirect first, fall back to Google Search
                resolved = _resolve_url_fast(gn_url)
                if resolved:
                    final_url = resolved
                    url_date = _extract_date_from_url(resolved)
                    if url_date and int(url_date[:4]) >= 2026:
                        pub_date = url_date
                else:
                    search_q = f'"{title_text}" {gn_source}'.strip()
                    final_url = f"https://www.google.com/search?q={quote(search_q)}"

                if _url_date_conflicts(final_url, pub_date):
                    continue

                item = NewsItem(
                    title=title_text,
                    url=final_url,
                    summary=raw_summary,
                    source=gn_source,
                    published=pub_date,
                )
                items.append(item)

            time.sleep(0.3)

        except Exception as e:
            logger.warning(f"Google News RSS search failed for '{query}': {e}")

    return items


def load_existing_news() -> list[dict]:
    """Load previously saved news from JSON file."""
    news_file = DATA_DIR / "news.json"
    if news_file.exists():
        with open(news_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_news(items: list[dict]):
    """Save news items to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    news_file = DATA_DIR / "news.json"
    with open(news_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(items)} news items to {news_file}")


def _title_key(title: str) -> str:
    """Extract first 35 chars of cleaned title for similarity matching."""
    t = re.sub(r"^【[^】]+】\s*", "", title)
    t = re.sub(r"\s*-\s*[^-]+$", "", t)
    return t.strip().lower()[:35]


def _title_keys_for_item(item: dict) -> set[str]:
    """Generate multiple title keys from an item for broader dedup."""
    keys = set()
    for field in ("title", "title_cn", "title_zh"):
        val = item.get(field, "")
        if val:
            k = _title_key(val)
            if k and len(k) > 10:
                keys.add(k)
    return keys


def deduplicate(new_items: list[NewsItem], existing: list[dict]) -> list[NewsItem]:
    """Remove duplicates based on URL and title similarity."""
    existing_urls = {item["url"] for item in existing}
    existing_keys: set[str] = set()
    for item in existing:
        existing_keys.update(_title_keys_for_item(item))
    seen_keys: set[str] = set()
    result = []
    for item in new_items:
        if item.url in existing_urls:
            continue
        key = _title_key(item.title)
        if key and len(key) > 10 and (key in existing_keys or key in seen_keys):
            continue
        if key and len(key) > 10:
            seen_keys.add(key)
        result.append(item)
    return result
