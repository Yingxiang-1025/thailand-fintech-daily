"""
Configuration for Thailand Fintech Daily Brief auto-updater.
"""
import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR
PAGES_DIR = OUTPUT_DIR / "pages"
DATA_DIR = Path(__file__).resolve().parent / "data"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# ─── OpenAI / LLM API (for Chinese summaries) ───────────
# Set via environment variable or .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
ENABLE_AI_SUMMARY = bool(OPENAI_API_KEY)

# ─── SerpAPI (for Google-like web search) ────────────────
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# ─── RSS Feeds ───────────────────────────────────────────
RSS_FEEDS = [
    {
        "name": "Bangkok Post",
        "url": "https://www.bangkokpost.com/rss/data/business",
        "category": "mainstream",
    },
    {
        "name": "The Nation",
        "url": "https://www.nationthailand.com/rss/business",
        "category": "mainstream",
    },
    {
        "name": "Techsauce",
        "url": "https://techsauce.co/feed",
        "category": "fintech",
    },
    {
        "name": "Brand Inside",
        "url": "https://brandinside.asia/feed",
        "category": "fintech",
    },
    {
        "name": "Thairath",
        "url": "https://www.thairath.co.th/rss",
        "category": "mainstream",
    },
]

# ─── Web Search Queries (run daily) ─────────────────────
SEARCH_QUERIES = [
    "Thailand fintech lending news 2026",
    "Thailand digital bank BNPL 2026",
    "PAYPAYA Thailand loan",
    "กู้เงินถูกกฎหมาย 2026",
    "TrueMoney PromptPay Thailand fintech",
    "Thailand cash loan pinjaman online 2026",
    "BOT Thailand fintech regulation 2026",
    "Thailand P2P lending news",
    "Thailand e-wallet digital payment 2026",
]

# ─── Keyword Filters ────────────────────────────────────
# News must match at least one keyword group to be included

SECTION_KEYWORDS = {
    "regulation": [
        "BOT", "Bank of Thailand", "ธปท", "SEC Thailand", "กลต", "regulation", "กฎหมาย",
        "consumer protection", "licensing",
    ],
    "credit_card": [
        "credit card", "บัตรเครดิต", "Mastercard", "Visa", "KBank card", "SCB card",
    ],
    "digital_lending": [
        "digital lending", "สินเชื่อดิจิทัล", "MSME", "SME", "fintech lending", "Ascend Money",
    ],
    "cash_loan": [
        "cash loan", "เงินกู้", "สินเชื่อ", "personal loan", "pinjaman", "Speedy Cash", "MoneyThunder",
        "สินเชื่อส่วนบุคคล",
    ],
    "bnpl": [
        "BNPL", "paylater", "pay later", "Atome", "ShopBack", "Grab PayLater", "buy now pay later",
    ],
    "e_wallet": [
        "e-wallet", "TrueMoney", "PromptPay", "Rabbit LINE Pay", "digital wallet", "กระเป๋าเงิน", "QR payment",
    ],
    "digital_bank": [
        "digital bank", "LINE BK", "KBank", "SCB", "Kasikorn", "neobank", "ธนาคารดิจิทัล",
    ],
    "paypaya": [
        "PAYPAYA", "paypaya", "กู้เงินถูกกฎหมาย", "สินเชื่อถูกกฎหมาย",
    ],
}

# Global relevance filter: an article must contain at least ONE of these
# (kept specific to fintech/finance to avoid noise like mining, politics, etc.)
GLOBAL_KEYWORDS = [
    "fintech", "lending", "สินเชื่อ", "เงินกู้", "digital bank", "e-wallet", "BNPL", "paylater", "TrueMoney",
    "PromptPay", "PAYPAYA", "BOT", "Bank of Thailand", "QR payment", "digital payment", "neobank", "กู้เงิน",
    "Atome", "LINE BK", "cash loan",
]

# ─── Section → HTML page mapping ────────────────────────
SECTION_PAGES = {
    "regulation": "regulation.html",
    "credit_card": "credit-card.html",
    "digital_lending": "digital-lending.html",
    "cash_loan": "cash-loan.html",
    "bnpl": "bnpl.html",
    "e_wallet": "e-wallet.html",
    "digital_bank": "digital-bank.html",
    "paypaya": "paypaya.html",
}

# ─── Tag styling classes ─────────────────────────────────
SECTION_TAG_CLASSES = {
    "regulation": "tag-regulation",
    "credit_card": "tag-product",
    "digital_lending": "tag-funding",
    "cash_loan": "tag-product",
    "bnpl": "tag-market",
    "e_wallet": "tag-product",
    "digital_bank": "tag-product",
    "paypaya": "tag-akulaku",
}

SECTION_DISPLAY_NAMES = {
    "regulation": "监管动态",
    "credit_card": "信用卡",
    "digital_lending": "数字信贷",
    "cash_loan": "现金贷/สินเชื่อส่วนบุคคล",
    "bnpl": "先买后付",
    "e_wallet": "电子钱包",
    "digital_bank": "数字银行",
    "paypaya": "PAYPAYA专题",
}
