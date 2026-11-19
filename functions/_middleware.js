/**
 * Agent view: /?mode=agent redirects to the Markdown homepage.
 * Legacy conversation URLs: /chat?id=<id> and /chat.html?id=<id> go to /writing/<id>.
 * /music/report.html goes to the pretty URL /music/report.
 */
const CHAT_ID = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const path = url.pathname;
  const isHome = path === "/" || path === "/index.html";
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

  const writingExtra = path.match(/^\/writing\/([A-Za-z0-9][A-Za-z0-9_-]*)(\.html|\/)$/);
  if (writingExtra && CHAT_ID.test(writingExtra[1])) {
    return Response.redirect(new URL(`/writing/${writingExtra[1]}`, url.origin), 301);
  }

  return context.next();
}
