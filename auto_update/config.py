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
    # Thai fintech/tech media (active feeds)
    {"name": "Techsauce", "url": "https://techsauce.co/feed", "category": "fintech"},
    {"name": "Brand Inside", "url": "https://brandinside.asia/feed", "category": "fintech"},
    # Thai mainstream (Google News RSS since direct RSS is down)
    {"name": "GN Bangkok Post Finance", "url": "https://news.google.com/rss/search?q=site:bangkokpost.com+fintech+OR+lending+OR+digital+bank&hl=en&gl=TH&ceid=TH:en", "category": "mainstream"},
    {"name": "GN Nation Thailand", "url": "https://news.google.com/rss/search?q=site:nationthailand.com+fintech+OR+digital+payment&hl=en&gl=TH&ceid=TH:en", "category": "mainstream"},
    # Thai-language financial media (Google News RSS)
    {"name": "GN Prachachat Finance", "url": "https://news.google.com/rss/search?q=site:prachachat.net+%E0%B8%AA%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%8A%E0%B8%B7%E0%B9%88%E0%B8%AD&hl=th&gl=TH&ceid=TH:th", "category": "mainstream"},
    {"name": "GN Manager Finance", "url": "https://news.google.com/rss/search?q=site:mgronline.com+%E0%B8%9F%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%97%E0%B8%84&hl=th&gl=TH&ceid=TH:th", "category": "mainstream"},
    # Brand-specific Google News RSS
    {"name": "GN PAYPAYA", "url": "https://news.google.com/rss/search?q=PAYPAYA+Thailand&hl=en&gl=TH&ceid=TH:en", "category": "paypaya"},
    {"name": "GN PAYPAYA TH", "url": "https://news.google.com/rss/search?q=%E0%B9%80%E0%B8%9E%E0%B8%A2%E0%B9%8C%E0%B8%9E%E0%B8%B2%E0%B8%8D%E0%B9%88%E0%B8%B2+%E0%B8%AA%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%8A%E0%B8%B7%E0%B9%88%E0%B8%AD&hl=th&gl=TH&ceid=TH:th", "category": "paypaya"},
    {"name": "GN TrueMoney", "url": "https://news.google.com/rss/search?q=TrueMoney+Thailand&hl=en&gl=TH&ceid=TH:en", "category": "e_wallet"},
    {"name": "GN LINE BK", "url": "https://news.google.com/rss/search?q=%22LINE+BK%22+Thailand&hl=en&gl=TH&ceid=TH:en", "category": "digital_bank"},
    {"name": "GN Atome TH", "url": "https://news.google.com/rss/search?q=Atome+BNPL+Thailand&hl=en&gl=TH&ceid=TH:en", "category": "bnpl"},
    {"name": "GN Thai Fintech", "url": "https://news.google.com/rss/search?q=Thailand+fintech+lending+2026&hl=en&gl=TH&ceid=TH:en", "category": "fintech"},
    {"name": "GN Thai Fintech TH", "url": "https://news.google.com/rss/search?q=%E0%B8%9F%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%97%E0%B8%84+%E0%B8%AA%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%8A%E0%B8%B7%E0%B9%88%E0%B8%AD+2026&hl=th&gl=TH&ceid=TH:th", "category": "fintech"},
    # Cash loan / personal loan RSS (Thai)
    {"name": "GN Cash Loan TH", "url": "https://news.google.com/rss/search?q=%E0%B8%AA%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%8A%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B9%80%E0%B8%87%E0%B8%B4%E0%B8%99%E0%B8%AA%E0%B8%94+%E0%B9%84%E0%B8%97%E0%B8%A2+2026&hl=th&gl=TH&ceid=TH:th", "category": "cash_loan"},
    {"name": "GN Personal Loan TH", "url": "https://news.google.com/rss/search?q=%E0%B8%AA%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%8A%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%AA%E0%B9%88%E0%B8%A7%E0%B8%99%E0%B8%9A%E0%B8%B8%E0%B8%84%E0%B8%84%E0%B8%A5+%E0%B9%84%E0%B8%97%E0%B8%A2+2026&hl=th&gl=TH&ceid=TH:th", "category": "cash_loan"},
    {"name": "GN Legal Loan App", "url": "https://news.google.com/rss/search?q=%E0%B9%81%E0%B8%AD%E0%B8%9B%E0%B8%81%E0%B8%B9%E0%B9%89%E0%B9%80%E0%B8%87%E0%B8%B4%E0%B8%99%E0%B8%96%E0%B8%B9%E0%B8%81%E0%B8%81%E0%B8%8E%E0%B8%AB%E0%B8%A1%E0%B8%B2%E0%B8%A2+2026&hl=th&gl=TH&ceid=TH:th", "category": "cash_loan"},
    # BNPL / paylater RSS
    {"name": "GN BNPL TH", "url": "https://news.google.com/rss/search?q=BNPL+paylater+Thailand+2026&hl=en&gl=TH&ceid=TH:en", "category": "bnpl"},
    {"name": "GN Installment TH", "url": "https://news.google.com/rss/search?q=%E0%B8%9C%E0%B9%88%E0%B8%AD%E0%B8%99%E0%B8%8A%E0%B8%B3%E0%B8%A3%E0%B8%B0+%E0%B9%84%E0%B8%97%E0%B8%A2+%E0%B8%9F%E0%B8%B4%E0%B8%99%E0%B9%80%E0%B8%97%E0%B8%84+2026&hl=th&gl=TH&ceid=TH:th", "category": "bnpl"},
    {"name": "GN ShopBack TH", "url": "https://news.google.com/rss/search?q=ShopBack+Thailand+paylater&hl=en&gl=TH&ceid=TH:en", "category": "bnpl"},
    # E-wallet / PromptPay
    {"name": "GN PromptPay", "url": "https://news.google.com/rss/search?q=PromptPay+Thailand+2026&hl=en&gl=TH&ceid=TH:en", "category": "e_wallet"},
    {"name": "GN E-wallet TH", "url": "https://news.google.com/rss/search?q=%E0%B8%81%E0%B8%A3%E0%B8%B0%E0%B9%80%E0%B8%9B%E0%B9%8B%E0%B8%B2%E0%B9%80%E0%B8%87%E0%B8%B4%E0%B8%99%E0%B8%94%E0%B8%B4%E0%B8%88%E0%B8%B4%E0%B8%97%E0%B8%B1%E0%B8%A5+%E0%B9%84%E0%B8%97%E0%B8%A2+2026&hl=th&gl=TH&ceid=TH:th", "category": "e_wallet"},
    # Peer brands
    {"name": "GN Grab Financial TH", "url": "https://news.google.com/rss/search?q=Grab+Financial+Thailand+2026&hl=en&gl=TH&ceid=TH:en", "category": "bnpl"},
    {"name": "GN Ascend Money", "url": "https://news.google.com/rss/search?q=%22Ascend+Money%22+Thailand&hl=en&gl=TH&ceid=TH:en", "category": "e_wallet"},
    # Regional English fintech media (geo-filtered)
    {"name": "Fintech News SG", "url": "https://fintechnews.sg/feed/", "category": "fintech"},
    {"name": "e27", "url": "https://e27.co/feed/", "category": "fintech"},
]

# ─── Web Search Queries (run daily) ─────────────────────
SEARCH_QUERIES = [
    # ── PAYPAYA Group (highest priority, 10 queries) ──
    "PAYPAYA Thailand loan fintech",
    "PAYPAYA เพย์พาญ่า app 2026",
    "เพย์พาญ่า สินเชื่อ ล่าสุด",
    "PAYPAYA สินเชื่อถูกกฎหมาย",
    "Akulaku X SCBX PAYPAYA Thailand",
    "PAYPAYA Prompt Cash Thailand",
    "เพย์พาญ่า กู้เงินถูกกฎหมาย",
    "PAYPAYA app review Thailand 2026",
    "SCBX fintech Thailand PAYPAYA",
    "Akulaku X Thailand lending 2026",
    # ── Peer brands - English ──
    "TrueMoney Thailand news 2026",
    "LINE BK Thailand digital bank 2026",
    "Atome Thailand BNPL paylater",
    "ShopBack Thailand BNPL 2026",
    "Grab PayLater Thailand news",
    "Ascend Money Thailand fintech",
    "KBank digital lending Thailand",
    "SCB digital banking Thailand 2026",
    "Rabbit LINE Pay Thailand",
    # ── Peer brands - Thai ──
    "ทรูมันนี่ โปรโมชั่น ล่าสุด 2026",
    "LINE BK สินเชื่อ ล่าสุด",
    "แอปกู้เงินถูกกฎหมาย 2026",
    "สินเชื่อออนไลน์ถูกกฎหมาย แอป 2026",
    "BNPL ไทย ผ่อนชำระ 2026",
    "กระเป๋าเงินดิจิทัล ไทย 2026",
    # ── Cash loan / personal loan - expanded ──
    "สินเชื่อเงินสด อนุมัติเร็ว ไทย 2026",
    "สินเชื่อส่วนบุคคล ดอกเบี้ยต่ำ ไทย 2026",
    "กู้เงินด่วน ออนไลน์ ถูกกฎหมาย ไทย",
    "Speedy Cash สินเชื่อ ไทย",
    "MoneyThunder สินเชื่อ Thailand",
    "cash loan Thailand app 2026",
    "personal loan fintech Thailand 2026",
    # ── BNPL / paylater - expanded ──
    "BNPL Thailand market 2026",
    "paylater Thailand growth 2026",
    "ผ่อนชำระ ไม่ใช้บัตรเครดิต ไทย 2026",
    "Atome Thailand paylater 2026",
    "ShopBack paylater Thailand 2026",
    "Grab PayLater Thailand news 2026",
    "ผ่อน 0% ออนไลน์ ไทย 2026",
    # ── Regulation (fintech-focused) ──
    "BOT Thailand fintech regulation 2026",
    "ธปท กฎเกณฑ์ สินเชื่อดิจิทัล 2026",
    "BOT lending license Thailand 2026",
    "กฎหมายสินเชื่อออนไลน์ ไทย ล่าสุด",
    # ── General fintech - English ──
    "Thailand fintech lending news 2026",
    "Thailand digital bank BNPL 2026",
    "Thailand cash loan สินเชื่อเงินสด 2026",
    "Thailand P2P lending news 2026",
    "Thailand e-wallet digital payment 2026",
    "Thailand neobank challenger bank 2026",
    # ── General fintech - Thai ──
    "ฟินเทค ไทย ข่าวล่าสุด 2026",
    "สินเชื่อเงินสด ออนไลน์ ไทย 2026",
    "ธนาคารดิจิทัล ไทย ล่าสุด",
    "QR payment PromptPay ล่าสุด",
]

# ─── Keyword Filters ────────────────────────────────────

SECTION_KEYWORDS = {
    "regulation": [
        "กฎหมายสินเชื่อ", "กฎหมายฟินเทค", "กฎหมายดิจิทัล",
        "กฎเกณฑ์", "ใบอนุญาต", "regulation", "regulatory",
        "licensing", "compliance", "กำกับดูแล",
        "consumer protection", "PDPA", "พรบ คุ้มครองข้อมูล",
        "sandbox", "แซนด์บ็อกซ์",
    ],
    "credit_card": [
        "credit card", "บัตรเครดิต", "Mastercard", "Visa", "KBank card", "SCB card",
    ],
    "digital_lending": [
        "สินเชื่อดิจิทัล", "MSME", "SME lending", "SME loan",
        "P2P lending", "peer-to-peer lending", "crowdlending",
        "สินเชื่อ SME", "สินเชื่อ MSME", "revenue-based financing",
    ],
    "cash_loan": [
        "cash loan", "เงินกู้", "สินเชื่อ", "personal loan", "Speedy Cash", "MoneyThunder",
        "สินเชื่อส่วนบุคคล", "สินเชื่อเงินสด", "กู้เงิน",
        "สินเชื่อออนไลน์", "กู้เงินด่วน", "เงินด่วน", "อนุมัติเร็ว",
        "สินเชื่อถูกกฎหมาย", "แอปกู้เงิน", "แอปสินเชื่อ",
        "ดอกเบี้ย", "interest rate",
    ],
    "bnpl": [
        "BNPL", "paylater", "pay later", "Atome", "ShopBack", "Grab PayLater",
        "buy now pay later", "ผ่อนชำระ", "ผ่อน 0%",
        "ผ่อนสินค้า", "ผ่อนจ่าย", "installment", "ผ่อนได้",
        "ซื้อก่อนจ่ายทีหลัง",
    ],
    "e_wallet": [
        "e-wallet", "TrueMoney", "PromptPay", "Rabbit LINE Pay", "digital wallet",
        "กระเป๋าเงิน", "QR payment", "mobile payment", "digital payment",
        "Ascend Money", "Wise", "cross-border payment",
    ],
    "virtual_bank": [
        "virtual bank", "วิร์ชวลแบงก์", "virtual banking",
        "BankX", "BankX Bank", "virtual bank license",
        "ใบอนุญาตธนาคารเสมือน",
    ],
    "digital_bank": [
        "digital bank", "LINE BK", "KBank", "Kasikorn", "neobank", "ธนาคารดิจิทัล",
    ],
    "paypaya": [
        "PAYPAYA", "paypaya", "เพย์พาญ่า", "Akulaku X", "akulaku x",
        "Prompt Cash", "กู้เงินถูกกฎหมาย", "สินเชื่อถูกกฎหมาย",
        "แอปเงินกู้ถูกกฎหมาย", "สินเชื่อออนไลน์ถูกกฎหมาย",
    ],
}

# Regulation compound matching: regulator + financial keyword
REGULATION_REGULATORS = [
    "ธปท", "Bank of Thailand", "BOT",
    "ก.ล.ต.", "กลต", "SEC Thailand", "SEC",
    "คปภ", "OIC",
]
REGULATION_FINANCE_KEYWORDS = [
    "สินเชื่อ", "เงินกู้", "ฟินเทค", "fintech", "lending", "payment",
    "ดิจิทัล", "digital", "license", "ใบอนุญาต", "กฎเกณฑ์",
    "regulation", "regulatory", "policy", "นโยบาย", "กำกับดูแล",
    "ธนาคาร", "bank", "insurance", "ประกัน", "กองทุน", "fund",
    "e-wallet", "BNPL", "virtual bank", "crypto", "คริปโท",
    "ชำระเงิน", "บัญชี", "สถาบันการเงิน", "financial institution",
]

# Non-fintech BOT/regulatory news to exclude
REGULATION_EXCLUDE_KEYWORDS = [
    "กรรมการผู้ทรงคุณวุฒิ", "qualified directors", "board appointment",
    "ทองคำ", "gold trading", "gold price",
    "ค่าธรรมเนียม", "bank fee",
    "เฟด", "Federal Reserve", "Fed rate", "Fed policy",
    "พ.ร.ก. เงินกู้", "เงินกู้ 4 แสนล้าน", "borrowing decree",
    "GDP", "inflation rate", "อัตราเงินเฟ้อ",
    "quick commerce", "e-commerce market",
]

GLOBAL_KEYWORDS = [
    # English core
    "fintech", "lending", "digital bank", "e-wallet", "BNPL", "paylater",
    "QR payment", "digital payment", "neobank", "cash loan",
    # Thai core
    "สินเชื่อ", "เงินกู้", "กู้เงิน", "ฟินเทค", "ธนาคารดิจิทัล",
    "กระเป๋าเงิน", "ผ่อนชำระ", "สินเชื่อดิจิทัล",
    "สินเชื่อถูกกฎหมาย", "แอปเงินกู้", "สินเชื่อเงินสด",
    # Brands
    "PAYPAYA", "เพย์พาญ่า", "Akulaku X", "TrueMoney", "PromptPay",
    "Atome", "LINE BK", "ShopBack", "Grab PayLater",
    "Ascend Money", "Rabbit LINE Pay",
    # Regulation (narrow)
    "ธปท", "Bank of Thailand",
]

WORD_BOUNDARY_KEYWORDS = ["BOT", "SCB"]

# Thailand geographic keywords — used to filter regional sources
THAILAND_GEO_KEYWORDS = [
    "thailand", "thai", "bangkok", "baht", "ธปท",
    "ไทย", "กรุงเทพ", "泰国", "曼谷",
    "truemoney", "promptpay", "paypaya", "เพย์พาญ่า",
    "line bk", "kbank", "kasikorn", "scb", "krungsri",
    "ascend money", "rabbit line pay", "atome thailand",
    "กู้เงิน", "สินเชื่อ", "ฟินเทค",
]

REGIONAL_SOURCES = [
    "Fintech News SG", "e27", "Tech in Asia",
    "fintechnews.sg", "e27.co", "techinasia.com",
]

EXCLUDE_KEYWORDS = [
    # Indonesia brands/regulators
    "AdaKami", "Asetku", "Kredivo", "OJK", "Investree",
    "KoinWorks", "Modalku", "Danamas", "Amartha", "Kredit Pintar",
    "pinjaman online", "pinjol", "Indonesia GDP", "印度尼西亚",
    "印尼GDP", "Indonesia fintech", "Indonesian fintech",
    "Indonesia BNPL", "Indonesia lending",
    "GoPay Indonesia", "OVO Indonesia", "DANA Indonesia",
    "Tokopedia", "GoPayLater",
    # Philippines
    "BSP Philippines", "Bangko Sentral", "Philippines fintech",
    "GCash", "Maya Philippines", "UnionBank Philippines",
    # Non-fintech macro/noise
    "papaya fruit", "papaya tree", "pad thai", "Gordon Ramsay",
    "gangster", "murder", "Koh Samui crime",
    "quick commerce", "Quick Commerce",
]

# Maximum number of regulation items in daily/monthly summaries
REGULATION_DAILY_CAP = 5

# ─── Section → HTML page mapping ────────────────────────
SECTION_PAGES = {
    "regulation": "regulation.html",
    "credit_card": "credit-card.html",
    "digital_lending": "digital-lending.html",
    "cash_loan": "cash-loan.html",
    "bnpl": "bnpl.html",
    "e_wallet": "e-wallet.html",
    "virtual_bank": "virtual-bank.html",
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
    "virtual_bank": "tag-market",
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
    "virtual_bank": "虚拟银行",
    "digital_bank": "数字银行",
    "paypaya": "PAYPAYA专题",
}
