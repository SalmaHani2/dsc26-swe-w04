
import json
from pathlib import Path

from jsonschema import validate


SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "transfer_card.schema.json"
)


def load_schema():
    with SCHEMA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def test_transfer_card_matches_json_schema(client):
    created = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 20,
        },
    )

    assert created.status_code == 201

    card = created.json()

    schema = load_schema()

    validate(
        instance=card,
        schema=schema,
    )


def test_transfer_card_has_exact_expected_fields(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 20,
        },
    )

    assert response.status_code == 201

    card = response.json()

    assert set(card.keys()) == {
        "id",
        "itemCode",
        "fromBranch",
        "toBranch",
        "quantity",
        "priority",
        "status",
        "requestedAt",
    }


def test_transfer_card_uses_camel_case_fields(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 20,
        },
    )

    assert response.status_code == 201

    card = response.json()

    assert "itemCode" in card
    assert "fromBranch" in card
    assert "toBranch" in card
    assert "requestedAt" in card

    assert "item_code" not in card
    assert "from_branch" not in card
    assert "to_branch" not in card
    assert "requested_at" not in card


def test_requested_at_is_utc_with_z(client):
    response = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 20,
        },
    )

    assert response.status_code == 201

    requested_at = response.json()["requestedAt"]

    assert requested_at == "2026-11-03T09:30:00Z"
    assert requested_at.endswith("Z")


def test_transfer_ids_follow_request_order(client):
    first = client.post(
        "/v1/transfers",
        json={
            "itemCode": "MET500",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 1,
        },
    )

    second = client.post(
        "/v1/transfers",
        json={
            "itemCode": "AMOX250",
            "fromBranch": "heliopolis",
            "toBranch": "tanta",
            "quantity": 1,
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["id"] == "tr_1"
    assert second.json()["id"] == "tr_2"
