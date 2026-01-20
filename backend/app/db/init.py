from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from app.core.config import settings


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return any((r[1] == column) for r in rows)


def _apply_migrations(conn: sqlite3.Connection) -> None:
    # schema.sql is authoritative for new DBs; existing DBs need additive migrations.
    if not _column_exists(conn, "users", "totp_last_used_step"):
        conn.execute("ALTER TABLE users ADD COLUMN totp_last_used_step INTEGER;")


def init_sqlite_schema() -> None:
    """Initialize SQLite schema from the versioned SQL file.

    Rationale:
    - schema.sql remains the authoritative, auditable schema document,
    - on first start the DB file is created and schema applied.
    """

    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        db_path.touch(mode=0o600)

    # Resolve schema file (works both locally and in Docker).
    schema_path: Path | None = None
    checked: list[str] = []
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "database" / "schema.sql"
        checked.append(str(candidate))
        if candidate.exists():
            schema_path = candidate
            break
    if schema_path is None:
        raise RuntimeError(
            "database/schema.sql not found. Checked:\n- " + "\n- ".join(checked)
        )

    sql = schema_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(sql)
        _apply_migrations(conn)
        conn.commit()
    finally:
        conn.close()

    try:
        os.chmod(db_path, 0o600)
    except Exception:
        # Best-effort on platforms that do not support chmod semantics.
        pass
