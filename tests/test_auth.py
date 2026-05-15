def test_register_login_and_bad_credentials(client):
    # register
    resp = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "secret123", "role": "client"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"

    # login success
    resp = client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    token = resp.json().get("access_token")
    assert token

    # bad credentials
    resp = client.post("/auth/login", json={"email": "alice@example.com", "password": "wrong"})
    assert resp.status_code == 401
