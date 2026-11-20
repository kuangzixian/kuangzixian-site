#!/usr/bin/env python3
"""Copy the static site into dist/ for wrangler pages deploy / pages dev."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

INCLUDE_FILES = ("index.html", "chat.html")
INCLUDE_DIRS = ("css", "js", "data", "images", "music")
SKIP_NAMES = {".DS_Store"}

REPORT_CREDIT_MARK = "music-report-powered"


def ensure_report_credit(path: Path) -> None:
    """Add a discreet Powered-by credit to the hosted 声迹 report, if missing."""
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if REPORT_CREDIT_MARK in text:
        return
    snippet = (
        '<style>'
        '.music-report-powered{position:fixed;left:16px;bottom:12px;z-index:40;'
        'display:inline-flex;align-items:center;gap:8px;padding:6px 12px 6px 6px;'
        'border-radius:999px;background:#ffffffd9;border:1px solid #dedfd6;'
        'color:#76796f;text-decoration:none;font-size:11px;letter-spacing:.02em;'
        'font-family:"Avenir Next","PingFang SC","Microsoft Yahei",sans-serif;'
        'backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}'
        '.music-report-powered img{width:20px;height:20px;border-radius:50%;object-fit:cover;background:#fff}'
        '.music-report-powered strong{color:#232420;font-weight:650}'
        '.music-report-powered:hover{color:#232420;border-color:#b8bcae}'
        '@media(max-width:760px){.music-report-powered{left:10px;bottom:10px;font-size:10px}}'
        '</style>'
        '<a class="music-report-powered" href="https://github.com/ryohgicc/musicanalysis"'
        ' target="_blank" rel="noopener noreferrer">'
        '<img src="../images/music/ryohgicc.png" width="20" height="20" alt="">'
        '<span>Powered by <strong>musicanalysis</strong></span></a>\n'
    )
    lower = text.lower()
    idx = lower.rfind("</body>")
    if idx < 0:
        text = text + snippet
    else:
        text = text[:idx] + snippet + text[idx:]
    path.write_text(text, encoding="utf-8")




def should_skip(path: Path) -> bool:
    name = path.name
    if name in SKIP_NAMES or name.startswith("."):
        return True
    if name.startswith("preview") and name.endswith(".png"):
        return True
    if name.startswith("_i18n"):
        return True
    return False


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for name in INCLUDE_FILES:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, DIST / name)
    for dirname in INCLUDE_DIRS:
        src = ROOT / dirname
        if not src.exists():
            continue
        dest = DIST / dirname
        shutil.copytree(
            src,
            dest,
            ignore=lambda _dir, names: [n for n in names if should_skip(Path(n))],
        )
    ensure_report_credit(ROOT / "music" / "report.html")
    ensure_report_credit(DIST / "music" / "report.html")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_ai import write_ai_files
    from build_html import write_pages

    write_ai_files(DIST)
    write_pages(DIST)

    headers = DIST / "_headers"
    headers.write_text(
        "/api/*\n"
        "  Cache-Control: no-store\n"
        "  X-Content-Type-Options: nosniff\n"
        "\n"
        "/*.md\n"
        "  Content-Type: text/markdown; charset=utf-8\n"
        "  X-Content-Type-Options: nosniff\n"
        "\n"
        "/*/writing/*.md\n"
        "  Content-Type: text/markdown; charset=utf-8\n"
        "  X-Content-Type-Options: nosniff\n"
        "\n"
        "/*.txt\n"
        "  Content-Type: text/plain; charset=utf-8\n"
        "  X-Content-Type-Options: nosniff\n",
        encoding="utf-8",
    )
    # Pretty URL for the music report. Do not add a /* /index.html 200 SPA fallback:
    # unknown paths must hit 404.html with HTTP 404.
    (DIST / "_redirects").write_text(
        "/music/report.html /music/report 301\n",
        encoding="utf-8",
    )
    print(f"Built {DIST}")


if __name__ == "__main__":
    main()
