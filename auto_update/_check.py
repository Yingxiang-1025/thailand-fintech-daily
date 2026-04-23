import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

pp = [n for n in news if "paypaya" in n.get("sections", [])]
pp.sort(key=lambda x: x.get("published", ""), reverse=True)

for i, n in enumerate(pp):
    title = (n.get("title_zh") or n.get("title", ""))[:90]
    url = n.get("url", "")
    src = n.get("source_zh") or n.get("source", "")
    pub = n.get("published", "")
    print(f"--- Item {i+1} [{pub}] ---")
    print(f"  Title: {title}")
    print(f"  URL:   {url}")
    print(f"  Src:   {src}")
    print()
