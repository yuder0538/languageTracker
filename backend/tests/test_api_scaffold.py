def test_health_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ping_uses_db_dependency(client):
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
