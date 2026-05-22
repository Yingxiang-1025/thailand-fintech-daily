"""
WeChat Work (企业微信) webhook notification for Thailand daily news.

Format:
  Part 1 — 昨日动态：200-300字通顺中文段落
  Part 2 — 明细：每条含完整中文标题 + 完整摘要 + 原文链接
  Footer — 查看完整日报链接
Priority: PAYPAYA集团(🔥最高优先级) → 监管 → 同行品牌 → 其他
监管仅含金融科技相关，最多2条。其他板块最多2条。总量不超8条。
"""
import json
import re
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

MIN_PUSH_ITEMS = 3
MAX_PUSH_ITEMS = 8
MAX_REGULATION_IN_PUSH = 2
MAX_OTHER_IN_PUSH = 2

PEER_SECTIONS = {"bnpl", "e_wallet", "cash_loan", "digital_bank"}

WECHAT_WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=9fa02664-7bca-4059-aeab-fa9dd1b79289"
)

WEBSITE_URL = "https://yingxiang-1025.github.io/thailand-fintech-daily/"

SECTION_META = {
    "paypaya":        {"priority": 0, "label": "🔥 PAYPAYA",  "emoji": "🔥", "show_all": True},
    "regulation":     {"priority": 1, "label": "监管动态",     "emoji": "📋", "show_all": True},
    "bnpl":           {"priority": 2, "label": "BNPL同行",     "emoji": "🛒", "show_all": True},
    "e_wallet":       {"priority": 3, "label": "电子钱包",     "emoji": "📲", "show_all": True},
    "cash_loan":      {"priority": 4, "label": "现金贷",       "emoji": "💵", "show_all": True},
    "digital_lending":{"priority": 5, "label": "数字信贷",     "emoji": "💰", "show_all": False},
    "credit_card":    {"priority": 6, "label": "信用卡",       "emoji": "💳", "show_all": False},
    "digital_bank":   {"priority": 7, "label": "数字银行",     "emoji": "📱", "show_all": False},
}

_DEFAULT_META = {"priority": 99, "label": "金融科技", "emoji": "📊", "show_all": False}

CONNECTORS = {
    "paypaya": "PAYPAYA方面，",
    "regulation": "监管层面，",
    "bnpl": "BNPL/同行竞品方面，",
    "e_wallet": "电子钱包领域，",
    "cash_loan": "现金贷方面，",
    "digital_lending": "数字信贷方面，",
    "credit_card": "信用卡领域，",
    "digital_bank": "数字银行领域，",
}

_INNER_CONNECTORS = ["同时，", "此外，", "另外，", "值得关注的是，"]

_PUSH_HISTORY_FILE = Path(__file__).parent / "data" / "pushed_history.json"


# ─── Push History ─────────────────────────────────────────

def _load_push_history() -> dict:
    if _PUSH_HISTORY_FILE.exists():
        try:
            with open(_PUSH_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_push_history(history: dict):
    _PUSH_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_PUSH_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _filter_unpushed(items: list[dict]) -> list[dict]:
    """Remove items that were already pushed before."""
    history = _load_push_history()
    pushed_urls = set()
    for day_urls in history.values():
        pushed_urls.update(day_urls)
    return [item for item in items if item.get("url", "") not in pushed_urls]


def _record_pushed(items: list[dict], date_str: str):
    history = _load_push_history()
    urls = [item.get("url", "") for item in items if item.get("url")]
    if date_str in history:
        history[date_str].extend(urls)
        history[date_str] = list(set(history[date_str]))
    else:
        history[date_str] = urls
    # Keep only last 30 days
    sorted_keys = sorted(history.keys())
    while len(sorted_keys) > 30:
        del history[sorted_keys.pop(0)]
    _save_push_history(history)


# ─── Text Utils ──────────────────────────────────────────

def _clean(text: str) -> str:
    if not text:
        return ""
    out = text.replace("\n", " ").strip()
    if "<" in out:
        from bs4 import BeautifulSoup
        out = BeautifulSoup(out, "html.parser").get_text()
    return out


def _strip_trailing(text: str) -> str:
    for sep in [" - ", " — ", " | ", " · "]:
        pos = text.rfind(sep)
        if pos > len(text) // 3:
            text = text[:pos].strip()
    text = re.sub(r"\s+[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]+)*\s*$", "", text)
    text = re.sub(r"\s*https?://\S+$", "", text)
    return text.strip()


def _sentence_cut(text: str, max_len: int) -> str:
    text = text.rstrip("。；，、 ")
    if len(text) <= max_len:
        return text
    window = text[:max_len]
    for punc in ["。", "；"]:
        pos = window.rfind(punc)
        if pos > max_len * 0.35:
            return window[:pos].rstrip("。；，、 ")
    return window.rstrip("。；，、 ")


def _get_summary(item: dict) -> str:
    raw = _clean(item.get("summary_zh") or item.get("summary", ""))
    return _strip_trailing(raw)


def _title_text(item: dict) -> str:
    raw = item.get("title_zh") or item.get("title", "")
    body = raw.split("】")[-1].strip() if "】" in raw else raw
    return _strip_trailing(body)


# ─── Grouping ────────────────────────────────────────────

def _best_section(item: dict) -> str:
    sections = item.get("sections", [])
    if not sections:
        return "other"
    return min(sections, key=lambda s: SECTION_META.get(s, _DEFAULT_META)["priority"])


def _meta(section: str) -> dict:
    return SECTION_META.get(section, _DEFAULT_META)


def _group_by_section(items: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for item in items:
        sec = _best_section(item)
        groups.setdefault(sec, []).append(item)
    return dict(
        sorted(groups.items(), key=lambda kv: _meta(kv[0])["priority"])
    )


# ─── Part 1: 昨日动态 ────────────────────────────────────

def _build_digest(groups: dict[str, list[dict]], total: int) -> str:
    all_sentences = []
    items_per_section = max(1, 5 // max(len(groups), 1))

    for sec, items in groups.items():
        prefix = CONNECTORS.get(sec, "此外，")
        for idx, item in enumerate(items[:items_per_section]):
            summary = _get_summary(item)
            title = _title_text(item)
            text = summary if len(summary) > 15 else title
            text = _sentence_cut(text, 90)

            if idx == 0:
                all_sentences.append(f"{prefix}{text}")
            else:
                conn = _INNER_CONNECTORS[min(idx - 1, len(_INNER_CONNECTORS) - 1)]
                all_sentences.append(f"{conn}{text}")

            current = "。".join(all_sentences) + "。"
            if len(current) >= 280:
                break
        if len("。".join(all_sentences) + "。") >= 280:
            break

    digest = "。".join(all_sentences)
    if not digest.endswith("。"):
        digest += "。"
    return digest


# ─── Part 2: 明细 ────────────────────────────────────────

def _build_details(groups: dict[str, list[dict]], digest: str = "") -> list[str]:
    lines = []
    item_no = 0
    for sec, items in groups.items():
        meta = _meta(sec)
        lines.append(f"{meta['emoji']} **{meta['label']}**（{len(items)}条）")
        cap = len(items) if meta.get("show_all") else 3
        for item in items[:cap]:
            item_no += 1
            title = _title_text(item)
            url = item.get("url", "")
            major_tag = "🔴" if item.get("is_major") else ""
            summary = _get_summary(item)
            summary = _sentence_cut(summary, 120)

            display_title = f"{major_tag}{title}" if major_tag else title
            lines.append(f"{item_no}. **{display_title}**")
            if summary and summary[:20] not in digest:
                lines.append(f"> {summary}")
            if url:
                lines.append(f"[查看原文]({url})")
        if len(items) > cap:
            lines.append(f"...另有{len(items) - cap}条")
        lines.append("")
    return lines


# ─── Assemble ────────────────────────────────────────────

def build_message(new_items: list[dict], today_str: str) -> str | None:
    if not new_items:
        return None

    groups = _group_by_section(new_items)
    total = len(new_items)
    major_count = sum(1 for n in new_items if n.get("is_major"))
    digest = _build_digest(groups, total)

    lines = [
        f"📰 **泰国金融科技日报 | {today_str}**",
        f"新增<font color=\"info\">{total}</font>条资讯",
    ]
    if major_count:
        lines[-1] += f"　其中<font color=\"warning\">{major_count}条重大</font>"
    lines.append("")

    lines.append("**📋 昨日动态**")
    lines.append(f"> {digest}")
    lines.append("")

    lines.append("**📝 明细**")
    lines.extend(_build_details(groups, digest))

    lines.append(f"[🌐 查看完整日报]({WEBSITE_URL})")

    return "\n".join(lines)


def send_wechat_notification(new_items: list[dict], today_str: str) -> bool:
    unpushed = _filter_unpushed(new_items) if new_items else []

    if not unpushed:
        message = (
            f"📰 **泰国金融科技日报 | {today_str}**\n\n"
            f"昨日无新增资讯更新。\n\n"
            f"[🌐 查看完整日报]({WEBSITE_URL})"
        )
        logger.info("No unpushed yesterday news — sending 'no update' notification.")
    else:
        items = sorted(unpushed, key=lambda n: _meta(_best_section(n))["priority"])
        # Apply per-category caps
        reg_count = 0
        other_count = 0
        capped_items = []
        for item in items:
            sec = _best_section(item)
            if sec == "regulation":
                reg_count += 1
                if reg_count > MAX_REGULATION_IN_PUSH:
                    continue
            elif sec == "paypaya" or sec in PEER_SECTIONS:
                pass
            else:
                other_count += 1
                if other_count > MAX_OTHER_IN_PUSH:
                    continue
            capped_items.append(item)
        if reg_count > MAX_REGULATION_IN_PUSH:
            logger.info(f"Regulation cap: {reg_count} -> {MAX_REGULATION_IN_PUSH}")
        if other_count > MAX_OTHER_IN_PUSH:
            logger.info(f"Other cap: {other_count} -> {MAX_OTHER_IN_PUSH}")
        items = capped_items

        if len(items) > MAX_PUSH_ITEMS:
            logger.info(f"Push cap: trimming {len(items)} items to {MAX_PUSH_ITEMS}")
            items = items[:MAX_PUSH_ITEMS]
        if len(items) < MIN_PUSH_ITEMS:
            logger.info(f"Only {len(items)} items, below minimum {MIN_PUSH_ITEMS}")
        message = build_message(items, today_str)
        if not message:
            return False

        while len(message.encode("utf-8")) > 3800 and len(items) > MIN_PUSH_ITEMS:
            items = items[:-1]
            message = build_message(items, today_str)
        logger.info(f"Message length: {len(message)} chars, {len(message.encode('utf-8'))} bytes, items: {len(items)}")

    payload = {"msgtype": "markdown", "markdown": {"content": message}}

    try:
        resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=10)
        result = resp.json()
        if result.get("errcode") == 0:
            if unpushed:
                _record_pushed(unpushed, today_str)
            logger.info(f"WeChat push OK: {len(new_items)} items sent")
            return True
        logger.warning(f"WeChat webhook error: {result.get('errmsg', '?')}")
        return False
    except Exception as e:
        logger.error(f"WeChat push failed: {e}")
        return False
