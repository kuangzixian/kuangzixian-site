/**
 * Agent view: /?mode=agent redirects to the Markdown homepage.
 * Legacy conversation URLs: /chat?id=<id> and /chat.html?id=<id> go to /writing/<id>.
 * /music/report.html goes to the pretty URL /music/report.
 * Locale-prefixed writing pretty URLs and 404 pages are preserved.
 */
const CHAT_ID = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;
const LOCALES = /^(en|es|ko|ja)$/;

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
