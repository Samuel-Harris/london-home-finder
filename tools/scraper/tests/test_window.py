from dataclasses import replace

import pytest
from lhf.scraper.window import DEFAULT_WINDOW, IngestWindow


def test_default_window_is_the_product_search_window() -> None:
    assert (
        IngestWindow(
            min_price=350_000,
            max_price=800_000,
            min_bedrooms=2,
            property_types=("detached", "semi-detached", "terraced", "bungalow"),
            tenure="FREEHOLD",
        )
        == DEFAULT_WINDOW
    )


def test_ingest_window_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="min_price"):
        IngestWindow(min_price=0)
    with pytest.raises(ValueError, match="max_price"):
        IngestWindow(min_price=500_000, max_price=400_000)
    with pytest.raises(ValueError, match="min_bedrooms"):
        IngestWindow(min_bedrooms=-1)


def test_replace_keeps_unspecified_defaults() -> None:
    narrowed = replace(DEFAULT_WINDOW, min_price=500_000, max_price=500_000)
    assert narrowed.min_bedrooms == 2
    assert narrowed.property_types == DEFAULT_WINDOW.property_types
    assert narrowed.tenure == "FREEHOLD"
