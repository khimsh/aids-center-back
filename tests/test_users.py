def test_users_admin_endpoints_and_permissions(client, create_user, auth_headers):
    admin = create_user("admin@example.com", "adminpass", role="admin", full_name="Admin")
    editor = create_user("editor@example.com", "editorpass", role="editor", full_name="Editor")

    admin_headers = auth_headers("admin@example.com", "adminpass")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    forbidden_list = client.get("/api/users", headers=editor_headers)
    assert forbidden_list.status_code == 403

    listed = client.get("/api/users", headers=admin_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    created = client.post(
        "/api/users",
        json={
            "email": "neweditor@example.com",
            "full_name": "New Editor",
            "password": "newpass",
            "role": "editor",
        },
        headers=admin_headers,
    )
    assert created.status_code == 201, created.text
    new_user_id = created.json()["id"]

    duplicate = client.post(
        "/api/users",
        json={
            "email": "neweditor@example.com",
            "full_name": "Dup",
            "password": "newpass",
            "role": "editor",
        },
        headers=admin_headers,
    )
    assert duplicate.status_code == 409

    self_delete = client.delete(f"/api/users/{admin['id']}", headers=admin_headers)
    assert self_delete.status_code == 400

    pw_change = client.patch(
        f"/api/users/{editor['id']}/password",
        json={"new_password": "changed123"},
        headers=admin_headers,
    )
    assert pw_change.status_code == 204

    login_with_new_password = client.post(
        "/auth/login",
        json={"username": "editor@example.com", "password": "changed123"},
    )
    assert login_with_new_password.status_code == 200

    delete_new = client.delete(f"/api/users/{new_user_id}", headers=admin_headers)
    assert delete_new.status_code == 204


def test_users_requires_authentication(client):
    res = client.get("/api/users")
    assert res.status_code == 401
