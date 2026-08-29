from pathlib import Path

from lhf.db.session import create_session_factory
from sqlalchemy import text


def test_session_factory_applies_sqlite_pragmas(tmp_path: Path) -> None:
    sessions = create_session_factory(tmp_path / "db.sqlite3")

    with sessions() as session:
        assert session.scalar(text("PRAGMA foreign_keys")) == 1
        assert session.scalar(text("PRAGMA journal_mode")) == "wal"
        assert session.scalar(text("PRAGMA busy_timeout")) == 5000
