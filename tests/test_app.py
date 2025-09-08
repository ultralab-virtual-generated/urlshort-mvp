import os
import tempfile
from fastapi.testclient import TestClient


def get_app():
    tmpdir = tempfile.TemporaryDirectory()
    os.environ["DB_PATH"] = os.path.join(tmpdir.name, "test.db")
    from src.app import app  # import after setting DB_PATH
    app._tmpdir = tmpdir  # prevent GC of temp dir
    return app


def test_shorten_and_redirect_and_stats():
    app = get_app()
    with TestClient(app) as client:
        # shorten
        r = client.post("/api/shorten", json={"url": "https://example.com"})
        assert r.status_code == 200, r.text
        data = r.json()
        code = data["code"]

        # redirect
        r2 = client.get(f"/{code}", allow_redirects=False)
        assert r2.status_code == 307
        assert r2.headers["location"].rstrip("/") == "https://example.com"

        # stats
        r3 = client.get(f"/api/{code}/stats")
        assert r3.status_code == 200
        stats = r3.json()
        assert stats["total_clicks"] >= 1
        assert stats["code"] == code
        assert stats["long_url"].rstrip("/") == "https://example.com"
        assert stats.get("last_access") is not None


def test_qr_endpoint():
    app = get_app()
    with TestClient(app) as client:
        r = client.post("/api/shorten", json={"url": "https://example.com/qr"})
        code = r.json()["code"]
        r2 = client.get(f"/api/{code}/qr")
        assert r2.status_code == 200
        assert r2.headers["content-type"].startswith("image/png")
