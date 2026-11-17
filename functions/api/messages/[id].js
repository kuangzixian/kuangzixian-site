import { json, adminAuthorized, hideMessage } from "../../_lib/guestbook.js";

export async function onRequestDelete(context) {
  try {
    if (!adminAuthorized(context.request, context.env)) {
      return json({ ok: false, error: "forbidden" }, 401);
    }
    if (!context.env || !context.env.DB) {
      return json({ ok: false, error: "unavailable" }, 503);
    }
    const result = await hideMessage(context.env.DB, context.params.id);
    if (!result.ok) {
      return json({ ok: false, error: result.error }, result.status);
    }
    return json({ ok: true });
  } catch (err) {
    console.error("DELETE /api/messages/:id", err);
    return json({ ok: false, error: "unavailable" }, 503);
  }
}
