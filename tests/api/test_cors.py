
import pytest


ALLOWED_ORIGINS = [
    "https://branch.nour.example",
    "http://localhost:5173",
]


@pytest.mark.parametrize("origin", ALLOWED_ORIGINS)
def test_allowed_origins_pass_preflight(client, origin):
    response = client.options(
        "/v1/transfers",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert response.status_code == 200

    assert response.headers.get(
        "access-control-allow-origin"
    ) == origin

    assert response.headers.get(
        "access-control-allow-credentials"
    ) == "true"


def test_disallowed_origin_fails_preflight(client):
    response = client.options(
        "/v1/transfers",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400

    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("origin", ALLOWED_ORIGINS)
def test_normal_request_from_allowed_origin(client, origin):
    response = client.get(
        "/v1/branches/tanta/stock/MET500",
        headers={
            "Origin": origin,
        },
    )

    assert response.status_code == 200

    assert response.headers.get(
        "access-control-allow-origin"
    ) == origin


def test_normal_request_from_disallowed_origin_has_no_cors_header(client):
    response = client.get(
        "/v1/branches/tanta/stock/MET500",
        headers={
            "Origin": "https://evil.example",
        },
    )

    assert response.status_code == 200

    assert "access-control-allow-origin" not in response.headers

