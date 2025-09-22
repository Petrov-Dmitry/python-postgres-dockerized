-- Migration: 20250922002855_initial
-- Title: initial
-- Created: 2025-09-22 00:28:55

-- UP migration
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level INTEGER,
    message TEXT
);

-- DOWN migration
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS logs;
