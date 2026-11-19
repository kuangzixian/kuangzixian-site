#!/usr/bin/env python3
"""A small Markdown renderer matching js/markdown.js (no extra dependency)."""
from __future__ import annotations

import re

KEYWORDS = (
    "break case catch class const continue debugger default delete do else export extends "
    "finally for function if import in instanceof let new return static super switch this "
    "throw try typeof var void while with yield async await of from as "
    "func package import type struct interface map chan go defer select range "
    "true false null nil undefined"
).split()
KW_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in KEYWORDS) + r")\b")
FENCE_OPEN = re.compile(r"^```([\w+-]*)\s*$")
FENCE_CLOSE = re.compile(r"^```\s*$")
HR_RE = re.compile(r"^(---+|\*\*\*+)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
UL_RE = re.compile(r"^[-*+]\s+(.+)$")
OL_RE = re.compile(r"^\d+\.\s+(.+)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")


def escape_html(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _highlight(code: str) -> str:
    s = escape_html(code)
    slots: list[str] = []

    def stash(html: str) -> str:
        slots.append(html)
        return f"\0{len(slots) - 1}\0"

    s = re.sub(r"/\*[\s\S]*?\*/", lambda m: stash(f'<span class="tok-cmt">{m.group(0)}</span>'), s)
    s = re.sub(r"(^|[^:\\])//[^\n]*", lambda m: stash(f'<span class="tok-cmt">{m.group(0)}</span>'), s, flags=re.M)
    s = re.sub(r"`(?:\\.|[^`\\])*`", lambda m: stash(f'<span class="tok-str">{m.group(0)}</span>'), s)
    s = re.sub(r"&quot;(?:\\.|[^&])*?&quot;", lambda m: stash(f'<span class="tok-str">{m.group(0)}</span>'), s)
    s = re.sub(r"'(?:\\.|[^'\\])*'", lambda m: stash(f'<span class="tok-str">{m.group(0)}</span>'), s)
    s = re.sub(r"\b0x[0-9a-fA-F]+\b|\b\d+(?:\.\d+)?\b", lambda m: stash(f'<span class="tok-num">{m.group(0)}</span>'), s)
    s = KW_RE.sub(r'<span class="tok-kw">\1</span>', s)
    s = re.sub(r"\0(\d+)\0", lambda m: slots[int(m.group(1))], s)
    return s


def _inline_md(s: str) -> str:
    s = escape_html(s)
    s = re.sub(
        r"\\.",
        lambda m: {"<": "&lt;", ">": "&gt;", "&": "&amp;"}.get(m.group(0)[1], m.group(0)[1]),
        s,
    )
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(
        r"\[([^\]]+)\]\((https?:[^)\s]+)\)",
        r'<a href="\2" rel="noopener noreferrer">\1</a>',
        s,
    )
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(^|[^*])\*([^*\n]+)\*", r"\1<em>\2</em>", s)
    return s


def _render_list(items: list[str], ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    parts = [f"<{tag}>"]
    for item in items:
        body = "".join((("<br>" if i else "") + _inline_md(line)) for i, line in enumerate(item.split("\n")))
        parts.append(f"<li>{body}</li>")
    parts.append(f"</{tag}>")
    return "".join(parts)


def _line_has_table(line: str) -> bool:
    if not line or not line.strip():
        return False
    return bool(TABLE_SEP_RE.match(line) or "|" in line)


def _split_cells(line: str) -> list[str]:
    t = line.strip()
    if t.startswith("|"):
        t = t[1:]
    if t.endswith("|"):
        t = t[:-1]
    return [c.strip() for c in t.split("|")]


def _render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    html = ['<div class="md-table"><table><thead><tr>']
    for c in head:
        html.append(f"<th>{_inline_md(c)}</th>")
    html.append("</tr></thead><tbody>")
    for row in body:
        html.append("<tr>")
        for c in row:
            html.append(f"<td>{_inline_md(c)}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    return "".join(html)


def render_markdown(src: str | None) -> str:
    text = str(src or "").replace("\r\n", "\n").replace("\t", "    ")
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    para: list[str] = []
    quote: list[str] = []
    lst: list[str] | None = None
    list_ordered = False

    def flush_para() -> None:
        nonlocal para
        if not para:
            return
        body = "\n".join(para).strip()
        if body:
            out.append("<p>" + "<br>".join(_inline_md(line) for line in body.split("\n")) + "</p>")
        para = []

    def flush_quote() -> None:
        nonlocal quote
        if not quote:
            return
        out.append("<blockquote>" + render_markdown("\n".join(quote)) + "</blockquote>")
        quote = []

    def flush_list() -> None:
        nonlocal lst
        if not lst:
            return
        out.append(_render_list(lst, list_ordered))
        lst = None

    def flush_all() -> None:
        flush_para()
        flush_quote()
        flush_list()

    n = len(lines)
    while i < n:
        line = lines[i]
        fence = FENCE_OPEN.match(line)
        if fence:
            flush_all()
            lang = fence.group(1) or ""
            code: list[str] = []
            i += 1
            while i < n and not FENCE_CLOSE.match(lines[i]):
                code.append(lines[i])
                i += 1
            out.append(
                f'<pre><code class="lang-{escape_html(lang)}">{_highlight(chr(10).join(code))}</code></pre>'
            )
            i += 1
            continue

        if "|" in line and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            flush_all()
            rows = [_split_cells(line)]
            i += 2
            while i < n and _line_has_table(lines[i]):
                if not TABLE_SEP_RE.match(lines[i]):
                    rows.append(_split_cells(lines[i]))
                i += 1
            out.append(_render_table(rows))
            continue

        if HR_RE.match(line):
            flush_all()
            out.append("<hr>")
            i += 1
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush_all()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline_md(heading.group(2))}</h{level}>")
            i += 1
            continue

        q = QUOTE_RE.match(line)
        if q:
            flush_para()
            flush_list()
            quote.append(q.group(1))
            i += 1
            continue
        if quote:
            flush_quote()

        ul = UL_RE.match(line)
        ol = OL_RE.match(line)
        if ul or ol:
            flush_para()
            ordered = bool(ol)
            if not lst or list_ordered != ordered:
                flush_list()
                lst = []
                list_ordered = ordered
            lst.append((ul or ol).group(1))
            i += 1
            continue
        if lst and re.match(r"^\s{2,}\S", line):
            lst[-1] += "\n" + re.sub(r"^\s+", "", line)
            i += 1
            continue
        if lst:
            flush_list()

        if re.match(r"^\s*$", line):
            flush_para()
            i += 1
            continue
        para.append(line)
        i += 1

    flush_all()
    return "\n".join(out)
