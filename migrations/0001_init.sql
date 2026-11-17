-- Guestbook schema for kuangzixian
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL,
  ip_hash TEXT NOT NULL,
  hidden INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_messages_visible_created
  ON messages (hidden, created_at DESC);

-- Rate-limit log: one row per accepted POST, keyed by salted IP hash
CREATE TABLE IF NOT EXISTS rate_limits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_time
  ON rate_limits (ip_hash, created_at);
