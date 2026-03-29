def test_upload_requires_auth(client):
    res = client.post(
        "/api/uploads/image",
        files={"file": ("pic.png", b"fakepng", "image/png")},
    )
    assert res.status_code == 401


def test_upload_valid_image_and_invalid_content_type(client, create_user, auth_headers, uploads_dir):
    create_user("editor@example.com", "editorpass", role="editor")
    headers = auth_headers("editor@example.com", "editorpass")

    invalid = client.post(
        "/api/uploads/image",
        headers=headers,
        files={"file": ("bad.txt", b"hello", "text/plain")},
    )
    assert invalid.status_code == 415

    valid = client.post(
        "/api/uploads/image",
        headers=headers,
        files={"file": ("ok.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert valid.status_code == 200, valid.text
    url = valid.json()["url"]
    assert url.startswith("/uploads/")

    saved_name = url.split("/uploads/")[1]
    assert (uploads_dir / saved_name).exists()


def test_upload_empty_file_rejected(client, create_user, auth_headers):
    create_user("editor@example.com", "editorpass", role="editor")
    headers = auth_headers("editor@example.com", "editorpass")

    empty = client.post(
        "/api/uploads/image",
        headers=headers,
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert empty.status_code == 422
