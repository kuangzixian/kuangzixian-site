const NICKNAME_MIN = 1;
const NICKNAME_MAX = 20;
const CONTENT_MIN = 1;
const CONTENT_MAX = 500;
const RATE_LIMIT_MAX = 3;
const RATE_WINDOW_MS = 10 * 60 * 1000;

const SPAM_KEYWORDS = [
  "加微信",
  "加微信号",
  "加v信",
  "免费领取",
  "点击领取",
  "兼职日赚",
  "刷单",
  "代刷",
  "彩票平台",
  "viagra",
  "cialis",
  "crypto airdrop",
  "t.me/",
  "telegram.me/",
  "推广返利",
];

const LINK_RE =
  /https?:\/\/|https?\s*:\s*\/\//i;
const WWW_RE = /\bwww\./i;
const DOMAIN_RE =
  /(?:^|[\s<(（【[])[a-z0-9][a-z0-9.-]*\.(?:com|cn|net|org|xyz|top|info|io|cc|me|co|shop|vip|app|dev)\b/i;

export function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

export function clientIp(request) {
  const cf = request.headers.get("CF-Connecting-IP");
  if (cf && cf.trim()) return cf.trim();
  const xff = request.headers.get("X-Forwarded-For");
  if (xff) {
    const first = xff.split(",")[0].trim();
    if (first) return first;
  }
  const real = request.headers.get("X-Real-IP");
  if (real && real.trim()) return real.trim();
  return "127.0.0.1";
}

export async function hashIp(ip, salt) {
  const data = new TextEncoder().encode(String(salt) + ":" + String(ip));
  const buf = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(buf);
  let out = "";
  for (let i = 0; i < bytes.length; i++) {
    out += bytes[i].toString(16).padStart(2, "0");
  }
  return out;
}

function stripHtml(input) {
  return String(input || "").replace(/<[^>]*>/g, "");
}

function stripControls(input, allowNewline) {
  let out = "";
  for (const ch of input) {
    const code = ch.codePointAt(0);
    if (code === 9) {
      out += " ";
      continue;
    }
    if (allowNewline && (code === 10 || code === 13)) {
      out += ch;
      continue;
    }
    if (code < 32 || code === 127) continue;
    out += ch;
  }
  return out;
}

function charLen(s) {
  return Array.from(s).length;
}

export function cleanNickname(raw) {
  const s = stripControls(stripHtml(raw), false).replace(/\s+/g, " ").trim();
  return s;
}

export function cleanContent(raw) {
  const s = stripControls(stripHtml(raw), true)
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return s;
}

export function hasLink(text) {
  return LINK_RE.test(text) || WWW_RE.test(text) || DOMAIN_RE.test(text);
}

export function hasSpam(text) {
  const lower = text.toLowerCase();
  for (let i = 0; i < SPAM_KEYWORDS.length; i++) {
    const kw = SPAM_KEYWORDS[i];
    if (kw.toLowerCase() !== kw) {
      if (text.indexOf(kw) !== -1) return true;
    } else if (lower.indexOf(kw) !== -1) {
      return true;
    }
  }
  return false;
}

export function validatePost(nickname, content, honeypot) {
  if (honeypot && String(honeypot).trim() !== "") {
    return { ok: false, honeypot: true };
  }
  if (!nickname || charLen(nickname) < NICKNAME_MIN || charLen(nickname) > NICKNAME_MAX) {
    return { ok: false, error: "invalid_nickname", status: 400 };
  }
  if (!content || charLen(content) < CONTENT_MIN || charLen(content) > CONTENT_MAX) {
    return { ok: false, error: "invalid_content", status: 400 };
  }
  if (hasLink(nickname) || hasLink(content)) {
    return { ok: false, error: "has_link", status: 400 };
  }
  if (hasSpam(nickname) || hasSpam(content)) {
    return { ok: false, error: "spam", status: 400 };
  }
  return { ok: true };
}

export function publicMessage(row) {
  return {
    id: row.id,
    nickname: row.nickname,
    content: row.content,
    created_at: row.created_at,
  };
}

export function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const max = Math.max(a.length, b.length);
  let r = a.length ^ b.length;
  for (let i = 0; i < max; i++) {
    r |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  }
  return r === 0;
}

export function adminAuthorized(request, env) {
  const token = env && env.ADMIN_TOKEN;
  if (!token) return false;
  const header = request.headers.get("Authorization") || "";
  const bearer = header.startsWith("Bearer ") ? header.slice(7).trim() : "";
  const alt = (request.headers.get("X-Admin-Token") || "").trim();
  return safeEqual(bearer, token) || safeEqual(alt, token);
}

export async function listMessages(db) {
  const result = await db
    .prepare(
      "SELECT id, nickname, content, created_at FROM messages WHERE hidden = 0 ORDER BY created_at DESC, id DESC LIMIT 50"
    )
    .all();
  return (result.results || []).map(publicMessage);
}

export async function addMessage(db, env, request, nickname, content) {
  const salt = env && env.IP_HASH_SALT;
  if (!salt) {
    return { ok: false, error: "unavailable", status: 500 };
  }
  const ip = clientIp(request);
  const ipHash = await hashIp(ip, salt);
  const now = new Date();
  const createdAt = now.toISOString();
  const windowStart = new Date(now.getTime() - RATE_WINDOW_MS).toISOString();

  const counted = await db
    .prepare(
      "SELECT COUNT(*) AS n FROM rate_limits WHERE ip_hash = ? AND created_at >= ?"
    )
    .bind(ipHash, windowStart)
    .first();
  const n = counted && typeof counted.n === "number" ? counted.n : Number(counted && counted.n) || 0;
  if (n >= RATE_LIMIT_MAX) {
    return { ok: false, error: "too_fast", status: 429 };
  }

  const inserted = await db
    .prepare(
      "INSERT INTO messages (nickname, content, created_at, ip_hash, hidden) VALUES (?, ?, ?, ?, 0) RETURNING id, nickname, content, created_at"
    )
    .bind(nickname, content, createdAt, ipHash)
    .first();

  await db
    .prepare("INSERT INTO rate_limits (ip_hash, created_at) VALUES (?, ?)")
    .bind(ipHash, createdAt)
    .run();

  await db
    .prepare("DELETE FROM rate_limits WHERE created_at < ?")
    .bind(windowStart)
    .run();

  return { ok: true, message: publicMessage(inserted) };
}

export async function hideMessage(db, id) {
  const num = Number(id);
  if (!Number.isInteger(num) || num <= 0) {
    return { ok: false, error: "not_found", status: 404 };
  }
  const existing = await db
    .prepare("SELECT id, hidden FROM messages WHERE id = ?")
    .bind(num)
    .first();
  if (!existing || existing.hidden) {
    return { ok: false, error: "not_found", status: 404 };
  }
  await db.prepare("UPDATE messages SET hidden = 1 WHERE id = ?").bind(num).run();
  return { ok: true };
}
