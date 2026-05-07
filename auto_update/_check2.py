import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

today = [n for n in news if n.get("fetched_date") == "2026-05-07"]
print(f"Today items: {len(today)}")
for n in today:
    print(f"  Title: {n.get('title', '')[:80]}")
    print(f"  Title_zh: {n.get('title_zh', '')[:80]}")
    print(f"  URL: {n.get('url', '')[:80]}")
    print()
