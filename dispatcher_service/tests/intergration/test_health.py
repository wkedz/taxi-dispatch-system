def test_health(client):
    # ACT & ASSERT
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
