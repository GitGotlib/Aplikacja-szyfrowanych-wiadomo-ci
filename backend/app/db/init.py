from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from app.core.config import settings


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
        conn.commit()
    finally:
        conn.close()

    try:
        os.chmod(db_path, 0o600)
    except Exception:
        # Best-effort on platforms that do not support chmod semantics.
        pass
