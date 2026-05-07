import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from notifier import build_message, WEBSITE_URL, WECHAT_WEBHOOK_URL

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

today = [n for n in news if n.get("fetched_date") == "2026-05-07"]
print(f"Today items in DB: {len(today)}")
print(f"Website URL: {WEBSITE_URL}")
print(f"Webhook: {WECHAT_WEBHOOK_URL[:60]}...")

# Check the message that was built from todays_new_items (simulated)
from fetcher import fetch_rss_feeds, search_web, deduplicate, load_existing_news
# Just show what was pushed
print(f"\n--- Last push content verification ---")
# Check all titles for Indonesia contamination
for n in news:
    tz = n.get("title_zh", "") or n.get("title", "")
    if any(w in tz.lower() for w in ["indonesia", "印尼", "印度尼西亚", "adakami"]):
        print(f"  WARNING: Indonesia content found: {tz[:60]}")

print("Country validation: PASS" if not any(
    any(w in (n.get("title_zh","") or "").lower() for w in ["indonesia", "印尼", "adakami"])
    for n in news
) else "Country validation: ISSUES FOUND")
