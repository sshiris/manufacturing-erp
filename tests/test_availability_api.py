from fastapi.testclient import TestClient
from backend.main import app
from backend.services.availability import calculate_availability

client = TestClient(app)

def test_negative_order_qty():
    response = client.post("/availability-check",
                           json={
                               "product_id": 1,
                               "order_qty": -5
                           })
    assert response.status_code == 422
    
def test_nonexistent_product_id():
    response = client.post("/availability-check",
                           json={
                               "product_id": 9999,
                               "order_qty": 10
                           })
    assert response.status_code == 404
    assert response.json()["detail"] == "item does not exist"
    
def test_nonexistent_product_in_bom():
    response = client.post("/availability-check",
                           json={
                               "product_id": 2,
                               "order_qty": 10
                           })
    assert response.status_code == 404
    assert response.json()["detail"] == "item does not exist in bom"
