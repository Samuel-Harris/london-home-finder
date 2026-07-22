import json

from lhf.api.openapi import render_openapi


def test_openapi_contains_the_public_routes() -> None:
    document = json.loads(render_openapi())

    assert set(document["paths"]) == {"/health", "/listings"}
    assert document["paths"]["/health"]["get"]["operationId"] == "health"
    assert document["paths"]["/listings"]["get"]["operationId"] == "listListings"
