import pytest
from fastapi.testclient import TestClient

from app import config, security
from app.create_admin import make_admin
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "test.db"))
    security._failed_logins.clear()
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(client, username, password="secret123"):
    client.post("/auth/register", json={"username": username, "password": password})
    response = client.post("/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def alice(client):
    return register_and_login(client, "alice")


@pytest.fixture
def bob(client):
    return register_and_login(client, "bob")


@pytest.fixture
def admin(client):
    headers = register_and_login(client, "admin1")
    make_admin("admin1")
    return headers