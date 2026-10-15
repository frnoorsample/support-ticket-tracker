import pytest

from app.categorise import categorise

VPN_TICKET = {"title": "Cannot connect to VPN", "description": "VPN drops every hour", "priority": "high"}


def create_ticket(client, headers, data=VPN_TICKET):
    return client.post("/tickets", json=data, headers=headers)


def test_create_ticket(client, alice):
    response = create_ticket(client, alice)
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "network"
    assert body["status"] == "open"
    assert body["priority"] == "high"


def test_tickets_require_login(client):
    assert client.get("/tickets").status_code == 401
    assert client.post("/tickets", json=VPN_TICKET).status_code == 401


def test_invalid_ticket_rejected(client, alice):
    bad_priority = {**VPN_TICKET, "priority": "urgent"}
    short_title = {**VPN_TICKET, "title": "hi"}
    assert create_ticket(client, alice, bad_priority).status_code == 422
    assert create_ticket(client, alice, short_title).status_code == 422


def test_users_only_see_their_own_tickets(client, alice, bob):
    create_ticket(client, alice)
    create_ticket(client, bob, {"title": "Printer jam", "description": "Floor 2 printer"})
    alice_tickets = client.get("/tickets", headers=alice).json()
    assert len(alice_tickets) == 1
    assert alice_tickets[0]["title"] == "Cannot connect to VPN"


def test_user_cannot_read_or_edit_someone_elses_ticket(client, alice, bob):
    ticket_id = create_ticket(client, alice).json()["id"]
    assert client.get(f"/tickets/{ticket_id}", headers=bob).status_code == 404
    assert client.patch(f"/tickets/{ticket_id}", json={"title": "Hacked"}, headers=bob).status_code == 404


def test_owner_can_edit_ticket(client, alice):
    ticket_id = create_ticket(client, alice).json()["id"]
    response = client.patch(
        f"/tickets/{ticket_id}",
        json={"title": "Laptop screen flickering", "description": "Screen goes black"},
        headers=alice,
    )
    assert response.status_code == 200
    assert response.json()["category"] == "hardware"
    assert response.json()["priority"] == "high"


def test_normal_user_cannot_change_status_or_delete(client, alice):
    ticket_id = create_ticket(client, alice).json()["id"]
    assert client.patch(f"/tickets/{ticket_id}/status", json={"status": "closed"}, headers=alice).status_code == 403
    assert client.delete(f"/tickets/{ticket_id}", headers=alice).status_code == 403


def test_admin_sees_all_and_can_change_status(client, alice, bob, admin):
    ticket_id = create_ticket(client, alice).json()["id"]
    create_ticket(client, bob)
    assert len(client.get("/tickets", headers=admin).json()) == 2
    response = client.patch(f"/tickets/{ticket_id}/status", json={"status": "resolved"}, headers=admin)
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_invalid_status_rejected(client, alice, admin):
    ticket_id = create_ticket(client, alice).json()["id"]
    response = client.patch(f"/tickets/{ticket_id}/status", json={"status": "done"}, headers=admin)
    assert response.status_code == 422


def test_closed_ticket_cannot_be_edited(client, alice, admin):
    ticket_id = create_ticket(client, alice).json()["id"]
    client.patch(f"/tickets/{ticket_id}/status", json={"status": "closed"}, headers=admin)
    response = client.patch(f"/tickets/{ticket_id}", json={"priority": "low"}, headers=alice)
    assert response.status_code == 409


def test_admin_can_delete(client, alice, admin):
    ticket_id = create_ticket(client, alice).json()["id"]
    assert client.delete(f"/tickets/{ticket_id}", headers=admin).status_code == 204
    assert client.get(f"/tickets/{ticket_id}", headers=admin).status_code == 404


def test_filters(client, alice):
    create_ticket(client, alice)
    create_ticket(client, alice, {"title": "Invoice missing", "description": "No invoice", "priority": "low"})
    assert len(client.get("/tickets?priority=high", headers=alice).json()) == 1
    assert len(client.get("/tickets?category=billing", headers=alice).json()) == 1
    assert len(client.get("/tickets?status=closed", headers=alice).json()) == 0


@pytest.mark.parametrize(
    "title, description, expected",
    [
        ("Forgot my password", "Need a reset", "account"),
        ("Wifi not working", "No internet", "network"),
        ("Printer broken", "Paper jam", "hardware"),
        ("Excel keeps crashing", "Error on open", "software"),
        ("Refund request", "Charged twice", "billing"),
        ("Question", "General query", "general"),
    ],
)
def test_categorise(title, description, expected):
    assert categorise(title, description) == expected