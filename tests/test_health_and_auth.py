def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_login_invalid_credentials_returns_401(client):
    res = client.post("/auth/login", json={"username": "missing@example.com", "password": "bad"})
    assert res.status_code == 401


def test_login_me_logout_and_refresh_flow(client, create_user, auth_headers):
    user = create_user("admin@example.com", "pass123", role="admin", full_name="Admin")
    headers = auth_headers("admin@example.com", "pass123")

    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == user["id"]
    assert me.json()["role"] == "admin"

    logout = client.post("/auth/logout")
    assert logout.status_code == 200
    assert logout.json() == {"ok": True}

    refresh = client.post("/auth/refresh", headers=headers)
    assert refresh.status_code == 200
    assert refresh.json()["token_type"] == "bearer"
    assert refresh.json()["access_token"]
