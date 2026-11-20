#!/usr/bin/env python3
"""Build static HTML: per-post writing pages, inject lists into index, write 404."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md import escape_html, render_markdown
import i18n_lib

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://kuangzixian.pages.dev"
PERSON_ID = f"{SITE}/#person"
AVATAR = f"{SITE}/images/avatar.jpg"


def load_json(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def writing_url(chat_id: str) -> str:
    return f"{SITE}/writing/{chat_id}"


def attr(s: object) -> str:
    return escape_html("" if s is None else str(s))


def replace_inner_by_id(html: str, elem_id: str, new_inner: str) -> str:
    start_re = re.compile(
        rf"<(div|section|article|nav|main|ul|ol)(\s[^>]*?\sid=[\"']{re.escape(elem_id)}[\"'][^>]*)>",
        re.I | re.S,
    )
    m = start_re.search(html)
    if not m:
        raise ValueError(f"element #{elem_id} not found")
    tag = m.group(1).lower()
    open_re = re.compile(rf"<{tag}\b", re.I)
    close_re = re.compile(rf"</{tag}\s*>", re.I)
    pos = m.end()
    depth = 1
    while pos < len(html) and depth:
        open_m = open_re.search(html, pos)
        close_m = close_re.search(html, pos)
        if not close_m:
            raise ValueError(f"unclosed #{elem_id}")
        if open_m and open_m.start() < close_m.start():
            depth += 1
            pos = open_m.end()
            continue
        depth -= 1
        if depth == 0:
            return html[: m.end()] + "\n        " + new_inner.strip() + "\n      " + html[close_m.start() :]
        pos = close_m.end()
    raise ValueError(f"unclosed #{elem_id}")


def tags_html(tags: list | None) -> str:
    if not tags:
        return ""
    inner = "".join(f'<span class="pill">{escape_html(t)}</span>' for t in tags)
    return f'<div class="article-tags">{inner}</div>'


def site_card_html(site: dict, loc: str = "zh") -> str:
    url = site.get("url") or site.get("canonical") or ""
    name = site.get("name") or i18n_lib.pick(site, "title", loc) or url
    domain = site.get("domain") or ""
    desc = i18n_lib.pick(site, "description", loc)
    own_class = " is-own" if site.get("own") else ""
    emoji = site.get("emoji") or "🌐"
    alt = i18n_lib.pick(site, "image_alt", loc) or name
    src = site.get("image") or site.get("favicon") or ""
    if src and not src.startswith(("http://", "https://", "/")):
        src = "/" + src
    if src:
        icon = (
            '<span class="site-icon-wrap">'
            f'<img class="site-icon" src="{attr(src)}" alt="{attr(alt)}" width="56" height="56" loading="lazy" '
            'onerror="this.hidden=true;var f=this.nextElementSibling;if(f)f.hidden=false;">'
            f'<span class="site-fallback" hidden aria-hidden="true">{escape_html(emoji)}</span>'
            "</span>"
        )
    else:
        icon = f'<span class="site-fallback" aria-hidden="true">{escape_html(emoji)}</span>'
    badge = ""
    if site.get("own"):
        badge = (
            '<span class="site-badge">'
            '<span class="zh">自己做的</span>'
            '<span class="en-only">Made by me</span>'
            "</span>"
        )
    domain_html = f'<span class="site-domain">{escape_html(domain)}</span>' if domain else ""
    desc_html = f'<span class="site-desc">{escape_html(desc)}</span>' if desc else ""
    return (
        f'<a class="card site-card{own_class}" href="{attr(url)}" target="_blank" rel="noopener noreferrer">'
        f"{icon}"
        '<span class="site-body">'
        f'<span class="site-head"><strong class="site-name">{escape_html(name)}</strong>{badge}</span>'
        f"{domain_html}{desc_html}"
        "</span>"
        "</a>"
    )


def sites_list_html(sites_data: dict, loc: str = "zh") -> str:
    return "\n        ".join(site_card_html(s, loc) for s in (sites_data.get("sites") or []))


def writing_card_html(chat: dict, loc: str = "zh") -> str:
    href = i18n_lib.localize_path(f"/writing/{chat.get('id') or ''}", loc)
    title = escape_html(i18n_lib.pick(chat, "title", loc))
    summary = escape_html(i18n_lib.pick(chat, "summary", loc))
    date = chat.get("date") or ""
    date_label = i18n_lib.format_date(date, loc) if date else ""
    time_html = f'<time datetime="{escape_html(date)}">{escape_html(date_label)}</time>' if date else ""
    return (
        f'<a class="card article" href="{href}">'
        f'<div class="meta"><span class="zh">对话</span><span class="en-only">Conversation</span>{time_html}</div>'
        f"<h3>{title}</h3>"
        f"<p>{summary}</p>"
        f"{tags_html(i18n_lib.pick_list(chat, 'tags', loc))}"
        "</a>"
    )


def writing_list_html(chats: list[dict], loc: str = "zh") -> str:
    return "\n        ".join(writing_card_html(c, loc) for c in chats)


def boardgame_card_html(game: dict, loc: str = "zh") -> str:
    gid = game.get("id") or ""
    emoji = game.get("emoji") or "🎲"
    name = i18n_lib.pick(game, "name", loc)
    name_zh = game.get("name_zh") or ""
    blurb = i18n_lib.pick(game, "blurb", loc)
    aka = ""
    if loc == "zh":
        name_en = game.get("name_en") or ""
        if name_en and name_zh and name_en != name_zh:
            aka = f'<p class="bgame-aka">{escape_html(name_en)}</p>'
    elif name_zh and name and name_zh != name:
        aka = f'<p class="bgame-aka">{escape_html(name_zh)}</p>'
    desc = f'<p class="bgame-desc">{escape_html(blurb)}</p>' if blurb else ""
    return (
        f'<article class="card bgame-card" data-game="{attr(gid)}">'
        f'<span class="bgame-icon" data-game="{attr(gid)}" aria-hidden="true">{escape_html(emoji)}</span>'
        '<div class="bgame-body">'
        f'<h3 class="bgame-name">{escape_html(name)}</h3>'
        f"{aka}{desc}"
        "</div>"
        "</article>"
    )


def boardgames_list_html(data: dict, loc: str = "zh") -> str:
    return "\n        ".join(boardgame_card_html(g, loc) for g in (data.get("games") or []))


def visible_messages(chat: dict) -> list[dict]:
    prompt = (chat.get("prompt") or "").strip()
    messages = list(chat.get("messages") or [])
    if (
        messages
        and messages[0].get("role") == "user"
        and prompt
        and (messages[0].get("content") or "").strip() == prompt
    ):
        return messages[1:]
    return messages


def role_label(msg: dict) -> tuple[str, str, str]:
    if msg.get("role") == "assistant":
        name = msg.get("name") or "GPT"
        return name, name, "is-assistant"
    name = msg.get("name") or "匡子闲"
    return name, name, "is-user"


def prompt_text(chat: dict, loc: str = "zh") -> str:
    return i18n_lib.pick(chat, "prompt", loc)


def prompt_block_html(chat: dict, loc: str = "zh") -> str:
    prompt = prompt_text(chat, loc)
    if not prompt:
        return ""
    kind = chat.get("prompt_kind") or "prompt"
    key = "my_question" if kind == "question" else "my_prompt"
    # Fall back to the zh/en pair labels if ui keys are absent; use known UI keys via i18n.js names in catalog if present.
    label = i18n_lib.t_ui("my_question" if kind == "question" else "my_prompt", loc)
    return (
        '<aside class="prompt-block">'
        f'<p class="prompt-kicker">{escape_html(label)}</p>'
        f'<div class="prompt-body">{render_markdown(prompt)}</div>'
        "</aside>"
    )


def thread_html(chat: dict, loc: str = "zh") -> str:
    parts = []
    for msg in visible_messages(chat):
        zh, en, cls = role_label(msg)
        name = zh
        content = i18n_lib.pick(msg, "content", loc)
        parts.append(
            f'<section class="turn {cls}">'
            f'<p class="turn-role">{escape_html(name)}</p>'
            f'<div class="turn-body md">{render_markdown(content)}</div>'
            "</section>"
        )
    return "".join(parts)


def sources_html(chat: dict, loc: str = "zh") -> str:
    sources = []
    if chat.get("source_url"):
        sources.append(
            f'<a href="{attr(chat["source_url"])}" rel="noopener noreferrer">'
            f'{escape_html(i18n_lib.t_ui("source_chat", loc))}'
            "</a>"
        )
    if chat.get("prompt_url"):
        sources.append(
            f'<a href="{attr(chat["prompt_url"])}" rel="noopener noreferrer">'
            f'{escape_html(i18n_lib.t_ui("source_prompt", loc))}'
            "</a>"
        )
    if not sources:
        return ""
    return '<p class="post-source">' + " · ".join(sources) + "</p>"


def original_note_html(chat: dict, loc: str) -> str:
    if loc == "zh":
        return ""
    href = i18n_lib.localize_path(f"/writing/{chat.get('id') or ''}", "zh")
    note = i18n_lib.t_ui("original_conversation", loc)
    link = i18n_lib.t_ui("original_link", loc)
    return (
        f'<p class="post-original-note">{escape_html(note)} '
        f'<a href="{attr(href)}">{escape_html(link)}</a></p>'
    )


def article_html(chat: dict, loc: str = "zh") -> str:
    date = chat.get("date") or ""
    title = i18n_lib.pick(chat, "title", loc) or chat.get("title") or ""
    date_label = i18n_lib.format_date(date, loc) if date else ""
    time_html = f'<time datetime="{attr(date)}">{escape_html(date_label)}</time>' if date else ""
    kicker = i18n_lib.t_ui("writing_kicker", loc)
    with_gpt = i18n_lib.t_ui("with_gpt", loc)
    back = i18n_lib.t_ui("back_writing", loc)
    return (
        f'<p class="post-back"><a href="/#writing">{escape_html(back)}</a></p>'
        '<header class="post-head">'
        f'<p class="kicker">{escape_html(kicker)}</p>'
        f"<h1>{escape_html(title)}</h1>"
        '<div class="meta">'
        f"{time_html}"
        f"<span>{escape_html(with_gpt)}</span>"
        "</div>"
        f"{tags_html(i18n_lib.pick_list(chat, 'tags', loc))}"
        "</header>"
        f"{original_note_html(chat, loc)}"
        f"{prompt_block_html(chat, loc)}"
        f'<div class="thread">{thread_html(chat, loc)}</div>'
        f"{sources_html(chat, loc)}"
    )


def json_ld(chat: dict, loc: str = "zh") -> str:
    title = i18n_lib.pick(chat, "title", loc) or chat.get("title") or ""
    summary = i18n_lib.pick(chat, "summary", loc) or title
    url = i18n_lib.abs_url(f"/writing/{chat['id']}", loc)
    published = chat.get("datetime") or chat.get("date") or ""
    comments = []
    if chat.get("prompt"):
        comments.append(
            {
                "@type": "Comment",
                "author": {"@type": "Person", "name": "匡子闲", "@id": PERSON_ID},
                "text": i18n_lib.pick(chat, "prompt", loc) or chat.get("prompt") or "",
            }
        )
    for msg in visible_messages(chat):
        if msg.get("role") == "assistant":
            author: dict = {"@type": "Organization", "name": msg.get("name") or "GPT"}
        else:
            author = {"@type": "Person", "name": msg.get("name") or "匡子闲", "@id": PERSON_ID}
        comments.append({"@type": "Comment", "author": author, "text": i18n_lib.pick(msg, "content", loc) or ""})
    data = {
        "@context": "https://schema.org",
        "@type": "DiscussionForumPosting",
        "headline": title,
        "alternativeHeadline": chat.get("title_en") or chat.get("title") or title,
        "description": summary,
        "url": url,
        "mainEntityOfPage": url,
        "image": AVATAR,
        "datePublished": published,
        "inLanguage": i18n_lib.locales()[loc]["html_lang"],
        "author": {"@type": "Person", "name": "匡子闲", "alternateName": "kuangzixian", "@id": PERSON_ID, "url": f"{SITE}/"},
        "publisher": {"@type": "Person", "name": "匡子闲", "@id": PERSON_ID},
        "text": summary,
        "comment": comments,
    }
    if chat.get("source_url"):
        data["sameAs"] = [chat["source_url"]]
    return json.dumps(data, ensure_ascii=False, indent=2)


def skin_boot_script() -> str:
    return i18n_lib.BOOT_SCRIPT


def topbar_html(*, back_href: str = "/#writing", back_zh: str = "返回日志", back_en: str = "Back to logs") -> str:
    return f"""  <a class="skip" href="#main"><span class="zh">跳到正文</span><span class="en-only">Skip to content</span></a>
  <div class="qz-topbar">
    <div class="qz-topbar-inner">
      <a class="qz-top-name" href="/">匡子闲的空间</a>
      <a href="{attr(back_href)}"><span class="zh">{escape_html(back_zh)}</span><span class="en-only">{escape_html(back_en)}</span></a>
      <div class="qz-top-actions">
        <button type="button" id="qzSnowBtn" class="qz-snow-btn" aria-pressed="true" title="飘雪特效" aria-label="飘雪特效：开">❄</button>
        <div class="qz-desktop-tools">
          <button type="button" class="qz-skin-dot" data-skin-set="blue" title="晴空蓝" aria-label="晴空蓝皮肤"></button>
          <button type="button" class="qz-skin-dot" data-skin-set="pink" title="粉钻粉" aria-label="粉钻粉皮肤"></button>
          <button type="button" class="qz-skin-dot" data-skin-set="night" title="夜空" aria-label="夜空皮肤"></button>
        </div>
        <div class="qz-lang-slot" data-lang-slot="top"></div>
        <div class="qz-menu">
          <button type="button" id="qzMenuBtn" class="qz-menu-btn" aria-expanded="false" aria-controls="qzMenuPanel">
            <span class="zh">设置</span><span class="en-only">Menu</span>
          </button>
          <div id="qzMenuPanel" class="qz-menu-panel" hidden>
            <p class="qz-menu-label"><span class="zh">皮肤</span><span class="en-only">Skin</span></p>
            <div class="qz-skin-row">
              <button type="button" class="qz-skin-choice" data-skin-set="blue">晴空蓝</button>
              <button type="button" class="qz-skin-choice" data-skin-set="pink">粉钻粉</button>
              <button type="button" class="qz-skin-choice" data-skin-set="night">夜空</button>
            </div>
            <button type="button" id="qzSnowToggle" class="qz-snow-toggle" aria-pressed="true">
              <span class="zh">飘雪特效：开</span><span class="en-only">Snow: On</span>
            </button>
            <div data-lang-slot="menu"></div>
          </div>
        </div>
      </div>
    </div>
  </div>"""


def banner_html(sign_zh: str, sign_en: str) -> str:
    return f"""  <div class="qz-banner" id="top">
    <span class="qz-cloud"></span>
    <span class="qz-cloud"></span>
    <span class="qz-cloud"></span>
    <span class="qz-sun" aria-hidden="true"></span>
    <div class="qz-banner-text">
      <p class="qz-space-name">匡子闲的空间</p>
      <p class="qz-sign zh">{escape_html(sign_zh)}</p>
      <p class="qz-sign en-only">{escape_html(sign_en)}</p>
    </div>
  </div>"""


def tabs_html(current: str) -> str:
    items = [
        ("home", "/#home", "主页", "Home"),
        ("writing", "/#writing", "日志", "Logs"),
        ("reading", "/#reading", "读书", "Reading"),
        ("music", "/#music", "音乐", "Music"),
        ("boardgames", "/#boardgames", "桌游", "Games"),
        ("sites", "/#sites", "推荐网站", "Sites"),
        ("guestbook", "/#guestbook", "留言板", "Guestbook"),
        ("profile", "/#profile", "个人档", "Profile"),
    ]
    links = []
    for key, href, zh, en in items:
        on = ' class="qz-tab is-on" aria-current="page"' if key == current else ' class="qz-tab"'
        links.append(
            f'<a{on} href="{href}"><span class="zh">{zh}</span><span class="en-only">{en}</span></a>'
        )
    return '      <nav class="qz-tabs" aria-label="空间栏目">\n        ' + "\n        ".join(links) + "\n      </nav>"


def page_scripts(*extra: str) -> str:
    srcs = ["/js/i18n.js", "/js/main.js", "/js/qzone.js", "/js/snow.js", "/js/visits.js", *extra]
    return "\n".join(f'  <script src="{s}"></script>' for s in srcs)



def build_chat_page(chat: dict, loc: str = "zh") -> str:
    title = i18n_lib.pick(chat, "title", loc) or chat.get("title") or ""
    desc = i18n_lib.pick(chat, "summary", loc) or title
    full_title = f"{title} · 匡子闲"
    url = i18n_lib.abs_url(f"/writing/{chat['id']}", loc)
    date = chat.get("date") or ""
    published = chat.get("datetime") or date
    md_href = f"/writing/{chat['id']}.md"
    published_meta = (
        f'  <meta property="article:published_time" content="{attr(published)}">\n' if published else ""
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape_html(full_title)}</title>
  <meta name="description" content="{attr(desc)}">
  <meta name="author" content="匡子闲">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="匡子闲的空间">
  <meta property="og:title" content="{attr(full_title)}">
  <meta property="og:description" content="{attr(desc)}">
  <meta property="og:url" content="{attr(url)}">
  <meta property="og:image" content="{AVATAR}">
  <meta property="og:image:alt" content="匡子闲">
  <meta property="og:locale" content="zh_CN">
{published_meta}  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{attr(full_title)}">
  <meta name="twitter:description" content="{attr(desc)}">
  <meta name="twitter:image" content="{AVATAR}">
  <meta name="twitter:image:alt" content="匡子闲">
  <meta name="theme-color" content="#4a9de0" id="themeColor">
{skin_boot_script()}
  <link rel="icon" href="/images/avatar.jpg" type="image/jpeg">
  <link rel="canonical" href="{attr(url)}">
  <link rel="alternate" type="text/markdown" href="{attr(md_href)}" title="Markdown" id="mdAlternate">
  <link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="stylesheet" href="/css/qzone.css">
  <script type="application/ld+json">
{json_ld(chat, loc)}
  </script>
</head>
<body class="qzone-body chat-page">
{topbar_html()}
{banner_html("日志", "Diary / Logs")}

  <div class="qz-shell">
    <div class="qz-content">
{tabs_html("writing")}
      <main id="main" class="qz-main post-wrap">
        <p class="qz-log-kicker"><span class="zh">日志</span><span class="en-only">Log</span></p>
    <article id="chatPost" data-chat-id="{attr(chat.get('id') or '')}" data-rendered="static">
      {article_html(chat, loc)}
    </article>
      </main>
    </div>
  </div>

  <footer class="site-footer">
    <div class="wrap">
      <p>{escape_html(i18n_lib.t_ui("footer_chat", loc))}</p>
      <p><a href="/">{escape_html(i18n_lib.t_ui("home_link", loc))}</a> · <a href="/#writing">{escape_html(i18n_lib.t_ui("writing", loc))}</a> · <a href="/data/chats.json">chats.json</a> · <a href="{attr(md_href)}">Markdown</a></p>
      <p><a href="/llms.txt">For AI agents: llms.txt</a></p>
    </div>
  </footer>
  <div class="cursor-glow" id="cursorGlow" aria-hidden="true"></div>
{page_scripts("/js/markdown.js", "/js/chat.js")}
</body>
</html>
"""
    return i18n_lib.localize_document(
        html,
        loc,
        path=f"/writing/{chat['id']}",
        title=full_title,
        desc=desc,
    )


def build_404_page(loc: str = "zh") -> str:
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>页面不存在 · 匡子闲</title>
  <meta name="description" content="这个地址在匡子闲的空间里找不到对应页面。">
  <meta name="robots" content="noindex">
  <meta name="theme-color" content="#4a9de0" id="themeColor">
{skin_boot_script()}
  <link rel="icon" href="/images/avatar.jpg" type="image/jpeg">
  <link rel="stylesheet" href="/css/style.css">
  <link rel="stylesheet" href="/css/qzone.css">
</head>
<body class="qzone-body">
{topbar_html(back_href="/", back_zh="返回首页", back_en="Back home")}
{banner_html("走丢了", "Page not found")}

  <div class="qz-shell">
    <div class="qz-content">
{tabs_html("")}
      <main id="main" class="qz-main">
        <section class="qz-404">
          <p class="qz-404-code">404</p>
          <h1 class="qz-404-title"><span class="zh">空间里没有这个页面</span><span class="en-only">This page isn’t in the zone.</span></h1>
          <p class="lede zh">这个地址没有对应的内容。可能是链接写错了，或页面已经换了地方。</p>
          <p class="lede en-only">Nothing lives at this address. The link may be mistyped, or the page has moved.</p>
          <p class="qz-404-actions">
            <a class="play-btn" href="/"><span class="zh">回到首页</span><span class="en-only">Back to home</span></a>
            <a class="play-btn" href="/#writing"><span class="zh">去看日志</span><span class="en-only">Read the logs</span></a>
          </p>
        </section>
      </main>
    </div>
  </div>

  <footer class="site-footer">
    <div class="wrap">
      <p>{escape_html(i18n_lib.t_ui("site_name", loc))}</p>
      <p><a href="/">{escape_html(i18n_lib.t_ui("home_link", loc))}</a> · <a href="/llms.txt">{escape_html(i18n_lib.t_ui("ai_agents", loc))}</a></p>
    </div>
  </footer>
  <div class="cursor-glow" id="cursorGlow" aria-hidden="true"></div>
{page_scripts()}
</body>
</html>
"""
    return i18n_lib.localize_document(
        html,
        loc,
        path="/404",
        title=i18n_lib.t_ui("not_found_code_title", loc),
        desc=i18n_lib.t_ui("not_found_desc", loc),
    )


def patch_index(html: str, *, chats: list[dict], sites: dict, boardgames: dict, loc: str = "zh") -> str:
    html = html.replace("<h1 class=\"qz-space-name\">匡子闲的空间</h1>", '<p class="qz-space-name">匡子闲的空间</p>')
    html = html.replace('href="music/report.html"', 'href="/music/report"')
    html = html.replace('href="chat.html?id=', 'href="/writing/')
    html = replace_inner_by_id(html, "qzSitesList", sites_list_html(sites, loc))
    html = replace_inner_by_id(html, "writingList", writing_list_html(chats, loc))
    html = replace_inner_by_id(html, "qzBoardgamesList", boardgames_list_html(boardgames, loc))

    def set_intro(html: str, zh_id: str, en_id: str, data: dict, prefix: str) -> str:
        zh = data.get(f"{prefix}zh") or data.get("intro_zh")
        en = data.get(f"{prefix}en") or data.get("intro_en")
        # keep both so localize_pairs can translate via catalog / locale field
        loc_text = data.get("intro_zh" if loc == "zh" else f"intro_{loc}") or en or zh
        if zh:
            html = re.sub(
                rf'(<p class="lede zh" id="{zh_id}">)(.*?)(</p>)',
                lambda m, text=zh: m.group(1) + escape_html(text) + m.group(3),
                html,
                count=1,
                flags=re.S,
            )
        if en:
            html = re.sub(
                rf'(<p class="lede en-only" id="{en_id}">)(.*?)(</p>)',
                lambda m, text=en: m.group(1) + escape_html(text) + m.group(3),
                html,
                count=1,
                flags=re.S,
            )
        return html

    html = set_intro(html, "qzSitesIntroZh", "qzSitesIntroEn", sites, "intro_")
    html = set_intro(html, "qzBoardgamesIntroZh", "qzBoardgamesIntroEn", boardgames, "intro_")
    html = i18n_lib.localize_document(html, loc, path="/")
    return html


def write_pages(dest: Path) -> None:
    chats_data = load_json("chats.json")
    chats = list(chats_data.get("chats") or [])
    sites = load_json("sites.json")
    boardgames = load_json("boardgames.json")

    raw_index = (dest / "index.html").read_text(encoding="utf-8")

    for loc in i18n_lib.ORDER:
        html = patch_index(raw_index, chats=chats, sites=sites, boardgames=boardgames, loc=loc)
        if loc == "zh":
            (dest / "index.html").write_text(html, encoding="utf-8")
        else:
            folder = dest / loc
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(html, encoding="utf-8")

        writing_dir = dest / "writing" if loc == "zh" else dest / loc / "writing"
        writing_dir.mkdir(parents=True, exist_ok=True)
        for chat in chats:
            chat_id = chat.get("id")
            if not chat_id:
                continue
            (writing_dir / f"{chat_id}.html").write_text(build_chat_page(chat, loc), encoding="utf-8")

        if loc == "zh":
            (dest / "404.html").write_text(build_404_page(loc), encoding="utf-8")
        else:
            (dest / loc / "404.html").write_text(build_404_page(loc), encoding="utf-8")


if __name__ == "__main__":
    write_pages(ROOT / "dist")
