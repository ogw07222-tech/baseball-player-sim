"""Transactional session persistence for the HTTP production bridge."""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class StoredSession:
    session_id: str
    payload: dict[str, object]
    revision: int
    save_version: int
    updated_at: str


@dataclass(frozen=True)
class MutationCommit:
    response: dict[str, object]
    revision: int
    replayed: bool


class RevisionConflict(RuntimeError):
    def __init__(self, revision: int) -> None:
        super().__init__(f"expected revision does not match current revision {revision}")
        self.revision = revision


class IdempotencyConflict(RuntimeError):
    pass


class StoreUnavailable(RuntimeError):
    """Raised when the configured durable store cannot complete an operation."""


class SessionStore(Protocol):
    def get(self, session_id: str) -> StoredSession | None: ...
    def replace(self, session_id: str, payload: dict[str, object]) -> StoredSession: ...
    def mutate(
        self,
        session_id: str,
        *,
        expected_revision: int,
        idempotency_key: str,
        fingerprint: str,
        mutator: Callable[[dict[str, object]], tuple[dict[str, object], dict[str, object]]],
    ) -> MutationCommit: ...


class _JsonCodec:
    @staticmethod
    def _encode(payload: dict[str, object]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

    @staticmethod
    def _decode(raw: object) -> dict[str, object]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        if not isinstance(raw, str):
            raise ValueError("stored save payload must be JSON object data")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("stored save payload must be an object")
        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


class SQLiteSessionStore(_JsonCodec):
    """SQLite adapter for local development and CI.

    SQLite provides the exact transaction/CAS semantics required by the vertical
    slice. It is intentionally not treated as a production Vercel authority.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    save_payload TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    save_version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency (
                    session_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    response_payload TEXT NOT NULL,
                    resulting_revision INTEGER NOT NULL,
                    PRIMARY KEY (session_id, idempotency_key),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
                """
            )

    def get(self, session_id: str) -> StoredSession | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT session_id, save_payload, revision, save_version, updated_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredSession(
            session_id=str(row["session_id"]),
            payload=self._decode(str(row["save_payload"])),
            revision=int(row["revision"]),
            save_version=int(row["save_version"]),
            updated_at=str(row["updated_at"]),
        )

    def replace(self, session_id: str, payload: dict[str, object]) -> StoredSession:
        save_version = int(payload.get("save_version", 1))
        updated_at = self._now()
        encoded = self._encode(payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO sessions(session_id, save_payload, revision, save_version, updated_at)
                    VALUES(?, ?, 1, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        save_payload=excluded.save_payload,
                        revision=1,
                        save_version=excluded.save_version,
                        updated_at=excluded.updated_at
                    """,
                    (session_id, encoded, save_version, updated_at),
                )
                connection.execute("DELETE FROM idempotency WHERE session_id = ?", (session_id,))
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return StoredSession(session_id, payload, 1, save_version, updated_at)

    def mutate(
        self,
        session_id: str,
        *,
        expected_revision: int,
        idempotency_key: str,
        fingerprint: str,
        mutator: Callable[[dict[str, object]], tuple[dict[str, object], dict[str, object]]],
    ) -> MutationCommit:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                replay = connection.execute(
                    """
                    SELECT fingerprint, response_payload, resulting_revision
                    FROM idempotency WHERE session_id = ? AND idempotency_key = ?
                    """,
                    (session_id, idempotency_key),
                ).fetchone()
                if replay is not None:
                    if str(replay["fingerprint"]) != fingerprint:
                        raise IdempotencyConflict("idempotency key reused with a different request")
                    response = self._decode(str(replay["response_payload"]))
                    revision = int(replay["resulting_revision"])
                    connection.execute("COMMIT")
                    return MutationCommit(response=response, revision=revision, replayed=True)

                row = connection.execute(
                    "SELECT save_payload, revision FROM sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(session_id)
                revision = int(row["revision"])
                if revision != expected_revision:
                    raise RevisionConflict(revision)

                current_payload = self._decode(str(row["save_payload"]))
                new_payload, response = mutator(current_payload)
                new_revision = revision + 1
                updated_at = self._now()
                save_version = int(new_payload.get("save_version", 1))
                cursor = connection.execute(
                    """
                    UPDATE sessions
                    SET save_payload = ?, revision = ?, save_version = ?, updated_at = ?
                    WHERE session_id = ? AND revision = ?
                    """,
                    (
                        self._encode(new_payload),
                        new_revision,
                        save_version,
                        updated_at,
                        session_id,
                        revision,
                    ),
                )
                if cursor.rowcount != 1:
                    latest = connection.execute(
                        "SELECT revision FROM sessions WHERE session_id = ?", (session_id,)
                    ).fetchone()
                    raise RevisionConflict(int(latest["revision"]) if latest else revision)
                response_with_revision = dict(response)
                response_with_revision["meta"] = {"revision": new_revision}
                connection.execute(
                    """
                    INSERT INTO idempotency(
                        session_id, idempotency_key, fingerprint, response_payload, resulting_revision
                    ) VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        idempotency_key,
                        fingerprint,
                        self._encode(response_with_revision),
                        new_revision,
                    ),
                )
                connection.execute("COMMIT")
                return MutationCommit(
                    response=response_with_revision,
                    revision=new_revision,
                    replayed=False,
                )
            except Exception:
                connection.execute("ROLLBACK")
                raise


class PostgresSessionStore(_JsonCodec):
    """External transactional store for Vercel/serverless production.

    The adapter intentionally uses only the SessionStore contract. A row-level
    lock serializes mutations per anonymous career session, so only the request
    that owns the current revision can run the authoritative simulation.
    """

    def __init__(self, database_url: str) -> None:
        if not database_url.strip():
            raise ValueError("database_url is required")
        self.database_url = database_url
        self._initialized = False
        self._initialize_lock = threading.Lock()

    def _connect(self):
        return psycopg.connect(
            self.database_url,
            connect_timeout=10,
            row_factory=dict_row,
        )

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._initialize_lock:
            if self._initialized:
                return
            try:
                with self._connect() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS baseball_sim_sessions (
                                session_id TEXT PRIMARY KEY,
                                save_payload JSONB NOT NULL,
                                revision BIGINT NOT NULL CHECK (revision >= 1),
                                save_version INTEGER NOT NULL,
                                updated_at TIMESTAMPTZ NOT NULL
                            )
                            """
                        )
                        cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS baseball_sim_idempotency (
                                session_id TEXT NOT NULL REFERENCES baseball_sim_sessions(session_id)
                                    ON DELETE CASCADE,
                                idempotency_key TEXT NOT NULL,
                                fingerprint TEXT NOT NULL,
                                response_payload JSONB NOT NULL,
                                resulting_revision BIGINT NOT NULL,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                PRIMARY KEY (session_id, idempotency_key)
                            )
                            """
                        )
                self._initialized = True
            except psycopg.Error as exc:
                raise StoreUnavailable("external durable store initialization failed") from exc

    @staticmethod
    def _timestamp(value: object) -> str:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return str(value)

    def get(self, session_id: str) -> StoredSession | None:
        self._ensure_initialized()
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT session_id, save_payload, revision, save_version, updated_at
                        FROM baseball_sim_sessions WHERE session_id = %s
                        """,
                        (session_id,),
                    )
                    row = cursor.fetchone()
        except psycopg.Error as exc:
            raise StoreUnavailable("external durable store read failed") from exc
        if row is None:
            return None
        return StoredSession(
            session_id=str(row["session_id"]),
            payload=self._decode(row["save_payload"]),
            revision=int(row["revision"]),
            save_version=int(row["save_version"]),
            updated_at=self._timestamp(row["updated_at"]),
        )

    def replace(self, session_id: str, payload: dict[str, object]) -> StoredSession:
        self._ensure_initialized()
        save_version = int(payload.get("save_version", 1))
        encoded = self._encode(payload)
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO baseball_sim_sessions(
                            session_id, save_payload, revision, save_version, updated_at
                        )
                        VALUES(%s, %s::jsonb, 1, %s, NOW())
                        ON CONFLICT(session_id) DO UPDATE SET
                            save_payload=EXCLUDED.save_payload,
                            revision=1,
                            save_version=EXCLUDED.save_version,
                            updated_at=NOW()
                        RETURNING updated_at
                        """,
                        (session_id, encoded, save_version),
                    )
                    row = cursor.fetchone()
                    cursor.execute(
                        "DELETE FROM baseball_sim_idempotency WHERE session_id = %s",
                        (session_id,),
                    )
        except psycopg.Error as exc:
            raise StoreUnavailable("external durable store replace failed") from exc
        updated_at = self._timestamp(row["updated_at"]) if row else self._now()
        return StoredSession(session_id, payload, 1, save_version, updated_at)

    def mutate(
        self,
        session_id: str,
        *,
        expected_revision: int,
        idempotency_key: str,
        fingerprint: str,
        mutator: Callable[[dict[str, object]], tuple[dict[str, object], dict[str, object]]],
    ) -> MutationCommit:
        self._ensure_initialized()
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT save_payload, revision
                        FROM baseball_sim_sessions
                        WHERE session_id = %s
                        FOR UPDATE
                        """,
                        (session_id,),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise KeyError(session_id)

                    cursor.execute(
                        """
                        SELECT fingerprint, response_payload, resulting_revision
                        FROM baseball_sim_idempotency
                        WHERE session_id = %s AND idempotency_key = %s
                        """,
                        (session_id, idempotency_key),
                    )
                    replay = cursor.fetchone()
                    if replay is not None:
                        if str(replay["fingerprint"]) != fingerprint:
                            raise IdempotencyConflict(
                                "idempotency key reused with a different request"
                            )
                        return MutationCommit(
                            response=self._decode(replay["response_payload"]),
                            revision=int(replay["resulting_revision"]),
                            replayed=True,
                        )

                    revision = int(row["revision"])
                    if revision != expected_revision:
                        raise RevisionConflict(revision)

                    current_payload = self._decode(row["save_payload"])
                    new_payload, response = mutator(current_payload)
                    new_revision = revision + 1
                    save_version = int(new_payload.get("save_version", 1))
                    cursor.execute(
                        """
                        UPDATE baseball_sim_sessions
                        SET save_payload = %s::jsonb,
                            revision = %s,
                            save_version = %s,
                            updated_at = NOW()
                        WHERE session_id = %s AND revision = %s
                        """,
                        (
                            self._encode(new_payload),
                            new_revision,
                            save_version,
                            session_id,
                            revision,
                        ),
                    )
                    if cursor.rowcount != 1:
                        cursor.execute(
                            "SELECT revision FROM baseball_sim_sessions WHERE session_id = %s",
                            (session_id,),
                        )
                        latest = cursor.fetchone()
                        raise RevisionConflict(
                            int(latest["revision"]) if latest is not None else revision
                        )

                    response_with_revision = dict(response)
                    response_with_revision["meta"] = {"revision": new_revision}
                    cursor.execute(
                        """
                        INSERT INTO baseball_sim_idempotency(
                            session_id,
                            idempotency_key,
                            fingerprint,
                            response_payload,
                            resulting_revision
                        )
                        VALUES(%s, %s, %s, %s::jsonb, %s)
                        """,
                        (
                            session_id,
                            idempotency_key,
                            fingerprint,
                            self._encode(response_with_revision),
                            new_revision,
                        ),
                    )
                    return MutationCommit(
                        response=response_with_revision,
                        revision=new_revision,
                        replayed=False,
                    )
        except (KeyError, RevisionConflict, IdempotencyConflict):
            raise
        except psycopg.Error as exc:
            raise StoreUnavailable("external durable store mutation failed") from exc
