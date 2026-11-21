/**
 * Agent view: /?mode=agent redirects to the Markdown homepage.
 * Legacy conversation URLs: /chat?id=<id> and /chat.html?id=<id> go to /writing/<id>.
 * /music/report.html goes to the pretty URL /music/report.
 * Locale-prefixed writing pretty URLs and 404 pages are preserved.
 */
const CHAT_ID = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;
const LOCALES = /^(en|es|ko|ja)$/;


// Default language for the bare root, chosen from the visitor's country.
// An explicit choice from the language switcher (cookie "lang") wins.
const COUNTRY_LOCALE = { CN: "zh", HK: "zh", MO: "zh", TW: "zh", JP: "ja", KR: "ko", ES: "es" };
const LANG_COOKIE = /(?:^|;\s*)lang=(zh|en|es|ko|ja)(?:;|$)/;
const CRAWLER_UA = /bot\b|crawler|spider|slurp|googlebot|google-inspectiontool|googleother|bingbot|bingpreview|baiduspider|yandex|duckduckbot|applebot|sogou|360spider|bytespider|petalbot|facebookexternalhit|twitterbot|linkedinbot|embedly|slackbot|discordbot|telegrambot|whatsapp|ia_archiver|semrush|ahrefs|mj12bot|chatgpt|gptbot|claudebot|perplexity|ccbot/i;

function rootLanguageRedirect(request, url) {
  if (url.pathname !== "/" && url.pathname !== "/index.html") return null;
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  if (url.searchParams.has("mode")) return null;
  const ua = request.headers.get("User-Agent") || "";
  if (CRAWLER_UA.test(ua)) return null;
  const cookie = (request.headers.get("Cookie") || "").match(LANG_COOKIE);
  let want;
  if (cookie) {
    want = cookie[1];
  } else {
    const country = String((request.cf && request.cf.country) || "").toUpperCase();
    want = COUNTRY_LOCALE[country] || "en";
  }
  if (want === "zh") return null;
  const dest = new URL(`/${want}/${url.search}${url.hash}`, url.origin);
  return new Response(null, {
    status: 302,
    headers: {
      Location: dest.toString(),
      "Cache-Control": "private, no-store",
      Vary: "Cookie, User-Agent",
    },
  });
}

function withVary(response) {
  const headers = new Headers(response.headers);
  headers.set("Vary", headers.get("Vary") ? `${headers.get("Vary")}, Cookie` : "Cookie");
  headers.set("Cache-Control", "private, no-store");
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

function localePrefix(path) {
  const m = path.match(/^\/(en|es|ko|ja)(?=\/|$)/);
  return m ? m[1] : "";
}

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const path = url.pathname;
  const loc = localePrefix(path);
  const pre = loc ? `/${loc}` : "";
  const isHome = path === "/" || path === "/index.html" || path === `${pre}/` || path === `${pre}/index.html`;
  if (isHome && url.searchParams.get("mode") === "agent") {
    return Response.redirect(new URL("/index.md", url.origin), 302);
  }

  const langRedirect = rootLanguageRedirect(context.request, url);
  if (langRedirect) return langRedirect;
  if (path === "/" || path === "/index.html") {
    return withVary(await context.next());
  }

  if (path === "/chat" || path === "/chat.html") {
    const id = url.searchParams.get("id") || "";
    if (id && CHAT_ID.test(id)) {
      return Response.redirect(new URL(`/writing/${encodeURIComponent(id)}`, url.origin), 301);
    }
    return Response.redirect(new URL("/#writing", url.origin), 302);
  }

  if (path === "/music/report.html") {
    return Response.redirect(new URL("/music/report", url.origin), 301);
  }

  const writingExtra = path.match(/^(\/(?:en|es|ko|ja))?\/writing\/([A-Za-z0-9][A-Za-z0-9_-]*)(\.html|\/)$/);
  if (writingExtra && CHAT_ID.test(writingExtra[2])) {
    const prefix = writingExtra[1] || "";
    return Response.redirect(new URL(`${prefix}/writing/${writingExtra[2]}`, url.origin), 301);
  }

  const response = await context.next();
  if (response.status !== 404 || !loc) {
    return response;
  }
  try {
    const assetUrl = new URL(`/${loc}/404.html`, url.origin);
    const notFound = context.env && context.env.ASSETS
      ? await context.env.ASSETS.fetch(assetUrl)
      : await fetch(assetUrl);
    if (!notFound.ok) return response;
    const headers = new Headers(notFound.headers);
    headers.set("Cache-Control", "no-store");
    return new Response(notFound.body, { status: 404, statusText: "Not Found", headers });
  } catch (e) {
    return response;
  }
}
