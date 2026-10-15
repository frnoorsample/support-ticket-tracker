def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_returns_user_without_password(client):
    response = client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["role"] == "user"
    assert "password" not in body
    assert "password_hash" not in body


def test_password_is_hashed_in_database(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    from app.database import get_connection

    with get_connection() as conn:
        stored = conn.execute("SELECT password_hash FROM users WHERE username = 'alice'").fetchone()[0]
    assert stored != "secret123"
    assert stored.startswith("$2")


def test_duplicate_username_rejected(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    response = client.post("/auth/register", json={"username": "alice", "password": "other12345"})
    assert response.status_code == 409


def test_invalid_registration_rejected(client):
    assert client.post("/auth/register", json={"username": "al", "password": "secret123"}).status_code == 422
    assert client.post("/auth/register", json={"username": "a b c", "password": "secret123"}).status_code == 422
    assert client.post("/auth/register", json={"username": "alice", "password": "short"}).status_code == 422


def test_cannot_register_as_admin(client):
    response = client.post(
        "/auth/register", json={"username": "sneaky", "password": "secret123", "role": "admin"}
    )
    assert response.json()["role"] == "user"


def test_login_and_me(client, alice):
    response = client.get("/auth/me", headers=alice)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_wrong_password_and_unknown_user_give_same_error(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    wrong_password = client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    unknown_user = client.post("/auth/login", data={"username": "nobody", "password": "wrong"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_missing_or_fake_token_rejected(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer fake.token.here"}).status_code == 401


def test_lockout_after_too_many_failed_logins(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    for _ in range(5):
        client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    response = client.post("/auth/login", data={"username": "alice", "password": "secret123"})
    assert response.status_code == 429


def test_sql_injection_in_login_fails(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    response = client.post("/auth/login", data={"username": "alice' OR '1'='1", "password": "x"})
    assert response.status_code == 401