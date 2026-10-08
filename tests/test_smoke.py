"""
End-to-end smoke tests for Phase 1: register/login, browse catalogue,
ask the advisor, add to cart, place an order. Run with: pytest
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200


def test_categories_and_products_are_seeded():
    r = client.get("/categories/")
    assert r.status_code == 200
    r = client.get("/products/")
    assert r.status_code == 200


def _get_token():
    client.post("/auth/register", json={
        "full_name": "Test User",
        "email": "smoketest@example.com",
        "password": "Test@1234",
    })
    r = client.post("/auth/login", data={"username": "smoketest@example.com", "password": "Test@1234"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_register_login_and_me():
    token = _get_token()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "smoketest@example.com"


def test_advisor_matches_a_known_problem():
    r = client.post("/advisor/ask", json={"query": "my fan is running slowly"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["problem"]["slug"] == "fan-running-slowly"


def test_advisor_flags_high_danger_problems():
    r = client.post("/advisor/ask", json={"query": "my mcb keeps tripping"})
    body = r.json()
    assert body["matched"] is True
    assert body["problem"]["danger_level"] == "high"


def test_cart_and_order_flow():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}

    products = client.get("/products/").json()
    assert len(products) > 0
    product_id = products[0]["id"]

    r = client.post("/cart/items", json={"product_id": product_id, "quantity": 2}, headers=headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1

    r = client.post("/orders/", json={"payment_method": "cod"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["total_amount"] > 0
