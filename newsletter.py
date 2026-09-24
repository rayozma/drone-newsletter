import feedparser, json, os, requests, datetime, csv, re, html

FEEDS = ["https://dronedj.com/feed", "https://dronelife.com/feed", "https://dronexl.co/feed", "https://www.suasnews.com/feed"]
NEWSAPI_QUERY = "drone"
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(DIR, "sent_history.json")
SHEET_FILE = os.path.join(DIR, "drone_news_log.csv")
HTML_FILE = os.path.join(DIR, "index.html")
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
HEADER = ["Date", "Title", "Summary", "Link"]
PREAMBLE = re.compile(r"^\s*(here(?: is|'s)[^:\n]*summary[^:\n]*:|summary\s*:)\s*", re.I)

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    return set(json.load(open(HISTORY_FILE)))

def save_history(h):
    json.dump(sorted(h), open(HISTORY_FILE, "w"), indent=0)

def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def fetch_rss(history):
    items = []
    for url in FEEDS:
        for e in feedparser.parse(url).entries:
            if e.link not in history:
                items.append({"title": e.title, "link": e.link, "summary": strip_tags(e.get("summary", e.title))})
    return items

def fetch_newsapi(history):
    if not NEWSAPI_KEY: return []
    r = requests.get("https://newsapi.org/v2/everything", params={"q": NEWSAPI_QUERY, "sortBy": "publishedAt", "language": "en", "pageSize": 20}, headers={"X-Api-Key": NEWSAPI_KEY})
    r.raise_for_status()
    return [{"title": a["title"], "link": a["url"], "summary": strip_tags(a.get("description") or a.get("content") or a["title"])} for a in r.json().get("articles", []) if a["url"] not in history]

def clean_summary(s):
    return PREAMBLE.sub("", s.strip()).strip().strip('"').strip()

def summarize(item):
    prompt = ("Summarize this drone industry news article in 2-3 sentences for a busy reader. "
              "Output ONLY the summary text. No preamble, no heading, no phrases like 'Here is a summary'.\n\n"
              f"Title: {item['title']}\n\nContent: {item['summary']}")
    r = requests.post(OLLAMA_API, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    r.raise_for_status()
    return clean_summary(r.json()["response"])

def load_rows():
    if not os.path.exists(SHEET_FILE): return []
    with open(SHEET_FILE, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f)]

def save_rows(rows):
    with open(SHEET_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)

def render_html(rows):
    e = html.escape
    body = "\n".join(f'<tr><td class="d">{e(r["Date"])}</td><td><a href="{e(r["Link"])}" target="_blank" rel="noopener">{e(r["Title"])}</a></td><td>{e(r["Summary"])}</td></tr>' for r in reversed(rows))
    updated = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Drone News</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e5e5e5;--head:#f6f6f6;--link:#0b5fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121212;--fg:#e8e8e8;--muted:#999;--line:#2a2a2a;--head:#1c1c1c;--link:#6ea0ff}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:32px 20px}}
h1{{margin:0 0 4px;font-size:26px}} p.sub{{margin:0 0 24px;color:var(--muted)}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px}}
table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;vertical-align:top;padding:12px 14px;border-bottom:1px solid var(--line)}}
th{{background:var(--head);font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
tr:last-child td{{border-bottom:0}} td.d{{white-space:nowrap;color:var(--muted)}}
td a{{color:var(--link);font-weight:600;text-decoration:none}} td a:hover{{text-decoration:underline}}
th:nth-child(2){{width:30%}}
.banner{{position:relative;overflow:hidden}}
.banner img{{display:block;width:100%;height:280px;object-fit:cover;object-position:center 30%}}
.banner::before{{content:"";position:absolute;inset:0;background:linear-gradient(rgba(0,0,0,.45),transparent 55%)}}
.banner-text{{position:absolute;top:0;left:0;right:0;z-index:1;max-width:1100px;margin:0 auto;padding:28px 20px;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.6)}}
.banner-text h1{{margin:0;font-size:40px}}
.banner-text p{{margin:4px 0 0}}
@media (max-width:600px){{.banner img{{height:160px}} .banner-text h1{{font-size:28px}}}}
</style></head><body>
<header class="banner">
<img src="images/banner.webp" alt="Illustrated city skyline with drones flying over a river">
<div class="banner-text"><h1>Daily Drone News</h1><p>One summarized drone article per day &middot; updated {updated}</p></div>
</header>
<main>
<div class="wrap"><table><thead><tr><th>Date</th><th>Article</th><th>Summary</th></tr></thead><tbody>
{body}
</tbody></table></div></main></body></html>"""
    open(HTML_FILE, "w", encoding="utf-8").write(page)

def main():
    rows = load_rows()
    for r in rows: r["Summary"] = clean_summary(r["Summary"])
    history = load_history()
    candidates = fetch_rss(history) + fetch_newsapi(history)
    if candidates:
        pick = candidates[0]
        rows.append({"Date": datetime.date.today().isoformat(), "Title": pick["title"], "Summary": summarize(pick), "Link": pick["link"]})
        history.add(pick["link"])
        save_history(history)
        print("Logged:", pick["title"])
    else:
        print("No new articles today")
    save_rows(rows)
    render_html(rows)

if __name__ == "__main__":
    main()
