from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import Float, Integer, String, UniqueConstraint, create_engine, event, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from lhf_backend._listing import Listing, ListingDraft


class Base(DeclarativeBase):
    pass


class ListingRow(Base):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(500))
    asking_price_gbp: Mapped[int] = mapped_column(Integer)
    postcode: Mapped[str] = mapped_column(String(8), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    floor_area_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)


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


class ListingRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def upsert(self, drafts: Iterable[ListingDraft]) -> int:
        draft_list = list(drafts)
        if not draft_list:
            return 0

        statement = insert(ListingRow).values(
            [
                {
                    "source": draft.source,
                    "external_id": draft.external_id,
                    "title": draft.title,
                    "asking_price_gbp": draft.asking_price_gbp,
                    "postcode": draft.postcode,
                    "url": draft.url,
                    "floor_area_sqm": draft.floor_area_sqm,
                }
                for draft in draft_list
            ]
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ListingRow.source, ListingRow.external_id],
            set_={
                "title": statement.excluded.title,
                "asking_price_gbp": statement.excluded.asking_price_gbp,
                "postcode": statement.excluded.postcode,
                "url": statement.excluded.url,
                "floor_area_sqm": statement.excluded.floor_area_sqm,
            },
        )
        with self._sessions.begin() as session:
            session.execute(statement)
        return len(draft_list)

    def list_all(self) -> list[Listing]:
        with self._sessions() as session:
            rows = session.scalars(select(ListingRow).order_by(ListingRow.id)).all()
            return [_listing_from_row(row) for row in rows]


def _listing_from_row(row: ListingRow) -> Listing:
    return Listing(
        id=row.id,
        source=row.source,
        external_id=row.external_id,
        title=row.title,
        asking_price_gbp=row.asking_price_gbp,
        postcode=row.postcode,
        url=row.url,
        floor_area_sqm=row.floor_area_sqm,
    )


metadata = Base.metadata
