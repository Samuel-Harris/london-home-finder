from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry


def create_session_factory(database_path: str | Path) -> sessionmaker[Session]:
    path = Path(database_path).expanduser().resolve()
    engine = create_engine(
        f"sqlite+pysqlite:///{path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    def configure_sqlite(
        dbapi_connection: DBAPIConnection,
        _connection_record: ConnectionPoolEntry,
    ) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA busy_timeout = 5000")
        finally:
            cursor.close()

    event.listen(engine, "connect", configure_sqlite)
    return sessionmaker(engine, expire_on_commit=False)
