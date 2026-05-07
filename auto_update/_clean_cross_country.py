"""Clean cross-country contamination from Thailand news data."""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

INDONESIA_MARKERS = [
    "adakami", "investree", "koinworks", "modalku", "kredivo",
    "amartha", "danamas", "kredit pintar", "pinjol",
    "ojk", "indonesia gdp", "印度尼西亚", "印尼gdp",
    "indonesian", "pinjaman online",
]
PHILIPPINES_MARKERS = [
    "bsp ", "bangko sentral", "gcash", "maya philippines",
    "unionbank philippines", "sec philippines", "菲律宾",
]

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

before = len(news)
cleaned = []
removed = []

for n in news:
    text = " ".join([
        n.get("title", "") or "",
        n.get("title_zh", "") or "",
        n.get("summary", "") or "",
        n.get("summary_zh", "") or "",
    ]).lower()

    is_other_country = False
    for marker in INDONESIA_MARKERS + PHILIPPINES_MARKERS:
        if marker in text:
            has_thailand = any(t in text for t in ["thailand", "thai", "泰国", "กรุงเทพ", "paypaya", "เพย์พาญ่า", "bot "])
            if not has_thailand:
                is_other_country = True
                break

    if is_other_country:
        removed.append(n.get("title_zh", "") or n.get("title", ""))
    else:
        cleaned.append(n)

with open("data/news.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"Before: {before}, After: {len(cleaned)}, Removed: {len(removed)}")
for r in removed:
    print(f"  X {r[:70]}")
