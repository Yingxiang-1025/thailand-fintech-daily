"""
Built-in English/Thai→Chinese translation for fintech news.
Uses Google Translate (free, via deep-translator) with direct API and MyMemory fallbacks.
"""
import logging
import time

logger = logging.getLogger(__name__)

_translator = None
_fallback_translator_th = None
_fallback_translator_en = None


def _get_translator():
    global _translator
    if _translator is None:
        try:
            from deep_translator import GoogleTranslator
            _translator = GoogleTranslator(source="auto", target="zh-CN")
            logger.info("Google Translator initialized (auto-detect source)")
        except Exception as e:
            logger.warning(f"Failed to init Google Translator: {e}")
    return _translator


def _get_fallback_translator(text: str):
    """Get MyMemoryTranslator with correct source language based on text content."""
    global _fallback_translator_th, _fallback_translator_en
    from deep_translator import MyMemoryTranslator

    if _has_thai(text):
        if _fallback_translator_th is None:
            _fallback_translator_th = MyMemoryTranslator(source="th-TH", target="zh-CN")
            logger.info("MyMemory fallback initialized (Thai→Chinese)")
        return _fallback_translator_th
    else:
        if _fallback_translator_en is None:
            _fallback_translator_en = MyMemoryTranslator(source="en-GB", target="zh-CN")
            logger.info("MyMemory fallback initialized (English→Chinese)")
        return _fallback_translator_en


def _translate_direct_api(text: str) -> str | None:
    """Direct Google Translate API call via httpx (different endpoint from deep-translator)."""
    try:
        import httpx
    except ImportError:
        return None
    source = "th" if _has_thai(text) else "auto"
    params = {"client": "gtx", "sl": source, "tl": "zh-CN", "dt": "t", "q": text[:4500]}
    try:
        resp = httpx.get(
            "https://translate.googleapis.com/translate_a/single",
            params=params, timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            result = "".join(seg[0] for seg in data[0] if seg[0])
            if result and _has_chinese(result):
                return result
    except Exception as e:
        logger.debug(f"Direct API failed: {e}")
    return None


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in (text or ""))


def _has_thai(text: str) -> bool:
    return any("\u0e00" <= c <= "\u0e7f" for c in (text or ""))


def google_translate(text: str, retries: int = 2) -> str:
    """Translate text to Chinese. Fallback chain:
    1. deep-translator GoogleTranslator
    2. Direct translate.googleapis.com/translate_a/single
    3. MyMemoryTranslator
    """
    if not text or not text.strip():
        return text
    if _has_chinese(text):
        return text
    chunk = text[:4500] if len(text) > 4500 else text

    # Layer 1: deep-translator Google
    translator = _get_translator()
    if translator:
        for attempt in range(retries + 1):
            try:
                result = translator.translate(chunk)
                time.sleep(0.4)
                if result and _has_chinese(result):
                    return result
                if attempt < retries:
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Google Translate attempt {attempt+1} failed: {e}")
                if attempt < retries:
                    time.sleep(2)

    # Layer 2: direct googleapis endpoint
    result = _translate_direct_api(chunk)
    if result:
        time.sleep(0.5)
        return result

    # Layer 3: MyMemoryTranslator (500-char limit, rate-limited to ~5 req/s)
    fallback_chunk = chunk[:450] if len(chunk) > 450 else chunk
    for attempt in range(3):
        try:
            fallback = _get_fallback_translator(fallback_chunk)
            result = fallback.translate(fallback_chunk)
            time.sleep(1.2)
            if result and _has_chinese(result):
                return result
            break
        except Exception as e:
            if "too many requests" in str(e).lower() or "Server Error" in str(e):
                wait = 10 * (attempt + 1)
                logger.warning(f"MyMemory rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                logger.warning(f"MyMemory fallback failed: {e}")
                break

    return text


SOURCE_MAP = {
    "Bangkok Post": "曼谷邮报",
    "The Nation": "国民报",
    "Techsauce": "Techsauce科技",
    "Brand Inside": "Brand Inside",
    "Thairath": "泰叻报",
    "Google News": "谷歌新闻",
    "Money Buffalo": "Money Buffalo财经",
}


def _title_prefix(title: str) -> str:
    """Determine a Chinese category prefix based on English title keywords."""
    t = title.lower()
    if "paypaya" in t or "เพย์พาญ่า" in title or "akulaku x" in t or "prompt cash" in t or "กู้เงินถูกกฎหมาย" in title or "สินเชื่อถูกกฎหมาย" in title:
        return "【PAYPAYA】"
    if any(
        k in t
        for k in [
            "bot ", " bank of thailand", "sec thailand", "regulation", "compliance", "licensing", "กฎหมาย", "กลต",
        ]
    ):
        return "【监管】"
    if any(
        k in t
        for k in [
            "p2p", "peer-to-peer", "peer to peer", "fintech lending", "sme", "msme", "lending",
        ]
    ):
        return "【信贷】"
    if any(
        k in t
        for k in [
            "e-wallet", "e wallet", "truemoney", "promptpay", "rabbit line pay", "line pay",
            "digital wallet", "q payment", "qr payment", "กระเป๋าเงิน",
        ]
    ):
        return "【电子钱包】"
    if any(k in t for k in ["credit card", "mastercard", "visa ", "บัตรเครดิต", "scb card", "kbank card"]):
        return "【信用卡】"
    if any(
        k in t
        for k in [
            "bnpl", "buy now pay later", "paylater", "pay later", "atome", "shopback", "grab paylater",
        ]
    ):
        return "【BNPL】"
    if any(
        k in t
        for k in [
            "cash loan", "personal loan", "เงินกู้", "pinjaman", "speedy cash", "moneythunder", "สินเชื่อ", "เงิน",
        ]
    ):
        return "【现金贷】"
    if any(
        k in t
        for k in [
            "digital bank", "line bk", "kbank", "scb", "kasikorn", "neobank", "ธนาคาร", "neobank",
        ]
    ):
        return "【数字银行】"
    if any(
        k in t
        for k in [
            "lending", "loan", "สินเชื่อ", "financing", "fintech lending",
        ]
    ):
        return "【信贷】"
    if any(k in t for k in ["raises", "funding", "investment", " million", " billion"]):
        return "【融资】"
    if any(k in t for k in ["fintech", "digital", "payment", "remittance"]):
        return "【金融科技】"
    return "【金融科技】"


def translate_title(title: str) -> str:
    """Translate title to Chinese with a category prefix."""
    prefix = _title_prefix(title)
    zh = google_translate(title)
    return f"{prefix} {zh}"


def translate_summary(summary: str) -> str:
    """Translate summary to Chinese using Google Translate. Strips HTML first."""
    if not summary:
        return summary
    clean = _strip_html(summary)
    return google_translate(clean)


def translate_source(source: str) -> str:
    """Translate source name to Chinese (exact-match dictionary)."""
    return SOURCE_MAP.get(source, source)


def _title_body(title_zh: str) -> str:
    """Extract the body text after the 【xxx】 prefix."""
    if "】" in title_zh:
        return title_zh.split("】", 1)[-1].strip()
    return title_zh


def _has_non_cn_words(text: str) -> bool:
    """Check if text has significant non-Chinese/non-punctuation words,
    indicating untranslated Thai or English content."""
    import re
    latin_words = re.findall(r"[a-zA-Z]{3,}", text)
    return len(latin_words) >= 3


def translate_news_item(item: dict) -> dict:
    """Translate a news item dict in-place. Checks that the actual body
    (not just the prefix) contains Chinese, and detects mixed
    Thai/English that slipped through."""
    summary_en = item.get("summary", "")
    if "<" in summary_en:
        summary_en = _strip_html(summary_en)
        item["summary"] = summary_en

    summary_zh = item.get("summary_zh", "")
    needs_summary = (
        not summary_zh
        or summary_zh == summary_en
        or _looks_garbled(summary_zh)
        or not _has_chinese(summary_zh)
        or _has_non_cn_words(summary_zh)
    )
    if needs_summary:
        item["summary_zh"] = translate_summary(summary_en)

    title_zh = item.get("title_zh", "")
    body = _title_body(title_zh)
    if not title_zh or title_zh == item.get("title", "") or not _has_chinese(body) or _has_non_cn_words(body):
        item["title_zh"] = translate_title(item.get("title", ""))

    if not item.get("source_zh"):
        item["source_zh"] = translate_source(item.get("source", ""))

    return item


def _looks_garbled(text: str) -> bool:
    """Detect garbled or HTML-contaminated translations."""
    markers = [
        "SEC(证监会)", "BSP(央行)", "人工智能(AI)", "先买后付(BNPL)", "中小微企业(MSME)",
        "<一href", "<一个href", "&nbsp;", "target=\"_blank\"", "<font color",
    ]
    return any(m in text for m in markers)


def _strip_html(text: str) -> str:
    """Strip HTML tags from text before translation."""
    if "<" in text:
        from bs4 import BeautifulSoup
        return BeautifulSoup(text, "html.parser").get_text()
    return text
