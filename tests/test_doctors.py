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
        json={
            "name": "Dr X",
            "education": "Edu",
            "experience": "Exp",
            "sort_order": 10,
            "profile_url": "https://example.com/dr-x",
        },
        headers=editor_headers,
    )
    assert created.status_code == 201, created.text
    doctor = created.json()
    assert doctor["sort_order"] == 10
    assert doctor["profile_url"] == "https://example.com/dr-x"

    get_res = client.get(f"/api/doctors/{doctor['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Dr X"

    updated = client.put(
        f"/api/doctors/{doctor['id']}",
        json={"experience": "20 years", "department": "Lead Department"},
        headers=editor_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["experience"] == "20 years"
    assert updated.json()["department"] == "Lead Department"

    delete_as_editor = client.delete(f"/api/doctors/{doctor['id']}", headers=editor_headers)
    assert delete_as_editor.status_code == 403

    delete_as_admin = client.delete(f"/api/doctors/{doctor['id']}", headers=admin_headers)
    assert delete_as_admin.status_code == 204

    after_delete = client.get(f"/api/doctors/{doctor['id']}")
    assert after_delete.status_code == 404


def test_doctors_reorder_and_list_sorting(client, create_user, auth_headers):
    create_user("editor@example.com", "editorpass", role="editor")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    first = client.post(
        "/api/doctors",
        json={"name": "Dr A", "education": "Edu A", "experience": "Exp A"},
        headers=editor_headers,
    )
    second = client.post(
        "/api/doctors",
        json={"name": "Dr B", "education": "Edu B", "experience": "Exp B"},
        headers=editor_headers,
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    first_id = first.json()["id"]
    second_id = second.json()["id"]

    reorder = client.patch(
        "/api/doctors/reorder",
        json={
            "items": [
                {"id": second_id, "sort_order": 1},
                {"id": first_id, "sort_order": 2},
            ]
        },
        headers=editor_headers,
    )
    assert reorder.status_code == 200, reorder.text

    listed = client.get("/api/doctors")
    assert listed.status_code == 200
    names = [item["name"] for item in listed.json()]
    assert names == ["Dr B", "Dr A"]


def test_doctors_reorder_by_ids_ui_friendly(client, create_user, auth_headers):
    create_user("editor@example.com", "editorpass", role="editor")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    first = client.post(
        "/api/doctors",
        json={"name": "Dr A", "education": "Edu A", "experience": "Exp A"},
        headers=editor_headers,
    )
    second = client.post(
        "/api/doctors",
        json={"name": "Dr B", "education": "Edu B", "experience": "Exp B"},
        headers=editor_headers,
    )
    third = client.post(
        "/api/doctors",
        json={"name": "Dr C", "education": "Edu C", "experience": "Exp C"},
        headers=editor_headers,
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert third.status_code == 201, third.text

    reorder = client.patch(
        "/api/doctors/reorder-by-ids",
        json={"ids": [third.json()["id"], first.json()["id"], second.json()["id"]]},
        headers=editor_headers,
    )
    assert reorder.status_code == 200, reorder.text

    listed = client.get("/api/doctors")
    assert listed.status_code == 200
    ordered_names = [item["name"] for item in listed.json()]
    assert ordered_names == ["Dr C", "Dr A", "Dr B"]

    ordered_sort_values = [item["sort_order"] for item in listed.json()]
    assert ordered_sort_values == [1, 2, 3]


def test_doctors_reorder_move_single_and_multiple(client, create_user, auth_headers):
    create_user("editor@example.com", "editorpass", role="editor")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    created = []
    for name in ["Dr A", "Dr B", "Dr C", "Dr D"]:
        res = client.post(
            "/api/doctors",
            json={"name": name, "education": f"Edu {name}", "experience": f"Exp {name}"},
            headers=editor_headers,
        )
        assert res.status_code == 201, res.text
        created.append(res.json())

    id_a = created[0]["id"]
    id_b = created[1]["id"]
    id_c = created[2]["id"]
    id_d = created[3]["id"]

    move_one = client.patch(
        "/api/doctors/reorder-move",
        json={"ids": [id_d], "before_id": id_b},
        headers=editor_headers,
    )
    assert move_one.status_code == 200, move_one.text

    names_after_one = [item["name"] for item in move_one.json()]
    assert names_after_one == ["Dr A", "Dr D", "Dr B", "Dr C"]

    move_two = client.patch(
        "/api/doctors/reorder-move",
        json={"ids": [id_b, id_c], "after_id": id_a},
        headers=editor_headers,
    )
    assert move_two.status_code == 200, move_two.text

    names_after_two = [item["name"] for item in move_two.json()]
    assert names_after_two == ["Dr A", "Dr B", "Dr C", "Dr D"]


def test_doctors_list_filtering(client, create_user, auth_headers):
    create_user("editor@example.com", "editorpass", role="editor")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    payloads = [
        {
            "name": "ლალი შარვაძე",
            "education": "Edu 1",
            "experience": "Exp 1",
            "specialty": "ინფექციონისტი",
            "department": "აივ/შიდსის ამბულატორიული დეპარტამენტის ხელმძღვანელი",
        },
        {
            "name": "ვახტანგ ქერაშვილი",
            "education": "Edu 2",
            "experience": "Exp 2",
            "specialty": "ჰეპატოლოგი",
            "department": "ჰეპატიტების მიმართულების ხელმძღვანელი",
        },
        {
            "name": "მარინა ენდელაძე",
            "education": "Edu 3",
            "experience": "Exp 3",
            "specialty": "ინფექციონისტი",
            "department": "საიზოლაციო ინფექციების მიმართულების ხელმძღვანელი",
        },
    ]

    for payload in payloads:
        created = client.post("/api/doctors", json=payload, headers=editor_headers)
        assert created.status_code == 201, created.text

    by_specialty = client.get("/api/doctors", params={"specialty": "ჰეპატოლოგი"})
    assert by_specialty.status_code == 200
    assert [item["name"] for item in by_specialty.json()] == ["ვახტანგ ქერაშვილი"]

    by_department = client.get("/api/doctors", params={"department": "აივ/შიდსის"})
    assert by_department.status_code == 200
    assert [item["name"] for item in by_department.json()] == ["ლალი შარვაძე"]

    by_search = client.get("/api/doctors", params={"search": "მარინა"})
    assert by_search.status_code == 200
    assert [item["name"] for item in by_search.json()] == ["მარინა ენდელაძე"]

    by_q_alias = client.get("/api/doctors", params={"q": "ჰეპატიტების"})
    assert by_q_alias.status_code == 200
    assert [item["name"] for item in by_q_alias.json()] == ["ვახტანგ ქერაშვილი"]

    by_query_alias = client.get("/api/doctors", params={"query": "მარინა"})
    assert by_query_alias.status_code == 200
    assert [item["name"] for item in by_query_alias.json()] == ["მარინა ენდელაძე"]

    by_name = client.get("/api/doctors", params={"name": "ლალი"})
    assert by_name.status_code == 200
    assert [item["name"] for item in by_name.json()] == ["ლალი შარვაძე"]

    by_specialization_alias = client.get("/api/doctors", params={"specialization": "ჰეპატოლოგი"})
    assert by_specialization_alias.status_code == 200
    assert [item["name"] for item in by_specialization_alias.json()] == ["ვახტანგ ქერაშვილი"]


def test_doctor_translations_manual_crud(client, create_user, auth_headers):
    create_user("editor@example.com", "editorpass", role="editor")
    editor_headers = auth_headers("editor@example.com", "editorpass")

    doctor_res = client.post(
        "/api/doctors",
        json={"name": "ლალი შარვაძე", "education": "Edu", "experience": "Exp"},
        headers=editor_headers,
    )
    assert doctor_res.status_code == 201, doctor_res.text
    doctor_id = doctor_res.json()["id"]

    unauth_create = client.post(
        f"/api/doctors/{doctor_id}/translations",
        json={
            "lang": "en",
            "name": "Lali Sharvadze",
            "education": "Tbilisi State Medical Institute",
            "experience": "Head of HIV outpatient department",
        },
    )
    assert unauth_create.status_code == 401

    created = client.post(
        f"/api/doctors/{doctor_id}/translations",
        json={
            "lang": "EN",
            "name": "Lali Sharvadze",
            "specialty": "Infectious Disease Specialist",
            "education": "Tbilisi State Medical Institute",
            "experience": "Head of HIV outpatient department",
        },
        headers=editor_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["lang"] == "en"

    listed = client.get(f"/api/doctors/{doctor_id}/translations")
    assert listed.status_code == 200
    assert [item["lang"] for item in listed.json()] == ["en"]

    fetched = client.get(f"/api/doctors/{doctor_id}/translations/en")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Lali Sharvadze"

    updated = client.put(
        f"/api/doctors/{doctor_id}/translations/en",
        json={"department": "HIV Outpatient Department Lead"},
        headers=editor_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["department"] == "HIV Outpatient Department Lead"

    duplicate = client.post(
        f"/api/doctors/{doctor_id}/translations",
        json={
            "lang": "en",
            "name": "Lali Sharvadze",
            "education": "x",
            "experience": "y",
        },
        headers=editor_headers,
    )
    assert duplicate.status_code == 409
