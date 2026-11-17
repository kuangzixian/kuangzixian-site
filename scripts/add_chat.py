#!/usr/bin/env python3
"""Fetch a ChatGPT share link into data/chats.json.

Usage:
  python3 scripts/add_chat.py https://chatgpt.com/s/t_xxxx
  python3 scripts/add_chat.py https://chatgpt.com/s/t_xxxx --prompt-url https://chatgpt.com/s/p_xxxx
  python3 scripts/add_chat.py https://chatgpt.com/s/p_xxxx   # prompt-only share

After fetching, edit the new entry's title, summary and tags in data/chats.json.
The homepage writing list is rendered from that file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "chats.json"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SHANGHAI = timezone(timedelta(hours=8))
FOLLOWUP_MARK = "\n---\n\nIf you want, I can:"


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8", errors="replace")


def script_payloads(html: str):
    for raw in re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL):
        text = raw.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                yield json.loads(text)
            except json.JSONDecodeError:
                continue


def walk(obj):
    yield obj
    if isinstance(obj, dict):
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def extract_share(html: str, url: str) -> dict:
    conversation = None
    prompt = None
    prompt_meta = None
    created_ms = None
    title = None
    messages = []

    for data in script_payloads(html):
        if not isinstance(data, dict):
            continue
        conv = data.get("conversation")
        if isinstance(conv, dict) and conv.get("messages"):
            conversation = conv
        default = data.get("composerDefaultValue")
        if isinstance(default, str) and default.strip():
            prompt = default.strip()
        post = data.get("sharedPromptPost")
        if isinstance(post, dict):
            prompt_meta = post
        sc = (conv or {}).get("sharedContent") if isinstance(conv, dict) else None
        if isinstance(sc, dict):
            created_ms = sc.get("originalCreatedAt") or created_ms
            title = sc.get("title") or title

    if conversation:
        title = conversation.get("title") or title
        sc = conversation.get("sharedContent") or {}
        created_ms = sc.get("originalCreatedAt") or created_ms
        for msg in conversation.get("messages") or []:
            role = msg.get("role") or "assistant"
            content = msg.get("content") or ""
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            if FOLLOWUP_MARK in content:
                content = content[: content.find(FOLLOWUP_MARK)].rstrip() + "\n"
            content = content.replace("\\.", ".")
            name = "GPT" if role == "assistant" else "匡子闲"
            messages.append({"role": role, "name": name, "content": content})

    # Prompt share pages keep the text in a signal too.
    if not prompt:
        m = re.search(
            r"Based on everything you know about me,[^\"\\]*",
            html,
        )
        # don't overfit; generic extraction of composerDefaultValue already handled

    if not messages and not prompt:
        raise SystemExit(f"Could not find a conversation or prompt in {url}")

    date = None
    dt = None
    if created_ms:
        ts = float(created_ms)
        if ts > 1e12:
            ts /= 1000
        aware = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(SHANGHAI)
        date = aware.strftime("%Y-%m-%d")
        dt = aware.replace(microsecond=0).isoformat()

    kind = "prompt" if (prompt and not messages) else "conversation"
    return {
        "kind": kind,
        "title": None if (not title or title == "Check out this chat") else title,
        "date": date,
        "datetime": dt,
        "source_url": url if kind == "conversation" else None,
        "prompt_url": url if kind == "prompt" else None,
        "prompt": prompt,
        "messages": messages,
    }


def slugify(text: str, fallback: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    raw = raw[:48] or fallback
    return raw


def load_data() -> dict:
    if DATA.exists():
        return json.loads(DATA.read_text())
    return {"updated_at": None, "chats": []}


def unique_id(existing: set[str], base: str) -> str:
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="ChatGPT share URL (s/t_... or s/p_...)")
    parser.add_argument("--prompt-url", help="Optional shared prompt URL (s/p_...)")
    parser.add_argument("--id", help="Optional id for the new entry")
    args = parser.parse_args(argv)

    print("Fetching", args.url)
    primary = extract_share(fetch_html(args.url), args.url)
    if args.prompt_url:
        print("Fetching prompt", args.prompt_url)
        prompt_share = extract_share(fetch_html(args.prompt_url), args.prompt_url)
        if prompt_share.get("prompt"):
            primary["prompt"] = prompt_share["prompt"]
            primary["prompt_url"] = args.prompt_url
        if prompt_share.get("messages") and not primary.get("messages"):
            primary["messages"] = prompt_share["messages"]
            primary["source_url"] = primary.get("source_url") or args.url

    # If the primary URL was a prompt, keep it as the prompt and wait for messages.
    if primary["kind"] == "prompt" and not primary["messages"]:
        # Still store it as a user-only entry; reviewer should add the reply later.
        primary["messages"] = [
            {"role": "user", "name": "匡子闲", "content": primary["prompt"] or ""}
        ]

    if primary.get("prompt") and primary["messages"]:
        first = primary["messages"][0]
        if first.get("role") != "user" or first.get("content") != primary["prompt"]:
            primary["messages"] = [
                {"role": "user", "name": "匡子闲", "content": primary["prompt"]}
            ] + primary["messages"]

    data = load_data()
    ids = {c.get("id") for c in data.get("chats") or []}
    fallback = re.sub(r".*/s/", "", args.url).strip("/").replace("_", "-")[:24] or "chat"
    base = args.id or slugify(primary.get("title") or "", fallback)
    chat_id = unique_id(ids, base)

    now = datetime.now(SHANGHAI).replace(microsecond=0).isoformat()
    entry = {
        "id": chat_id,
        "title": primary.get("title") or "请填写标题",
        "title_en": "",
        "summary": "请填写摘要",
        "summary_en": "",
        "date": primary.get("date") or now[:10],
        "datetime": primary.get("datetime") or now,
        "tags": ["ChatGPT"],
        "source_url": primary.get("source_url") or args.url,
        "prompt_url": primary.get("prompt_url") or "",
        "prompt": primary.get("prompt") or "",
        "messages": primary["messages"],
    }
    data.setdefault("chats", [])
    data["chats"].insert(0, entry)
    data["updated_at"] = now
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Added {chat_id} with {len(entry['messages'])} message(s) to {DATA}")
    if entry["title"] == "请填写标题":
        print("Title was generic; please edit title, summary and tags in data/chats.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
