def test_doctors_crud_and_permissions(client, create_user, auth_headers):
    create_user("admin@example.com", "adminpass", role="admin")
    create_user("editor@example.com", "editorpass", role="editor")

    admin_headers = auth_headers("admin@example.com", "adminpass")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    list_res = client.get("/api/doctors")
    assert list_res.status_code == 200
    assert list_res.json() == []

    unauth_create = client.post(
        "/api/doctors",
        json={"name": "Dr X", "education": "Edu", "experience": "Exp"},
    )
    assert unauth_create.status_code == 401

    created = client.post(
        "/api/doctors",
        json={"name": "Dr X", "education": "Edu", "experience": "Exp"},
        headers=editor_headers,
    )
    assert created.status_code == 201, created.text
    doctor = created.json()

    get_res = client.get(f"/api/doctors/{doctor['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Dr X"

    updated = client.put(
        f"/api/doctors/{doctor['id']}",
        json={"experience": "20 years"},
        headers=editor_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["experience"] == "20 years"

    delete_as_editor = client.delete(f"/api/doctors/{doctor['id']}", headers=editor_headers)
    assert delete_as_editor.status_code == 403

    delete_as_admin = client.delete(f"/api/doctors/{doctor['id']}", headers=admin_headers)
    assert delete_as_admin.status_code == 204

    after_delete = client.get(f"/api/doctors/{doctor['id']}")
    assert after_delete.status_code == 404
