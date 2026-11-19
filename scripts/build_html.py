#!/usr/bin/env python3
"""Build static HTML: per-post writing pages, inject lists into index, write 404."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md import escape_html, render_markdown

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


def site_card_html(site: dict) -> str:
    url = site.get("url") or site.get("canonical") or ""
    name = site.get("name") or site.get("title") or url
    domain = site.get("domain") or ""
    desc = site.get("description") or ""
    own_class = " is-own" if site.get("own") else ""
    emoji = site.get("emoji") or "🌐"
    alt = site.get("image_alt") or name
    src = site.get("image") or site.get("favicon") or ""
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


def sites_list_html(sites_data: dict) -> str:
    return "\n        ".join(site_card_html(s) for s in (sites_data.get("sites") or []))


def writing_card_html(chat: dict) -> str:
    href = f"/writing/{attr(chat.get('id') or '')}"
    title = escape_html(chat.get("title") or "")
    title_en = escape_html(chat.get("title_en") or chat.get("title") or "")
    summary = escape_html(chat.get("summary") or "")
    summary_en = escape_html(chat.get("summary_en") or chat.get("summary") or "")
    date = escape_html(chat.get("date") or "")
    time_html = f'<time datetime="{date}">{date}</time>' if date else ""
    return (
        f'<a class="card article" href="{href}">'
        f'<div class="meta"><span class="zh">对话</span><span class="en-only">Conversation</span>{time_html}</div>'
        f'<h3><span class="zh">{title}</span><span class="en-only">{title_en}</span></h3>'
        f'<p class="zh">{summary}</p>'
        f'<p class="en-only">{summary_en}</p>'
        f"{tags_html(chat.get('tags'))}"
        "</a>"
    )


def writing_list_html(chats: list[dict]) -> str:
    return "\n        ".join(writing_card_html(c) for c in chats)


def boardgame_card_html(game: dict) -> str:
    gid = game.get("id") or ""
    emoji = game.get("emoji") or "🎲"
    name_zh = game.get("name_zh") or ""
    name_en = game.get("name_en") or ""
    blurb_zh = game.get("blurb_zh") or ""
    blurb_en = game.get("blurb_en") or ""
    aka = ""
    if name_en and name_zh and name_en != name_zh:
        aka = (
            f'<p class="bgame-aka zh">{escape_html(name_en)}</p>'
            f'<p class="bgame-aka en-only">{escape_html(name_zh)}</p>'
        )
    desc = ""
    if blurb_zh:
        desc += f'<p class="bgame-desc zh">{escape_html(blurb_zh)}</p>'
    if blurb_en:
        desc += f'<p class="bgame-desc en-only">{escape_html(blurb_en)}</p>'
    return (
        f'<article class="card bgame-card" data-game="{attr(gid)}">'
        f'<span class="bgame-icon" data-game="{attr(gid)}" aria-hidden="true">{escape_html(emoji)}</span>'
        '<div class="bgame-body">'
        "<h3 class=\"bgame-name\">"
        f'<span class="zh">{escape_html(name_zh or name_en)}</span>'
        f'<span class="en-only">{escape_html(name_en or name_zh)}</span>'
        "</h3>"
        f"{aka}{desc}"
        "</div>"
        "</article>"
    )


def boardgames_list_html(data: dict) -> str:
    return "\n        ".join(boardgame_card_html(g) for g in (data.get("games") or []))


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


def prompt_block_html(chat: dict) -> str:
    if not chat.get("prompt"):
        return ""
    kind = chat.get("prompt_kind") or "prompt"
    label_zh = "我的问题" if kind == "question" else "我的 Prompt"
    label_en = "My question" if kind == "question" else "My prompt"
    return (
        '<aside class="prompt-block">'
        f'<p class="prompt-kicker"><span class="zh">{label_zh}</span><span class="en-only">{label_en}</span></p>'
        f'<div class="prompt-body">{render_markdown(chat["prompt"])}</div>'
        "</aside>"
    )


def thread_html(chat: dict) -> str:
    parts = []
    for msg in visible_messages(chat):
        zh, en, cls = role_label(msg)
        parts.append(
            f'<section class="turn {cls}">'
            f'<p class="turn-role"><span class="zh">{escape_html(zh)}</span>'
            f'<span class="en-only">{escape_html(en)}</span></p>'
            f'<div class="turn-body md">{render_markdown(msg.get("content") or "")}</div>'
            "</section>"
        )
    return "".join(parts)


def sources_html(chat: dict) -> str:
    sources = []
    if chat.get("source_url"):
        sources.append(
            f'<a href="{attr(chat["source_url"])}" rel="noopener noreferrer">'
            '<span class="zh">原始 ChatGPT 分享链接</span>'
            '<span class="en-only">Original ChatGPT share link</span></a>'
        )
    if chat.get("prompt_url"):
        sources.append(
            f'<a href="{attr(chat["prompt_url"])}" rel="noopener noreferrer">'
            '<span class="zh">原始 Prompt 分享链接</span>'
            '<span class="en-only">Original prompt share link</span></a>'
        )
    if not sources:
        return ""
    return '<p class="post-source">' + " · ".join(sources) + "</p>"


def article_html(chat: dict) -> str:
    date = chat.get("date") or ""
    title = chat.get("title") or ""
    title_en = chat.get("title_en") or title
    time_html = f'<time datetime="{attr(date)}">{escape_html(date)}</time>' if date else ""
    return (
        '<p class="post-back"><a href="/#writing"><span class="zh">← 返回文章列表</span>'
        '<span class="en-only">← Back to writing</span></a></p>'
        '<header class="post-head">'
        '<p class="kicker">Writing</p>'
        f'<h1><span class="zh">{escape_html(title)}</span>'
        f'<span class="en-only">{escape_html(title_en)}</span></h1>'
        '<div class="meta">'
        f"{time_html}"
        '<span class="zh">匡子闲 与 GPT</span><span class="en-only">匡子闲 and GPT</span>'
        "</div>"
        f"{tags_html(chat.get('tags'))}"
        "</header>"
        f"{prompt_block_html(chat)}"
        f'<div class="thread">{thread_html(chat)}</div>'
        f"{sources_html(chat)}"
    )


def json_ld(chat: dict) -> str:
    title = chat.get("title") or ""
    summary = chat.get("summary") or title
    url = writing_url(chat["id"])
    published = chat.get("datetime") or chat.get("date") or ""
    comments = []
    if chat.get("prompt"):
        comments.append(
            {
                "@type": "Comment",
                "author": {"@type": "Person", "name": "匡子闲", "@id": PERSON_ID},
                "text": chat["prompt"],
            }
        )
    for msg in visible_messages(chat):
        if msg.get("role") == "assistant":
            author: dict = {"@type": "Organization", "name": msg.get("name") or "GPT"}
        else:
            author = {"@type": "Person", "name": msg.get("name") or "匡子闲", "@id": PERSON_ID}
        comments.append({"@type": "Comment", "author": author, "text": msg.get("content") or ""})
    data = {
        "@context": "https://schema.org",
        "@type": "DiscussionForumPosting",
        "headline": title,
        "alternativeHeadline": chat.get("title_en") or title,
        "description": summary,
        "url": url,
        "mainEntityOfPage": url,
        "image": AVATAR,
        "datePublished": published,
        "inLanguage": "zh-CN",
        "author": {"@type": "Person", "name": "匡子闲", "alternateName": "kuangzixian", "@id": PERSON_ID, "url": f"{SITE}/"},
        "publisher": {"@type": "Person", "name": "匡子闲", "@id": PERSON_ID},
        "text": summary,
        "comment": comments,
    }
    if chat.get("source_url"):
        data["sameAs"] = [chat["source_url"]]
    return json.dumps(data, ensure_ascii=False, indent=2)


def skin_boot_script() -> str:
    return """  <script>
  (function () {
    try {
      var l = localStorage.getItem("kuang-lang");
      if (l === "en") document.documentElement.setAttribute("lang", "en");
      var s = localStorage.getItem("kuang-skin");
      if (s !== "blue" && s !== "pink" && s !== "night") {
        s = localStorage.getItem("kuang-theme") === "dark" ? "night" : "blue";
      }
      document.documentElement.setAttribute("data-skin", s);
      document.documentElement.setAttribute("data-theme", s === "night" ? "dark" : "light");
      var colors = { blue: "#4a9de0", pink: "#ee7aa8", night: "#1b1530" };
      var m = document.getElementById("themeColor");
      if (m) m.setAttribute("content", colors[s] || colors.blue);
    } catch (e) {}
  })();
  </script>"""


def topbar_html(*, back_href: str = "/#writing", back_zh: str = "返回日志", back_en: str = "Back to logs") -> str:
    return f"""  <a class="skip" href="#main">跳到正文 Skip to content</a>
  <div class="qz-topbar">
    <div class="qz-topbar-inner">
      <a class="qz-top-name" href="/">匡子闲的空间</a>
      <a href="{attr(back_href)}"><span class="zh">{escape_html(back_zh)}</span><span class="en-only">{escape_html(back_en)}</span></a>
      <div class="qz-top-actions">
        <button type="button" id="qzMusic" class="qz-music" aria-expanded="false" aria-controls="qzMusicBox" aria-label="背景音乐">
          ♫ <span id="qzMusicState" class="qz-music-state"><span class="zh">背景音乐</span><span class="en-only">Music</span></span>
        </button>
        <button type="button" id="qzSnowBtn" class="qz-snow-btn" aria-pressed="true" title="飘雪特效" aria-label="飘雪特效：开">❄</button>
        <div class="qz-desktop-tools">
          <button type="button" class="qz-skin-dot" data-skin-set="blue" title="晴空蓝" aria-label="晴空蓝皮肤"></button>
          <button type="button" class="qz-skin-dot" data-skin-set="pink" title="粉钻粉" aria-label="粉钻粉皮肤"></button>
          <button type="button" class="qz-skin-dot" data-skin-set="night" title="夜空" aria-label="夜空皮肤"></button>
          <button class="lang-toggle" type="button" id="langToggle" aria-label="Switch language">EN</button>
        </div>
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
            <button class="lang-toggle qz-menu-lang" type="button" id="langToggleMobile" aria-label="Switch language">EN</button>
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


def music_box_html() -> str:
    return """  <div id="qzMusicBox" class="qz-music-box" hidden>
    <div class="qz-music-box-inner" role="dialog" aria-modal="true" aria-labelledby="qzMusicTitle">
      <header class="qz-music-head">
        <strong id="qzMusicTitle"><span class="zh">背景音乐</span><span class="en-only">Background music</span></strong>
        <button type="button" class="qz-music-close" id="qzMusicClose" aria-label="关闭音乐盒">×</button>
      </header>
      <ul class="qz-playlist">
        <li class="qz-track" data-song-id="167827" data-outchain="1">
          <div class="qz-track-meta">
            <span class="qz-track-title">素颜</span>
            <span class="qz-track-artist">许嵩 / 何曼婷</span>
          </div>
          <button type="button" class="qz-track-load play-btn">
            <span class="zh">播放</span><span class="en-only">Play</span>
          </button>
          <a class="qz-track-link" href="https://music.163.com/song?id=167827" target="_blank" rel="noopener noreferrer">
            <span class="zh">网易云</span><span class="en-only">NetEase</span>
          </a>
          <div class="qz-track-player" hidden></div>
        </li>
        <li class="qz-track" data-song-id="174956" data-outchain="1">
          <div class="qz-track-meta">
            <span class="qz-track-title">坏女孩</span>
            <span class="qz-track-artist">徐良 / 小凌</span>
          </div>
          <button type="button" class="qz-track-load play-btn">
            <span class="zh">播放</span><span class="en-only">Play</span>
          </button>
          <a class="qz-track-link" href="https://music.163.com/song?id=174956" target="_blank" rel="noopener noreferrer">
            <span class="zh">网易云</span><span class="en-only">NetEase</span>
          </a>
          <div class="qz-track-player" hidden></div>
        </li>
      </ul>
      <p class="qz-music-note zh">使用网易云官方外链播放器，点播放后才会加载，不会自动播放。</p>
      <p class="qz-music-note en-only">Official NetEase Cloud Music player. It loads only after you click, and never autoplays.</p>
    </div>
  </div>"""


def page_scripts(*extra: str) -> str:
    srcs = ["/js/main.js", "/js/qzone.js", "/js/snow.js", "/js/visits.js", *extra]
    return "\n".join(f'  <script src="{s}"></script>' for s in srcs)


def build_chat_page(chat: dict) -> str:
    title = chat.get("title") or ""
    title_en = chat.get("title_en") or title
    full_title = f"{title} · 匡子闲"
    desc = chat.get("summary") or title
    url = writing_url(chat["id"])
    date = chat.get("date") or ""
    published = chat.get("datetime") or date
    md_href = f"/writing/{chat['id']}.md"
    published_meta = (
        f'  <meta property="article:published_time" content="{attr(published)}">\n' if published else ""
    )
    return f"""<!DOCTYPE html>
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
  <meta property="og:locale:alternate" content="en_US">
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
{json_ld(chat)}
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
      {article_html(chat)}
    </article>
      </main>
    </div>
  </div>

{music_box_html()}

  <footer class="site-footer">
    <div class="wrap">
      <p class="zh">匡子闲 · 对话原文在本站呈现，便于国内访问。</p>
      <p class="en-only">匡子闲 · The conversation is hosted here so it can be read without chatgpt.com.</p>
      <p><a href="/">首页</a> · <a href="/#writing">日志</a> · <a href="/data/chats.json">chats.json</a> · <a href="{attr(md_href)}">Markdown</a></p>
      <p><a href="/llms.txt">For AI agents: llms.txt</a></p>
    </div>
  </footer>
  <div class="cursor-glow" id="cursorGlow" aria-hidden="true"></div>
  <script src="/js/main.js"></script>
  <script src="/js/markdown.js"></script>
  <script src="/js/chat.js"></script>
  <script src="/js/qzone.js"></script>
  <script src="/js/snow.js"></script>
  <script src="/js/visits.js"></script>
</body>
</html>
"""


def build_404_page() -> str:
    return f"""<!DOCTYPE html>
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

{music_box_html()}

  <footer class="site-footer">
    <div class="wrap">
      <p class="zh">匡子闲的空间</p>
      <p class="en-only">匡子闲’s homepage</p>
      <p><a href="/">首页</a> · <a href="/llms.txt">For AI agents: llms.txt</a></p>
    </div>
  </footer>
  <div class="cursor-glow" id="cursorGlow" aria-hidden="true"></div>
{page_scripts()}
</body>
</html>
"""


def patch_index(html: str, *, chats: list[dict], sites: dict, boardgames: dict) -> str:
    html = html.replace("<h1 class=\"qz-space-name\">匡子闲的空间</h1>", '<p class="qz-space-name">匡子闲的空间</p>')
    html = html.replace('href="music/report.html"', 'href="/music/report"')
    html = html.replace('href="chat.html?id=', 'href="/writing/')
    # After the naive replace, href="/writing/ai-hack-bitcoin" is already correct if we also
    # strip the old prefix carefully. chat.html?id=X becomes /writing/X — good.
    html = replace_inner_by_id(html, "qzSitesList", sites_list_html(sites))
    html = replace_inner_by_id(html, "writingList", writing_list_html(chats))
    html = replace_inner_by_id(html, "qzBoardgamesList", boardgames_list_html(boardgames))
    intro_zh = sites.get("intro_zh")
    intro_en = sites.get("intro_en")
    if intro_zh:
        html = re.sub(
            r'(<p class="lede zh" id="qzSitesIntroZh">)(.*?)(</p>)',
            lambda m: m.group(1) + escape_html(intro_zh) + m.group(3),
            html,
            count=1,
            flags=re.S,
        )
    if intro_en:
        html = re.sub(
            r'(<p class="lede en-only" id="qzSitesIntroEn">)(.*?)(</p>)',
            lambda m: m.group(1) + escape_html(intro_en) + m.group(3),
            html,
            count=1,
            flags=re.S,
        )
    bg_intro_zh = boardgames.get("intro_zh")
    bg_intro_en = boardgames.get("intro_en")
    if bg_intro_zh:
        html = re.sub(
            r'(<p class="lede zh" id="qzBoardgamesIntroZh">)(.*?)(</p>)',
            lambda m: m.group(1) + escape_html(bg_intro_zh) + m.group(3),
            html,
            count=1,
            flags=re.S,
        )
    if bg_intro_en:
        html = re.sub(
            r'(<p class="lede en-only" id="qzBoardgamesIntroEn">)(.*?)(</p>)',
            lambda m: m.group(1) + escape_html(bg_intro_en) + m.group(3),
            html,
            count=1,
            flags=re.S,
        )
    return html


def write_pages(dest: Path) -> None:
    chats_data = load_json("chats.json")
    chats = list(chats_data.get("chats") or [])
    sites = load_json("sites.json")
    boardgames = load_json("boardgames.json")

    index_path = dest / "index.html"
    index_path.write_text(
        patch_index(index_path.read_text(encoding="utf-8"), chats=chats, sites=sites, boardgames=boardgames),
        encoding="utf-8",
    )

    writing_dir = dest / "writing"
    writing_dir.mkdir(parents=True, exist_ok=True)
    for chat in chats:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        # writing/<id>.html is served at the pretty URL /writing/<id> with HTTP 200.
        # A directory index would 308 /writing/<id> to /writing/<id>/.
        (writing_dir / f"{chat_id}.html").write_text(build_chat_page(chat), encoding="utf-8")

    (dest / "404.html").write_text(build_404_page(), encoding="utf-8")


if __name__ == "__main__":
    write_pages(ROOT / "dist")
