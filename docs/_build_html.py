"""docs/*.md → docs/html/*.html 변환 스크립트.

문서(00-INDEX.md, 01~12)를 사이드바 내비게이션이 있는 정적 HTML로 변환한다.
브라우저에서 docs/html/index.html 을 열면 된다. 외부 CDN 없이 오프라인 동작.

실행 (프로젝트 루트에서, 프로젝트 venv 를 건드리지 않음):
    uv run --no-project --with markdown --with pygments python docs/_build_html.py
"""

from __future__ import annotations

import html as html_mod
import re
import sys
from datetime import datetime
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode
from pygments.formatters import HtmlFormatter

DOCS_DIR = Path(__file__).resolve().parent
OUT_DIR = DOCS_DIR / "html"

# 내비게이션 순서: (md 파일명, 출력 html 이름, 난이도 배지)
PAGES = [
    ("00-INDEX.md", "index.html", "📚"),
    ("01-overview.md", "01-overview.html", "🟢"),
    ("02-python-basics.md", "02-python-basics.html", "🟢"),
    ("03-python-advanced.md", "03-python-advanced.html", "🟡"),
    ("04-architecture.md", "04-architecture.html", "🟡"),
    ("05-config-and-models.md", "05-config-and-models.html", "🟢🟡"),
    ("06-decorators.md", "06-decorators.html", "🟡"),
    ("07-repository.md", "07-repository.html", "🟡🔴"),
    ("08-services.md", "08-services.html", "🟡🔴"),
    ("09-cli.md", "09-cli.html", "🟡"),
    ("10-advanced-design.md", "10-advanced-design.html", "🔴"),
    ("11-faq-and-glossary.md", "11-faq-and-glossary.html", "🟢"),
    ("12-syntax-and-stdlib.md", "12-syntax-and-stdlib.html", "📘"),
]

MD_LINK_RE = re.compile(r"\]\(\./([0-9A-Za-z-]+)\.md(#[^)]*)?\)")


def md_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "(제목 없음)"


def rewrite_links(text: str) -> str:
    """상대 .md 링크를 같은 폴더의 .html 링크로 바꾼다."""

    def repl(m: re.Match) -> str:
        name, frag = m.group(1), m.group(2) or ""
        target = "index.html" if name == "00-INDEX" else f"{name}.html"
        return f"]({target}{frag})"

    return MD_LINK_RE.sub(repl, text)


def build_css() -> str:
    light = HtmlFormatter(style="default").get_style_defs(".codehilite")
    dark = HtmlFormatter(style="native").get_style_defs(".codehilite")
    return f"""
:root {{
  --bg: #ffffff; --fg: #1f2328; --muted: #57606a; --border: #d0d7de;
  --accent: #0969da; --code-bg: #f6f8fa; --sidebar-bg: #f6f8fa;
  --quote: #57606a; --quote-border: #d0d7de; --current: #ddf4ff;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --border: #30363d;
    --accent: #4493f8; --code-bg: #161b22; --sidebar-bg: #10151c;
    --quote: #8b949e; --quote-border: #30363d; --current: #0c2d6b;
  }}
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0; background: var(--bg); color: var(--fg);
  font-family: "Segoe UI", "Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
  line-height: 1.75;
}}
.layout {{ display: grid; grid-template-columns: 300px minmax(0, 1fr); min-height: 100vh; }}
nav.sidebar {{
  background: var(--sidebar-bg); border-right: 1px solid var(--border);
  padding: 1rem; position: sticky; top: 0; height: 100vh; overflow-y: auto;
}}
nav.sidebar .brand {{ font-weight: 700; font-size: 1.05rem; margin: .3rem 0 1rem; }}
nav.sidebar .brand a {{ color: var(--fg); text-decoration: none; }}
.navlist {{ list-style: none; margin: 0; padding: 0; }}
.navlist li {{ margin: 0; }}
.navlist a {{
  display: block; padding: .4rem .6rem; border-radius: 6px;
  color: var(--fg); text-decoration: none; font-size: .88rem;
}}
.navlist a:hover {{ background: var(--code-bg); }}
.navlist a.current {{ background: var(--current); font-weight: 600; }}
.navlist .badge {{ margin-right: .35rem; }}
details.nav > summary {{
  cursor: pointer; font-weight: 600; padding: .4rem .2rem; list-style: none;
}}
details.nav > summary::before {{ content: "☰ "; }}
main {{ padding: 2rem 2.5rem 4rem; max-width: 940px; }}
h1 {{ font-size: 1.9rem; line-height: 1.3; border-bottom: 2px solid var(--border); padding-bottom: .5rem; }}
h2 {{ font-size: 1.45rem; margin-top: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: .3rem; }}
h3 {{ font-size: 1.15rem; margin-top: 1.8rem; }}
h4 {{ font-size: 1rem; margin-top: 1.4rem; }}
a {{ color: var(--accent); }}
blockquote {{
  margin: 1rem 0; padding: .2rem 1rem; color: var(--quote);
  border-left: 4px solid var(--quote-border);
}}
code {{
  font-family: Consolas, "D2Coding", "Cascadia Mono", "Courier New", monospace;
  font-size: .85em; background: var(--code-bg);
  padding: .15em .35em; border-radius: 4px;
}}
pre {{ background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px;
  padding: .9rem 1rem; overflow-x: auto; line-height: 1.5; }}
pre code {{ background: none; padding: 0; font-size: .84rem; }}
.codehilite {{ border-radius: 8px; overflow: hidden; }}
.codehilite pre {{ margin: 0; border: 1px solid var(--border); }}
.table-wrap {{ overflow-x: auto; margin: 1rem 0; }}
table {{ border-collapse: collapse; font-size: .9rem; }}
th, td {{ border: 1px solid var(--border); padding: .45rem .7rem; text-align: left; }}
th {{ background: var(--code-bg); }}
hr {{ border: none; border-top: 1px solid var(--border); margin: 2.2rem 0; }}
details.page-toc {{
  background: var(--code-bg); border: 1px solid var(--border);
  border-radius: 8px; padding: .6rem 1rem; margin: 1.4rem 0;
}}
details.page-toc summary {{ cursor: pointer; font-weight: 600; }}
details.page-toc ul {{ margin: .5rem 0 .3rem; padding-left: 1.2rem; }}
.pager {{
  display: flex; justify-content: space-between; gap: 1rem;
  margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--border);
}}
.pager a {{ text-decoration: none; max-width: 46%; }}
footer {{ margin-top: 2rem; color: var(--muted); font-size: .8rem; }}
@media (max-width: 900px) {{
  .layout {{ grid-template-columns: 1fr; }}
  nav.sidebar {{ position: static; height: auto; border-right: none; border-bottom: 1px solid var(--border); }}
  main {{ padding: 1.2rem 1rem 3rem; }}
}}
@media (min-width: 901px) {{
  details.nav > summary {{ display: none; }}
  details.nav:not([open]) > .navlist {{ display: block; }}
}}
{light}
@media (prefers-color-scheme: dark) {{
{dark}
}}
"""


def nav_html(current_out: str, titles: dict[str, str]) -> str:
    items = []
    for md_name, out_name, badge in PAGES:
        title = titles[md_name]
        cls = ' class="current"' if out_name == current_out else ""
        items.append(
            f'<li><a href="{out_name}"{cls}><span class="badge">{badge}</span>'
            f"{html_mod.escape(title)}</a></li>"
        )
    return (
        '<nav class="sidebar"><div class="brand"><a href="index.html">📖 budget_app 학습 문서</a></div>'
        '<details class="nav" open><summary>목차</summary><ul class="navlist">'
        + "".join(items)
        + "</ul></details></nav>"
    )


def page_toc_html(toc_tokens: list[dict]) -> str:
    h2s = [t for t in toc_tokens if t["level"] == 1 or t["level"] == 2]
    # 문서 최상위가 h1 하나이므로 toc_tokens 루트는 h1 — 그 children 이 h2
    if len(toc_tokens) == 1 and toc_tokens[0]["level"] == 1:
        h2s = toc_tokens[0]["children"]
    if not h2s:
        return ""
    lis = "".join(
        f'<li><a href="#{t["id"]}">{html_mod.escape(t["name"])}</a></li>' for t in h2s
    )
    return (
        '<details class="page-toc" open><summary>이 문서의 목차</summary>'
        f"<ul>{lis}</ul></details>"
    )


def convert(md_text: str) -> tuple[str, list[dict]]:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "toc"],
        extension_configs={
            "codehilite": {"guess_lang": False},
            "toc": {"slugify": slugify_unicode, "permalink": False},
        },
        output_format="html5",
    )
    body = md.convert(md_text)
    body = body.replace("<table>", '<div class="table-wrap"><table>')
    body = body.replace("</table>", "</table></div>")
    return body, getattr(md, "toc_tokens", [])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = {name: (DOCS_DIR / name).read_text(encoding="utf-8") for name, _, _ in PAGES}
    titles = {name: md_title(text) for name, text in sources.items()}
    css = build_css()
    (OUT_DIR / "style.css").write_text(css, encoding="utf-8")

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    problems: list[str] = []

    for i, (md_name, out_name, _badge) in enumerate(PAGES):
        text = rewrite_links(sources[md_name])
        body, toc_tokens = convert(text)

        toc_block = page_toc_html(toc_tokens)
        if toc_block:
            pos = body.find("<h2")
            if pos != -1:
                body = body[:pos] + toc_block + body[pos:]

        prev_link = next_link = ""
        if i > 0:
            p_md, p_out, _ = PAGES[i - 1]
            prev_link = f'<a href="{p_out}">← {html_mod.escape(titles[p_md])}</a>'
        if i < len(PAGES) - 1:
            n_md, n_out, _ = PAGES[i + 1]
            next_link = f'<a href="{n_out}">{html_mod.escape(titles[n_md])} →</a>'

        title = titles[md_name]
        tab_title = title if "budget_app 학습 문서" in title else f"{title} — budget_app 학습 문서"
        page = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_mod.escape(tab_title)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="layout">
{nav_html(out_name, titles)}
<main>
{body}
<div class="pager"><span>{prev_link}</span><span>{next_link}</span></div>
<footer>docs/{md_name} 에서 자동 생성됨 ({stamp}) — 내용 수정은 마크다운 원본에서 하고 docs/_build_html.py 를 다시 실행하세요.</footer>
</main>
</div>
</body>
</html>
"""
        (OUT_DIR / out_name).write_text(page, encoding="utf-8")

        # 변환 후 자가 검증: 남아 있는 .md 링크가 없어야 한다
        if re.search(r'href="[^"]*\.md[#"]', page):
            problems.append(f"{out_name}: 변환되지 않은 .md 링크가 남아 있음")

    generated = sorted(p.name for p in OUT_DIR.glob("*.html"))
    expected = sorted(out for _, out, _ in PAGES)
    if generated != expected:
        problems.append(f"생성 파일 불일치: {set(expected) ^ set(generated)}")

    print(f"생성 완료: {len(expected)}개 HTML + style.css → {OUT_DIR}")
    for p in problems:
        print("[문제]", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
