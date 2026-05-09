"""Diagnose today's push status."""
import json, sys, io
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from notifier import build_message

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

today = datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

print(f"=== INDONESIA DIAGNOSIS {today} ===")
print(f"Total items in DB: {len(news)}")

from collections import Counter
pub_dates = Counter(n.get("published", "?") for n in news)
fetch_dates = Counter(n.get("fetched_date", "?") for n in news)
print(f"\nRecent published dates:")
for d, c in sorted(pub_dates.items(), reverse=True)[:7]:
    print(f"  {d}: {c}")
print(f"\nRecent fetched dates:")
for d, c in sorted(fetch_dates.items(), reverse=True)[:7]:
    print(f"  {d}: {c}")

yn = [n for n in news if n.get("published") == yesterday]
tn = [n for n in news if n.get("published") == today]
push_items = yn + tn
print(f"\nYesterday ({yesterday}) published: {len(yn)}")
print(f"Today ({today}) published: {len(tn)}")
print(f"Push items (yesterday+today): {len(push_items)}")

if push_items:
    msg = build_message(push_items, today)
    if msg:
        print(f"\nPush message ({len(msg)} chars):")
        print(msg[:400])
    else:
        print("\nbuild_message returned None")
else:
    print("\nNO PUSH: zero items match yesterday/today published date")
    print("This is why no push was sent!")
    last_3 = [n for n in news if n.get("published","") >= (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")]
    print(f"\nLast 3 days published: {len(last_3)} items")
    for n in last_3[:5]:
        tz = n.get("title_zh") or n.get("title", "")
        print(f"  [{n.get('published')}] {tz[:55]}")
