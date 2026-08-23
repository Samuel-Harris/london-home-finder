import pytest
from lhf.listings.listing import (
    ListingDraft,
    is_within_budget,
    normalise_postcode,
    price_per_square_metre,
)


def test_normalise_postcode() -> None:
    assert normalise_postcode(" sw1a  1aa ") == "SW1A 1AA"


def test_listing_draft_normalises_its_postcode() -> None:
    draft = ListingDraft(
        source="example",
        external_id="home-1",
        display_address="A Westminster flat",
        asking_price_gbp=650_000,
        postcode="sw1a1aa",
        url="https://example.test/home-1",
    )

    assert draft.postcode == "SW1A 1AA"


def test_listing_draft_allows_missing_economics() -> None:
    draft = ListingDraft(
        source="rightmove",
        external_id="poa-1",
        url="https://www.rightmove.co.uk/properties/1",
    )

    assert draft.asking_price_gbp is None
    assert draft.postcode is None
    assert draft.display_address is None


def test_listing_draft_rejects_invalid_postcode() -> None:
    with pytest.raises(ValueError, match="invalid UK postcode"):
        ListingDraft(
            source="rightmove",
            external_id="poa-1",
            url="https://www.rightmove.co.uk/properties/1",
            postcode="London",
        )


def test_listing_draft_treats_blank_postcode_as_missing() -> None:
    draft = ListingDraft(
        source="rightmove",
        external_id="poa-1",
        url="https://www.rightmove.co.uk/properties/1",
        postcode="  ",
    )

    assert draft.postcode is None


def test_listing_draft_rejects_non_positive_lease_years() -> None:
    with pytest.raises(ValueError, match="years_remaining_on_lease"):
        ListingDraft(
            source="rightmove",
            external_id="1",
            url="https://www.rightmove.co.uk/properties/1",
            years_remaining_on_lease=0,
        )


def test_domain_calculations() -> None:
    assert is_within_budget(650_000, 700_000)
    assert price_per_square_metre(650_000, 65) == 10_000


@pytest.mark.parametrize("postcode", ["", "London", "SW1"])
def test_rejects_invalid_postcodes(postcode: str) -> None:
    with pytest.raises(ValueError, match="invalid UK postcode"):
        normalise_postcode(postcode)
