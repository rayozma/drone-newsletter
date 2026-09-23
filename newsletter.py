import feedparser, json, os, requests, datetime, csv

FEEDS = ["https://dronedj.com/feed", "https://dronelife.com/feed", "https://dronexl.co/feed", "https://www.suasnews.com/feed"]
NEWSAPI_QUERY = "drone"
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
DIR = os.path.dirname(__file__)
HISTORY_FILE = os.path.join(DIR, "sent_history.json")
SHEET_FILE = os.path.join(DIR, "drone_news_log.csv")
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    return set(json.load(open(HISTORY_FILE)))

def save_history(h):
    json.dump(list(h), open(HISTORY_FILE, "w"))

def fetch_rss(history):
    items = []
    for url in FEEDS:
        for e in feedparser.parse(url).entries:
            if e.link not in history:
                items.append({"title": e.title, "link": e.link, "summary": e.get("summary", e.title)})
    return items

def fetch_newsapi(history):
    if not NEWSAPI_KEY:
        return []
    r = requests.get("https://newsapi.org/v2/everything",
        params={"q": NEWSAPI_QUERY, "sortBy": "publishedAt", "language": "en", "pageSize": 20},
        headers={"X-Api-Key": NEWSAPI_KEY})
    r.raise_for_status()
    items = []
    for a in r.json().get("articles", []):
        if a["url"] not in history:
            items.append({"title": a["title"], "link": a["url"], "summary": a.get("description") or a.get("content") or a["title"]})
    return items

def fetch_candidates(history):
    return fetch_rss(history) + fetch_newsapi(history)

def summarize(item):
    prompt = f"Summarize this drone industry news article in 2-3 sentences for a busy reader. Title: {item['title']}\n\nContent: {item['summary']}"
    r = requests.post(OLLAMA_API, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    r.raise_for_status()
    return r.json()["response"].strip()

def append_row(date, title, summary, link):
    is_new = not os.path.exists(SHEET_FILE)
    with open(SHEET_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["Date", "Title", "Summary", "Link"])
        w.writerow([date, title, summary, link])

def main():
    history = load_history()
    candidates = fetch_candidates(history)
    if not candidates:
        print("No new articles today")
        return
    pick = candidates[0]
    summary = summarize(pick)
    append_row(datetime.date.today().isoformat(), pick["title"], summary, pick["link"])
    history.add(pick["link"])
    save_history(history)
    print("Logged:", pick["title"])

if __name__ == "__main__":
    main()
