SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  display_name TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);
CREATE INDEX IF NOT EXISTS sessions_expires_at_idx ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS canonical_entities (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  country_code TEXT,
  metadata TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(kind, name COLLATE NOCASE)
);
CREATE INDEX IF NOT EXISTS canonical_entities_kind_idx ON canonical_entities(kind);
CREATE TABLE IF NOT EXISTS entity_aliases (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES canonical_entities(id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(entity_id, alias COLLATE NOCASE)
);
CREATE INDEX IF NOT EXISTS entity_aliases_entity_id_idx ON entity_aliases(entity_id);

CREATE TABLE IF NOT EXISTS beans (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  roaster_id TEXT NOT NULL REFERENCES canonical_entities(id),
  producer_id TEXT REFERENCES canonical_entities(id),
  farm_id TEXT REFERENCES canonical_entities(id),
  country_code TEXT,
  variety_id TEXT REFERENCES canonical_entities(id),
  process_id TEXT REFERENCES canonical_entities(id),
  roast_level TEXT,
  roast_date TEXT,
  notes TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS beans_roaster_id_idx ON beans(roaster_id);

CREATE TABLE IF NOT EXISTS shots (
  id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  duration REAL NOT NULL,
  measurements BLOB NOT NULL,
  workflow TEXT NOT NULL DEFAULT '{}',
  annotations TEXT,
  created_at TEXT NOT NULL
);
"""

DEFAULT_PROCESSES = (
    "Washed",
    "Natural",
    "Honey",
    "Anaerobic",
    "Anaerobic Natural",
    "Anaerobic Washed",
    "Carbonic Maceration",
    "Decaf",
)
