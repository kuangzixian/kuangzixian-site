#!/usr/bin/env bash
# Deploy the site and guestbook API to Cloudflare Pages with D1.
# Requires:
#   CLOUDFLARE_API_TOKEN   (see README for required permissions)
#   CLOUDFLARE_ACCOUNT_ID  defaults to the kuangzixian Pages account
#
# This script does not set ADMIN_TOKEN or IP_HASH_SALT.
# After the first deploy, set them once:
#   npx wrangler pages secret put ADMIN_TOKEN --project-name kuangzixian
#   npx wrangler pages secret put IP_HASH_SALT --project-name kuangzixian
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PROJECT_NAME="kuangzixian"
DB_NAME="kuangzixian-guestbook"
ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-5c671af519baf38ea22b836d9430674a}"
export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "CLOUDFLARE_API_TOKEN is required. Do not use the dashboard zip upload;" >&2
  echo "Functions are only deployed by wrangler." >&2
  exit 1
fi

WRANGLER=(npx --yes wrangler)

echo "==> Looking up D1 database $DB_NAME"
DB_ID=""
if LIST_JSON="$("${WRANGLER[@]}" d1 list --json 2>/dev/null)"; then
  DB_ID="$(python3 -c '
import json, sys
name = sys.argv[1]
rows = json.loads(sys.stdin.read() or "[]")
if isinstance(rows, dict):
    rows = rows.get("result") or rows.get("databases") or []
for row in rows:
    if row.get("name") == name:
        print(row.get("uuid") or row.get("id") or "")
        break
' "$DB_NAME" <<<"$LIST_JSON")"
fi

if [[ -z "$DB_ID" ]]; then
  echo "==> Creating D1 database $DB_NAME"
  CREATE_OUT="$("${WRANGLER[@]}" d1 create "$DB_NAME")"
  printf "%s\n" "$CREATE_OUT"
  DB_ID="$(printf "%s\n" "$CREATE_OUT" | python3 -c '
import re, sys
text = sys.stdin.read()
m = re.search(r"database_id\s*=\s*\"([0-9a-fA-F-]{36})\"", text)
if not m:
    m = re.search(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", text)
print(m.group(1) if m and m.lastindex else (m.group(0) if m else ""))
')"
fi

if [[ -z "$DB_ID" ]]; then
  echo "Could not determine D1 database id for $DB_NAME" >&2
  exit 1
fi

echo "==> Using database_id=$DB_ID"
python3 - "$ROOT/wrangler.toml" "$DB_ID" << 'PY'
from pathlib import Path
import re, sys
path = Path(sys.argv[1])
db_id = sys.argv[2]
text = path.read_text()
new, n = re.subn(
    r'(database_id\s*=\s*")[^"]*(")',
    r"\1" + db_id + r"\2",
    text,
    count=1,
)
if n != 1:
    raise SystemExit("failed to update database_id in wrangler.toml")
path.write_text(new)
PY

echo "==> Applying D1 migrations (remote)"
"${WRANGLER[@]}" d1 migrations apply "$DB_NAME" --remote

echo "==> Building static output"
python3 "$ROOT/scripts/build_dist.py"

echo "==> Deploying Pages project $PROJECT_NAME (branch main)"
"${WRANGLER[@]}" pages deploy "$ROOT/dist" --project-name "$PROJECT_NAME" --branch main

echo
echo "Deploy finished."
echo "If this is the first time, set the secrets (values are not stored in the repo):"
echo "  npx wrangler pages secret put ADMIN_TOKEN --project-name $PROJECT_NAME"
echo "  npx wrangler pages secret put IP_HASH_SALT --project-name $PROJECT_NAME"
