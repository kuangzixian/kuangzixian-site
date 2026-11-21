"""Locale helpers and HTML localization for the personal site."""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://kuangzixian.pages.dev"
ORDER = ("zh", "en", "es", "ko", "ja")


@lru_cache(maxsize=1)
def catalog() -> dict:
    return json.loads((ROOT / "data" / "i18n.json").read_text(encoding="utf-8"))


def locales() -> dict:
    return catalog()["locales"]


def t_ui(key: str, loc: str, **fmt) -> str:
    pack = catalog()["ui"].get(key) or {}
    text = pack.get(loc) or pack.get("en") or pack.get("zh") or key
    if fmt:
        try:
            text = text.format(**fmt)
        except (KeyError, IndexError):
            pass
    return text


@lru_cache(maxsize=1)
def reading_terms() -> dict:
    path = ROOT / "data" / "reading_terms.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


_HAN = re.compile(r"[\u4e00-\u9fff]")


def t_term(zh: str, loc: str) -> str:
    """Translate a WeRead category, preference, or time-of-day value.

    Unknown values fall back to the original string. Composite labels such as
    「计算机-编程设计」 are translated part by part when each part is known.
    """
    text = (zh or "").strip()
    if not text or loc == "zh":
        return zh if zh is not None else ""
    table = reading_terms()

    def one(key: str) -> str | None:
        pack = table.get(key)
        if not pack:
            return None
        return pack.get(loc) or pack.get("en") or key

    direct = one(text)
    if direct is not None:
        return direct
    if "-" in text:
        parts = text.split("-")
        mapped: list[str] = []
        for part in parts:
            item = one(part)
            if item is None:
                if _HAN.search(part):
                    return text
                mapped.append(part)
            else:
                mapped.append(item)
        return " · ".join(mapped)
    return text


def write_reading_terms_js(dest: Path | None = None) -> Path:
    dest = dest or (ROOT / "js" / "reading-terms.js")
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(reading_terms(), ensure_ascii=False, indent=2)
    dest.write_text(
        "/* Generated from data/reading_terms.json. Do not edit by hand. */\n"
        "(function (global) {\n"
        f"  global.KUANG_READING_TERMS = {payload};\n"
        "})(window);\n",
        encoding="utf-8",
    )
    return dest


def pick(obj: dict, base: str, loc: str, default: str = "") -> str:
    if loc == "zh":
        return obj.get(base) or obj.get(base + "_zh") or default
    return obj.get(f"{base}_{loc}") or obj.get(f"{base}_en") or obj.get(base) or obj.get(base + "_zh") or default


def pick_list(obj: dict, base: str, loc: str) -> list:
    if loc == "zh":
        return list(obj.get(base) or obj.get(base + "_zh") or [])
    return list(obj.get(f"{base}_{loc}") or obj.get(f"{base}_en") or obj.get(base) or obj.get(base + "_zh") or [])


def prefix(loc: str) -> str:
    return locales()[loc]["prefix"]


def localize_path(path: str, loc: str) -> str:
    p = re.sub(r"^/(en|es|ko|ja)(?=/|$)", "", path or "/") or "/"
    if p in ("/index.html", "/index.htm"):
        p = "/"
    pre = prefix(loc)
    if p == "/":
        return f"{pre}/" if pre else "/"
    return f"{pre}{p}"


def abs_url(path: str, loc: str | None = None) -> str:
    if loc is not None:
        path = localize_path(path, loc)
    if not path.startswith("/"):
        path = "/" + path
    return SITE + path


def format_date(value: str, loc: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    parsed = None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            if fmt.endswith("%z") and raw.endswith("Z"):
                parsed = datetime.strptime(raw.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
            else:
                parsed = datetime.strptime(raw[: len("2015-10-10T12:00:00") if "T" in raw else 10], fmt if "T" not in raw else "%Y-%m-%dT%H:%M:%S")
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = date.fromisoformat(raw[:10])
        except ValueError:
            return raw
    if isinstance(parsed, datetime):
        d = parsed.date()
    else:
        d = parsed
    info = locales()[loc]
    # Prefer a compact locale-aware form without depending on system locales.
    if loc == "zh":
        return f"{d.year}年{d.month}月{d.day}日"
    if loc == "ja":
        return f"{d.year}年{d.month}月{d.day}日"
    if loc == "ko":
        return f"{d.year}년 {d.month}월 {d.day}일"
    months_en = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    months_es = "ene feb mar abr may jun jul ago sep oct nov dic".split()
    if loc == "es":
        return f"{d.day} {months_es[d.month - 1]} {d.year}"
    return f"{d.day} {months_en[d.month - 1]} {d.year}"


def _norm_key(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pair_index() -> dict[str, dict]:
    idx = {}
    for item in catalog()["pairs"]:
        idx[_norm_key(item["zh"])] = item
        # also index by text without tags for more flexible match
        plain = _norm_key(re.sub(r"<[^>]+>", "", item["zh"]))
        idx.setdefault(plain, item)
    return idx


def lookup_pair(zh_inner: str, loc: str) -> str | None:
    idx = _pair_index_cached()
    key = _norm_key(zh_inner)
    item = idx.get(key)
    if not item:
        item = idx.get(_norm_key(re.sub(r"<[^>]+>", "", zh_inner)))
    if not item:
        return None
    if loc == "zh":
        return item.get("zh")
    return item.get(loc) or item.get("en") or item.get("zh")


@lru_cache(maxsize=1)
def _pair_index_cached() -> dict:
    return pair_index()


_ELEM_RE = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)([^>]*\sclass="([^"]*)"[^>]*)>', re.S)


def _iter_class_elems(html: str, token: str):
    i = 0
    while True:
        m = _ELEM_RE.search(html, i)
        if not m:
            break
        classes = m.group(3).split()
        if token not in classes:
            i = m.end()
            continue
        tag = m.group(1)
        start = m.start()
        pos = m.end()
        depth = 1
        open_re = re.compile(rf"<{tag}\b[^>]*>", re.I)
        close_re = re.compile(rf"</{tag}\s*>", re.I)
        found = False
        while pos < len(html) and depth:
            om = open_re.search(html, pos)
            cm = close_re.search(html, pos)
            if not cm:
                break
            if om and om.start() < cm.start():
                depth += 1
                pos = om.end()
            else:
                depth -= 1
                if depth == 0:
                    yield {
                        "tag": tag,
                        "classes": classes,
                        "attrs": m.group(2),
                        "inner": html[m.end() : cm.start()],
                        "start": start,
                        "end": cm.end(),
                        "open_end": m.end(),
                        "close_start": cm.start(),
                    }
                    i = cm.end()
                    found = True
                    break
                pos = cm.end()
        if not found:
            i = m.end()


def _set_inner(html: str, el: dict, new_inner: str) -> str:
    return html[: el["open_end"]] + new_inner + html[el["close_start"] :]


def _drop(html: str, el: dict) -> str:
    return html[: el["start"]] + html[el["end"] :]


def _class_attr_replace(attrs: str, remove: set[str]) -> str:
    def repl(m):
        classes = [c for c in m.group(1).split() if c not in remove]
        if not classes:
            return ""
        return f' class="{" ".join(classes)}"'

    return re.sub(r'\sclass="([^"]*)"', repl, attrs, count=1)


def localize_pairs(html: str, loc: str) -> str:
    zh_elems = list(_iter_class_elems(html, "zh"))
    en_elems = list(_iter_class_elems(html, "en-only"))
    used_en = set()
    operations = []  # (start, end, replacement) applied from the end

    def find_en(z):
        candidates = [
            (i, e)
            for i, e in enumerate(en_elems)
            if i not in used_en and e["start"] >= z["start"] - 20 and e["start"] < z["end"] + 800
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda p: (0 if p[1]["tag"] == z["tag"] else 1, abs(p[1]["start"] - z["end"])))
        i, e = candidates[0]
        if e["start"] - z["end"] > 600 and e["tag"] != z["tag"]:
            return None
        return i, e

    for z in zh_elems:
        pair = find_en(z)
        en = None
        if pair:
            used_en.add(pair[0])
            en = pair[1]
        translated = lookup_pair(z["inner"], loc)
        if translated is None:
            # keep zh text for this locale if we have no pair; for non-zh prefer en inner
            if loc != "zh" and en:
                translated = en["inner"]
            else:
                translated = z["inner"]
        # Preserve a wrapping type-target if the original had one and the translation does not.
        zt = z["inner"].strip()
        type_m = re.fullmatch(r'<span class="type-target">(.*)</span>', zt, re.S)
        if type_m and "type-target" not in translated:
            translated = f'<span class="type-target">{translated}</span>'
        # Rebuild the zh element without zh/en-only classes, drop the en-only sibling.
        new_open = f'<{z["tag"]}{_class_attr_replace(z["attrs"], {"zh", "en-only"})}>'
        new_el = new_open + translated + f'</{z["tag"]}>'
        operations.append((z["start"], z["end"], new_el))
        if en:
            operations.append((en["start"], en["end"], ""))

    # leftover en-only
    for i, e in enumerate(en_elems):
        if i not in used_en:
            operations.append((e["start"], e["end"], "" if loc != "en" else None))
            if loc == "en":
                new_open = f'<{e["tag"]}{_class_attr_replace(e["attrs"], {"zh", "en-only"})}>'
                operations[-1] = (e["start"], e["end"], new_open + e["inner"] + f'</{e["tag"]}>')

    operations.sort(key=lambda o: o[0], reverse=True)
    # skip overlapping (shouldn't happen often)
    last_start = 10**18
    kept = []
    for start, end, rep in operations:
        if end > last_start:
            continue
        kept.append((start, end, rep))
        last_start = start
    for start, end, rep in kept:
        html = html[:start] + (rep if rep is not None else html[start:end]) + html[end:]
    return html


def rewrite_root_paths(html: str) -> str:
    """Make asset and data links root-absolute so locale subpaths work."""

    def fix_attr(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        if url.startswith(("http://", "https://", "/", "#", "mailto:", "data:", "javascript:")):
            return m.group(0)
        if re.match(r"^(css|js|data|images|music)/", url) or url.startswith("images/"):
            return f"{attr}={q}/{url}{q}"
        return m.group(0)

    return re.sub(r'\b(href|src)=([\'"])([^\'"]+)\2', fix_attr, html)


def localize_internal_hrefs(html: str, loc: str) -> str:
    pre = prefix(loc)

    def fix(m):
        q, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:")):
            return m.group(0)
        # already localized or non-page asset
        if re.match(r"^/(en|es|ko|ja)(/|$)", url):
            return m.group(0)
        if url.startswith(("/css/", "/js/", "/data/", "/images/", "/music/", "/llms", "/robots", "/sitemap", "/api/")):
            return m.group(0)
        if url in ("/llms.txt", "/llms-full.txt", "/index.md", "/reading.md", "/writing.md", "/music.md", "/boardgames.md", "/sites.md", "/sitemap.md", "/sitemap.xml"):
            return m.group(0)
        path, frag = url, ""
        if "#" in url:
            path, frag = url.split("#", 1)
            frag = "#" + frag
        if path.startswith("/writing/") or path in ("/", "/index.html", "") or path.startswith("/#") or path.startswith("/chat"):
            if path.startswith("/#"):
                dest = (pre + "/" if pre else "/") + path[1:]
            elif path in ("",):
                dest = (pre + "/" if pre else "/") + frag
            else:
                dest = localize_path(path, loc) + frag
            return f"href={q}{dest}{q}"
        return m.group(0)

    return re.sub(r'href=([\'"])([^\'"]+)\1', fix, html)


def hreflang_tags(path: str) -> str:
    """path is the zh (unprefixed) path, e.g. / or /writing/foo"""
    lines = []
    for loc in ORDER:
        href = abs_url(path, loc)
        lines.append(f'  <link rel="alternate" hreflang="{locales()[loc]["hreflang"]}" href="{href}">')
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="{abs_url(path, "zh")}">')
    return "\n".join(lines)


def og_locale_alts(loc: str) -> str:
    lines = []
    for other in ORDER:
        if other == loc:
            continue
        lines.append(f'  <meta property="og:locale:alternate" content="{locales()[other]["og_locale"]}">')
    return "\n".join(lines)


BOOT_SCRIPT = r"""  <script>
  (function () {
    try {
      var LOCALES = {zh:"",en:"/en",es:"/es",ko:"/ko",ja:"/ja"};
      function pathLocale(p) {
        var m = String(p || "").match(/^\/(en|es|ko|ja)(?=\/|$)/);
        return m ? m[1] : "zh";
      }
      function strip(p) {
        p = String(p || "/").replace(/^\/(en|es|ko|ja)(?=\/|$)/, "") || "/";
        if (p === "/index.html") p = "/";
        return p;
      }
      function dest(p, loc, search, hash) {
        var pre = LOCALES[loc] || "";
        p = strip(p);
        var d = p === "/" ? (pre ? pre + "/" : "/") : (pre + p);
        return d + (search || "") + (hash || "");
      }
      function isBot() {
        return /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|embedly|linkedinbot|pinterest|googleother|wget|curl|python-requests/i.test(navigator.userAgent || "");
      }
      var cur = pathLocale(location.pathname);
      var saved = null;
      try { saved = localStorage.getItem("kuang-lang"); } catch (e) {}
      if (saved && !LOCALES.hasOwnProperty(saved)) saved = null;
      if (cur !== "zh") {
        if (saved !== cur) try { localStorage.setItem("kuang-lang", cur); } catch (e) {}
      } else if (!isBot()) {
        var want = saved;
        if (!want) {
          var list = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language];
          for (var i = 0; i < (list || []).length && !want; i++) {
            var n = String(list[i] || "").toLowerCase();
            if (n.indexOf("zh") === 0) want = "zh";
            else if (n.indexOf("en") === 0) want = "en";
            else if (n.indexOf("es") === 0) want = "es";
            else if (n.indexOf("ko") === 0) want = "ko";
            else if (n.indexOf("ja") === 0) want = "ja";
          }
        }
        if (want && want !== "zh" && LOCALES.hasOwnProperty(want)) {
          try { localStorage.setItem("kuang-lang", want); } catch (e) {}
          var next = dest(location.pathname, want, location.search, location.hash);
          if (next !== location.pathname + location.search + location.hash) location.replace(next);
        }
      }
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
    var raw = (location.hash || "#home").replace(/^#/, "").split("?")[0];
    var map = {
      "": "home", top: "home", home: "home",
      writing: "writing", logs: "writing", log: "writing",
      reading: "reading",
      music: "music",
      boardgames: "boardgames", games: "boardgames",
      sites: "sites", links: "sites", friends: "sites",
      guestbook: "guestbook",
      profile: "profile", projects: "profile", social: "profile",
      ideas: "home"
    };
    var tab = map[raw] || "home";
    if (document.documentElement.getAttribute("data-tab") == null && !/\/writing\//.test(location.pathname)) {
      document.documentElement.setAttribute("data-tab", tab);
    }
  })();
  </script>"""


def lang_switcher_html(loc: str, *, variant: str = "dropdown") -> str:
    info = locales()
    label = t_ui("lang_label", loc)
    current = info[loc]["name"]
    if variant == "list":
        items = []
        for code in ORDER:
            cur = ' aria-current="true"' if code == loc else ""
            href = (prefix(code) + "/") if prefix(code) else "/"
            items.append(
                f'<li><a href="{href}" hreflang="{info[code]["hreflang"]}" lang="{info[code]["html_lang"]}" data-lang="{code}"{cur}>{info[code]["name"]}</a></li>'
            )
        return (
            f'<p class="qz-menu-label">{label}</p>'
            f'<ul class="lang-list" data-lang-list>{"".join(items)}</ul>'
        )
    items = []
    for code in ORDER:
        selected = "true" if code == loc else "false"
        cur = ' aria-current="true"' if code == loc else ""
        href = (prefix(code) + "/") if prefix(code) else "/"
        items.append(
            f'<li role="none"><a href="{href}" role="option" id="lang-opt-{code}" aria-selected="{selected}" hreflang="{info[code]["hreflang"]}" lang="{info[code]["html_lang"]}" data-lang="{code}"{cur}>{info[code]["name"]}</a></li>'
        )
    return (
        f'<div class="lang-switcher" data-lang-switcher>'
        f'<button type="button" class="lang-switcher-btn" id="lang-switcher-btn" aria-expanded="false" aria-haspopup="listbox" aria-controls="lang-switcher-menu" aria-label="{label}">{current}</button>'
        f'<ul class="lang-switcher-menu" id="lang-switcher-menu" hidden role="listbox" aria-labelledby="lang-switcher-btn">{"".join(items)}</ul>'
        f"</div>"
    )


def replace_boot_script(html: str) -> str:
    # Replace the existing inline boot <script> in <head> (the first one that mentions kuang-lang).
    def repl(m):
        return BOOT_SCRIPT

    new, n = re.subn(
        r"  <script>\s*\(function \(\) \{.*?kuang-lang[\s\S]*?</script>",
        BOOT_SCRIPT,
        html,
        count=1,
    )
    if n:
        return new
    # fallback: insert before </head>
    return html.replace("</head>", BOOT_SCRIPT + "\n</head>", 1)


def insert_hreflang(html: str, path: str, loc: str) -> str:
    tags = hreflang_tags(path)
    alts = og_locale_alts(loc)
    # replace existing canonical with canonical + hreflang after it
    def canon(m):
        return m.group(0) + "\n" + tags

    html2, n = re.subn(r'[ \t]*<link rel="canonical" href="[^"]*">', canon, html, count=1)
    if n == 0:
        html2 = html.replace("</head>", tags + "\n</head>", 1)
    # replace og:locale and drop old single alternate
    info = locales()[loc]
    html2 = re.sub(
        r'<meta property="og:locale" content="[^"]*">',
        f'<meta property="og:locale" content="{info["og_locale"]}">',
        html2,
        count=1,
    )
    html2 = re.sub(r'\n[ \t]*<meta property="og:locale:alternate" content="[^"]*">', "", html2)
    html2 = re.sub(
        r'(<meta property="og:locale" content="[^"]*">)',
        r"\1\n" + alts,
        html2,
        count=1,
    )
    return html2


def set_html_lang(html: str, loc: str) -> str:
    lang = locales()[loc]["html_lang"]
    return re.sub(r'<html\b[^>]*>', f'<html lang="{lang}">', html, count=1, flags=re.I)


def set_title_desc(html: str, loc: str, *, title: str | None = None, desc: str | None = None, url: str | None = None) -> str:
    if title is None:
        title = t_ui("page_title", loc)
    if desc is None:
        desc = t_ui("page_desc", loc)
    def esc(s):
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
    html = re.sub(r"<title>[^<]*</title>", f"<title>{esc(title)}</title>", html, count=1)
    html = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{esc(desc)}">',
        html,
        count=1,
    )
    for prop in ("og:title", "twitter:title"):
        html = re.sub(
            rf'<meta (?:property|name)="{prop}" content="[^"]*">',
            lambda m, p=prop, t=esc(title): m.group(0).split("content=")[0] + f'content="{t}">' if False else re.sub(r'content="[^"]*"', f'content="{t}"', m.group(0)),
            html,
            count=1,
        )
    for prop in ("og:description", "twitter:description"):
        html = re.sub(
            rf'<meta (?:property|name)="{prop}" content="[^"]*">',
            lambda m, t=esc(desc): re.sub(r'content="[^"]*"', f'content="{t}"', m.group(0)),
            html,
            count=1,
        )
    if url:
        html = re.sub(
            r'<meta property="og:url" content="[^"]*">',
            f'<meta property="og:url" content="{esc(url)}">',
            html,
            count=1,
        )
        html = re.sub(
            r'<link rel="canonical" href="[^"]*">',
            f'<link rel="canonical" href="{esc(url)}">',
            html,
            count=1,
        )
    site_name = t_ui("site_name", loc)
    html = re.sub(
        r'<meta property="og:site_name" content="[^"]*">',
        f'<meta property="og:site_name" content="{esc(site_name)}">',
        html,
        count=1,
    )
    return html


def update_jsonld(html: str, loc: str, *, url: str, page_name: str | None = None, description: str | None = None) -> str:
    m = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.S)
    if not m:
        return html
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return html
    data["url"] = url
    if page_name:
        data["name"] = page_name
    entity = data.get("mainEntity") or data
    if isinstance(entity, dict):
        if entity.get("@type") == "Person" or data.get("@type") == "ProfilePage":
            person = entity if entity.get("@type") == "Person" else entity
            person["url"] = url if person.get("@type") == "Person" else person.get("url") or url
            if person.get("@type") == "Person":
                person["jobTitle"] = t_ui("job_title", loc)
                person["description"] = description or t_ui("page_desc", loc)
        if data.get("@type") == "ProfilePage":
            data["name"] = page_name or t_ui("jsonld_name", loc)
            if isinstance(data.get("mainEntity"), dict):
                data["mainEntity"]["jobTitle"] = t_ui("job_title", loc)
                data["mainEntity"]["description"] = description or t_ui("page_desc", loc)
                data["mainEntity"]["url"] = SITE + "/"
    dumped = json.dumps(data, ensure_ascii=False, indent=2)
    return html[: m.start(1)] + dumped + html[m.end(1) :]


def ensure_i18n_script(html: str) -> str:
    html = html.replace('src="js/reading-terms.js"', 'src="/js/reading-terms.js"')
    html = html.replace('src="js/i18n.js"', 'src="/js/i18n.js"')
    if 'js/reading-terms.js' not in html:
        needle = '<script src="/js/i18n.js"></script>'
        inject = '<script src="/js/reading-terms.js"></script>\n  ' + needle
        if needle in html:
            html = html.replace(needle, inject, 1)
        else:
            html = re.sub(
                r'(<script src="(?:/)?js/main\.js"></script>)',
                '  <script src="/js/reading-terms.js"></script>\n  <script src="/js/i18n.js"></script>\n  \\1',
                html,
                count=1,
            )
    if 'src="/js/i18n.js"' not in html:
        html = html.replace(
            "</body>",
            '  <script src="/js/reading-terms.js"></script>\n  <script src="/js/i18n.js"></script>\n</body>',
            1,
        )
    return html



def _rewrite_class_text(html: str, cls: str, fn, tags: str = "span|p|h3") -> str:
    def repl(m, fn=fn):
        return m.group(1) + fn(m.group(2)) + m.group(3)
    return re.sub(
        rf'(<(?:{tags})\b[^>]*class="[^"]*\b{cls}\b[^"]*"[^>]*>)([^<]*)(</(?:{tags})>)',
        repl,
        html,
    )


def format_zh_duration(text: str, loc: str) -> str:
    if loc == "zh":
        return text
    def dur(m):
        hour, minute = m.group(1), m.group(2)
        return f"{hour} {t_ui('unit_hour', loc)} {minute} {t_ui('unit_minute', loc)}"
    text = re.sub(r"([\d,]+)小时([\d,]+)分钟", dur, text)
    text = re.sub(r"([\d,]+)分钟", lambda m: f"{m.group(1)} {t_ui('unit_minute', loc)}", text)
    return text


def format_zh_counts(text: str, loc: str) -> str:
    if loc == "zh":
        return text
    def books(m):
        n = m.group(1)
        num = int(n.replace(",", ""))
        if loc == "en":
            word = "book" if num == 1 else "books"
        elif loc == "es":
            word = "libro" if num == 1 else "libros"
        else:
            word = t_ui("unit_book_word", loc)
        return f"{n} {word}".strip() if word else n
    # "376本 / 108本" or "58本"
    text = re.sub(r"([\d,]+)本", books, text)
    text = re.sub(r"([\d,]+)\s*天", lambda m: f"{m.group(1)} {t_ui('unit_day', loc)}", text)
    text = re.sub(r"([\d,]+)条(?!笔)", lambda m: f"{m.group(1)} {t_ui('unit_note', loc)}", text)
    return text


def apply_reading_chrome(html: str, loc: str) -> str:
    """Translate reading-stat labels, units, and note chrome. Book titles stay as-is."""
    labels = {
        "总时长": "total_time",
        "有效阅读": "active_reading",
        "读过 / 读完": "opened_finished",
        "笔记": "notes",
        "内容偏好": "content_pref",
        "时段偏好": "time_pref",
        "时长": "duration",
        "自然日均": "daily_avg",
        "偏好": "pref",
        "版本覆盖": "editions",
        "重读": "reread",
    }
    def kv_label(text: str) -> str:
        key = labels.get(text.strip())
        return t_ui(key, loc) if key else text
    html = _rewrite_class_text(html, "k", kv_label, tags="span")

    def value(text: str) -> str:
        text = format_zh_counts(format_zh_duration(text, loc), loc)
        stripped = text.strip()
        mapped = t_term(stripped, loc)
        return mapped if mapped != stripped else text
    html = _rewrite_class_text(html, "v", value, tags="span")

    def bar_count(m):
        inner = format_zh_counts(m.group(1), loc)
        return f"</div><span>{inner}</span></div>"
    html = re.sub(r"</div><span>([^<]*本)</span></div>", bar_count, html)

    def bar_name(m):
        return m.group(1) + t_term(m.group(2), loc) + m.group(3)
    html = re.sub(r'(<div class="bar-row"><span>)([^<]+)(</span>)', bar_name, html)

    def meta(text: str) -> str:
        text = text.replace("尚未阅读", t_ui("not_started", loc))
        text = text.replace("最近阅读", t_ui("last_read", loc))
        text = text.replace("读完于", t_ui("finished_on", loc))
        text = text.replace("后来又翻到", t_ui("reread_to", loc))
        # "最近" after a category middot, not inside last_read which already replaced
        text = re.sub(r"(· )最近( )", lambda m: m.group(1) + t_ui("last", loc) + m.group(2), text)
        text = format_zh_counts(format_zh_duration(text, loc), loc)
        m = re.match(r"^(.+?)( · )", text)
        if m:
            text = t_term(m.group(1), loc) + m.group(2) + text[m.end():]
        return text
    html = _rewrite_class_text(html, "meta", meta, tags="p")

    def note_count(text: str) -> str:
        m = re.search(r"([\d,]+)\s*条笔记", text)
        if m:
            return t_ui("n_notes", loc, n=m.group(1))
        return text
    html = _rewrite_class_text(html, "note-count", note_count, tags="span")

    def pill(text: str) -> str:
        s = text.strip()
        mapping = {"划线": "highlight", "想法": "thought", "读完": "finished", "重读": "reread", "有声书": "audiobook"}
        key = mapping.get(s)
        return t_ui(key, loc) if key else text
    html = _rewrite_class_text(html, "pill", pill, tags="span")

    html = re.sub(
        r'alt="《([^"]+)》封面"',
        lambda m: f'alt="{t_ui("cover_of", loc, title=m.group(1))}"',
        html,
    )
    html = re.sub(
        r'aria-label="进度 (\d+)%"',
        lambda m: f'aria-label="{t_ui("progress", loc, n=m.group(1))}"',
        html,
    )

    def chip_visible(m):
        prefix, cat, label, suffix = m.group(1), m.group(2), m.group(3), m.group(4)
        if cat == "all":
            return m.group(0)
        parts = label.rsplit(None, 1)
        if len(parts) == 2 and re.fullmatch(r"[\d,]+", parts[1]):
            return f"{prefix}{t_term(parts[0], loc)} {parts[1]}{suffix}"
        return f"{prefix}{t_term(label, loc)}{suffix}"

    html = re.sub(
        r'(<button\b[^>]*data-shelf-filter="([^"]+)"[^>]*>)([^<]*)(</button>)',
        chip_visible,
        html,
    )
    return html


def apply_music_chrome(html: str, loc: str) -> str:
    """Translate music kickers, evidence captions, and cover alt chrome."""
    html = _rewrite_class_text(html, "music-kicker", lambda t: t_term(t.strip(), loc), tags="p")

    def ev_caption(m):
        return m.group(1) + t_term(m.group(2).strip(), loc)

    html = re.sub(
        r'(<span class="music-ev-artist">[^<]*</span>\s*—\s*)([^<]+)',
        ev_caption,
        html,
    )
    html = re.sub(
        r'alt="([^"]+?) 封面"',
        lambda m: f'alt="{t_ui("cover_of", loc, title=m.group(1))}"',
        html,
    )
    return html


def apply_section_heads(html: str, loc: str) -> str:
    mapping = [
        ("分类偏好", "category_pref"),
        ("风格时间线", "timeline"),
        ("推荐网站", "sites"),
        ("社交链接", "social"),
        ("笔记与划线", "notes_highlights"),
        ("2026 年 11 月", "month_2026_11"),
        ("2026 年", "year_2026"),
        ("几本简介", "blurbs"),
        ("正在读", "reading_now"),
        ("说说", "mood"),
        ("读书", "reading"),
        ("音乐", "music"),
        ("偏好", "pref"),
        ("推荐", "recs"),
        ("桌游", "boardgames"),
        ("日志", "writing"),
        ("项目", "projects"),
        ("留言板", "guestbook"),
        ("累计", "all_time"),
        ("读完", "finished"),
        ("书架", "shelf"),
    ]
    for zh, key in mapping:
        heading = t_ui(key, loc)
        html = re.sub(
            r"(<h[23]\b[^>]*>)" + re.escape(zh) + r"(</h[23]>)",
            lambda m, heading=heading: m.group(1) + heading + m.group(2),
            html,
        )
        # English subtitle .en next to it: keep English as decorative subtitle, or use zh when loc is en
    # Replace remaining <span class="en">English</span> with a small subtitle
    # When locale is en, show Chinese as the small mark if we can; otherwise leave English.
    def sub_en(m):
        en = m.group(1)
        if loc == "en":
            # keep as is visually but without needing a second language
            return f'<span class="en">{en}</span>'
        return f'<span class="en">{en}</span>'

    html = re.sub(r'<span class="en">([^<]*)</span>', sub_en, html)
    return html


def apply_plain_ui(html: str, loc: str) -> str:
    """Replace leftover unlabeled UI strings."""
    replacements = [
        ('跳到正文 Skip to content', t_ui("skip", loc)),
        (">匡子闲的空间<", f'>{t_ui("site_name", loc)}<'),
        (">Personal homepage<", f'>{t_ui("personal_homepage", loc)}<'),
        (">人气 / Popularity<", f'>{t_ui("popularity", loc)}<'),
        ('aria-label="访问量"', f'aria-label="{t_ui("visits", loc)}"'),
        ('aria-label="空间栏目"', f'aria-label="{t_ui("tabs_label", loc)}"'),
        ('aria-label="阅读概览"', f'aria-label="{t_ui("reading_overview", loc)}"'),
        ('title="空间装扮：自制黄钻徽章 LV7，非腾讯会员标识"', f'title="{t_ui("vip_title", loc)}"'),
        ('alt="匡子闲的公开即刻头像：江南水乡场景中的个人照片"', f'alt="{t_ui("avatar_alt", loc)}"'),
        (">晴空蓝<", f'>{t_ui("skin_blue", loc)}<'),
        (">粉钻粉<", f'>{t_ui("skin_pink", loc)}<'),
        (">夜空<", f'>{t_ui("skin_night", loc)}<'),
        ('title="晴空蓝"', f'title="{t_ui("skin_blue", loc)}"'),
        ('title="粉钻粉"', f'title="{t_ui("skin_pink", loc)}"'),
        ('title="夜空"', f'title="{t_ui("skin_night", loc)}"'),
        ('aria-label="晴空蓝皮肤"', f'aria-label="{t_ui("skin_blue_aria", loc)}"'),
        ('aria-label="粉钻粉皮肤"', f'aria-label="{t_ui("skin_pink_aria", loc)}"'),
        ('aria-label="夜空皮肤"', f'aria-label="{t_ui("skin_night_aria", loc)}"'),
        (">后端工程师<", f'>{t_ui("job_title", loc)}<'),
        (">计科，炒股<", f'>{t_ui("tag_cs_stocks", loc)}<'),
        (">按时长排列，来自官方阅读统计。<", f'>{t_ui("by_duration", loc)}<'),
        (">分类偏好<", f'>{t_ui("category_pref", loc)}<'),
        (">偏好<", f'>{t_ui("pref", loc)}<'),
        (">风格时间线<", f'>{t_ui("timeline", loc)}<'),
        ('For AI agents: llms.txt', t_ui("ai_agents", loc)),
        ('aria-label="按分类筛选书架"', f'aria-label="{t_ui("shelf_filter", loc)}"'),
        ('title="飘雪特效"', f'title="{t_ui("snow_btn_title", loc)}"'),
        ('aria-label="飘雪特效：开"', f'aria-label="{t_ui("snow_on", loc)}"'),
        ('aria-label="随机抽一本书"', f'aria-label="{t_ui("random_book", loc)}"'),
        ('aria-label="代表封面"', f'aria-label="{t_ui("featured_covers", loc)}"'),

        (">显示名 匡子闲 · 公司字段 IFTech<", f'>{t_ui("display_company", loc)}<'),
        (">未确认 / unverified<", f'>{t_ui("unverified", loc)} / unverified<' if loc == "zh" else f'>{t_ui("unverified", loc)}<'),
    ]
    for old, new in replacements:
        html = html.replace(old, new)
    # shelf more / all filter
    html = re.sub(
        r">显示全部 (\d+) 册<",
        lambda m: f'>{t_ui("show_all", loc, n=m.group(1))}<',
        html,
    )
    html = re.sub(
        r">全部 (\d+)<",
        lambda m: f'>{t_ui("filter_all", loc, n=m.group(1))}<',
        html,
    )
    # easylife project blurb
    html = html.replace(
        "好好生活：基于 HowToLiveBetter 的微信小程序，支持顺序阅读、带出处的本地问句检索和随机建议卡片。",
        t_ui("easylife_repo", loc),
    )
    html = html.replace(
        "EasyLife：基于 HowToLiveBetter 的微信小程序，支持顺序阅读、带出处的本地问句检索和随机建议卡片。",
        t_ui("easylife_repo", loc),
    )
    # social counts
    html = re.sub(
        r">(\d+) 关注者 · (\d+) 篇文章 · ([\d,]+) 阅读<",
        lambda m: f'>{m.group(1)} {t_ui("followers", loc)} · {m.group(2)} {t_ui("articles", loc)} · {m.group(3)} {t_ui("article_views", loc)}<',
        html,
    )
    html = re.sub(
        r">(\d+) 被关注 · (\d+) 关注<",
        lambda m: f'>{m.group(1)} {t_ui("followed", loc)} · {m.group(2)} {t_ui("following", loc)}<',
        html,
    )
    html = re.sub(
        r">(\d+) 关注者 · (\d+) 个公开仓库 · (\d+) 年加入<",
        lambda m: f'>{m.group(1)} {t_ui("followers", loc)} · {m.group(2)} {t_ui("public_repos", loc)} · {m.group(3)} {t_ui("joined_year", loc)}<',
        html,
    )
    html = re.sub(
        r">(\d+) 关注者 · (\d+) 回答 · ([\d,]+) 赞同<",
        lambda m: f'>{m.group(1)} {t_ui("followers", loc)} · {m.group(2)} {t_ui("answers", loc)} · {m.group(3)} {t_ui("upvotes", loc)}<',
        html,
    )
    if loc != "zh":
        html = html.replace("JUEJIN · 掘金", "Juejin")
        html = html.replace("JIKE · 即刻", "Jike")
        html = html.replace("ZHIHU · 知乎", "Zhihu")
        html = html.replace("小红书 · 微博 · 抖音 · X", t_ui("unconfirmed_platforms", loc))
    html = html.replace("<h3>easy-life</h3>", "<h3>EasyLife</h3>")
    html = html.replace("<h3>easy-offer</h3>", "<h3>EasyOffer</h3>")
    return html


def format_time_tags(html: str, loc: str) -> str:
    def repl(m):
        dt, text = m.group(1), m.group(2)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text.strip()):
            return f'<time datetime="{dt}">{format_date(dt, loc)}</time>'
        return m.group(0)

    return re.sub(r'<time datetime="([^"]+)">([^<]*)</time>', repl, html)


def localize_document(html: str, loc: str, *, path: str = "/", title: str | None = None, desc: str | None = None) -> str:
    html = replace_boot_script(html)
    html = rewrite_root_paths(html)
    html = localize_pairs(html, loc)
    html = apply_section_heads(html, loc)
    html = apply_plain_ui(html, loc)
    html = apply_reading_chrome(html, loc)
    html = apply_music_chrome(html, loc)
    html = format_time_tags(html, loc)
    html = set_html_lang(html, loc)
    url = abs_url(path, loc)
    html = set_title_desc(html, loc, title=title, desc=desc, url=url)
    if path.rstrip("/") != "/404":
        html = insert_hreflang(html, path, loc)
    html = update_jsonld(
        html,
        loc,
        url=url,
        page_name=title or t_ui("jsonld_name", loc),
        description=desc or t_ui("page_desc", loc),
    )
    html = localize_internal_hrefs(html, loc)
    html = ensure_i18n_script(html)
    html = html.replace(
        '<div class="qz-lang-slot" data-lang-slot="top"></div>',
        '<div class="qz-lang-slot" data-lang-slot="top">' + lang_switcher_html(loc) + "</div>",
    )
    html = html.replace(
        '<div data-lang-slot="menu"></div>',
        lang_switcher_html(loc, variant="list"),
    )
    # data-static on injected lists if present
    html = html.replace('id="qzSitesList"', 'id="qzSitesList" data-static="1"', 1)
    html = html.replace('id="qzBoardgamesList"', 'id="qzBoardgamesList" data-static="1"', 1)
    html = html.replace('id="writingList"', 'id="writingList" data-static="1"', 1)
    return html
