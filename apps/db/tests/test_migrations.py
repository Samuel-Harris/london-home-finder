from pathlib import Path

from lhf.db_app.migrations import upgrade_database
from sqlalchemy import create_engine, inspect

LISTING_COLUMNS = {
    "id",
    "source",
    "external_id",
    "url",
    "display_address",
    "asking_price_gbp",
    "price_qualifier",
    "bedrooms",
    "property_type",
    "property_sub_type",
    "postcode",
    "floor_area_sqm",
    "tenure_type",
    "years_remaining_on_lease",
    "annual_service_charge_gbp",
    "annual_ground_rent_gbp",
    "key_features",
    "description",
    "bathrooms",
    "garden",
    "parking",
    "latitude",
    "longitude",
    "nearest_stations",
    "listing_update_reason",
    "listing_update_date",
    "first_visible_date",
}


def test_upgrade_database_creates_listings_table(tmp_path: Path) -> None:
    database_path = tmp_path / "migrated.sqlite3"
    upgrade_database(database_path)

    inspector = inspect(create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}"))
    assert inspector.has_table("listings")
    assert {column["name"] for column in inspector.get_columns("listings")} == LISTING_COLUMNS
