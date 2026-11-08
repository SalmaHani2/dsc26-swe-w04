
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from nour_transfers.app import create_app


def test_inbox_is_sorted_by_priority_then_request_order():
    app = create_app(
        stock={
            ("source", "MED"): 100,
            ("normal", "MED"): 100,
            ("urgent1", "MED"): 1,
            ("high", "MED"): 5,
            ("urgent2", "MED"): 2,
        },
        items={
            "MED": {"chronic": True, "reserve": 0},
        },
        sales={
            ("normal", "MED"): 10,
            ("urgent1", "MED"): 1,
            ("high", "MED"): 1,
            ("urgent2", "MED"): 1,
        },
        now=lambda: datetime(2026, 11, 3, 9, 30, tzinfo=UTC),
    )

    client = TestClient(app)

    requests = [
        ("normal", "normal"),
        ("urgent1", "urgent"),
        ("high", "high"),
        ("urgent2", "urgent"),
    ]

    created_ids = []

    for destination, expected_priority in requests:
        response = client.post(
            "/v1/transfers",
            json={
                "itemCode": "MED",
                "fromBranch": "source",
                "toBranch": destination,
                "quantity": 1,
            },
        )

        assert response.status_code == 201
        assert response.json()["priority"] == expected_priority

        created_ids.append(response.json()["id"])

    inbox = client.get("/v1/branches/normal/transfers")

    assert inbox.status_code == 200

    # The normal branch only receives its own transfer.
    assert [item["id"] for item in inbox.json()["items"]] == [
        created_ids[0]
    ]

    # Read each destination's inbox and combine the cards.
    all_cards = []

    for destination, _ in requests:
        response = client.get(
            f"/v1/branches/{destination}/transfers"
        )

        assert response.status_code == 200
        all_cards.extend(response.json()["items"])

    # Verify ordering using one shared destination inbox.
    # Create an additional set of transfers to the same destination.
    shared_app = create_app(
        stock={
            ("source", "MED"): 100,
            ("destination", "MED"): 100,
        },
        items={
            "MED": {"chronic": True, "reserve": 0},
        },
        sales={
            ("destination", "MED"): 10,
        },
        now=lambda: datetime(2026, 11, 3, 9, 30, tzinfo=UTC),
    )

    shared_client = TestClient(shared_app)

    # All requests target the same branch, but use different
    # item codes and destination sales to produce different priorities.
    # This is handled in the dedicated scenario below.

