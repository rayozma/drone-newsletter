# Daily Drone News

Every morning, this repo picks one new drone-industry article, summarizes it
with a free local AI model, and publishes it to a web page:

**https://rayozma.github.io/drone-newsletter/**

Everything runs on GitHub's servers via GitHub Actions — no computer of your
own needs to be on, and there are no API costs.

## How it works

1. **Collect** — reads RSS feeds from DroneDJ, DroneLife, DroneXL and sUAS News,
   plus a NewsAPI.org search for "drone" (if a key is set).
2. **Pick** — takes the first article that hasn't been used before
   (`sent_history.json` keeps track).
3. **Summarize** — a small Ollama model (`llama3.2:3b` by default) writes a
   2–3 sentence summary.
4. **Save** — adds a row to `drone_news_log.csv` and rebuilds `index.html`.
5. **Publish** — commits both files; GitHub Pages serves `index.html` as the site.

Runs daily at **01:13 UTC (≈ 08:13 WIB)**. GitHub sometimes starts scheduled
runs 10–30 minutes late, which is normal.

## Files

| File | What it is |
|---|---|
| `newsletter.py` | The whole pipeline, including the web page template (`render_html`) |
| `.github/workflows/daily-drone-news.yml` | The schedule and the steps GitHub runs |
| `requirements.txt` | Python libraries the script needs |
| `images/banner.webp` | The banner image at the top of the page |
| `drone_news_log.csv` | The log of all articles (generated) |
| `index.html` | The web page (generated) |
| `sent_history.json` | Links already used, so nothing repeats (generated) |

## Editing the web page

⚠️ **Don't edit `index.html` directly.** It is rebuilt on every run, so your
changes would be overwritten. Edit the `render_html` function in
`newsletter.py` instead — that's the template the page is generated from.

The HTML sits inside a Python f-string, so:

- CSS braces must be **doubled**: `.banner{{height:280px}}`, not `.banner{height:280px}`.
  A single brace will make the script crash.
- Single braces like `{updated}` are Python variables being inserted — leave them as they are.

Useful places to tweak:

- **Banner height** — `height:` in the `.banner img` line (desktop), and in the
  `@media` line (phones).
- **Which part of the banner shows** — `object-position:center 30%`
  (`0%` = top of the image, `100%` = bottom).
- **Colors** — the `:root` line (light mode) and the `prefers-color-scheme:dark` line (dark mode).

After editing, commit and push, then run the workflow so the page is rebuilt.

## Making changes (GitHub Desktop)

1. Edit or replace files in your local `drone-newsletter` folder.
2. In GitHub Desktop: write a commit message → **Commit to main** → **Push origin**.
3. On GitHub: **Actions → Daily Drone News → Run workflow** to test right away.
4. Once that's green, wait for the **pages-build-deployment** run to finish,
   then reload the site with **Ctrl+F5**.

Note: GitHub Desktop may also show the bot's daily commits as incoming changes —
click **Fetch/Pull origin** before you start editing so you're up to date.

## Settings (one-time)

- **Let the workflow save its results:** Settings → Actions → General →
  Workflow permissions → **Read and write permissions**.
- **Turn on the website:** Settings → Pages → Source: *Deploy from a branch* →
  `main` / `/ (root)`.
- **(Optional) NewsAPI:** get a free key at newsapi.org, then Settings → Secrets
  and variables → Actions → **Secrets** → `NEWSAPI_KEY`. Without it, the script
  just uses the RSS feeds. Always use *Secrets* (hidden), never *Variables*
  (public), for keys.
- **(Optional) different model:** Settings → Secrets and variables → Actions →
  **Variables** → `OLLAMA_MODEL` (e.g. `llama3.1`). Bigger models write better
  summaries but make each run slower.

## Troubleshooting

- **Test with "Run workflow", not "Re-run jobs".** Re-running an old run replays
  the old code from that time, not your latest version.
- **Run failed:** open the run → click the **run** job → expand the step with the
  red ❌ to see the actual error message.
- **Error in the Python step after editing the template:** almost always a
  single `{` or `}` in the CSS — double it.
- **Several rows with the same date:** each run adds one article, so manual test
  runs on the same day add extra rows. Not a bug.
- **Site still shows old content:** check that pages-build-deployment finished,
  then press Ctrl+F5 to skip the browser cache.
