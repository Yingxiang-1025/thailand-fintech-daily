"""Remove duplicate articles with similar titles but different URLs."""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def normalize(title):
    t = re.sub(r"^【[^】]+】\s*", "", title)
    t = re.sub(r"\s*-\s*[^-]+$", "", t)
    t = t.strip().lower()
    return t

def get_key(title):
    """Extract first 25 chars of normalized title as similarity key."""
    norm = normalize(title)
    return norm[:25] if len(norm) >= 25 else norm

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

before = len(news)
seen_keys = {}
cleaned = []
removed = []

for n in news:
    title = n.get("title_zh") or n.get("title", "")
    key = get_key(title)
    if key and len(key) > 10 and key in seen_keys:
        removed.append(f"{title[:70]} (dup of: {seen_keys[key][:40]})")
    else:
        if key and len(key) > 10:
            seen_keys[key] = title
        cleaned.append(n)

with open("data/news.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"Before: {before}, After: {len(cleaned)}, Removed: {len(removed)}")
for r in removed:
    print(f"  X {r}")
