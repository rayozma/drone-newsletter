# Drone Newsletter (Sheet log, GitHub Actions)

Daily job: pulls drone news RSS, picks one unseen article, summarizes it with
a local Ollama model, appends a row (Date, Title, Summary, Link) to
`drone_news_log.csv`, and commits the update back to the repo.
Runs automatically via GitHub Actions. No server of your own needed.

## 1. Create the repo and push these files

```bash
cd drone-newsletter
git init
git add .
git commit -m "Initial commit: drone newsletter"
```

Create an empty repo on GitHub (github.com/new — do NOT initialize it with a
README, .gitignore, or license, since your local repo already has files),
then:

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## 2. Enable Actions to push back

Settings → Actions → General → Workflow permissions → set to
**"Read and write permissions"**. This lets the workflow commit the updated
`drone_news_log.csv` back to the repo using the built-in `GITHUB_TOKEN`
(no personal access token or secret needed).

## 3. (Optional) add NewsAPI as a second source

Candidates come from RSS feeds plus, if configured, a NewsAPI.org keyword
search for "drone". Get a free key at newsapi.org/register (100 req/day),
then add it as a repo secret: Settings → Secrets and variables → Actions →
Secrets → New repository secret → name `NEWSAPI_KEY`, paste the key. Without
it, the script silently falls back to RSS-only — nothing breaks.

## 4. (Optional) choose the model

Default is `llama3.2:3b` — small enough to download and run within a GitHub
Actions job in a few minutes. To use a different model, set a repo variable:
Settings → Secrets and variables → Actions → Variables → New repository
variable → `OLLAMA_MODEL` → e.g. `llama3.1`. Bigger models mean longer runs
and more download time every day (models aren't guaranteed to stay cached
between runs).

## 5. Trigger it

- Runs automatically at 01:00 UTC (08:00 WIB) daily.
- To test immediately: Actions tab → "Daily Drone News" → **Run workflow**.

## Files
- `newsletter.py` — the pipeline (fetch → select → summarize → append)
- `.github/workflows/daily-drone-news.yml` — schedule + Ollama setup + commit-back
- `requirements.txt` — Python deps
- `drone_news_log.csv` — output, created on first run
- `sent_history.json` — dedupe log, created on first run

## Notes
- Selection is currently "first unseen item across feeds" — easy to swap for
  an LLM ranking step if you want topic-relevance filtering instead.
- If a run finds no new articles, it skips the commit (no empty commits).
- GitHub-hosted runners are ephemeral; nothing persists except what's
  committed back to the repo (the csv and history file).
