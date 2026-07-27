def test_get_settings_creates_seed_row_on_first_read(client):
    response = client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json() == {"daily_new_card_limit": 15}


def test_patch_settings_updates_value(client):
    response = client.patch("/api/v1/settings", json={"daily_new_card_limit": 20})

    assert response.status_code == 200
    assert response.json() == {"daily_new_card_limit": 20}

    follow_up = client.get("/api/v1/settings")
    assert follow_up.json() == {"daily_new_card_limit": 20}


def test_patch_settings_rejects_zero(client):
    response = client.patch("/api/v1/settings", json={"daily_new_card_limit": 0})

    assert response.status_code == 422


def test_patch_settings_rejects_negative(client):
    response = client.patch("/api/v1/settings", json={"daily_new_card_limit": -1})

    assert response.status_code == 422


def test_patch_settings_rejects_above_max(client):
    response = client.patch("/api/v1/settings", json={"daily_new_card_limit": 501})

    assert response.status_code == 422


def test_patch_settings_rejects_non_integer(client):
    response = client.patch("/api/v1/settings", json={"daily_new_card_limit": "abc"})

    assert response.status_code == 422


def test_patch_settings_invalid_payload_does_not_change_stored_value(client):
    client.patch("/api/v1/settings", json={"daily_new_card_limit": 42})

    response = client.patch("/api/v1/settings", json={"daily_new_card_limit": 0})
    assert response.status_code == 422

    follow_up = client.get("/api/v1/settings")
    assert follow_up.json() == {"daily_new_card_limit": 42}
