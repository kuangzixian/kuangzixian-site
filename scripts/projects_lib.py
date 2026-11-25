"""Single source of truth for projects: data/projects.json.

Used by the homepage project cards, the profile tab, data/profile.json,
llms.txt / llms-full.txt / index.md and the JSON-LD Person entity.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "data" / "projects.json"

LABELS = {
    "heading": {"zh": "我做的东西", "en": "Things I’ve built", "es": "Cosas que he hecho", "ko": "제가 만든 것", "ja": "つくったもの"},
    "try": {"zh": "去体验", "en": "Try it", "es": "Probar", "ko": "써 보기", "ja": "試してみる"},
    "source": {"zh": "看源码", "en": "Source", "es": "Código", "ko": "소스 보기", "ja": "ソースを見る"},
    "all": {"zh": "全部项目见个人档", "en": "All projects are in my profile", "es": "Todos mis proyectos están en el perfil", "ko": "전체 프로젝트는 프로필에 있어요", "ja": "すべてのプロジェクトはプロフィールに"},
}


def esc(s: object) -> str:
    return (
        str("" if s is None else s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@lru_cache(maxsize=1)
def load() -> list[dict]:
    return list(json.loads(PROJECTS.read_text(encoding="utf-8")).get("projects") or [])


def label(key: str, loc: str) -> str:
    pack = LABELS[key]
    return pack.get(loc) or pack["en"]


def one_liner(p: dict, loc: str) -> str:
    return p.get(f"one_liner_{loc}") or p.get("one_liner_en") or p.get("one_liner_zh") or ""


def _actions(p: dict, loc: str) -> str:
    bits = []
    if p.get("demo_url"):
        bits.append(
            f'<a class="chip project-btn is-try" href="{esc(p["demo_url"])}" target="_blank" rel="noopener noreferrer">{esc(label("try", loc))} ↗</a>'
        )
    if p.get("source_url"):
        bits.append(
            f'<a class="chip project-btn is-src" href="{esc(p["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(label("source", loc))}</a>'
        )
    return f'<div class="project-actions">{"".join(bits)}</div>'


def home_cards_html(loc: str) -> str:
    cards = []
    for p in load():
        if not p.get("featured"):
            continue
        cards.append(
            '<article class="card home-project">'
            f'<h3>{esc(p["name"])}</h3>'
            f'<p>{esc(one_liner(p, loc))}</p>'
            f"{_actions(p, loc)}"
            "</article>"
        )
    return (
        f'<div class="section-head"><h2>{esc(label("heading", loc))}</h2><span class="en">Projects</span></div>'
        f'<div class="home-project-grid">{"".join(cards)}</div>'
    )


def profile_cards_html(loc: str) -> str:
    cards = []
    for p in load():
        cards.append(
            '<article class="card project">'
            f'<span class="lang-pill">{esc(p.get("language") or "")}</span>'
            f'<h3>{esc(p["name"])}</h3>'
            f'<p>{esc(one_liner(p, loc))}</p>'
            f"{_actions(p, loc)}"
            "</article>"
        )
    return "".join(cards)


def jsonld(loc: str) -> list[dict]:
    out = []
    for p in load():
        item = {
            "@type": "SoftwareSourceCode",
            "name": p["name"],
            "description": one_liner(p, loc),
            "codeRepository": p.get("source_url"),
            "programmingLanguage": p.get("language"),
        }
        if p.get("demo_url"):
            item["targetProduct"] = {
                "@type": "SoftwareApplication",
                "name": p["name"],
                "url": p["demo_url"],
                "applicationCategory": "WebApplication",
                "operatingSystem": "Web",
            }
        out.append(item)
    return out


def sync_profile(path: Path | None = None) -> bool:
    """Rewrite profile.json's projects list from projects.json. Returns True if changed."""
    path = path or (ROOT / "data" / "profile.json")
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    projects = []
    for p in load():
        projects.append({
            "name": p["name"],
            "repo": p.get("repo"),
            "url": p.get("source_url"),
            "demo_url": p.get("demo_url"),
            "description": p.get("one_liner_zh"),
            "description_en": p.get("one_liner_en"),
            "language": p.get("language"),
            "fork": False,
            "created_at": p.get("created_at"),
        })
    data["projects"] = projects
    new = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if new != raw:
        path.write_text(new, encoding="utf-8")
        return True
    return False
