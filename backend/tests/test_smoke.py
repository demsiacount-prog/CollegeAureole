"""Tests de fumée : l'app FastAPI démarre et le routage de base répond."""


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "running"
    assert body["database"] == "connected"


def test_health_check_msqlite_database_connected(client):
    resp = client.get("/api/health")
    assert resp.json()["database"] == "connected"


def test_endpoint_sans_token_est_refuse(client):
    # Les routes sous /api/salles exigent un token valide (get_current_user).
    resp = client.get("/api/salles/")
    assert resp.status_code == 401
