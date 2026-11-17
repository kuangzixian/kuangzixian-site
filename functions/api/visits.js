import { json } from "../_lib/guestbook.js";
import { handleVisits } from "../_lib/visits.js";

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const increment = url.searchParams.get("increment") === "1";
  return handleVisits(context, increment);
}

export async function onRequestPost(context) {
  return handleVisits(context, true);
}

export async function onRequestOptions() {
  return json({ ok: true }, 200);
}
