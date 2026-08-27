from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
def test_get_order_success(reset_test_database):
    response = client.get("/orders/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["product_id"] == 1
    assert data["product_name"] == "DESK"
    assert data["quantity"] == 1
    assert data["unit_price"] == 250.00
    assert data["total_price"] == 250.00
    assert data["status"] == "pending"
    
def test_get_order_not_found(reset_test_database):
    response = client.get("/orders/999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Order not found"
    