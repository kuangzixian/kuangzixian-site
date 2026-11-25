#!/usr/bin/env python3
"""Generate AI-friendly Markdown, llms.txt, sitemaps, and robots.txt from site data."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n_lib

SITE = "https://kuangzixian.pages.dev"
DATA = ROOT / "data"
MUSIC_REPORT = f"{SITE}/music/report"


def writing_html_url(chat_id: str, loc: str = "zh") -> str:
    if loc == "zh":
        return f"{SITE}/writing/{chat_id}"
    return f"{SITE}/{loc}/writing/{chat_id}"


def writing_md_url(chat_id: str, loc: str = "zh") -> str:
    if loc == "zh":
        return f"{SITE}/writing/{chat_id}.md"
    return f"{SITE}/{loc}/writing/{chat_id}.md"


def load_json(name: str) -> Any:
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def load_sites() -> dict:
    path = DATA / "sites.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"sites": data}
    return data


def site_entries(data: dict | list | None) -> list[dict]:
    if not data:
        return []
    if isinstance(data, list):
        return data
    return list(data.get("sites") or data.get("friends") or [])


def site_brief_lines(data: dict | None = None) -> list[str]:
    data = data or load_sites()
    sites = site_entries(data)
    if not sites:
        return []
    names = []
    for site in sites:
        name = site.get("name") or site.get("title") or ""
        if site.get("own") and name:
            name = f"{name}（自己做的）"
        if name:
            names.append(name)
    return [
        f"- 推荐网站，当前收录 {len(sites)} 个：" + "、".join(names) + "。",
        "- 介绍摘自各站点自己的公开信息，没有编造。标了「自己做的」的是匡子闲本人的项目。不要补充未列出的网站或未记录的说明。",
        f"- 推荐网站栏目：[HTML]({SITE}/#sites)，[Markdown]({SITE}/sites.md)，JSON：[sites.json]({SITE}/data/sites.json)。旧地址 #friends、#links 会转到这个栏目。",
    ]


def build_sites_md(data: dict | None = None) -> str:
    data = data or load_sites()
    sites = site_entries(data)
    if not data and not sites:
        return ""
    intro = (data or {}).get("intro_zh") or "推荐看看的网站。"
    lines = [
        "# 推荐网站 / Recommended sites",
        "",
        intro,
        "",
        "介绍摘自各站点自己的公开信息，没有编造。标了「自己做的」的是匡子闲本人的项目。",
        f"页面：[HTML]({SITE}/#sites)，机器可读 JSON：[{SITE}/data/sites.json]({SITE}/data/sites.json)。旧地址 #friends、#links 会转到这个栏目。",
        "",
    ]
    for site in sites:
        name = site.get("name") or site.get("title") or site.get("url") or ""
        title = site.get("title") or name
        url = site.get("url") or site.get("canonical") or ""
        heading = name
        if site.get("own"):
            heading = f"{heading}（自己做的）"
        lines.append(f"## {heading}")
        lines.append("")
        if title and title != name:
            lines.append(title)
            lines.append("")
        if url:
            domain = site.get("domain") or ""
            label = domain or url
            lines.append(f"- 网址：[{label}]({url})")
        desc = (site.get("description") or "").strip()
        if desc:
            lines.append(f"- 介绍：{desc}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"




def load_boardgames() -> dict:
    path = DATA / "boardgames.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def boardgame_brief_lines(data: dict | None) -> list[str]:
    data = data or {}
    games = list(data.get("games") or [])
    if not games:
        return []
    names = "、".join(
        (g.get("name_zh") or g.get("name_en") or "")
        + (f"（{g.get('name_en')}）" if g.get("name_en") and g.get("name_zh") and g.get("name_en") != g.get("name_zh") else "")
        for g in games
        if g.get("name_zh") or g.get("name_en")
    )
    return [
        f"- 玩过、也爱玩的桌游，当前收录 {len(games)} 款：{names}。",
        "- 介绍只含公开的人数和类型，没有个人评分、排名或对局次数。不要编造未列出的游戏或评价。",
        f"- 桌游栏目：[HTML]({SITE}/#boardgames)，[Markdown]({SITE}/boardgames.md)，JSON：[boardgames.json]({SITE}/data/boardgames.json)。",
    ]


def build_boardgames_md(data: dict | None) -> str:
    data = data or load_boardgames()
    games = list((data or {}).get("games") or [])
    if not data and not games:
        return ""
    intro = data.get("intro_zh") or "玩过、也爱玩的桌游。"
    lines = [
        "# 桌游 / Board games",
        "",
        intro,
        "",
        "介绍只含公开的人数和类型，没有个人评分、排名或对局次数。",
        f"页面：[HTML]({SITE}/#boardgames)，机器可读 JSON：[{SITE}/data/boardgames.json]({SITE}/data/boardgames.json)。",
        "",
    ]
    for game in games:
        name_zh = game.get("name_zh") or ""
        name_en = game.get("name_en") or ""
        title = name_zh or name_en
        if name_zh and name_en and name_en != name_zh:
            title = f"{name_zh} / {name_en}"
        lines.append(f"## {title}")
        lines.append("")
        bits = []
        if game.get("players"):
            bits.append(f"人数：{game['players']}")
        genre = game.get("genre_zh") or game.get("genre_en")
        if genre:
            bits.append(f"类型：{genre}")
        if bits:
            lines.append(" · ".join(bits))
            lines.append("")
        blurb = game.get("blurb_zh") or game.get("blurb_en") or ""
        if blurb:
            lines.append(blurb)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def md_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def book_title(title: str) -> str:
    return f"《{title}》"


def book_link(title: str, url: str | None) -> str:
    label = md_escape(book_title(title))
    if url:
        return f"[{label}]({url})"
    return label



def load_music() -> dict:
    path = DATA / "music.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def music_brief_lines(music: dict | None) -> list[str]:
    if not music:
        return []
    pl = music.get("playlist") or {}
    artists = "、".join(
        f"{a.get('artist')} {a.get('count')}" for a in (music.get("topArtists") or [])[:8]
    )
    tool = music.get("tool") or {}
    return [
        f"- 网易云歌单「{pl.get('name') or ''}」共 {pl.get('trackCount') or 0} 首，导出于 {pl.get('exportedAtShanghai') or ''}（{pl.get('timezone') or 'Asia/Shanghai'}）。分析来自收藏，不是播放次数。",
        f"- 按网易云「我喜欢的音乐」默认顺序解读：第 1 首视为最新收藏。用户未另行确认排序，编号不是年份。",
        f"- 出现较多的艺人（按演唱参与计，含合作与不同发行）：{artists}。",
        f"- 口味摘要：{music.get('summary') or ''}",
        f"- 音乐栏目：[HTML]({SITE}/#music)，[Markdown]({SITE}/music.md)，完整「声迹」报告：[music/report]({SITE}/music/report)，JSON：[music.json]({SITE}/data/music.json)。Powered by [musicanalysis]({tool.get('url') or 'https://github.com/ryohgicc/musicanalysis'})。",
    ]


def build_music_md(music: dict | None) -> str:
    music = music or load_music()
    if not music:
        return ""
    pl = music.get("playlist") or {}
    tool = music.get("tool") or {}
    lines = [
        "# 音乐 / Music",
        "",
        f"来源：[网易云歌单「{pl.get('name') or ''}」]({pl.get('sourceUrl') or ''})，共 {pl.get('trackCount') or 0} 首，{pl.get('artistCount') or 0} 位艺人（按演唱参与计）。",
        f"导出于 {pl.get('exportedAtShanghai') or ''}（{pl.get('timezone') or 'Asia/Shanghai'}）。",
        "",
        music.get("orderNoteZh") or "",
        "",
        f"## {music.get('title') or '口味摘要'}",
        "",
        music.get("summary") or "",
        "",
        "## 出现最多的艺人",
        "",
        "次数含合作与不同发行，不是播放次数，也不能当作流派占比。",
        "",
    ]
    for artist in music.get("topArtists") or []:
        lines.append(f"- {artist.get('artist')}：{artist.get('count')}")
    if music.get("topAlbums"):
        lines += ["", "## 收藏较多的专辑", ""]
        for album in music["topAlbums"]:
            names = " / ".join(album.get("artists") or [])
            lines.append(f"- {names}《{album.get('album')}》：{album.get('count')} 首")
    lines += ["", "## 偏好", ""]
    for ins in music.get("insights") or []:
        lines.append(f"### {ins.get('title')}")
        lines.append("")
        lines.append(ins.get("summary") or "")
        lines.append("")
        lines.append(ins.get("body") or "")
        lines.append("")
        for ev in ins.get("evidence") or []:
            lines.append(f"- {ev.get('title')} / {ev.get('artist')}：{ev.get('note')}")
        lines.append("")
    lines += [
        "## 风格时间线",
        "",
        "九段按旧→新排列。因为第 1 首视为最新，时间线从第 286 首读到第 1 首。编号是歌单位置，不是年份。",
        "",
    ]
    for stage in music.get("stages") or []:
        lo, hi = (stage.get("range") or [None, None])[:2]
        lines.append(f"### {stage.get('tag')} · {stage.get('title')}（#{hi}–#{lo}）")
        lines.append("")
        if stage.get("subtitle"):
            lines.append(stage["subtitle"])
            lines.append("")
        lines.append(stage.get("body") or "")
        lines.append("")
        if stage.get("insight"):
            lines.append(stage["insight"])
            lines.append("")
        anchors = stage.get("anchors") or []
        if anchors:
            bits = "；".join(f"{a.get('title')} / {a.get('artist')}" for a in anchors)
            lines.append(f"证据曲：{bits}")
            lines.append("")
    lines += ["", "## 推荐", "", "以下 12 首都不在这张歌单里，曲目和封面已核对来源。喜欢与否要听过才知道。", ""]
    current = None
    for rec in music.get("recommendations") or []:
        if rec.get("tier") != current:
            current = rec.get("tier")
            lines += [f"### {current}", ""]
        lines.append(f"- [{rec.get('title')}]({rec.get('source')}) — {rec.get('artist')}（{rec.get('album') or ''}）：{rec.get('reason')} 可能的差别：{rec.get('difference')}")
    lines += [
        "",
        "## 完整报告与工具",
        "",
        f"- 本站托管的「声迹」完整报告：[music/report]({SITE}/music/report)",
        f"- 空间里的音乐选项卡：[{SITE}/#music]({SITE}/#music)",
        f"- 机器可读 JSON：[{SITE}/data/music.json]({SITE}/data/music.json)",
        f"- Powered by [musicanalysis]({tool.get('url') or 'https://github.com/ryohgicc/musicanalysis'})",
        "",
        "## 限制",
        "",
    ]
    for item in music.get("limitationsZh") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def iso_date(value: str | None) -> str | None:
    if not value:
        return None
    return value[:10]


def fmt_int(n: int) -> str:
    return f"{n:,}"


def verified_profiles(profile: dict) -> list[dict]:
    return [p for p in profile.get("profiles") or [] if p.get("status") == "verified" and p.get("url")]


def latest_dates(profile: dict, reading: dict, chats: list[dict], music: dict | None = None, boardgames: dict | None = None, sites: dict | None = None) -> str:
    candidates = [
        iso_date(profile.get("updated_at")),
        iso_date(reading.get("retrieved_at")),
        iso_date(((music or {}).get("playlist") or {}).get("exportedAt")),
        iso_date((boardgames or {}).get("updated_at")),
        iso_date((sites or {}).get("updated_at")),
    ]
    for chat in chats:
        candidates.append(iso_date(chat.get("date") or chat.get("datetime")))
    dates = [d for d in candidates if d]
    return max(dates) if dates else "2026-11-17"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def progress_text(item: dict) -> str:
    progress = item.get("progress")
    if progress is None or progress == "":
        return ""
    return f"进度 {progress}%"


def shelf_line(item: dict) -> str:
    kind = "有声书" if item.get("kind") == "album" else "书"
    title = item.get("title") or ""
    author = item.get("author") or ""
    category = item.get("category_full") or item.get("category") or ""
    bits = [book_link(title, item.get("readerLink")), "—"]
    if author:
        bits.append(author)
    meta = [kind]
    if category:
        meta.append(category)
    if item.get("finished"):
        meta.append("已读完")
    if item.get("last_read"):
        meta.append(f"最近 {item['last_read']}")
    elif not item.get("finished") and not item.get("last_read"):
        meta.append("尚未阅读")
    bits.append("· " + " · ".join(meta))
    return "- " + " ".join(bits)



PROJECT_DISPLAY_NAMES = {"easy-life": "EasyLife", "easy-offer": "EasyOffer"}
I18N_LOCALES = ("zh", "en", "es", "ko", "ja")
HREFLANG = {"zh": "zh-CN", "en": "en", "es": "es", "ko": "ko", "ja": "ja"}


def project_display_name(proj: dict) -> str:
    name = (proj.get("name") or "").strip()
    return PROJECT_DISPLAY_NAMES.get(name, name)


def locale_page_url(path: str, loc: str) -> str:
    if path == "/":
        return f"{SITE}/" if loc == "zh" else f"{SITE}/{loc}/"
    prefix = "" if loc == "zh" else f"/{loc}"
    return f"{SITE}{prefix}{path}"


def xhtml_links(path: str) -> list[str]:
    lines = []
    for loc in I18N_LOCALES:
        lines.append(
            f'    <xhtml:link rel="alternate" hreflang="{HREFLANG[loc]}" href="{xml_escape(locale_page_url(path, loc))}"/>'
        )
    lines.append(
        f'    <xhtml:link rel="alternate" hreflang="x-default" href="{xml_escape(locale_page_url(path, "zh"))}"/>'
    )
    return lines


def build_llms_txt(profile: dict, reading: dict, chats: list[dict], sites: dict | None = None) -> str:
    bio = profile.get("bio") or {}
    shelf = reading.get("public_shelf") or {}
    stats = (reading.get("stats") or {}).get("overall") or {}
    year = (reading.get("stats") or {}).get("year_2026") or {}
    lines = [
        "# 匡子闲",
        "",
        f"> {bio['combined_zh']}",
        "",
        "## Canonical URLs",
        "",
        f"- [Homepage]({SITE}/)",
        f"- [English]({SITE}/en/)",
        f"- [Español]({SITE}/es/)",
        f"- [한국어]({SITE}/ko/)",
        f"- [日本語]({SITE}/ja/)",
        f"- [Agent-optimized homepage]({SITE}/?mode=agent)",
        f"- [Markdown homepage]({SITE}/index.md)",
        f"- [Reading]({SITE}/reading.md)",
        f"- [Writing]({SITE}/writing.md)",
        f"- [Music]({SITE}/music.md)",
        f"- [Music tab]({SITE}/#music)",
        f"- [Music report]({SITE}/music/report)",
        f"- [Board games]({SITE}/boardgames.md)",
        f"- [Board games tab]({SITE}/#boardgames)",
        f"- [Recommended sites]({SITE}/sites.md)",
        f"- [Recommended sites tab]({SITE}/#sites)",
    ]
    for chat in chats:
        lines.append(f"- [{chat['title']}]({writing_html_url(chat['id'])})（Markdown：[writing/{chat['id']}.md]({writing_md_url(chat['id'])})）")
    lines += [
        f"- [Guestbook]({SITE}/#guestbook)",
        f"- [Full agent context]({SITE}/llms-full.txt)",
        f"- [Markdown sitemap]({SITE}/sitemap.md)",
        f"- [XML sitemap]({SITE}/sitemap.xml)",
        "",
        "## What this site is",
        "",
        "这是匡子闲的个人主页，页面装扮成经典 QQ 空间的样子，用选项卡分别查看主页、日志、读书、音乐、桌游、推荐网站、留言板和个人档。本站不是公开 API、SDK 文档，也不是产品定价或登录平台。",
        "站点提供中文、英语、西班牙语、韩语和日语界面：中文首页在 `/`，其他语言分别在 `/en/`、`/es/`、`/ko/`、`/ja/`。对话正文仍以原文托管在本站，方便中国大陆和海外访问。",
        "机器可读入口是 `/llms.txt`、`/llms-full.txt`、各页 Markdown，以及 `/data/profile.json`、`/data/reading.json`、`/data/chats.json`、`/data/sites.json`、`/data/music.json`、`/data/boardgames.json`。",
        "",
        "## Best-known work",
        "",
    ]
    for proj in profile.get("projects") or []:
        name = project_display_name(proj)
        url = proj.get("url") or ""
        desc = proj.get("description")
        note = proj.get("note")
        lang = proj.get("language") or ""
        title = f"[{name}]({url})" if url else name
        if proj.get("demo_url"):
            title += f"（在线体验：{proj['demo_url']}）"
        if desc:
            extra = desc.rstrip()
            if extra and extra[-1] not in "。．.！？!?":
                extra += "。"
            if lang:
                extra += f" 主要语言：{lang}。"
            lines.append(f"- {title}：{extra}")
        else:
            remark = note or "公开仓库无简介，这里不编造功能说明。"
            extra = remark.rstrip()
            if extra and extra[-1] not in "。．.！？!?":
                extra += "。"
            if lang:
                extra += f" 主要语言：{lang}。"
            lines.append(f"- {title}：{extra}")

    retrieved = reading.get("retrieved_at") or profile.get("updated_at") or ""
    tz = reading.get("timezone") or profile.get("timezone") or "Asia/Shanghai"
    lines += [
        "",
        f"- 微信读书公开档案（检索于 {retrieved}，时区 {tz}）：累计阅读 {stats.get('total_read_time') or ''}，有效阅读 {fmt_int(stats.get('read_days') or 0)} 天，读过 {stats.get('books_read')} 本、读完 {stats.get('books_finished')} 本，笔记 {fmt_int(stats.get('notes') or 0)} 条。官方统计口径可能包含未出现在公开书架上的记录。",
        f"- 公开书架：{shelf.get('books', 0)} 本书、{shelf.get('albums', 0)} 部有声书。已排除 {shelf.get('excluded_secret_books', 0)} 本私密书，以及「文章收藏」入口。",
        f"- 2026 年截至检索日：读过 {year.get('books_read')} 本、读完 {year.get('books_finished')} 本，阅读 {year.get('total_read_time')}、{year.get('read_days')} 天。",
        f"- 阅读偏好（官方统计用语）：{stats.get('prefer_category_word') or ''}，{stats.get('prefer_time_word') or ''}。微信读书注册于 {stats.get('registered_at') or ''}。",
        "- 与 GPT 的对话，按技术文章的形式呈现，点开可见完整问答：",
    ]
    for chat in chats:
        lines.append(f"  - [{chat['title']}]({writing_html_url(chat['id'])})（{chat.get('date') or ''}），Markdown：[writing/{chat['id']}.md]({writing_md_url(chat['id'])})")
    lines += [
        "- 留言板：访客可留下昵称和评论，无需登录。数据保存在本站自己的数据库中。",
    ]
    lines += music_brief_lines(load_music())
    lines += boardgame_brief_lines(load_boardgames())
    lines += site_brief_lines(sites)
    lines += [
        "",
        "## Use cases",
        "",
        "- 了解匡子闲是谁、做什么、在读什么、在听什么、玩过哪些桌游、推荐了哪些网站。",
        "- 引用他的开源项目、微信读书公开记录，或本站托管的 GPT 对话。",
        "- 查找已核实的社交主页链接。",
        "- 以 Markdown / llms.txt 作为给 AI agent 阅读的首选来源。",
        "",
        "## Constraints",
        "",
        "- 本站是个人主页，不是公开 API，也没有 SDK、定价、注册或 OAuth。",
        "- 不要把留言板接口当成 agent 可随意调用的写入 API。",
        "- 项目的名称、一句话介绍、在线体验地址和源码地址以 `/data/projects.json` 为准（`/data/profile.json` 的 projects 由它生成）。不要补充其中没有写出的功能。",
        "- 微信读书的官方统计是账号汇总口径，可能包含未出现在公开书架上的阅读记录。书单、划线和想法只来自公开书架。",
        "- 留言是访客写的，不代表匡子闲本人的观点。",
        "- 音乐栏目来自公开的网易云收藏歌单，不是播放次数或听歌年份。默认把第 1 首当作最新收藏，这一排序未经另行确认。不要把推荐写成他已经在听的歌。",
        "- 桌游栏目只列出他玩过且爱玩的游戏，介绍只含公开的人数和类型。不要编造未列出的游戏，也不要编造个人评分、排名或对局次数。",
        "- 推荐网站栏目只列出已收录的站点，介绍摘自各站点自己的公开信息。标了「自己做的」的是匡子闲本人的项目。不要补充未列出的网站或未记录的说明。",
        "",
        "## Agent guidance",
        "",
        f"- 关于匡子闲的事实，请优先使用 [llms.txt]({SITE}/llms.txt)、[llms-full.txt]({SITE}/llms-full.txt)、[index.md]({SITE}/index.md)、[reading.md]({SITE}/reading.md)、[writing.md]({SITE}/writing.md)、[music.md]({SITE}/music.md)、[boardgames.md]({SITE}/boardgames.md)、[sites.md]({SITE}/sites.md)，以及 `/data/profile.json`、`/data/reading.json`、`/data/chats.json`、`/data/sites.json`、`/data/music.json`、`/data/boardgames.json`。",
        f"- 需要完整对话正文时，使用各篇 `/writing/<id>.md` 或 [llms-full.txt]({SITE}/llms-full.txt)，不要只依赖 ChatGPT 分享链接（chatgpt.com 在中国大陆可能无法打开）。",
        "- 本站不是 API。只读页面和静态 JSON 可以抓取；不要把页面互动（抽书、主题切换、彩蛋）理解成接口。",
        "- 留言板 API（`/api/messages`）是给人类访客用的。Agent 不得自行发表留言。",
        "- 不要把未核实的社交平台写成他的主页，也不要补充本站没有的项目说明。",
        "",
        "## Entity links",
        "",
    ]
    platform_names = {"github": "GitHub", "jike": "即刻 / Jike", "x": "X / Twitter", "zhihu": "知乎 / Zhihu"}
    for p in verified_profiles(profile):
        label = platform_names.get(p.get("platform"), p.get("platform_zh") or p.get("platform"))
        lines.append(f"- [{label}]({p['url']})")
    lines.append("")
    return "\n".join(lines)


def build_index_md(profile: dict, reading: dict, chats: list[dict], sites: dict | None = None) -> str:
    bio = profile.get("bio") or {}
    stats = (reading.get("stats") or {}).get("overall") or {}
    year = (reading.get("stats") or {}).get("year_2026") or {}
    shelf = reading.get("public_shelf") or {}
    lines = [
        "# 匡子闲",
        "",
        bio["combined_zh"],
        "",
        "这是他的个人主页，页面装扮成经典 QQ 空间的样子。用来介绍自己、公开的微信读书记录、音乐口味、玩过的桌游、推荐网站、开源项目，以及与 GPT 的对话。本站不是公开 API。",
        "",
        "## 阅读",
        "",
        f"微信读书记录始于 {stats.get('registered_at')}。截至 {reading.get('retrieved_at')}（{reading.get('timezone') or 'Asia/Shanghai'}）：累计阅读 {stats.get('total_read_time')}，有效阅读 {fmt_int(stats.get('read_days') or 0)} 天，读过 {stats.get('books_read')} 本、读完 {stats.get('books_finished')} 本。2026 年读过 {year.get('books_read')} 本、读完 {year.get('books_finished')} 本。{stats.get('prefer_category_word') or ''}，{stats.get('prefer_time_word') or ''}。",
        f"公开书架有 {shelf.get('books', 0)} 本书和 {shelf.get('albums', 0)} 部有声书。完整书单、在读书和划线见 [reading.md]({SITE}/reading.md)。",
        "",
        "## 项目",
        "",
    ]
    for proj in profile.get("projects") or []:
        name = project_display_name(proj)
        url = proj.get("url") or ""
        title = f"[{name}]({url})" if url else name
        if proj.get("demo_url"):
            title += f"（在线体验：{proj['demo_url']}）"
        if proj.get("description"):
            lines.append(f"- {title}：{proj['description']}")
        else:
            lines.append(f"- {title}：{proj.get('note') or '公开仓库无简介，不编造功能说明。'}")
    lines += ["", "## 文章 / Writing", ""]
    for chat in chats:
        summary = chat.get("summary") or ""
        lines.append(f"- [{chat['title']}]({writing_html_url(chat['id'])})（{chat.get('date') or ''}）：{summary} Markdown：[writing/{chat['id']}.md]({writing_md_url(chat['id'])})")
    lines += [
        "",
        "## 音乐",
        "",
        *music_brief_lines(load_music()),
        f"更完整的口味说明、风格时间线和推荐见 [music.md]({SITE}/music.md)。",
        "",
        "## 桌游",
        "",
        *boardgame_brief_lines(load_boardgames()),
        f"完整列表见 [boardgames.md]({SITE}/boardgames.md)。",
        "",
        "## 推荐网站",
        "",
        *site_brief_lines(sites),
        f"完整列表见 [sites.md]({SITE}/sites.md)。",
        "",
        "## 留言板",
        "",
        f"访客可以在首页 [留言板]({SITE}/#guestbook) 留下昵称和评论，无需登录。该接口是给人类访客用的，agent 不要自行留言。",
        "",
        "## 即刻动态",
        "",
        f"以下动态来自即刻公开主页，检索于 {profile.get('research_retrieved_at') or reading.get('retrieved_at')}。时间是当时页面上的相对时间，多数没有独立链接。",
        "",
    ]
    for post in profile.get("jike_posts") or []:
        when = post.get("relative_time_as_retrieved") or ""
        text = (post.get("text") or "").replace("\n", " ")
        lines.append(f"- {when}：{text}")
    lines += [
        "",
        "## 给 AI agent 的入口",
        "",
        f"- [llms.txt]({SITE}/llms.txt)",
        f"- [llms-full.txt]({SITE}/llms-full.txt)",
        f"- [sitemap.md]({SITE}/sitemap.md)",
        f"- 机器可读 JSON：[{SITE}/data/profile.json]({SITE}/data/profile.json)、[reading.json]({SITE}/data/reading.json)、[chats.json]({SITE}/data/chats.json)、[sites.json]({SITE}/data/sites.json)、[music.json]({SITE}/data/music.json)、[boardgames.json]({SITE}/data/boardgames.json)",
        "",
    ]
    return "\n".join(lines)


def prefer_categories(stats_block: dict) -> list[str]:
    rows = []
    for item in stats_block.get("prefer_categories") or []:
        title = item.get("title") or ""
        count = item.get("reading_count")
        time = item.get("reading_time") or ""
        if title:
            bits = [title]
            if count is not None:
                bits.append(f"{count} 本")
            if time:
                bits.append(time)
            rows.append("- " + "，".join(bits))
    return rows


def build_reading_md(reading: dict) -> str:
    stats = reading.get("stats") or {}
    overall = stats.get("overall") or {}
    year = stats.get("year_2026") or {}
    month = stats.get("month_2026_11") or {}
    shelf = reading.get("public_shelf") or {}
    lines = [
        "# 阅读 / Reading",
        "",
        "这是匡子闲个人主页的阅读档案。",
        "",
        f"来源：{reading.get('source') or '微信读书'}。检索时间：{reading.get('retrieved_at')}（{reading.get('timezone') or 'Asia/Shanghai'}）。",
        "",
        reading.get("privacy_note") or "",
        "",
        "## 官方统计",
        "",
        "### 累计",
        "",
        f"- 阅读时长：{overall.get('total_read_time')}（{overall.get('total_read_time_sec')} 秒）",
        f"- 有效阅读天数：{fmt_int(overall.get('read_days') or 0)} 天",
        f"- 读过 / 读完：{overall.get('books_read')} 本 / {overall.get('books_finished')} 本",
        f"- 笔记：{fmt_int(overall.get('notes') or 0)} 条",
        f"- {overall.get('prefer_category_word') or ''}，{overall.get('prefer_time_word') or ''}",
        f"- 注册时间：{overall.get('registered_at')}",
    ]
    if overall.get("read_rate_percent") is not None:
        lines.append(f"- 阅读占比：{overall.get('read_rate_percent')}%")
    cats = prefer_categories(overall)
    if cats:
        lines += ["", "分类偏好：", ""] + cats
    lines += [
        "",
        "### 2026 年",
        "",
        f"- 阅读时长：{year.get('total_read_time')}",
        f"- 阅读天数：{year.get('read_days')} 天，日均 {year.get('day_average')}",
        f"- 读过 / 读完：{year.get('books_read')} 本 / {year.get('books_finished')} 本",
        f"- 笔记：{year.get('notes')} 条",
        f"- {year.get('prefer_category_word') or ''}",
    ]
    ycats = prefer_categories(year)
    if ycats:
        lines += ["", "分类偏好：", ""] + ycats
    lines += [
        "",
        "### 2026 年 11 月（截至检索日）",
        "",
        f"- 阅读时长：{month.get('total_read_time')}",
        f"- 阅读天数：{month.get('read_days')} 天，日均 {month.get('day_average')}",
        f"- 读过 / 读完：{month.get('books_read')} 本 / {month.get('books_finished')} 本",
        f"- 笔记：{month.get('notes')} 条",
        f"- {month.get('prefer_category_word') or ''}",
        "",
        "## 正在读",
        "",
    ]
    for book in reading.get("currently_reading") or []:
        meta = [book.get("author") or "", book.get("category") or "", progress_text(book)]
        if book.get("last_read"):
            meta.append(f"最近 {book['last_read']}")
        if book.get("reread"):
            meta.append("重读")
        if book.get("finish_date"):
            meta.append(f"曾读完于 {book['finish_date']}")
        meta_s = " · ".join(x for x in meta if x)
        lines.append(f"- {book_link(book.get('title') or '', book.get('readerLink'))} — {meta_s}")
    lines += ["", "## 公开书架上能核对到读完时间的书", ""]
    for book in reading.get("finished_on_public_shelf") or []:
        meta = [book.get("author") or "", book.get("category") or ""]
        if book.get("finish_date"):
            meta.append(f"读完 {book['finish_date']}")
        pt = progress_text(book)
        if pt:
            meta.append(pt)
        meta_s = " · ".join(x for x in meta if x)
        lines.append(f"- {book_link(book.get('title') or '', book.get('readerLink'))} — {meta_s}")
    lines += ["", "## 书简介", ""]
    for book in reading.get("featured_summaries") or []:
        lines.append(f"### {book_title(book.get('title') or '')}")
        bits = [book.get("author") or ""]
        if book.get("rating") is not None:
            bits.append(f"微信读书推荐值 {book['rating']}")
        if book.get("readerLink"):
            bits.append(f"[阅读链接]({book['readerLink']})")
        lines.append(" · ".join(x for x in bits if x))
        lines.append("")
        intro = book.get("intro") or book.get("intro_short") or ""
        if intro:
            lines.append(intro)
            lines.append("")
    lines += ["## 划线和想法", ""]
    for note in reading.get("curated_notes") or []:
        counts = []
        if note.get("note_count") is not None:
            counts.append(f"{note['note_count']} 条笔记")
        if note.get("underline_count") is not None:
            counts.append(f"{note['underline_count']} 条划线")
        if note.get("thought_count") is not None:
            counts.append(f"{note['thought_count']} 条想法")
        heading = book_link(note.get("title") or "", note.get("readerLink"))
        author = note.get("author") or ""
        extra = f" — {author}" if author else ""
        if counts:
            extra += f"（{'，'.join(counts)}）"
        lines.append(f"### {heading}{extra}")
        lines.append("")
        for item in note.get("items") or []:
            typ = item.get("type")
            text = (item.get("text") or "").strip()
            quote = (item.get("quote") or "").strip()
            if typ == "thought":
                if quote:
                    lines.append(f"> {quote}")
                    lines.append("")
                if text:
                    lines.append(f"想法：{text}")
                    lines.append("")
            else:
                if text:
                    lines.append(f"> {text}")
                    lines.append("")
    lines += [
        "## 公开书架",
        "",
        f"共 {shelf.get('books', 0)} 本书、{shelf.get('albums', 0)} 部有声书。",
        "",
    ]
    counts = shelf.get("category_counts") or {}
    if counts:
        lines.append("分类数量：")
        lines.append("")
        for cat, n in counts.items():
            lines.append(f"- {cat}：{n}")
        lines.append("")
    for item in shelf.get("items") or []:
        lines.append(shelf_line(item))
    notebooks = reading.get("notebooks") or {}
    if notebooks:
        lines += [
            "",
            "## 笔记范围说明",
            "",
            f"账号下有笔记的书共 {notebooks.get('total_books_with_notes')} 本，笔记合计 {notebooks.get('total_note_count')} 条（口径：{notebooks.get('note_count_formula')}）。公开书架上有笔记的书有 {notebooks.get('public_shelf_books_with_notes')} 本。本页划线只收录站点已整理的公开条目。",
            "",
        ]
    return "\n".join(lines)


def chat_body(chat: dict, loc: str = "zh") -> list[str]:
    lines: list[str] = []
    prompt = (i18n_lib.pick(chat, "prompt", loc) or "").strip()
    if prompt:
        kind = chat.get("prompt_kind") or "prompt"
        label = i18n_lib.t_ui("my_question" if kind == "question" else "my_prompt", loc)
        lines += [f"## {label}", "", prompt, ""]
    prompt_orig = (chat.get("prompt") or "").strip()
    messages = list(chat.get("messages") or [])
    if messages and messages[0].get("role") == "user" and prompt_orig and (messages[0].get("content") or "").strip() == prompt_orig:
        messages = messages[1:]
    if messages:
        heading = {"zh": "对话", "en": "Conversation", "es": "Conversación", "ko": "대화", "ja": "対話"}[loc]
        lines += [f"## {heading}", ""]
        for msg in messages:
            role = msg.get("role")
            name = msg.get("name") or ("GPT" if role == "assistant" else "匡子闲")
            lines.append(f"### {name}")
            lines.append("")
            lines.append((i18n_lib.pick(msg, "content", loc) or "").rstrip())
            lines.append("")
    return lines


def build_writing_md(chats: list[dict]) -> str:
    lines = [
        "# 文章 / Writing",
        "",
        "这里按技术文章的形式呈现匡子闲与 GPT 的对话。标题在列表里，点进去是完整问答。正文托管在本站。",
        "",
    ]
    for chat in chats:
        tags = ", ".join(chat.get("tags") or [])
        lines.append(f"## [{chat['title']}]({writing_html_url(chat['id'])})")
        lines.append("")
        meta = [chat.get("date") or ""]
        if chat.get("title_en"):
            meta.append(chat["title_en"])
        if tags:
            meta.append(tags)
        lines.append(" · ".join(x for x in meta if x))
        lines.append("")
        if chat.get("summary"):
            lines.append(chat["summary"])
            lines.append("")
        lines.append(f"HTML：[{writing_html_url(chat['id'])}]({writing_html_url(chat['id'])}) · Markdown：[writing/{chat['id']}.md]({writing_md_url(chat['id'])})")
        lines.append("")
    return "\n".join(lines)


def build_writing_post_md(chat: dict, loc: str = "zh") -> str:
    tags = ", ".join(i18n_lib.pick_list(chat, "tags", loc))
    title = i18n_lib.pick(chat, "title", loc) or chat.get("title") or ""
    blurb = {
        "zh": "匡子闲与 GPT 的对话。",
        "en": "A conversation between 匡子闲 and GPT.",
        "es": "Una conversación entre 匡子闲 y GPT.",
        "ko": "匡子闲과 GPT의 대화.",
        "ja": "匡子闲と GPT の対話。",
    }[loc]
    date_label = {"zh": "日期", "en": "Date", "es": "Fecha", "ko": "날짜", "ja": "日付"}[loc]
    tags_label = {"zh": "标签", "en": "Tags", "es": "Etiquetas", "ko": "태그", "ja": "タグ"}[loc]
    html_label = {"zh": "HTML 版本", "en": "HTML version", "es": "Versión HTML", "ko": "HTML 버전", "ja": "HTML 版"}[loc]
    lines = [
        f"# {title}",
        "",
        blurb,
        "",
    ]
    if loc == "zh" and chat.get("title_en"):
        lines += [chat["title_en"], ""]
    meta = [f"{date_label}：{chat.get('date') or ''}"]
    if tags:
        meta.append(f"{tags_label}：{tags}")
    lines.append(" · ".join(meta))
    lines.append("")
    summary = i18n_lib.pick(chat, "summary", loc)
    if summary:
        lines.append(summary)
        lines.append("")
    if loc == "zh" and chat.get("summary_en"):
        lines.append(chat["summary_en"])
        lines.append("")
    if loc != "zh":
        lines.append(i18n_lib.t_ui("original_conversation", loc) + f" [{i18n_lib.t_ui('original_link', loc)}]({writing_html_url(chat['id'])})")
        lines.append("")
    lines.append(f"{html_label}：[{writing_html_url(chat['id'], loc)}]({writing_html_url(chat['id'], loc)})")
    if chat.get("source_url"):
        share = {"zh": "原始分享链接", "en": "Original share link", "es": "Enlace original", "ko": "원래 공유 링크", "ja": "元の共有リンク"}[loc]
        lines.append(f"{share}：{chat['source_url']}")
    if chat.get("prompt_url"):
        plabel = {"zh": "Prompt 链接", "en": "Prompt link", "es": "Enlace del prompt", "ko": "프롬프트 링크", "ja": "プロンプトのリンク"}[loc]
        lines.append(f"{plabel}：{chat['prompt_url']}")
    lines.append("")
    lines += chat_body(chat, loc)
    return "\n".join(lines)


def build_llms_full(profile: dict, reading: dict, chats: list[dict], sites: dict | None = None) -> str:
    bio = profile.get("bio") or {}
    lines = [
        "# 匡子闲 full agent context",
        "",
        f"这是匡子闲（{profile.get('latin_handle') or 'kuangzixian'}）个人主页的完整机器可读版本，供 AI agent 使用。站点地址：{SITE}/",
        "",
        "## 身份 / Profile",
        "",
        bio["combined_zh"],
        "",
        f"- 姓名：匡子闲",
        f"- 拉丁名 / handle：{profile.get('latin_handle') or 'kuangzixian'}",
        f"- 职业：{bio.get('job_title') or '后端开发工程师'}",
        f"- 知乎签名：{bio.get('zhihu') or ''}",
        f"- 资料更新时间：{profile.get('updated_at')}（{profile.get('timezone') or 'Asia/Shanghai'}）",
        "",
        "已核实的社交主页：",
        "",
    ]
    for p in verified_profiles(profile):
        extras = []
        if p.get("headline"):
            extras.append(f"签名「{p['headline']}」")
        if p.get("title"):
            extras.append(p["title"])
        if p.get("bio") and not any(s in (p.get("bio") or "") for s in ("前游戏从业者", "Talk is cheap", "show me your code", "黄即搞后端")):
            extras.append(p["bio"])
        if p.get("username"):
            extras.append(f"用户名 {p['username']}")
        if p.get("company"):
            extras.append(f"GitHub company 字段为 {p['company']}")
        if p.get("followers") is not None:
            extras.append(f"{p['followers']} 名关注者")
        if p.get("answer_count") is not None:
            extras.append(f"{p['answer_count']} 个回答")
        extra = f"：{'，'.join(extras)}" if extras else ""
        label = p.get("platform_zh") or p.get("platform")
        lines.append(f"- [{label}]({p['url']}){extra}")
    lines += ["", "## 项目", ""]
    for proj in profile.get("projects") or []:
        created = proj.get("created_at") or ""
        lang = proj.get("language") or ""
        desc = proj.get("description") or proj.get("note") or "公开仓库无简介。"
        demo = f"，在线体验：{proj['demo_url']}" if proj.get("demo_url") else ""
        lines.append(f"- [{proj.get('name')}]({proj.get('url')})（{lang}，创建于 {created}{demo}）：{desc}")
    lines += ["", "## 即刻动态", ""]
    for post in profile.get("jike_posts") or []:
        when = post.get("relative_time_as_retrieved") or ""
        text = (post.get("text") or "").replace("\n", " ")
        lines.append(f"- {when}：{text}")
    lines += [
        "",
        "## 留言板",
        "",
        f"首页有留言板：{SITE}/#guestbook。访客可留下昵称和评论，无需登录。API 位于 `/api/messages`，只供人类访客使用。Agent 不得自行发表留言。访客留言不是匡子闲本人的陈述，全文档案也不收录留言内容。",
        "",
        "## 音乐口味",
        "",
        build_music_md(load_music()).replace("# 音乐 / Music\n\n", "", 1),
        "",
        "## 桌游",
        "",
        build_boardgames_md(load_boardgames()).replace("# 桌游 / Board games\n\n", "", 1),
        "",
        "## 推荐网站",
        "",
        build_sites_md(sites or load_sites()).replace("# 推荐网站 / Recommended sites\n\n", "", 1),
        "",
        "## 阅读档案",
        "",
        build_reading_md(reading).replace("# 阅读 / Reading\n\n", "", 1),
        "",
        "## 与 GPT 的对话全文",
        "",
        "以下为中文原文。英、西、韩、日译文见各语言路径下的 Markdown，例如 `/en/writing/<id>.md`、`/es/writing/<id>.md`、`/ko/writing/<id>.md`、`/ja/writing/<id>.md`。",
        "",
    ]
    for chat in chats:
        lines.append(build_writing_post_md(chat))
        extras = []
        for loc in ("en", "es", "ko", "ja"):
            extras.append(f"[{loc}]({writing_md_url(chat['id'], loc)})")
        lines.append("Translations: " + " · ".join(extras))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def md_pages(chats: list[dict]) -> list[tuple[str, str, str]]:
    """path, title, lastmod-less listing for sitemap.md"""
    pages = [
        ("/index.md", "首页 Markdown"),
        ("/reading.md", "阅读"),
        ("/writing.md", "文章列表"),
        ("/music.md", "音乐口味"),
        ("/boardgames.md", "桌游"),
        ("/sites.md", "推荐网站"),
    ]
    for chat in chats:
        pages.append((f"/writing/{chat['id']}", chat["title"]))
        pages.append((f"/writing/{chat['id']}.md", chat["title"] + "（Markdown）"))
    pages += [
        ("/llms.txt", "llms.txt"),
        ("/llms-full.txt", "llms-full.txt"),
        ("/sitemap.md", "Markdown sitemap"),
        ("/sitemap.xml", "XML sitemap"),
    ]
    return pages


def build_sitemap_md(chats: list[dict]) -> str:
    lines = [
        "# Sitemap",
        "",
        "匡子闲个人主页的 Markdown 与机器可读页面。",
        "",
        "## HTML",
        "",
        f"- [首页]({SITE}/)",
        f"- [English]({SITE}/en/)",
        f"- [Español]({SITE}/es/)",
        f"- [한국어]({SITE}/ko/)",
        f"- [日本語]({SITE}/ja/)",
        f"- [Agent 视图]({SITE}/?mode=agent)（重定向到 /index.md）",
    ]
    for chat in chats:
        lines.append(f"- [{chat['title']}]({writing_html_url(chat['id'])})")
        for loc in ("en", "es", "ko", "ja"):
            lines.append(f"- [{chat['title']}]({SITE}/{loc}/writing/{chat['id']})（{loc}）")
    lines += [f"- [留言板]({SITE}/#guestbook)", f"- [音乐]({SITE}/#music)", f"- [音乐完整报告]({SITE}/music/report)", f"- [桌游]({SITE}/#boardgames)", f"- [推荐网站]({SITE}/#sites)", "", "## Markdown 与文本", ""]
    for path, title in [
        ("/index.md", "首页"),
        ("/reading.md", "阅读"),
        ("/writing.md", "文章列表"),
        ("/music.md", "音乐口味"),
        ("/boardgames.md", "桌游"),
        ("/sites.md", "推荐网站"),
    ]:
        lines.append(f"- [{title}]({SITE}{path})")
    for chat in chats:
        lines.append(f"- [{chat['title']}（Markdown）]({writing_md_url(chat['id'])})")
    lines += [
        f"- [llms.txt]({SITE}/llms.txt)",
        f"- [llms-full.txt]({SITE}/llms-full.txt)",
        f"- [robots.txt]({SITE}/robots.txt)",
        f"- [sitemap.xml]({SITE}/sitemap.xml)",
        "",
        "## JSON",
        "",
        f"- [profile.json]({SITE}/data/profile.json)",
        f"- [reading.json]({SITE}/data/reading.json)",
        f"- [chats.json]({SITE}/data/chats.json)",
        f"- [music.json]({SITE}/data/music.json)",
        f"- [boardgames.json]({SITE}/data/boardgames.json)",
        f"- [sites.json]({SITE}/data/sites.json)",
        "",
    ]
    return "\n".join(lines)


def build_sitemap_xml(profile: dict, reading: dict, chats: list[dict], music: dict | None = None, boardgames: dict | None = None, sites: dict | None = None) -> str:
    home_last = latest_dates(profile, reading, chats, music, boardgames, sites)
    reading_last = iso_date(reading.get("retrieved_at")) or home_last
    urls: list[tuple[str, str, str]] = [
        (f"{SITE}/index.md", home_last, "weekly"),
        (f"{SITE}/reading.md", reading_last, "weekly"),
        (f"{SITE}/writing.md", home_last, "weekly"),
        (f"{SITE}/music.md", home_last, "weekly"),
        (f"{SITE}/music/report", home_last, "weekly"),
        (f"{SITE}/boardgames.md", home_last, "weekly"),
        (f"{SITE}/sites.md", home_last, "weekly"),
        (f"{SITE}/llms.txt", home_last, "weekly"),
        (f"{SITE}/llms-full.txt", home_last, "weekly"),
        (f"{SITE}/sitemap.md", home_last, "weekly"),
    ]
    for chat in chats:
        last = iso_date(chat.get("date") or chat.get("datetime")) or home_last
        urls.append((f"{SITE}/writing/{chat['id']}.md", last, "monthly"))
        for loc in ("en", "es", "ko", "ja"):
            urls.append((writing_md_url(chat["id"], loc), last, "monthly"))
    # Language-specific HTML pages with hreflang alternates.
    alt_paths: list[tuple[str, str, str]] = [
        ("/", home_last, "weekly"),
    ]
    for chat in chats:
        last = iso_date(chat.get("date") or chat.get("datetime")) or home_last
        alt_paths.append((f"/writing/{chat['id']}", last, "monthly"))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for path, lastmod, freq in alt_paths:
        for loc in I18N_LOCALES:
            parts += [
                "  <url>",
                f"    <loc>{xml_escape(locale_page_url(path, loc))}</loc>",
                *xhtml_links(path),
                f"    <lastmod>{xml_escape(lastmod)}</lastmod>",
                f"    <changefreq>{freq}</changefreq>",
                "  </url>",
            ]
    for loc, lastmod, freq in urls:
        parts += [
            "  <url>",
            f"    <loc>{xml_escape(loc)}</loc>",
            f"    <lastmod>{xml_escape(lastmod)}</lastmod>",
            f"    <changefreq>{freq}</changefreq>",
            "  </url>",
        ]
    parts.append("</urlset>")
    parts.append("")
    return "\n".join(parts)


def build_robots() -> str:
    return (
        "User-agent: *\n"
        "Content-Signal: search=yes, ai-input=yes, ai-train=no\n"
        "Allow: /\n"
        "\n"
        "User-agent: OAI-SearchBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: GPTBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: ChatGPT-User\n"
        "Allow: /\n"
        "\n"
        "User-agent: ClaudeBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: Google-Extended\n"
        "Allow: /\n"
        "\n"
        "User-agent: DeepSeekBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: Qwen-Agent\n"
        "Allow: /\n"
        "\n"
        "User-agent: CCBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: Bytespider\n"
        "Disallow: /\n"
        "\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )


def write_ai_files(dest: Path) -> None:
    profile = load_json("profile.json")
    reading = load_json("reading.json")
    chats_data = load_json("chats.json")
    chats = list(chats_data.get("chats") or chats_data if isinstance(chats_data, list) else chats_data.get("chats") or [])
    sites = load_sites()
    music = load_music()
    boardgames = load_boardgames()

    dest.mkdir(parents=True, exist_ok=True)
    write_text(dest / "llms.txt", build_llms_txt(profile, reading, chats, sites))
    write_text(dest / "llms-full.txt", build_llms_full(profile, reading, chats, sites))
    write_text(dest / "index.md", build_index_md(profile, reading, chats, sites))
    write_text(dest / "reading.md", build_reading_md(reading))
    write_text(dest / "writing.md", build_writing_md(chats))
    write_text(dest / "music.md", build_music_md(music))
    write_text(dest / "boardgames.md", build_boardgames_md(boardgames))
    write_text(dest / "sites.md", build_sites_md(sites))
    for chat in chats:
        write_text(dest / "writing" / f"{chat['id']}.md", build_writing_post_md(chat))
        for loc in ("en", "es", "ko", "ja"):
            folder = dest / loc / "writing"
            folder.mkdir(parents=True, exist_ok=True)
            write_text(folder / f"{chat['id']}.md", build_writing_post_md(chat, loc))
    write_text(dest / "sitemap.md", build_sitemap_md(chats))
    write_text(dest / "sitemap.xml", build_sitemap_xml(profile, reading, chats, music, boardgames, sites))
    write_text(dest / "robots.txt", build_robots())


def main() -> None:
    dest = ROOT / "dist"
    write_ai_files(dest)
    print(f"Wrote AI-friendly files to {dest}")


if __name__ == "__main__":
    main()
