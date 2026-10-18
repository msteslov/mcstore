from fastapi.testclient import TestClient


def user_payload(number: int) -> dict:
    return {
        "telegram_id": number,
        "minecraft_uuid": f"00000000-0000-0000-0000-{number:012d}",
        "minecraft_name": f"player{number}",
    }


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_full_transfer_flow(client: TestClient) -> None:
    first = client.post("/users", json=user_payload(1))
    second = client.post("/users", json=user_payload(2))
    assert first.status_code == second.status_code == 201

    source = client.post(
        f"/users/{first.json()['id']}/cards",
        json={"name": "Salary", "initial_balance": 90},
    )
    target = client.post(
        f"/users/{second.json()['id']}/cards",
        json={"name": "Savings"},
    )
    response = client.post(
        "/transfers",
        json={
            "source_card_id": source.json()["id"],
            "target_card_id": target.json()["id"],
            "amount": 40,
            "idempotency_key": "api-transfer-0001",
            "message": "test",
        },
    )

    assert response.status_code == 201
    source_cards = client.get(f"/users/{first.json()['id']}/cards").json()
    target_cards = client.get(f"/users/{second.json()['id']}/cards").json()
    assert source_cards[0]["balance"] == 50
    assert target_cards[0]["balance"] == 40


def test_duplicate_user_returns_conflict(client: TestClient) -> None:
    assert client.post("/users", json=user_payload(7)).status_code == 201
    response = client.post("/users", json=user_payload(7))
    assert response.status_code == 409


def test_missing_user_returns_not_found(client: TestClient) -> None:
    assert client.get("/users/999999").status_code == 404
