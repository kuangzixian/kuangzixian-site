#!/usr/bin/env python3
"""List leftover CJK-Han in built locale HTML (en/es), and Chinese-only text on ko/ja pages."""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data"
HAN = re.compile(r"[\u4e00-\u9fff]+")
HANGUL = re.compile(r"[\uac00-\ud7af]")
SIMP = set("这那们为发现经对会时过还没从里后说吗吧着给让儿喽啥咱们已经问题")
ALLOWED = {"匡子闲", "中文", "沈新宇", "珍珠阿西", "日本語", "周大福", "長鑫", "长鑫"}


def load_allowed_originals() -> set[str]:
    acc: set[str] = set(ALLOWED)
    keys = {
        "title", "author", "name", "label",
        "text", "quote", "content", "annotation", "markText", "abstract",
        "artist", "album", "song", "intro", "intro_short", "short_title",
    }

    def walk(obj, bag):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in keys and isinstance(v, str):
                    bag.add(v)
                walk(v, bag)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, bag)

    for name, extra in (
        ("reading.json", keys),
        ("music.json", {"title", "name", "artist", "album", "song"}),
    ):
        path = DATA / name
        if path.exists():
            walk(json.loads(path.read_text(encoding="utf-8")), acc)
    profile = json.loads((DATA / "profile.json").read_text(encoding="utf-8"))
    for post in profile.get("jike_posts") or []:
        if post.get("text"):
            acc.add(post["text"])
    bg = DATA / "boardgames.json"
    if bg.exists():
        for game in json.loads(bg.read_text(encoding="utf-8")).get("games") or []:
            if game.get("name_zh"):
                acc.add(game["name_zh"])
    return acc


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ignore = 0
        self.chunks: list[str] = []
        self.skip = {"script", "style", "noscript", "svg"}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip:
            self.ignore += 1
        if self.ignore:
            return
        ad = dict(attrs)
        for key in ("alt", "title", "aria-label", "placeholder"):
            if ad.get(key):
                self.chunks.append(ad[key])

    def handle_endtag(self, tag):
        if tag in self.skip and self.ignore:
            self.ignore -= 1

    def handle_data(self, data):
        if self.ignore:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.chunks.append(text)


def visible_text(html: str) -> str:
    html = re.sub(r'<script type="application/ld\+json">.*?</script>', "", html, flags=re.S)
    parser = VisibleText()
    parser.feed(html)
    return "\n".join(parser.chunks)


def original_context(ctx: str, allowed: set[str]) -> bool:
    return any(item and item in ctx for item in allowed)


def pages() -> list[Path]:
    out: list[Path] = []
    for loc in ("en", "es", "ko", "ja"):
        for name in ("index.html", "404.html"):
            path = DIST / loc / name
            if path.exists():
                out.append(path)
        writing = DIST / loc / "writing"
        if writing.exists():
            out.extend(sorted(writing.glob("*.html")))
    return out


def main() -> int:
    allowed = load_allowed_originals()
    findings = []
    for path in pages():
        rel = str(path.relative_to(DIST))
        loc = rel[:2]
        text = visible_text(path.read_text(encoding="utf-8"))
        seen = set()
        for match in HAN.finditer(text):
            span = match.group(0)
            if span in ALLOWED or any(name in span for name in ("匡子闲", "沈新宇", "珍珠阿西")):
                continue
            ctx = text[max(0, match.start() - 36) : match.end() + 36].replace("\n", " | ")
            if original_context(ctx, allowed):
                continue
            if loc in ("en", "es"):
                flag = True
            elif loc == "ko":
                flag = any(ch in SIMP for ch in span) or (not HANGUL.search(ctx) and len(span) >= 3)
            else:
                flag = any(ch in SIMP for ch in span)
            if not flag or span in seen:
                continue
            seen.add(span)
            findings.append((rel, span, ctx))
    for rel, span, ctx in findings:
        print(f"{rel}\t{span}\t{ctx}")
    print(f"# findings: {len(findings)}", file=sys.stderr)
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
