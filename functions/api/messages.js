import {
  json,
  cleanNickname,
  cleanContent,
  validatePost,
  listMessages,
  addMessage,
} from "../_lib/guestbook.js";

export async function onRequestGet(context) {
  try {
    if (!context.env || !context.env.DB) {
      return json({ ok: false, error: "unavailable" }, 503);
    }
    const messages = await listMessages(context.env.DB);
    return json({ ok: true, messages });
  } catch (err) {
    console.error("GET /api/messages", err);
    return json({ ok: false, error: "unavailable" }, 503);
  }
}

export async function onRequestPost(context) {
  try {
    if (!context.env || !context.env.DB) {
      return json({ ok: false, error: "unavailable" }, 503);
    }
    let body = {};
    try {
      body = await context.request.json();
    } catch (e) {
      return json({ ok: false, error: "invalid_content" }, 400);
    }
    const nickname = cleanNickname(body.nickname);
    const content = cleanContent(body.content);
    const honeypot = body.website || body.hp || "";
    const check = validatePost(nickname, content, honeypot);
    if (check.honeypot) {
      return json({ ok: true, ignored: true }, 201);
    }
    if (!check.ok) {
      return json({ ok: false, error: check.error }, check.status);
    }
    const result = await addMessage(
      context.env.DB,
      context.env,
      context.request,
      nickname,
      content
    );
    if (!result.ok) {
      return json({ ok: false, error: result.error }, result.status);
    }
    return json({ ok: true, message: result.message }, 201);
  } catch (err) {
    console.error("POST /api/messages", err);
    return json({ ok: false, error: "unavailable" }, 503);
  }
}
