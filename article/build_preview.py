"""Build the local article preview with Python's standard library only.

This renderer supports the deliberately small Markdown subset used by the draft.
It makes no network calls and adds no scripts, telemetry or external fonts.
"""

from html import escape
from pathlib import Path
import re


BASE = Path(__file__).resolve().parent


def inline(value):
    value = escape(value, quote=False)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
    return value


def render(markdown):
    lines = markdown.splitlines()
    blocks = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            blocks.append("<h1>" + inline(line[2:]) + "</h1>")
        elif line.startswith("## "):
            blocks.append("<h2>" + inline(line[3:]) + "</h2>")
        elif line.startswith("> "):
            blocks.append("<blockquote><p>" + inline(line[2:]) + "</p></blockquote>")
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line)
            if not match:
                raise ValueError("Unsupported image markup: " + line)
            alt, source = match.groups()
            blocks.append('<figure><img src="' + escape(source, quote=True)
                          + '" alt="' + escape(alt, quote=True) + '"></figure>')
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                rows.append(cells)
                index += 1
            header = "".join("<th scope=\"col\">" + inline(c) + "</th>" for c in rows[0])
            body = "".join("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in row)
                           + "</tr>" for row in rows[2:])
            blocks.append('<div class="table-wrap"><table><thead><tr>' + header
                          + "</tr></thead><tbody>" + body + "</tbody></table></div>")
            continue
        else:
            paragraph = [line]
            while index + 1 < len(lines) and lines[index + 1].strip():
                next_line = lines[index + 1].strip()
                if next_line.startswith(("#", "|", "![", "> ")):
                    break
                index += 1
                paragraph.append(next_line)
            blocks.append("<p>" + inline(" ".join(paragraph)) + "</p>")
        index += 1
    return "\n".join(blocks)


STYLE = """
:root{color-scheme:light;--red:#C74634;--ink:#312D2A;--paper:#F8F9FA;--line:#dedbd8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Georgia,'Times New Roman',serif;line-height:1.68}
.topbar{background:var(--ink);color:white;padding:13px 24px;font:13px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:.03em}
main{max-width:900px;margin:36px auto 72px;padding:40px 62px;background:white;border-top:5px solid var(--red)}
h1,h2,th{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}h1{font-size:clamp(30px,4.5vw,46px);line-height:1.12;letter-spacing:-.025em;margin:0 0 22px}
h2{font-size:25px;line-height:1.25;letter-spacing:-.015em;margin:44px 0 16px}p{font-size:18px;margin:0 0 20px}a{color:#a53729;text-decoration-thickness:1px;text-underline-offset:3px}a:hover{color:var(--red)}
code{font:14px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--paper);padding:2px 4px;border-radius:3px;overflow-wrap:anywhere}
blockquote{border-left:4px solid var(--red);background:var(--paper);margin:24px 0;padding:14px 18px}blockquote p{margin:0;font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
figure{margin:28px -22px 12px}img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:3px}figure+p:has(>em:only-child){font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#625c57}
.table-wrap{overflow-x:auto;margin:24px 0 30px}table{width:100%;border-collapse:collapse;font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}th{background:var(--ink);color:white;text-align:left;padding:12px 14px}td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}tbody tr:nth-child(even){background:var(--paper)}
footer{border-top:1px solid var(--line);margin-top:40px;padding-top:20px;font:13px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#625c57}
@media(max-width:700px){main{margin:0;padding:32px 22px;border-left:0;border-right:0}p{font-size:17px}h2{font-size:23px}figure{margin:24px 0 12px}th,td{padding:10px}}
@media print{.topbar{display:none}main{max-width:none;margin:0;padding:24px;border-top:3px solid var(--red)}h2{break-after:avoid}figure,.table-wrap{break-inside:avoid}a{color:var(--ink)}}
"""


if __name__ == "__main__":
    body = render((BASE / "medium-article.md").read_text())
    document = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Local review preview of the Meridian Demo Bank financial investigation article.">
<title>Financial Investigation Copilot — Article Preview</title><style>""" + STYLE + """</style></head>
<body><div class="topbar">LOCAL ARTICLE PREVIEW · PUBLICATION DRAFT</div><main>""" + body + """
<footer>Local review preview. <a href="medium-article.md">Markdown source</a> · <a href="../docs/research-sources.md">Research register</a> · <a href="medium-publishing.md">Publishing handoff</a></footer>
</main></body></html>
"""
    (BASE / "preview.html").write_text(document)
    print("Built article/preview.html")
