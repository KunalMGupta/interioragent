"""
Build a single static HTML preview of the docs/ Markdown pages so the documentation can be
visualized without the full Jekyll/Ruby toolchain.

Usage:
    python build_preview.py          # writes docs/preview.html

Then serve from docs/ so the relative image paths resolve:
    (cd docs && python -m http.server 8000)
    open http://localhost:8000/preview.html
"""
import os
import re
import html as _html

import markdown

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
PAGES = [
    "index", "installation", "getting-started", "object-registration",
    "groups", "relative-group", "around-group", "grid-group", "room-group", "hierarchical",
    "sentence-ascii-generator",
    "constraints", "gradient-constraints", "vlm-constraints",
]

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse(slug):
    with open(os.path.join(DOCS, f"{slug}.md"), encoding="utf-8") as f:
        text = f.read()
    meta = {}
    m = FRONTMATTER.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = text[m.end():]
    else:
        body = text
    # rewrite internal links like (relative-group) -> (#relative-group) so they jump within the page
    body = re.sub(r"\]\((?!https?://|#|assets/)([a-z0-9\-]+)\)", r"](#\1)", body)
    return meta, body


def main():
    pages = {slug: parse(slug) for slug in PAGES}

    # ordering: top-level by nav_order, children inserted after their parent
    def nav_order(slug):
        try:
            return int(pages[slug][0].get("nav_order", "999"))
        except ValueError:
            return 999

    title_to_slug = {pages[s][0].get("title", s): s for s in PAGES}
    top = [s for s in PAGES if "parent" not in pages[s][0]]
    top.sort(key=nav_order)

    ordered = []
    for s in top:
        ordered.append((s, 0))
        children = [c for c in PAGES if pages[c][0].get("parent") and
                    title_to_slug.get(pages[c][0]["parent"]) == s]
        children.sort(key=nav_order)
        for c in children:
            ordered.append((c, 1))

    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])

    nav_items, sections = [], []
    for slug, depth in ordered:
        meta, body = pages[slug]
        title = meta.get("title", slug)
        md.reset()
        content = md.convert(body)
        nav_items.append(
            f'<a class="d{depth}" href="#{slug}">{_html.escape(title)}</a>'
        )
        sections.append(
            f'<section id="{slug}"><div class="page">{content}</div></section>'
        )

    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>InteriorAgent-IDSDL — Documentation Preview</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         color:#27262b; line-height:1.6; }}
  #sidebar {{ position:fixed; top:0; left:0; width:280px; height:100vh; overflow-y:auto;
              background:#f7f7f9; border-right:1px solid #eaeaea; padding:24px 0; }}
  #sidebar .brand {{ font-weight:700; font-size:15px; padding:0 24px 16px; color:#5a4ff3; }}
  #sidebar a {{ display:block; padding:6px 24px; color:#44434d; text-decoration:none; font-size:14px; }}
  #sidebar a:hover {{ background:#ececf5; color:#5a4ff3; }}
  #sidebar a.d1 {{ padding-left:42px; font-size:13px; color:#6b6a75; }}
  main {{ margin-left:280px; max-width:900px; padding:48px 56px 120px; }}
  section {{ border-bottom:1px solid #eee; padding-bottom:48px; margin-bottom:48px; }}
  h1 {{ font-size:30px; border-bottom:2px solid #5a4ff3; padding-bottom:8px; margin-top:8px; }}
  h2 {{ font-size:22px; margin-top:36px; }}
  h3 {{ font-size:17px; margin-top:28px; }}
  code {{ background:#f3f3f6; padding:2px 6px; border-radius:4px; font-size:85%;
          font-family:"SF Mono",Menlo,Consolas,monospace; }}
  pre {{ background:#2d2b38; color:#f3f3f6; padding:16px 18px; border-radius:8px; overflow-x:auto; }}
  pre code {{ background:none; color:inherit; padding:0; }}
  table {{ border-collapse:collapse; width:100%; margin:16px 0; font-size:14px; }}
  th, td {{ border:1px solid #e2e2e8; padding:8px 12px; text-align:left; vertical-align:top; }}
  th {{ background:#f3f3f6; }}
  img {{ border:1px solid #eee; border-radius:6px; }}
  a {{ color:#5a4ff3; }}
</style></head>
<body>
<nav id="sidebar"><div class="brand">InteriorAgent-IDSDL</div>{''.join(nav_items)}</nav>
<main>{''.join(sections)}</main>
</body></html>"""

    out = os.path.join(DOCS, "preview.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {out} ({len(ordered)} pages)")


if __name__ == "__main__":
    main()
