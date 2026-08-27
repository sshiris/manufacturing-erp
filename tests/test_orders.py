from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_connection

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

def test_get_orders_success(reset_test_database):
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first_order = data[0]
    assert "id" in first_order
    assert "product_name" in first_order
    assert "quantity" in first_order
    assert "total_price" in first_order
    assert "status" in first_order
    assert "created_at" in first_order
    assert "estimated_delivery_date" in first_order
def test_get_orders_empty(reset_test_database):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM orders')
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data == []