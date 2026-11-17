/**
 * Agent view: /?mode=agent redirects to the Markdown homepage.
 */
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const isHome = url.pathname === "/" || url.pathname === "/index.html";
  if (isHome && url.searchParams.get("mode") === "agent") {
    return Response.redirect(new URL("/index.md", url.origin), 302);
  }
  return context.next();
}
