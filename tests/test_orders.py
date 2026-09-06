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
    
def test_update_order_status_reserved_to_in_progress(reset_test_database):
    response = client.patch(
        "/orders/4/status",
        json={"status": "in_progress"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["order_id"] == 4
    
def test_update_order_status_in_progress_to_completed(reset_test_database):
    response = client.patch(
    "/orders/5/status",
    json = {"status": "completed"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["order_id"] == 5
    
def test_update_order_status_pending_to_in_progress_not_allowed(reset_test_database):
    response = client.patch(
        "/orders/1/status",
        json={"status": "in_progress"}
    )
    assert response.status_code == 409
   
def test_update_order_status_invalid_status(reset_test_database):
    response = client.patch(
        "/orders/1/status",
        json={"status": "banana"}
    )
    assert response.status_code == 422
    
def test_update_order_status_order_not_found(reset_test_database):
    response = client.patch(
        "/orders/999/status",
        json={"status": "in_progress"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Order not found"
    
def test_complete_order_success(reset_test_database):
    response = client.post("orders/5/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                select quantity_on_hand, quantity_reserved
                from inventory
                where inventory.item_id in (3,4,5)
                order by item_id'''
            )
            row = cur.fetchall()
            assert row[0][0] == 46
            assert row[0][1] == 6
            
            assert row[1][0] == 5
            assert row[1][1] == 0
            
            assert row[2][0] == 492
            assert row[2][1] == 92
            