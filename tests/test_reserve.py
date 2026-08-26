from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_reserve_inventory_success(reset_test_database):
    response = client.post("/reserve",
                           json={
                               "order_id": 1
                           },)
    assert response.status_code == 200
    assert response.json()["order_status"] == "reserved"
def test_reserve_inventory_shortage(reset_test_database):
    response = client.post("/reserve",
                           json={
                               "order_id": 2
                           },)
    assert response.status_code == 409
    
def test_reserve_product_without_order(reset_test_database):
    response = client.post(
        "/reserve",
        json={
            "order_id": 999
        }
    )
    assert response.status_code == 404

def test_reserve_product_without_bom(reset_test_database):
    response = client.post(
        "/reserve",
        json={
            "order_id": 3
        }
    )
    assert response.status_code == 404
    
def test_reserve_product_with_non_pending_status(reset_test_database):
    response = client.post(
        "/reserve",
        json={
            "order_id": 4
        }
    )
    assert response.status_code == 409

