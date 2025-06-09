-- Drop old tables if they exist
DROP TABLE IF EXISTS coffee;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS cups;

-- Create settings table for user settings
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL
);

-- Create cups table for custom cup definitions
CREATE TABLE cups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    name TEXT NOT NULL,
    size REAL NOT NULL
);

-- Create coffee table with username for multi-user support
CREATE TABLE coffee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    amount REAL NOT NULL,
    cup_id INTEGER,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (cup_id) REFERENCES cups(id)
);

-- Insert default user and default cup
INSERT INTO settings (username) VALUES ('hlgr360');
INSERT INTO cups (user, name, size) VALUES ('hlgr360', 'Standard Cup', 200);
