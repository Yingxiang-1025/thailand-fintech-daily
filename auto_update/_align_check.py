"""Verify push content aligns with yesterday page."""
import json, sys, io
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from notifier import build_message

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

today = datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

yesterday_news = [n for n in news if n.get("published") == yesterday]
today_news = [n for n in news if n.get("published") == today]
push_items = yesterday_news + today_news

print(f"=== TH ALIGNMENT CHECK ===")
print(f"Yesterday ({yesterday}) news: {len(yesterday_news)} items")
for n in yesterday_news:
    print(f"  - {(n.get('title_zh') or n.get('title',''))[:60]}")
print(f"Today ({today}) news: {len(today_news)} items")
for n in today_news:
    print(f"  - {(n.get('title_zh') or n.get('title',''))[:60]}")
print(f"Total push items: {len(push_items)}")

msg = build_message(push_items, today)
if msg:
    print(f"\nPush message length: {len(msg)}")
    print(msg[:500])
else:
    print("\nNo push message (empty)")
