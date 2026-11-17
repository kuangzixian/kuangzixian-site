-- Visit counter for kuangzixian.pages.dev
-- Seeded from Cloudflare GraphQL Analytics, zone kuangzixian.pages.dev
-- (zoneTag b86624425e38a8dafd09512c9df9846b), dataset httpRequests1dGroups,
-- filter date_geq "2026-11-14" (site launch) through 2026-11-17 inclusive.
-- Metric: sum of daily uniq.uniques = 71+118+35+63 = 287.
-- Period-unique uniques (not split by day) was 285; pageViews summed to 1074.
-- Daily uniques is the closest historical match to "at most once per visitor per day".

CREATE TABLE IF NOT EXISTS visit_totals (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  total INTEGER NOT NULL,
  seed INTEGER NOT NULL,
  seed_note TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

INSERT INTO visit_totals (id, total, seed, seed_note, updated_at)
VALUES (
  1,
  287,
  287,
  'Cloudflare GraphQL httpRequests1dGroups uniq.uniques for zone kuangzixian.pages.dev, sum of daily uniques 2026-11-14..2026-11-17 (71+118+35+63). Period uniques=285, pageViews=1074. Snapshot queried 2026-11-17.',
  '2026-11-17T12:00:00+08:00'
);

CREATE TABLE IF NOT EXISTS visit_days (
  day TEXT PRIMARY KEY,
  count INTEGER NOT NULL
);

INSERT INTO visit_days (day, count) VALUES
  ('2026-11-14', 71),
  ('2026-11-15', 118),
  ('2026-11-16', 35),
  ('2026-11-17', 63);

CREATE TABLE IF NOT EXISTS visit_uniques (
  day TEXT NOT NULL,
  ip_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (day, ip_hash)
);
