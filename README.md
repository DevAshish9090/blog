# Notebook blog

A tiny FastAPI site that renders `.ipynb` files as faithful Jupyter-style pages
(In/Out prompts, notebook CSS, embedded plots). Drop a notebook into
`notebooks/` and it becomes a post automatically.

## How posts work

- Every `*.ipynb` in `notebooks/` becomes a post at `/p/<slug>`.
- The homepage `/` lists them, newest first.
- Notebooks are rendered once at startup and cached in memory.

Set per-notebook metadata in Jupyter via **Edit -> Edit Notebook Metadata**
(or the metadata is already there in the sample):

```json
"blog": {
  "title": "How LLMs Actually Work",
  "date": "2026-02-14",
  "description": "One-line summary shown on the homepage.",
  "slug": "how-llms-work",
  "draft": false
}
```

If `blog` is missing, the title falls back to the first heading (then the
filename), the date to the file's modified time, and the slug to the filename.
Set `"draft": true` to keep a notebook out of the listing.

Edit `SITE_TITLE` and `SITE_TAGLINE` at the top of `main.py`.

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

Drop another `.ipynb` into `notebooks/`, commit, push. Railway redeploys and the
new post appears. (Posts are cached at startup, so a redeploy — or a restart —
is what picks up changes.)
