-- Drop old tables if they exist
DROP TABLE IF EXISTS coffee;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS cups;
DROP TABLE IF EXISTS sessions;

-- Create users table for user settings and authentication
CREATE TABLE users (
    id TEXT PRIMARY KEY, -- UUID
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    must_change_password INTEGER NOT NULL DEFAULT 0
);

-- Create cups table for custom cup definitions
CREATE TABLE cups (
    id TEXT PRIMARY KEY, -- UUID
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    size REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create coffee table with user_id for multi-user support
CREATE TABLE coffee (
    id TEXT PRIMARY KEY, -- UUID
    user_id TEXT NOT NULL,
    amount REAL NOT NULL,
    cup_id TEXT, -- UUID
    timestamp TEXT NOT NULL,
    FOREIGN KEY (cup_id) REFERENCES cups(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create sessions table for session management
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

-- Insert default admin user (password: admin, must change on first login)
INSERT INTO users (id, username, password_hash, is_admin, must_change_password) VALUES (
    '00000000-0000-0000-0000-000000000000',
    'admin',
    '$2b$12$ovQIfjnEuhQAGAOE7JCbf.bfQRGAJxl5KkqYyvXxMIVS3bxf5P6vW',
    1,
    1
);

-- Insert default cup for admin
INSERT INTO cups (id, user_id, name, size) VALUES ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000000', 'Standard Cup', 200);
