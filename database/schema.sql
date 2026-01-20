PRAGMA foreign_keys = ON;

-- USERS
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY, -- UUID (TEXT) for portability in SQLite
  email TEXT NOT NULL UNIQUE,
  username TEXT NOT NULL UNIQUE,

  -- Argon2 encoded hash string (includes parameters + salt)
  password_hash TEXT NOT NULL,
  password_updated_at TEXT NOT NULL,

  -- 2FA (TOTP) state
  totp_enabled INTEGER NOT NULL DEFAULT 0,

  -- Anti-replay: last accepted TOTP time-step (monotonic counter)
  totp_last_used_step INTEGER,

  -- TOTP secret stored encrypted at rest (AES-256-GCM), encrypted server-side
  totp_secret_enc BLOB,
  totp_secret_nonce BLOB,
  totp_secret_tag BLOB,

  -- Per-user HMAC key (for message authenticity) stored encrypted at rest
  hmac_key_enc BLOB,
  hmac_key_nonce BLOB,
  hmac_key_tag BLOB,

  -- Account security state
  is_active INTEGER NOT NULL DEFAULT 1,
  failed_login_count INTEGER NOT NULL DEFAULT 0,
  locked_until TEXT,
  last_login_at TEXT,

  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- SESSIONS (server-side sessions recommended; token itself never stored)
CREATE TABLE IF NOT EXISTS user_sessions (
  id TEXT PRIMARY KEY, -- UUID
  user_id TEXT NOT NULL,

  -- SHA-256(token) to protect against DB read-only leakage
  session_token_hash BLOB NOT NULL,

  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  revoked_at TEXT,

  ip_address TEXT,
  user_agent TEXT,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_sessions_token_hash ON user_sessions(session_token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- MESSAGES
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY, -- UUID
  sender_user_id TEXT NOT NULL,

  -- Envelope encryption: per-message DEK encrypted with server KEK (AES-256-GCM)
  content_key_enc BLOB NOT NULL,
  content_key_nonce BLOB NOT NULL,
  content_key_tag BLOB NOT NULL,

  -- Encrypted subject/body (AES-256-GCM using per-message DEK)
  subject_ciphertext BLOB NOT NULL,
  subject_nonce BLOB NOT NULL,
  subject_tag BLOB NOT NULL,

  body_ciphertext BLOB NOT NULL,
  body_nonce BLOB NOT NULL,
  body_tag BLOB NOT NULL,

  -- Authenticity: HMAC-SHA-256 computed by backend using sender-specific key
  hmac_sha256 BLOB NOT NULL,

  created_at TEXT NOT NULL,
  deleted_by_sender_at TEXT,

  FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- MESSAGE RECIPIENTS (N:N)
CREATE TABLE IF NOT EXISTS message_recipients (
  message_id TEXT NOT NULL,
  recipient_user_id TEXT NOT NULL,

  delivered_at TEXT NOT NULL,
  read_at TEXT,
  deleted_at TEXT,

  -- Result of last authenticity verification (defense-in-depth, optional cache)
  authenticity_verified INTEGER NOT NULL DEFAULT 0,

  PRIMARY KEY (message_id, recipient_user_id),
  FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
  FOREIGN KEY (recipient_user_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_message_recipients_recipient ON message_recipients(recipient_user_id);

-- ATTACHMENTS (integral part of message, encrypted at rest)
CREATE TABLE IF NOT EXISTS attachments (
  id TEXT PRIMARY KEY, -- UUID
  message_id TEXT NOT NULL,

  filename TEXT NOT NULL,
  content_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,

  -- Encrypted blob (AES-256-GCM using message DEK or per-attachment DEK)
  blob_ciphertext BLOB NOT NULL,
  blob_nonce BLOB NOT NULL,
  blob_tag BLOB NOT NULL,

  created_at TEXT NOT NULL,

  FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attachments_message ON attachments(message_id);

-- AUDIT EVENTS (security-relevant events; do not store secrets)
CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,

  event_type TEXT NOT NULL,
  event_time TEXT NOT NULL,
  success INTEGER NOT NULL,

  ip_address TEXT,
  user_agent TEXT,

  -- Redacted detail (no tokens, no secrets, no ciphertext)
  details_redacted TEXT,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_time ON audit_events(event_time);
CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user_id);
