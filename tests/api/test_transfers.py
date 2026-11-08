
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from nour_transfers.app import create_app


FIXED_NOW = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)


def make_client(
    stock=None,
    items=None,
    sales=None,
):
    app = create_app(
        stock=stock or {
            ("heliopolis", "MET500"): 40,
            ("tanta", "MET500"): 2,
        },
        items=items or {
            "MET500": {"chronic": True, "reserve": 10},
        },
        sales=sales or {
            ("tanta", "MET500"): 1.0,
        },
        now=lambda: FIXED_NOW,
    )

    return TestClient(app)


def create_transfer(client, quantity=20):
    return client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": quantity,
        },
    )


def test_request_transfer_returns_a_pending_card(client):
    response = create_transfer(client)

    assert response.status_code == 201

    card = response.json()

    assert card["id"] == "tr_1"
    assert card["itemCode"] == "MET500"
    assert card["fromBranch"] == "heliopolis"
    assert card["toBranch"] == "tanta"
    assert card["quantity"] == 20
    assert card["priority"] == "urgent"
    assert card["status"] == "pending"


def test_transfer_priority_uses_destination_stock():
    client = make_client(
        stock={
            ("heliopolis", "MET500"): 100,
            ("tanta", "MET500"): 10,
        },
        sales={
            ("heliopolis", "MET500"): 1,
            ("tanta", "MET500"): 10,
        },
    )

    response = create_transfer(client)

    assert response.status_code == 201
    assert response.json()["priority"] == "urgent"


def test_request_does_not_move_stock(client):
    response = create_transfer(client)

    assert response.status_code == 201

    source = client.get(
        "/v1/branches/heliopolis/stock/MET500"
    )

    destination = client.get(
        "/v1/branches/tanta/stock/MET500"
    )

    assert source.json()["units"] == 40
    assert destination.json()["units"] == 2


def test_same_branch_transfer_is_rejected(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "heliopolis",
            "quantity": 1,
        },
    )

    assert response.status_code == 422
    assert response.json()["type"] == "/problems/same-branch"


def test_same_branch_error_uses_problem_json(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "heliopolis",
            "quantity": 1,
        },
    )

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )


def test_unknown_item_returns_404(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "UNKNOWN",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["type"] == "/problems/unknown-item"


def test_unknown_branch_returns_404(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "unknown",
            "toBranch": "tanta",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["type"] == "/problems/unknown-branch"


def test_invalid_quantity_returns_validation_problem(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 0,
        },
    )

    assert response.status_code == 422
    assert response.json()["type"] == "/problems/validation"
    assert "errors" in response.json()


def test_below_reserve_returns_409(client):
    response = create_transfer(client, quantity=31)

    assert response.status_code == 409
    assert response.json()["type"] == "/problems/below-reserve"


def test_unknown_transfer_approval_returns_404(client):
    response = client.post(
        "/v1/transfers/unknown/approve"
    )

    assert response.status_code == 404
    assert response.json()["type"] == "/problems/unknown-transfer"


def test_transfer_cannot_be_approved_twice(client):
    created = create_transfer(client)

    assert created.status_code == 201

    transfer_id = created.json()["id"]

    first_approval = client.post(
        f"/v1/transfers/{transfer_id}/approve"
    )

    assert first_approval.status_code == 200
    assert first_approval.json()["status"] == "approved"

    second_approval = client.post(
        f"/v1/transfers/{transfer_id}/approve"
    )

    assert second_approval.status_code == 409
    assert second_approval.json()["type"] == "/problems/not-pending"


def test_approval_moves_stock_to_destination_exactly_once(client):
    created = create_transfer(client)

    assert created.status_code == 201

    transfer_id = created.json()["id"]

    approval = client.post(
        f"/v1/transfers/{transfer_id}/approve"
    )

    assert approval.status_code == 200

    source = client.get(
        "/v1/branches/heliopolis/stock/MET500"
    )

    destination = client.get(
        "/v1/branches/tanta/stock/MET500"
    )

    assert source.json()["units"] == 20
    assert destination.json()["units"] == 22

    # A second approval must not move stock again.
    second = client.post(
        f"/v1/transfers/{transfer_id}/approve"
    )

    assert second.status_code == 409

    source_after = client.get(
        "/v1/branches/heliopolis/stock/MET500"
    )

    destination_after = client.get(
        "/v1/branches/tanta/stock/MET500"
    )

    assert source_after.json()["units"] == 20
    assert destination_after.json()["units"] == 22


def test_refused_approval_does_not_change_stock():
    client = make_client()

    created = create_transfer(client)

    transfer_id = created.json()["id"]

    # Create another transfer that consumes the remaining available stock.
    another = create_transfer(client, quantity=20)

    assert another.status_code == 201

    first_approval = client.post(
        f"/v1/transfers/{transfer_id}/approve"
    )

    assert first_approval.status_code == 200

    # Second transfer can no longer be approved.
    second_id = another.json()["id"]

    refused = client.post(
        f"/v1/transfers/{second_id}/approve"
    )

    assert refused.status_code == 409
    assert refused.json()["type"] == "/problems/below-reserve"

    source = client.get(
        "/v1/branches/heliopolis/stock/MET500"
    )

    destination = client.get(
        "/v1/branches/tanta/stock/MET500"
    )

    assert source.json()["units"] == 20
    assert destination.json()["units"] == 22
