import pytest

import app as helpdesk


@pytest.fixture
def client(tmp_path, monkeypatch):
    """The app with a fresh database of its own, and no server running."""
    monkeypatch.setattr(helpdesk, "DATABASE", str(tmp_path / "helpdesk.db"))
    helpdesk.create_database()
    return helpdesk.app.test_client()


def sign_in(client, user, password):
    assert client.post("/login", data={"user": user, "password": password}).status_code == 200
