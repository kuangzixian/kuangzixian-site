#!/usr/bin/env bash
# Soft-delete a guestbook message on the live site.
# Usage: scripts/delete_message.sh <id>
set -euo pipefail

ID="${1:-}"
if [[ ! "$ID" =~ ^[0-9]+$ ]]; then
  echo "Usage: $0 <id>" >&2
  exit 1
fi

TOKEN_FILE="${KUANG_ADMIN_TOKEN_FILE:-/home/box/secrets/kuangzixian-admin-token}"
if [[ ! -r "$TOKEN_FILE" ]]; then
  echo "Cannot read admin token file: $TOKEN_FILE" >&2
  exit 1
fi
TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
if [[ -z "$TOKEN" ]]; then
  echo "Admin token file is empty: $TOKEN_FILE" >&2
  exit 1
fi

BASE="${KUANG_SITE_URL:-https://kuangzixian.pages.dev}"

curl -sS -X DELETE "$BASE/api/messages/$ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
echo
