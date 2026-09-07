from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_connection

client = TestClient(app)

def test_get_inventory(reset_test_database):
    response = client.get("/inventory")
    
    inventory = response.json()
    assert response.status_code == 200
    assert isinstance(inventory, list)
    
    inventory_dict ={
        item["item_id"]: {
                "item_name": item["item_name"],
                "quantity_on_hand": item["quantity_on_hand"],
                "quantity_reserved": item["quantity_reserved"],
                "quantity_available": item["quantity_available"],
        }
        
        for item in inventory
    }
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                        select item_id, quantity_on_hand, quantity_reserved
                        from inventory
                        ''')
            rows = cur.fetchall()
            
            for row in rows: 
                assert inventory_dict[row[0]]["quantity_on_hand"] == row[1]
                assert inventory_dict[row[0]]["quantity_reserved"] == row[2]
                assert inventory_dict[row[0]]["quantity_available"] == row[1] - row[2]
            
def test_get_inventory_empty(reset_test_database):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM inventory')
    
    response = client.get("/inventory")
    inventory = response.json()
    assert response.status_code == 200
    assert inventory == []