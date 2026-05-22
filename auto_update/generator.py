"""
HTML page generator using Jinja2 templates.
"""
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import (
    DATA_DIR,
    OUTPUT_DIR,
    PAGES_DIR,
    REGULATION_DAILY_CAP,
    SECTION_DISPLAY_NAMES,
    SECTION_PAGES,
    SECTION_TAG_CLASSES,
    TEMPLATE_DIR,
)

logger = logging.getLogger(__name__)


def _validate_news_items(news_items: list[dict]) -> list[dict]:
    """Validate and filter news items before page generation."""
    valid = []
    removed_count = 0

    for item in news_items:
        pub = item.get("published", "")
        url = item.get("url", "")
        title = (item.get("title_zh") or item.get("title", ""))

        if not pub or len(pub) != 10:
            logger.warning(f"VALIDATION: removed (no/bad date): {title[:50]}")
            removed_count += 1
            continue

        try:
            pub_dt = datetime.strptime(pub, "%Y-%m-%d")
            if pub_dt.year < 2026:
                logger.warning(
                    f"VALIDATION: removed (pre-2026 date {pub}): {title[:50]}"
                )
                removed_count += 1
                continue
        except ValueError:
            logger.warning(f"VALIDATION: removed (invalid date {pub}): {title[:50]}")
            removed_count += 1
            continue

        url_year_matches = re.findall(r"/(\d{4})/", url)
        if url_year_matches:
            url_year = int(url_year_matches[-1])
            if url_year < 2026 and url_year != pub_dt.year:
                if abs(pub_dt.year - url_year) > 1:
                    logger.warning(
                        f"VALIDATION: removed (URL year {url_year} vs pub {pub}): "
                        f"{title[:50]}"
                    )
                    removed_count += 1
                    continue

        # Fix Google News unresolved URLs
        if "news.google.com/rss/articles/" in item.get("url", ""):
            from urllib.parse import quote
            title_raw = item.get("title", "")
            source = item.get("source", "")
            search_q = f'"{title_raw}" {source}'.strip()
            item["url"] = f"https://www.google.com/search?q={quote(search_q)}"

        fetch = item.get("fetched_date", "")
        if pub == fetch:
            summary = item.get("summary_zh") or item.get("summary", "")
            combined = title + " " + summary
            old_years_in_text = [
                int(y) for y in re.findall(r"20[12]\d", combined) if int(y) < 2025
            ]
            if old_years_in_text:
                logger.info(
                    f"VALIDATION: suspicious (text mentions {old_years_in_text}, "
                    f"pub={pub}, fetch={fetch}): {title[:50]}"
                )

        valid.append(item)

    if removed_count:
        logger.warning(f"VALIDATION: removed {removed_count} invalid items")
    else:
        logger.info(f"VALIDATION: all {len(valid)} items passed date checks")

    return valid


def _cap_regulation_in_list(items: list[dict], cap: int) -> list[dict]:
    """Cap regulation-only items in a list."""
    result = []
    reg_count = 0
    for item in items:
        sections = set(item.get("sections", []))
        is_pure_reg = sections == {"regulation"} or sections <= {"regulation"}
        if is_pure_reg:
            reg_count += 1
            if reg_count > cap:
                continue
        result.append(item)
    return result


def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )


def _load_all_news(data_dir: Path) -> list[dict]:
    news_file = data_dir / "news.json"
    if not news_file.exists():
        return []
    with open(news_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_key_points() -> dict:
    """Load curated key-points per section from JSON config."""
    kp_file = DATA_DIR / "key_points.json"
    if not kp_file.exists():
        return {}
    try:
        with open(kp_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load key_points.json: {e}")
        return {}


def generate_all_pages(news_items: list[dict], vol_number: int = 1):
    """Generate/update all HTML pages from news data."""
    news_items = _validate_news_items(news_items)

    env = _get_env()
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    today_str = today.strftime("%Y-%m-%d")
    new_cutoff = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    for item in news_items:
        fd = item.get("fetched_date", "")
        pub = item.get("published", "")
        item["is_new"] = (fd == today_str and pub >= new_cutoff)

    context = {
        "today_str": today_str,
        "today_day": today.strftime("%a"),
        "yesterday_str": yesterday.strftime("%Y-%m-%d"),
        "yesterday_day": yesterday.strftime("%a"),
        "month_str": today.strftime("%Y年%m月"),
        "vol": f"Vol.{vol_number:03d}",
        "section_pages": SECTION_PAGES,
        "section_tags": SECTION_TAG_CLASSES,
        "section_names": SECTION_DISPLAY_NAMES,
    }

    # Group news by section (items in paypaya section excluded from other sections)
    sections = {key: [] for key in SECTION_PAGES}
    for item in news_items:
        item_sections = item.get("sections", [])
        is_paypaya = "paypaya" in item_sections
        for sec in item_sections:
            if sec in sections:
                if is_paypaya and sec != "paypaya":
                    continue
                sections[sec].append(item)

    # Sort each section by date (newest first)
    for sec in sections:
        sections[sec].sort(key=lambda x: x.get("published", ""), reverse=True)

    # Today's and yesterday's news (cap regulation)
    today_news = [
        n for n in news_items if n.get("published") == today.strftime("%Y-%m-%d")
    ]
    today_news = _cap_regulation_in_list(today_news, REGULATION_DAILY_CAP)

    yesterday_news = [
        n for n in news_items if n.get("published") == yesterday.strftime("%Y-%m-%d")
    ]
    yesterday_news = _cap_regulation_in_list(yesterday_news, REGULATION_DAILY_CAP)

    # Current month news (cap regulation)
    month_prefix = today.strftime("%Y-%m")
    monthly_news = [
        n for n in news_items if n.get("published", "").startswith(month_prefix)
    ]
    monthly_news.sort(key=lambda x: x.get("published", ""), reverse=True)
    monthly_news = _cap_regulation_in_list(monthly_news, REGULATION_DAILY_CAP * 5)

    # Major news (top 5)
    major_news = [n for n in news_items if n.get("is_major")][:5]

    # Monthly major: prioritize is_major items, then most recent
    monthly_major = [n for n in monthly_news if n.get("is_major")]
    if len(monthly_major) < 5:
        remaining = [n for n in monthly_news if not n.get("is_major")]
        monthly_major.extend(remaining[: 5 - len(monthly_major)])

    context.update(
        {
            "sections": sections,
            "today_news": today_news,
            "yesterday_news": yesterday_news,
            "monthly_news": monthly_news,
            "monthly_major": monthly_major,
            "major_news": major_news,
            "all_news": news_items,
        }
    )

    # Generate each page
    # 1. Index page
    _render_template(env, "index.html", OUTPUT_DIR / "index.html", context)

    # 2. Section pages (skip curated pages marked with <!-- CURATED -->)
    all_key_points = _load_key_points()

    for sec_key, page_file in SECTION_PAGES.items():
        output_path = PAGES_DIR / page_file

        sec_context = {
            **context,
            "section_key": sec_key,
            "section_name": SECTION_DISPLAY_NAMES.get(sec_key, sec_key),
            "section_news": sections.get(sec_key, []),
            "page_file": page_file,
            "key_points": all_key_points.get(sec_key),
        }

        dedicated_template = f"{sec_key.replace('_', '')}.html"
        try:
            env.get_template(dedicated_template)
            _render_template(
                env, dedicated_template, PAGES_DIR / page_file, sec_context
            )
            continue
        except Exception:
            pass

        if output_path.exists():
            try:
                content = output_path.read_text(encoding="utf-8")
                if "<!-- CURATED -->" in content:
                    logger.info(f"Skipping curated page: {page_file}")
                    continue
            except Exception:
                pass

        _render_template(
            env, "section.html", PAGES_DIR / page_file, sec_context
        )

    # 3. Yesterday page
    _render_template(
        env, "yesterday.html", PAGES_DIR / "yesterday.html", context
    )

    # 4. Monthly page
    _render_template(
        env, "monthly.html", PAGES_DIR / "monthly.html", context
    )

    logger.info(f"Generated all HTML pages. Vol: {context['vol']}")


def _render_template(env: Environment, template_name: str, output_path: Path, context: dict):
    """Render a Jinja2 template to file."""
    try:
        template = env.get_template(template_name)
        html = template.render(**context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.debug(f"Generated: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate {output_path}: {e}")


def get_next_vol_number() -> int:
    """Determine the next volume number from existing data."""
    from config import DATA_DIR

    vol_file = DATA_DIR / "vol_counter.txt"
    if vol_file.exists():
        current = int(vol_file.read_text().strip())
    else:
        current = 0
    next_vol = current + 1
    vol_file.parent.mkdir(parents=True, exist_ok=True)
    vol_file.write_text(str(next_vol))
    return next_vol
