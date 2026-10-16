import pytest
from django.urls import reverse


@pytest.fixture
def dist(tmp_path, settings):
    """A fake React build so these tests don't depend on running npm."""
    build = tmp_path / "dist"
    (build / "assets").mkdir(parents=True)
    (build / "index.html").write_text("<!doctype html><title>Panjabi House</title><div id=root></div>")
    (build / "assets" / "app-abc123.js").write_text("console.log('hi')")
    (build / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    (tmp_path / "secret.txt").write_text("top secret")
    settings.FRONTEND_DIST_DIR = build
    return build


def _body(resp):
    return b"".join(resp.streaming_content).decode()


def test_index_is_served_at_root(client, dist):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/html")
    assert "Panjabi House" in _body(resp)


@pytest.mark.parametrize("route", ["/shop", "/product/some-slug", "/orders/123e4567-e89b-12d3-a456-426614174000"])
def test_client_side_routes_fall_back_to_index(client, dist, route):
    resp = client.get(route)
    assert resp.status_code == 200
    assert "<div id=root>" in _body(resp)


def test_hashed_assets_are_served_with_immutable_caching(client, dist):
    resp = client.get("/assets/app-abc123.js")
    assert resp.status_code == 200
    assert "javascript" in resp["Content-Type"]
    assert "immutable" in resp["Cache-Control"]


def test_missing_asset_is_a_404_not_html(client, dist):
    assert client.get("/assets/old-build.js").status_code == 404


def test_path_traversal_cannot_escape_the_build_dir(client, dist):
    resp = client.get("/assets/..%2f..%2fsecret.txt")
    assert resp.status_code == 404


def test_unknown_api_path_is_a_real_404(client, dist):
    resp = client.get("/api/v1/definitely-not-real/")
    assert resp.status_code == 404
    assert b"<div id=root>" not in resp.content
    # ...and it uses the same JSON envelope as every other API error
    assert resp.json() == {"success": False, "message": "Not found.", "errors": {}, "code": "not_found"}


def test_admin_without_slash_still_redirects(client, dist):
    assert client.get("/admin").status_code == 301


def test_non_get_methods_are_rejected(client, dist):
    assert client.post("/shop").status_code == 405


def test_helpful_page_when_frontend_not_built(client, settings, tmp_path):
    settings.FRONTEND_DIST_DIR = tmp_path / "nope"
    resp = client.get("/")
    assert resp.status_code == 503
    assert b"npm run build" in resp.content


@pytest.mark.django_db
def test_api_still_reachable_alongside_frontend(api_client, dist):
    assert api_client.get(reverse("v1:health-check")).status_code == 200
