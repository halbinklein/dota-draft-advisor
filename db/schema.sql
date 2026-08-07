CREATE TABLE IF NOT EXISTS heroes (
    hero_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_own_pool INTEGER,
    raw_json TEXT,
    patch_version TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hero_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_id TEXT NOT NULL,
    position TEXT NOT NULL,
    is_own_pool INTEGER,
    FOREIGN KEY (hero_id) REFERENCES heroes(hero_id),
    UNIQUE(hero_id, position, is_own_pool)
);

CREATE TABLE IF NOT EXISTS matchups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    own_hero_id TEXT NOT NULL,
    enemy_hero_id TEXT NOT NULL,
    enemy_position TEXT NOT NULL,
    patch_version TEXT,
    analisis_mecanico_previo TEXT,
    score_laning REAL,
    score_midgame REAL,
    score_lategame REAL,
    razon TEXT,
    recommended_items TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (own_hero_id) REFERENCES heroes(hero_id),
    FOREIGN KEY (enemy_hero_id) REFERENCES heroes(hero_id),
    UNIQUE(own_hero_id, enemy_hero_id, enemy_position, patch_version)
);

CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,
    name TEXT,
    raw_json TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);