import { json, clientIp, hashIp } from "./guestbook.js";

const COOKIE = "qz_visit_day";
const TZ = "Asia/Shanghai";

const BOT_RE = new RegExp(
  [
    "bot",
    "spider",
    "crawler",
    "crawl",
    "slurp",
    "headless",
    "puppeteer",
    "playwright",
    "lighthouse",
    "phantomjs",
    "selenium",
    "curl/",
    "wget",
    "httpie",
    "python-requests",
    "python-urllib",
    "go-http-client",
    "node-fetch",
    "axios/",
    "libwww",
    "scrapy",
    "cfnetwork/?0",
    "preview-extractor",
    "kuang-site-verify",
    "wrangler",
    "gptbot",
    "chatgpt",
    "claudebot",
    "anthropic",
    "ccbot",
    "bytespider",
    "google-extended",
    "googlebot",
    "bingbot",
    "baiduspider",
    "yandex",
    "duckduckbot",
    "facebookexternalhit",
    "twitterbot",
    "linkedinbot",
    "slackbot",
    "discordbot",
    "telegram",
    "whatsapp",
    "applebot",
    "semrush",
    "ahrefs",
    "mj12bot",
    "dotbot",
    "petalbot",
    "qwen-agent",
    "deepseekbot",
  ].join("|"),
  "i"
);

export function shanghaiDay(date) {
  const d = date || new Date();
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: TZ,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(d);
  } catch (e) {
    return d.toISOString().slice(0, 10);
  }
}

export function isBot(request) {
  const ua = request.headers.get("user-agent") || "";
  if (!ua.trim()) return true;
  if (BOT_RE.test(ua)) return true;
  return false;
}

function cookieDay(request) {
  const raw = request.headers.get("Cookie") || "";
  const parts = raw.split(";");
  for (const part of parts) {
    const [k, ...rest] = part.trim().split("=");
    if (k === COOKIE) return decodeURIComponent(rest.join("=") || "");
  }
  return "";
}

function setCookieHeader(day, request) {
  const url = new URL(request.url);
  const secure = url.protocol === "https:" ? "; Secure" : "";
  return `${COOKIE}=${encodeURIComponent(day)}; Path=/; Max-Age=172800; SameSite=Lax${secure}`;
}

export async function readCounts(env, day) {
  const totalRow = await env.DB.prepare(
    "SELECT total FROM visit_totals WHERE id = 1"
  ).first();
  const dayRow = await env.DB.prepare(
    "SELECT count FROM visit_days WHERE day = ?"
  )
    .bind(day)
    .first();
  return {
    total: Number((totalRow && totalRow.total) || 0),
    today: Number((dayRow && dayRow.count) || 0),
  };
}

export async function handleVisits(context, shouldIncrement) {
  const { request, env } = context;
  if (!env || !env.DB) {
    return json({ ok: false, error: "unavailable" }, 503);
  }
  const day = shanghaiDay();
  const alreadyCookie = cookieDay(request) === day;
  const bot = isBot(request);

  if (!shouldIncrement || bot || alreadyCookie) {
    const counts = await readCounts(env, day);
    const headers = { "cache-control": "no-store" };
    if (!bot && alreadyCookie) {
      // refresh cookie
    }
    const res = json(
      { ok: true, total: counts.total, today: counts.today, counted: false, already: alreadyCookie, bot },
      200
    );
    if (!bot) {
      const h = new Headers(res.headers);
      h.set("Set-Cookie", setCookieHeader(day, request));
      return new Response(res.body, { status: 200, headers: h });
    }
    return res;
  }

  const salt = env.IP_HASH_SALT || "visits-fallback-salt";
  const ip = clientIp(request);
  const ipHash = await hashIp(ip + ":" + day, salt);
  const now = new Date().toISOString();

  const inserted = await env.DB.prepare(
    "INSERT OR IGNORE INTO visit_uniques (day, ip_hash, created_at) VALUES (?, ?, ?)"
  )
    .bind(day, ipHash, now)
    .run();

  const changed = inserted && inserted.meta && inserted.meta.changes === 1;
  if (changed) {
    await env.DB.batch([
      env.DB.prepare(
        "INSERT INTO visit_days (day, count) VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET count = count + 1"
      ).bind(day),
      env.DB.prepare(
        "UPDATE visit_totals SET total = total + 1, updated_at = ? WHERE id = 1"
      ).bind(now),
    ]);
  }

  const counts = await readCounts(env, day);
  const body = {
    ok: true,
    total: counts.total,
    today: counts.today,
    counted: Boolean(changed),
    already: !changed,
    bot: false,
  };
  const res = json(body, 200);
  const headers = new Headers(res.headers);
  headers.set("Set-Cookie", setCookieHeader(day, request));
  return new Response(res.body, { status: 200, headers });
}
