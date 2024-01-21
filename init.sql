PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS rss(
    id INTEGER NOT NULL PRIMARY KEY,
    name text NOT NULL,
    link text NOT NULL,
    etag text,
    created_at timestamp NOT NULL DEFAULT current_timestamp,
    updated_at timestamp NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS urlCondition (
    id INTEGER NOT NULL PRIMARY KEY,
    url text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS contentCondition (
    id INTEGER NOT NULL PRIMARY KEY,
    content text NOT NULL,
    url_condition_id INTEGER NOT NULL,
    FOREIGN KEY (url_condition_id) REFERENCES urlCondition(id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS UpdateLastTime UPDATE OF name, link, etag ON rss
BEGIN
    UPDATE rss SET updated_at=CURRENT_TIMESTAMP WHERE id=NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS remove_url_condition AFTER DELETE ON urlCondition
BEGIN
  DELETE FROM urlCondition
  WHERE id = OLD.id
    AND NOT EXISTS (SELECT 1 FROM contentCondition WHERE url_condition_id = OLD.id);
END;