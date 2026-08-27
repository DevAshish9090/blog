"""
Notebook blog — renders .ipynb files as faithful Jupyter-style pages
wrapped in a proper editorial layout.

Drop any .ipynb into ./notebooks and it becomes a post automatically.
Optional per-notebook metadata (Notebook menu -> Edit Notebook Metadata):

    "blog": {
        "title": "How LLMs Actually Work",
        "date": "2026-02-14",
        "description": "Taking a small language model apart, one step at a time.",
        "eyebrow": "Notebook",
        "slug": "how-llms-work",
        "draft": false
    }
"""

import re
import warnings
from datetime import date, datetime
from pathlib import Path

import nbformat
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from nbconvert import HTMLExporter

warnings.filterwarnings("ignore", message="IPython3 lexer unavailable")

# ---- Configure your site here -------------------------------------------------
SITE_TITLE = "zvd's notebook"
SITE_TAGLINE = "Taking machine learning apart, one notebook at a time."
# Prose font: "serif" reads like a publication; flip to "sans" if you prefer.
PROSE = "serif"
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
NOTEBOOK_DIR = BASE_DIR / "notebooks"

exporter = HTMLExporter(template_name="lab", embed_images=True)

app = FastAPI(title=SITE_TITLE)
if (BASE_DIR / "static").is_dir():
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

_POSTS: dict[str, dict] = {}

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    "family=Space+Grotesk:wght@500;600;700&"
    "family=Newsreader:ital,wght@0,400;0,600;1,400&"
    "family=JetBrains+Mono:wght@400;500&display=swap"
    '" rel="stylesheet">'
)

# Design tokens shared by every page.
TOKENS = """
:root{
  --ink:#17171f; --ink-soft:#5b5b67; --faint:#8a8a97;
  --paper:#f3f3f6; --surface:#ffffff; --line:#e6e6ec;
  --accent:#4c3bcf; --accent-tint:#eeecfb;
  --display:'Space Grotesk',system-ui,sans-serif;
  --serif:'Newsreader',Georgia,'Times New Roman',serif;
  --mono:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --ui:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
}
"""

PROSE_FAMILY = "var(--serif)" if PROSE == "serif" else "var(--ui)"


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "post"


def _first_markdown(nb) -> str:
    for cell in nb.cells:
        if cell.cell_type == "markdown" and cell.source.strip():
            return cell.source
    return ""


def _derive_title(nb, fallback: str) -> str:
    for level in (r"^#\s+(.*)", r"^##\s+(.*)"):
        for cell in nb.cells:
            if cell.cell_type != "markdown":
                continue
            for line in cell.source.splitlines():
                m = re.match(level, line.strip())
                if m:
                    return m.group(1).strip()
    return fallback.replace("_", " ").replace("-", " ").title()


def _derive_description(nb) -> str:
    for line in _first_markdown(nb).splitlines():
        clean = line.strip().lstrip("#").strip()
        if clean:
            return (clean[:200] + "…") if len(clean) > 200 else clean
    return ""


def _post_style() -> str:
    return f"""
    <style>
      {TOKENS}
      body{{ background:var(--paper); }}

      /* slim sticky breadcrumb bar */
      .site-bar{{
        position:fixed; top:0; left:0; right:0; height:52px; z-index:1000;
        display:flex; align-items:center; gap:14px; padding:0 22px;
        background:rgba(243,243,246,.82); backdrop-filter:blur(12px);
        border-bottom:1px solid var(--line);
        font:600 14px/1 var(--display); letter-spacing:-.01em;
      }}
      .site-bar a{{ color:var(--accent); text-decoration:none; }}
      .site-bar a:hover{{ text-decoration:underline; }}
      .site-bar .sep{{ color:var(--faint); }}
      .site-bar .cur{{ color:var(--ink-soft); overflow:hidden;
        text-overflow:ellipsis; white-space:nowrap; }}

      /* editorial masthead */
      .masthead{{
        max-width:840px; margin:0 auto; padding:104px 28px 0;
        animation:rise .5s cubic-bezier(.2,.7,.2,1) both;
      }}
      .masthead .eyebrow{{
        font:600 12px/1 var(--display); letter-spacing:.18em;
        text-transform:uppercase; color:var(--accent);
        display:flex; align-items:center; gap:10px;
      }}
      .masthead .eyebrow::after{{
        content:""; height:1px; flex:1; background:var(--line);
      }}
      .masthead h1.post-title{{
        font:700 clamp(34px,5.5vw,52px)/1.05 var(--display);
        letter-spacing:-.025em; color:var(--ink);
        margin:20px 0 0;
      }}
      .masthead .lede{{
        font:400 20px/1.5 var(--serif); color:var(--ink-soft);
        margin:18px 0 0; max-width:60ch;
      }}
      .masthead .meta{{
        font:500 13px/1 var(--ui); color:var(--faint);
        margin:24px 0 0; display:flex; align-items:center; gap:10px;
        text-transform:uppercase; letter-spacing:.06em;
      }}
      .masthead .rule{{
        height:2px; background:var(--accent); width:56px;
        margin:26px 0 0; border-radius:2px;
      }}
      @keyframes rise{{ from{{opacity:0; transform:translateY(12px);}}
                        to{{opacity:1; transform:none;}} }}
      @media(prefers-reduced-motion:reduce){{ .masthead{{animation:none;}} }}

      /* notebook column */
      .jp-Notebook{{
        max-width:840px; margin:22px auto 0; padding:8px 28px 96px !important;
        background:transparent !important;
      }}

      /* prose */
      body .jp-RenderedHTMLCommon{{
        font-family:{PROSE_FAMILY}; font-size:18px; line-height:1.72;
        color:var(--ink);
      }}
      body .jp-RenderedHTMLCommon p{{ margin:.7em 0 1em; }}
      body .jp-RenderedHTMLCommon strong{{ color:var(--ink); font-weight:650; }}
      body .jp-RenderedHTMLCommon h1,
      body .jp-RenderedHTMLCommon h2,
      body .jp-RenderedHTMLCommon h3,
      body .jp-RenderedHTMLCommon h4{{
        font-family:var(--display); letter-spacing:-.02em; color:var(--ink);
      }}
      body .jp-RenderedHTMLCommon h1{{ font-size:30px; font-weight:700; }}
      body .jp-RenderedHTMLCommon h2{{
        font-size:26px; font-weight:700; margin-top:2.4em;
        padding-top:1.1em; border-top:1px solid var(--line);
      }}
      body .jp-RenderedHTMLCommon h3{{ font-size:19px; font-weight:600;
        color:var(--ink-soft); }}
      body .jp-RenderedHTMLCommon a{{ color:var(--accent); }}
      body .jp-RenderedHTMLCommon code{{
        font-family:var(--mono); font-size:.86em; background:var(--accent-tint);
        color:var(--accent); padding:.1em .35em; border-radius:5px;
      }}

      /* code cells: keep the In/Out gutter, refine the box */
      body .highlight pre,
      body .jp-RenderedHTMLCommon pre,
      body .jp-OutputArea-output pre,
      body .jp-InputArea-editor{{ font-family:var(--mono) !important; }}
      body .jp-InputArea-editor{{
        font-size:14px; background:#fbfbfd; border:1px solid var(--line);
        border-radius:10px;
      }}
      body .jp-InputPrompt,
      body .jp-OutputPrompt{{
        font-family:var(--mono) !important; color:var(--faint);
      }}
      body .jp-OutputArea-output{{ font-size:14px; }}

      @media(max-width:620px){{
        .masthead{{ padding:88px 20px 0; }}
        .jp-Notebook{{ padding:8px 20px 72px !important; }}
        body .jp-RenderedHTMLCommon{{ font-size:17px; }}
      }}
    </style>
    """


def _masthead(post: dict) -> str:
    d = post["date"].strftime("%d %b %Y").upper()
    lede = (
        f'<p class="lede">{post["description"]}</p>' if post["description"] else ""
    )
    return f"""
    <header class="masthead">
      <div class="eyebrow">{post["eyebrow"]}</div>
      <h1 class="post-title">{post["title"]}</h1>
      {lede}
      <div class="meta"><span>{d}</span></div>
      <div class="rule"></div>
    </header>
    """


def _inject_chrome(html: str, post: dict) -> str:
    head = FONTS + _post_style()
    html = html.replace("</head>", head + "</head>", 1)
    bar = (
        '<div class="site-bar">'
        f'<a href="/">← {SITE_TITLE}</a>'
        '<span class="sep">/</span>'
        f'<span class="cur">{post["title"]}</span>'
        "</div>"
    )
    html = re.sub(r"(<body[^>]*>)", r"\1" + bar + _masthead(post), html, count=1)
    return html


def _load_posts() -> None:
    _POSTS.clear()
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        if path.name.startswith("."):
            continue
        nb = nbformat.read(path, as_version=4)
        meta = nb.metadata.get("blog", {}) if isinstance(nb.metadata, dict) else {}
        if meta.get("draft"):
            continue

        slug = _slugify(meta.get("slug") or path.stem)
        title = meta.get("title") or _derive_title(nb, path.stem)
        description = meta.get("description") or _derive_description(nb)
        eyebrow = meta.get("eyebrow") or "Notebook"

        raw_date = meta.get("date")
        if raw_date:
            try:
                post_date = datetime.fromisoformat(str(raw_date)).date()
            except ValueError:
                post_date = date.fromtimestamp(path.stat().st_mtime)
        else:
            post_date = date.fromtimestamp(path.stat().st_mtime)

        body, _ = exporter.from_notebook_node(nb)
        post = {
            "slug": slug, "title": title, "description": description,
            "date": post_date, "eyebrow": eyebrow,
        }
        post["html"] = _inject_chrome(body, post)
        _POSTS[slug] = post


@app.on_event("startup")
def startup() -> None:
    _load_posts()


def _index_page() -> str:
    posts = sorted(_POSTS.values(), key=lambda p: p["date"], reverse=True)
    cards = "\n".join(
        f"""
        <a class="card" href="/p/{p['slug']}">
          <div class="card-eyebrow">{p['eyebrow']} · {p['date'].strftime('%d %b %Y').upper()}</div>
          <h2 class="card-title">{p['title']}</h2>
          <p class="card-desc">{p['description']}</p>
          <span class="card-go">Read notebook →</span>
        </a>"""
        for p in posts
    )
    if not cards:
        cards = '<p class="empty">No posts yet. Drop an .ipynb into /notebooks.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{SITE_TITLE}</title>
  {FONTS}
  <style>
    {TOKENS}
    *{{ box-sizing:border-box; }}
    body{{ margin:0; background:var(--paper); color:var(--ink);
      font-family:{PROSE_FAMILY}; -webkit-font-smoothing:antialiased; }}
    .wrap{{ max-width:760px; margin:0 auto; padding:88px 28px 120px; }}
    .brand{{ font:600 13px/1 var(--display); letter-spacing:.16em;
      text-transform:uppercase; color:var(--accent);
      display:flex; align-items:center; gap:12px; }}
    .brand::after{{ content:""; height:1px; flex:1; background:var(--line); }}
    header h1{{ font:700 clamp(40px,7vw,64px)/1.02 var(--display);
      letter-spacing:-.03em; margin:22px 0 0; }}
    header p.tag{{ font:400 21px/1.5 var(--serif); color:var(--ink-soft);
      margin:20px 0 64px; max-width:44ch; }}
    .card{{ display:block; text-decoration:none; color:inherit;
      padding:30px 32px; margin-bottom:20px; border-radius:18px;
      background:var(--surface); border:1px solid var(--line);
      transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease; }}
    .card:hover{{ transform:translateY(-3px);
      box-shadow:0 14px 40px rgba(23,23,31,.08); border-color:#d6d6e0; }}
    .card-eyebrow{{ font:600 12px/1 var(--display); letter-spacing:.12em;
      text-transform:uppercase; color:var(--faint); }}
    .card-title{{ font:700 27px/1.15 var(--display); letter-spacing:-.02em;
      margin:12px 0 0; color:var(--ink); }}
    .card-desc{{ font-family:var(--serif); font-size:18px; line-height:1.6;
      color:var(--ink-soft); margin:12px 0 0; }}
    .card-go{{ display:inline-block; margin-top:18px; font:600 14px/1 var(--display);
      color:var(--accent); }}
    .empty{{ color:var(--faint); }}
    footer{{ margin-top:64px; font:400 14px/1.5 var(--ui); color:var(--faint); }}
    @media(max-width:620px){{ .wrap{{ padding:64px 20px 96px; }}
      .card{{ padding:24px; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="brand">{SITE_TITLE}</div>
      <h1>Notebooks, in full.</h1>
      <p class="tag">{SITE_TAGLINE}</p>
    </header>
    {cards}
    <footer>Built with FastAPI + nbconvert.</footer>
  </div>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _index_page()


@app.get("/p/{slug}", response_class=HTMLResponse)
def post(slug: str) -> str:
    p = _POSTS.get(slug)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    return p["html"]


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "posts": len(_POSTS)}
