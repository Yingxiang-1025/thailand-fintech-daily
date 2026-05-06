"""
WeChat Work (企业微信) webhook notification for Thailand daily news.

Format:
  Part 1 — 昨日动态：200-300字通顺中文重点汇总
  Part 2 — 明细：每条含完整中文提炼 + 原文链接
  Footer — 查看完整日报（可点击直达网站）
Priority: PAYPAYA > 监管 > Others
PAYPAYA and regulation items shown in FULL; others capped.
"""
import logging
import requests

logger = logging.getLogger(__name__)

WECHAT_WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=9fa02664-7bca-4059-aeab-fa9dd1b79289"
)

WEBSITE_URL = "https://yingxiang-1025.github.io/thailand-fintech-daily/"

SECTION_META = {
    "paypaya":        {"priority": 0, "label": "PAYPAYA",   "emoji": "🏦", "show_all": True},
    "regulation":     {"priority": 1, "label": "监管动态",  "emoji": "📋", "show_all": True},
    "credit_card":    {"priority": 2, "label": "信用卡",    "emoji": "💳", "show_all": False},
    "digital_lending":{"priority": 3, "label": "数字信贷",  "emoji": "💰", "show_all": False},
    "cash_loan":      {"priority": 4, "label": "现金贷",    "emoji": "💵", "show_all": False},
    "bnpl":           {"priority": 5, "label": "先买后付",  "emoji": "🛒", "show_all": False},
    "e_wallet":       {"priority": 6, "label": "电子钱包",  "emoji": "📲", "show_all": False},
    "digital_bank":   {"priority": 7, "label": "数字银行",  "emoji": "📱", "show_all": False},
}

_DEFAULT_META = {"priority": 99, "label": "金融科技", "emoji": "📊", "show_all": False}

CONNECTORS = {
    "paypaya": "PAYPAYA方面，",
    "regulation": "监管层面，",
    "credit_card": "信用卡领域，",
    "digital_lending": "数字信贷方面，",
    "cash_loan": "现金贷方面，",
    "bnpl": "先买后付（BNPL）方面，",
    "e_wallet": "电子钱包领域，",
    "digital_bank": "数字银行领域，",
}


def _best_section(item: dict) -> str:
    sections = item.get("sections", [])
    if not sections:
        return "other"
    return min(sections, key=lambda s: SECTION_META.get(s, _DEFAULT_META)["priority"])


def _meta(section: str) -> dict:
    return SECTION_META.get(section, _DEFAULT_META)


def _clean(text: str) -> str:
    if not text:
        return ""
    out = text.replace("\n", " ").strip()
    if "<" in out:
        from bs4 import BeautifulSoup
        out = BeautifulSoup(out, "html.parser").get_text()
    return out


def _truncate(text: str, max_len: int = 80) -> str:
    clean = _clean(text)
    if len(clean) <= max_len:
        return clean
    cut = clean[:max_len]
    for sep in ["。", "；", "，", "、", " "]:
        pos = cut.rfind(sep)
        if pos > max_len // 2:
            return cut[:pos + 1].rstrip("，、；") + "…"
    return cut + "…"


def _title_text(item: dict) -> str:
    raw = item.get("title_zh") or item.get("title", "")
    return raw.split("】")[-1].strip() if "】" in raw else raw


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
    """Build 200-300 char fluent Chinese narrative summary.

    When few sections exist, includes multiple items from each section
    to produce a sufficiently detailed summary.
    """
    sentences = []
    items_per_section = max(1, 4 // max(len(groups), 1))

    for sec, items in groups.items():
        prefix = CONNECTORS.get(sec, "此外，")
        sec_parts = []
        for item in items[:items_per_section]:
            summary = _clean(item.get("summary_zh") or item.get("summary", ""))
            title = _clean(_title_text(item))
            text = summary if len(summary) > 20 else title
            text = _truncate(text, 55)
            if text.endswith("…"):
                last_punc = max(text.rfind("，"), text.rfind("、"), text.rfind("；"))
                if last_punc > len(text) // 2:
                    text = text[:last_punc] + "等"
            sec_parts.append(text)

        combined = "；".join(sec_parts)
        sentences.append(f"{prefix}{combined}")

        joined = "。".join(sentences) + "。"
        if len(joined) >= 280:
            break

    remaining = len(groups) - len(sentences)
    if remaining > 0:
        sentences.append(f"另有{remaining}个板块有新动态")

    digest = "。".join(sentences)
    if not digest.endswith("。"):
        digest += "。"
    if len(digest) > 300:
        digest = digest[:297] + "…"
    return digest


# ─── Part 2: 明细 ────────────────────────────────────────

def _build_details(groups: dict[str, list[dict]]) -> list[str]:
    """Build detail lines. PAYPAYA/regulation show ALL; others capped at 3."""
    lines = []
    item_no = 0
    for sec, items in groups.items():
        meta = _meta(sec)
        lines.append(f"{meta['emoji']} **{meta['label']}**（{len(items)}条）")
        cap = len(items) if meta.get("show_all") else 3
        for item in items[:cap]:
            item_no += 1
            title = _truncate(_title_text(item), 50)
            url = item.get("url", "")
            major_tag = "🔴" if item.get("is_major") else ""
            summary = _truncate(
                item.get("summary_zh") or item.get("summary", ""), 80
            )
            if major_tag:
                title = f"{major_tag}{title}"
            lines.append(f"{item_no}. **{title}**")
            if summary:
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
    lines.extend(_build_details(groups))

    lines.append(f"[🌐 查看完整日报]({WEBSITE_URL})")

    return "\n".join(lines)


def send_wechat_notification(new_items: list[dict], today_str: str) -> bool:
    if not new_items:
        logger.info("No new items today — skipping WeChat push.")
        return False

    message = build_message(new_items, today_str)
    if not message:
        return False

    payload = {"msgtype": "markdown", "markdown": {"content": message}}

    try:
        resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=10)
        result = resp.json()
        if result.get("errcode") == 0:
            logger.info(f"WeChat push OK: {len(new_items)} items sent")
            return True
        logger.warning(f"WeChat webhook error: {result.get('errmsg', '?')}")
        return False
    except Exception as e:
        logger.error(f"WeChat push failed: {e}")
        return False
