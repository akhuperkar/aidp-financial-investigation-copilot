"""Build the Medium-ready Markdown and optional table SVGs without changing the draft.

Uses Python's standard library. PNG companions can be rendered from these SVGs
with a trusted local SVG renderer; they are optional publishing aids.
"""

from html import escape
from pathlib import Path
import re
import textwrap
from urllib.parse import quote


BASE = Path(__file__).resolve().parent
REPO = BASE.parent
GITHUB = "https://github.com/akhuperkar/aidp-financial-investigation-copilot/blob/main/"
RAW = "https://raw.githubusercontent.com/akhuperkar/aidp-financial-investigation-copilot/main/"


def absolute_link(match):
    opening, target, closing = match.groups()
    if target.startswith(("https://", "http://", "#")):
        return match.group(0)
    path = (BASE / target).resolve()
    relative = path.relative_to(REPO).as_posix()
    if not path.is_file():
        raise FileNotFoundError(relative)
    prefix = RAW if opening.startswith("!") else GITHUB
    return opening + prefix + quote(relative, safe="/") + closing


def tables(markdown):
    found = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([c.strip() for c in lines[index].strip("|").split("|")])
                index += 1
            found.append([rows[0]] + rows[2:])
        else:
            index += 1
    return found


def table_svg(rows, widths, title):
    # Readable at Medium's article-column width rather than desktop-table scale.
    margin, fontsize, leading, pad = 24, 28, 38, 20
    total_width = sum(widths) + 2 * margin
    wrapped = []
    for row in rows:
        wrapped.append([textwrap.wrap(cell, width=max(5, int((width - pad * 2) / (fontsize * 0.50))),
                                       break_long_words=False, break_on_hyphens=False)
                        or [""] for cell, width in zip(row, widths)])
    heights = [max(84, max(map(len, row)) * leading + 36) for row in wrapped]
    total_height = sum(heights) + 2 * margin + 5
    description = "; ".join(" | ".join(row) for row in rows)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}" role="img" aria-labelledby="title description">',
           f'<title id="title">{escape(title)}</title>',
           f'<desc id="description">{escape(description)}</desc>',
           f'<rect width="{total_width}" height="{total_height}" fill="#FFFFFF"/>',
           f'<rect x="{margin}" y="{margin}" width="{sum(widths)}" height="5" fill="#C74634"/>']
    y = margin + 5
    for row_index, (row, lines, height) in enumerate(zip(rows, wrapped, heights)):
        color = "#312D2A" if row_index == 0 else ("#F8F9FA" if row_index % 2 == 0 else "#FFFFFF")
        ink = "#FFFFFF" if row_index == 0 else "#312D2A"
        svg.append(f'<rect x="{margin}" y="{y}" width="{sum(widths)}" height="{height}" fill="{color}"/>')
        x = margin
        for column, (cell_lines, width) in enumerate(zip(lines, widths)):
            align_right = len(widths) == 2 and column == 1 and row_index > 0
            anchor = "end" if align_right else "start"
            tx = x + width - pad if align_right else x + pad
            ty = y + (height - len(cell_lines) * leading) / 2 + fontsize
            weight = "700" if row_index == 0 else "400"
            svg.append(f'<text x="{tx}" y="{ty}" fill="{ink}" font-family="Arial, Helvetica, sans-serif" font-size="{fontsize}" font-weight="{weight}" text-anchor="{anchor}">')
            for line_index, line in enumerate(cell_lines):
                svg.append(f'<tspan x="{tx}" dy="{0 if line_index == 0 else leading}">{escape(line)}</tspan>')
            svg.append('</text>')
            x += width
        y += height
        if row_index > 0:
            svg.append(f'<path d="M {margin} {y} H {margin + sum(widths)}" stroke="#DEDbd8"/>')
    svg.append('</svg>')
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    source = (BASE / "medium-article.md").read_text()
    ready = re.sub(r"(!?\[[^\]]*\]\()([^)]+)(\))", absolute_link, source)
    (BASE / "medium-ready.md").write_text(ready)
    extracted = tables(source)
    if len(extracted) != 2:
        raise ValueError("Expected the article's two tables")
    assets = BASE / "assets"
    assets.mkdir(exist_ok=True)
    specifications = [
        ("december-reference-table", [580, 372], "December 2024 reference measures"),
        ("medallion-responsibilities-table", [150, 400, 402], "Data layer responsibilities"),
    ]
    for rows, (name, widths, title) in zip(extracted, specifications):
        (assets / (name + ".svg")).write_text(table_svg(rows, widths, title))
    print("Built article/medium-ready.md and two article/assets/ table SVGs")
