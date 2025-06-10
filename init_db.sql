-- Drop old tables if they exist
DROP TABLE IF EXISTS coffee;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS cups;

-- Create users table for user settings
CREATE TABLE users (
    id TEXT PRIMARY KEY, -- UUID
    username TEXT NOT NULL
);

-- Create cups table for custom cup definitions
CREATE TABLE cups (
    id TEXT PRIMARY KEY, -- UUID
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    size REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create coffee table with username for multi-user support
CREATE TABLE coffee (
    id TEXT PRIMARY KEY, -- UUID
    user_id TEXT NOT NULL,
    amount REAL NOT NULL,
    cup_id TEXT, -- UUID
    timestamp TEXT NOT NULL,
    FOREIGN KEY (cup_id) REFERENCES cups(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Insert default user and default cup
INSERT INTO users (id, username) VALUES ('00000000-0000-0000-0000-000000000001', 'hlgr360');
INSERT INTO cups (id, user_id, name, size) VALUES ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000001', 'Standard Cup', 200);
