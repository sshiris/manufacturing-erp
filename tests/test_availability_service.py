from fastapi.testclient import TestClient
from backend.main import app
from backend.services.availability import calculate_availability

client = TestClient(app)

def test_calculate_availability():
    result = calculate_availability(
        bom_quantity=2,
        quantity_on_hand=10,
        quantity_reserved=3,
        order_qty=4
    )
    assert result == {
        "quantity_required": 8,
        "quantity_available": 7,
        "quantity_shortage": 1
    }
def test_calculate_availability_no_shortage():
    result = calculate_availability(
        bom_quantity=1,
        quantity_on_hand=10,
        quantity_reserved=2,
        order_qty=5
    )
    assert result == {
        "quantity_required": 5,
        "quantity_available": 8,
        "quantity_shortage": 0
    }