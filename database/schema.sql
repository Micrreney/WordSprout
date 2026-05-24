PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS word_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL REFERENCES word_lists(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    definition TEXT DEFAULT '',
    phonetic TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL UNIQUE REFERENCES words(id) ON DELETE CASCADE,
    ease_factor REAL DEFAULT 2.5,
    interval INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    next_review_date DATE DEFAULT (date('now')),
    last_review_date DATE,
    last_quality INTEGER
);

CREATE TABLE IF NOT EXISTS daily_rewards (
    date DATE PRIMARY KEY,
    words_reviewed INTEGER DEFAULT 0,
    water_drops INTEGER DEFAULT 0,
    sunshine INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS plant_state (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    stage INTEGER DEFAULT 0,
    total_water INTEGER DEFAULT 0,
    total_sunshine INTEGER DEFAULT 0,
    plant_type TEXT DEFAULT 'default',
    last_water_decay_date DATE DEFAULT (date('now'))
);

INSERT OR IGNORE INTO plant_state (id) VALUES (1);
