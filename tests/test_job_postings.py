def test_job_postings_crud_and_public_visibility(client, create_user, auth_headers):
    create_user("admin@example.com", "adminpass", role="admin")
    create_user("editor@example.com", "editorpass", role="editor")

    admin_headers = auth_headers("admin@example.com", "adminpass")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    created = client.post(
        "/api/job-postings",
        json={"title_ka": "Vacancy A", "published": False},
        headers=editor_headers,
    )
    assert created.status_code == 201, created.text
    job = created.json()

    list_public = client.get("/api/job-postings")
    assert list_public.status_code == 200
    assert list_public.json() == []

    get_public = client.get(f"/api/job-postings/{job['id']}")
    assert get_public.status_code == 404

    published = client.put(
        f"/api/job-postings/{job['id']}",
        json={"published": True},
        headers=editor_headers,
    )
    assert published.status_code == 200
    assert published.json()["published"] is True
    assert published.json()["published_at"] is not None

    list_public_after = client.get("/api/job-postings")
    assert list_public_after.status_code == 200
    assert len(list_public_after.json()) == 1

    delete_as_editor = client.delete(f"/api/job-postings/{job['id']}", headers=editor_headers)
    assert delete_as_editor.status_code == 403

    delete_as_admin = client.delete(f"/api/job-postings/{job['id']}", headers=admin_headers)
    assert delete_as_admin.status_code == 204
