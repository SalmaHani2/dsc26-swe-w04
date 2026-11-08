
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from nour_transfers.app import create_app


def test_inbox_is_sorted_by_priority_then_request_order():
    app = create_app(
        stock={
            ("source", "NORMAL"): 100,
            ("source", "URGENT"): 100,
            ("source", "HIGH"): 100,
            ("destination", "NORMAL"): 100,
            ("destination", "URGENT"): 1,
            ("destination", "HIGH"): 5,
        },
        items={
            "NORMAL": {"chronic": True, "reserve": 0},
            "URGENT": {"chronic": True, "reserve": 0},
            "HIGH": {"chronic": True, "reserve": 0},
        },
        sales={
            ("destination", "NORMAL"): 10,
            ("destination", "URGENT"): 1,
            ("destination", "HIGH"): 1,
        },
        now=lambda: datetime(2026, 11, 3, 9, 30, tzinfo=UTC),
    )

    client = TestClient(app)

    requests = [
        ("NORMAL", "normal"),
        ("URGENT", "urgent"),
        ("HIGH", "high"),
        ("URGENT", "urgent"),
    ]

    created_ids = []

    for item_code, expected_priority in requests:
        response = client.post(
            "/v1/transfers",
            json={
                "itemCode": item_code,
                "fromBranch": "source",
                "toBranch": "destination",
                "quantity": 1,
            },
        )

        assert response.status_code == 201
        assert response.json()["priority"] == expected_priority

        created_ids.append(response.json()["id"])

    response = client.get(
        "/v1/branches/destination/transfers"
    )

    assert response.status_code == 200

    cards = response.json()["items"]

    assert [card["id"] for card in cards] == [
        created_ids[1],
        created_ids[3],
        created_ids[2],
        created_ids[0],
    ]

    assert [card["priority"] for card in cards] == [
        "urgent",
        "urgent",
        "high",
        "normal",
    ]


def test_unknown_branch_inbox_returns_empty_items(client):
    response = client.get(
        "/v1/branches/unknown/transfers"
    )

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_inbox_includes_approved_transfers(client):
    created = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 20,
        },
    )

    transfer_id = created.json()["id"]

    approval = client.post(
        f"/v1/transfers/{transfer_id}/approve"
    )

    assert approval.status_code == 200

    response = client.get(
        "/v1/branches/tanta/transfers"
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["status"] == "approved"
