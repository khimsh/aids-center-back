from pathlib import Path


def _create_article(client, headers, **overrides):
    payload = {
        "title_ka": "Sample Article",
        "title_en": "Sample article title with many words here",
        "body_ka": "body",
        "category": "news",
        "published": False,
    }
    payload.update(overrides)
    return client.post("/api/articles", json=payload, headers=headers)


def test_articles_public_list_excludes_drafts(client, create_user, auth_headers):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    _create_article(client, headers, title_ka="Draft", published=False)
    _create_article(client, headers, title_ka="Published", published=True)

    res = client.get("/api/articles")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["published"] is True


def test_articles_include_drafts_requires_auth(client):
    res = client.get("/api/articles", params={"include_drafts": True})
    assert res.status_code == 401


def test_articles_include_drafts_with_auth_returns_all(client, create_user, auth_headers):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    _create_article(client, headers, title_ka="Draft", published=False)
    _create_article(client, headers, title_ka="Published", published=True)

    res = client.get("/api/articles", params={"include_drafts": True}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2


def test_article_slug_generation_unicode_and_max_5_words(client, create_user, auth_headers):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    res = _create_article(
        client,
        headers,
        title_ka="დღეს თენგიზ ცერცვაძის დაბადების დღეა საქართველოში",
        title_en=None,
        published=True,
    )
    assert res.status_code == 201, res.text
    slug = res.json()["slug"]

    # At most 5 words
    assert len([part for part in slug.split("-") if part]) <= 5
    # Unicode should be preserved
    assert "დღეს" in slug


def test_get_article_draft_hidden_from_public_but_visible_with_auth(client, create_user, auth_headers):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    created = _create_article(client, headers, title_ka="Private Draft", published=False)
    slug = created.json()["slug"]

    public_res = client.get(f"/api/articles/{slug}")
    assert public_res.status_code == 404

    authed_res = client.get(f"/api/articles/{slug}", headers=headers)
    assert authed_res.status_code == 200


def test_featured_returns_featured_first(client, create_user, auth_headers):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    _create_article(client, headers, title_ka="Regular 1", published=True, featured=False)
    _create_article(client, headers, title_ka="Featured", published=True, featured=True)
    _create_article(client, headers, title_ka="Regular 2", published=True, featured=False)

    res = client.get("/api/articles/featured")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    assert body[0]["featured"] is True


def test_update_article_sets_published_at_when_publishing(client, create_user, auth_headers):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    created = _create_article(client, headers, title_ka="To Publish", published=False).json()

    res = client.put(
        f"/api/articles/{created['id']}",
        json={"published": True},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["published"] is True
    assert res.json()["published_at"] is not None


def test_delete_article_removes_attached_image_file(client, create_user, auth_headers, uploads_dir):
    create_user("editor@example.com", "pass123", role="editor")
    headers = auth_headers("editor@example.com", "pass123")

    image_name = "temp-image.jpg"
    image_path = uploads_dir / image_name
    image_path.write_bytes(b"123")

    created = _create_article(
        client,
        headers,
        title_ka="With image",
        image_url=f"/uploads/{image_name}",
        published=True,
    ).json()

    delete_res = client.delete(f"/api/articles/{created['id']}", headers=headers)
    assert delete_res.status_code == 204
    assert not image_path.exists()
