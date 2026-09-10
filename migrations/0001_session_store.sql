-- P0 production SessionStore schema.
-- Application traffic should use the pooled DATABASE_URL.
-- Operational migrations should use a direct/unpooled connection when run externally.

CREATE TABLE IF NOT EXISTS baseball_sim_sessions (
    session_id TEXT PRIMARY KEY,
    save_payload JSONB NOT NULL,
    revision BIGINT NOT NULL CHECK (revision >= 1),
    save_version INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS baseball_sim_idempotency (
    session_id TEXT NOT NULL REFERENCES baseball_sim_sessions(session_id) ON DELETE CASCADE,
    idempotency_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    response_payload JSONB NOT NULL,
    resulting_revision BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (session_id, idempotency_key)
);
