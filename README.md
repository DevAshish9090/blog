# Notebook blog

A tiny FastAPI site that renders `.ipynb` files as faithful Jupyter-style pages
(In/Out prompts, notebook CSS, embedded plots). Drop a notebook into
`notebooks/` and it becomes a post automatically.

## How posts work

- Every `*.ipynb` in `notebooks/` becomes a post at `/p/<slug>`.
- The homepage `/` lists them, newest first.
- Notebooks are rendered once at startup and cached in memory.

Post titles, dates, and summaries live in **`posts.json`** — one entry per
notebook, so you never have to edit anything inside the notebook itself:

```json
[
  {
    "file": "llm_working.ipynb",
    "title": "How LLMs Actually Work",
    "date": "2026-02-14",
    "description": "One-line summary shown on the homepage.",
    "slug": "how-llms-work",
    "eyebrow": "Notebook",
    "draft": false
  }
]
```

- `file` must match the notebook's filename exactly. Everything else is optional.
- A notebook that isn't listed still shows up — its title falls back to the
  first heading (then the filename), date to the file's modified time, slug to
  the filename.
- Set `"draft": true` to keep a notebook off the site.
- If `posts.json` has a typo, the site stays up and just uses those fallbacks;
  a note is printed in the deploy logs so you can spot it.

Edit `SITE_TITLE`, `SITE_TAGLINE`, `PROSE` ("serif"/"sans"), and the
`--accent` color at the top of `main.py`.

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# open http://127.0.0.1:8000
```

## Deploy to Railway

1. Push this folder to a GitHub repo.
2. Railway -> **New Project -> Deploy from GitHub repo** -> pick the repo.
3. Railway auto-detects Python from `requirements.txt` and starts it with the
   command in `Procfile` / `railway.json`. No extra config needed.
4. First deploy takes a couple of minutes (nbconvert pulls in a few deps).
   When it's live, open the Railway-provided `*.up.railway.app` URL.

## Custom .tech domain (GitHub Student Pack)

1. In Railway: your service -> **Settings -> Networking -> Custom Domain**.
2. Enter your domain. Use a subdomain like `www.yourname.tech` or
   `blog.yourname.tech` — Railway hands you a **CNAME target**.
3. In your .tech DNS panel (get.tech / the registrar in the student pack), add a
   **CNAME** record pointing that subdomain at the target Railway gave you.
4. Wait for DNS to propagate (minutes to an hour). Railway issues HTTPS
   automatically once it resolves.

Note on the root/apex (`yourname.tech` with no `www`): many .tech DNS panels
don't allow a CNAME at the apex. Easiest path is to use `www` (or `blog`) as
above and set the apex to redirect to it in the DNS panel. If your panel
supports ALIAS/ANAME at the apex, you can point that at the Railway target
instead.

## Adding more posts later

1. Drop the new `.ipynb` into `notebooks/`.
2. Add an entry for it in `posts.json` (optional, but gives it a clean
   title/date/URL).
3. Commit and push. Railway redeploys and the new post appears.

Posts are cached at startup, so a redeploy (the push) is what picks up changes.
