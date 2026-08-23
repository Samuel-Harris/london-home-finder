from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from lhf.db.session import create_session_factory
from lhf.listings.listing_repository import ListingRepository
from pydantic import BaseModel, ConfigDict

DEFAULT_DATABASE_PATH = Path("data/london-home-finder.sqlite3")


class HealthResponse(BaseModel):
    status: str


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    url: str
    display_address: str | None
    asking_price_gbp: int | None
    price_qualifier: str | None
    bedrooms: int | None
    postcode: str | None
    floor_area_sqm: float | None
    tenure_type: str | None
    years_remaining_on_lease: int | None
    annual_service_charge_gbp: int | None
    annual_ground_rent_gbp: int | None


def create_app(database_path: str | Path | None = None) -> FastAPI:
    configured_path = database_path or os.environ.get("LHF_DATABASE_PATH") or DEFAULT_DATABASE_PATH
    repository = ListingRepository(create_session_factory(configured_path))
    application = FastAPI(title="London Home Finder API", version="0.1.0")

    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    def list_listings() -> list[ListingResponse]:
        return [ListingResponse.model_validate(listing) for listing in repository.list_all()]

    application.add_api_route(
        "/health",
        health,
        methods=["GET"],
        operation_id="health",
        tags=["system"],
    )
    application.add_api_route(
        "/listings",
        list_listings,
        methods=["GET"],
        operation_id="listListings",
        tags=["listings"],
    )

    return application


app = create_app()
