from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_reserve_inventory_success(reset_test_database):
    response = client.post("/reserve",
                           json={
                               "product_id": 1,
                               "order_qty": 5
                           },)
    assert response.status_code == 200
def test_reserve_inventory_shortage(reset_test_database):
    response = client.post("/reserve",
                           json={
                               "product_id": 1,
                               "order_qty": 10
                           },)
    assert response.status_code == 409
    
def test_reserve_product_without_bom(reset_test_database):
    response = client.post(
        "/reserve",
        json={
            "product_id": 2,
            "order_qty": 5
        }
    )

    assert response.status_code == 404