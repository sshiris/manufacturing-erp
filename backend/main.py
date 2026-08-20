from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg
from backend.config import (
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME
)
from backend.services.availability import calculate_availability


app = FastAPI()

class AvailabilityRequest(BaseModel):
    product_id: int = Field(gt=0)
    order_qty: int = Field(gt=0)
    
def get_connection():
    return psycopg.connect(
        host = DB_HOST,
        port = DB_PORT,
        dbname = DATABASE_NAME,
        user = DB_USER,
        password = DB_PASSWORD
    )

    
@app.post("/availability-check")
def verify_availability_request(request: AvailabilityRequest):
    product_id = request.product_id
    order_qty = request.order_qty
    
    result = []
    can_fulfill = True
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(''' 
                        select id from items
                        where id = %s
                        ''', (product_id,))
            product = cur.fetchone()
            if product is None:
                raise HTTPException(status_code=404, detail="item does not exist")
            cur.execute('''
                        select parent_id from bom_item
                        where parent_id = %s
                        limit 1
                         ''',(product_id,))
            bom = cur.fetchone()
            if bom is None:
                raise HTTPException(status_code=404, detail="item does not exist in bom")
            cur.execute('''
                        select
                        bom_item.component_id as component_id,
                        items.name as name,
                        bom_item.quantity as quantity,
                        coalesce(inventory.quantity_on_hand,0) as quantity_on_hand,
                        coalesce(inventory.quantity_reserved,0) as quantity_reserved
                        from bom_item
                        join items
                            on bom_item.component_id = items.id 
                        left join inventory
                            on bom_item.component_id = inventory.item_id
                        where bom_item.parent_id = %s
                        ''',(product_id,))
            rows = cur.fetchall()
            for row in rows:
                component_id = row[0]
                name = row[1]
                quantity = row[2]
                quantity_on_hand = row[3]
                quantity_reserved = row[4]
                
                availability = calculate_availability(
                    bom_quantity=quantity,
                    quantity_on_hand=quantity_on_hand,
                    quantity_reserved=quantity_reserved,
                    order_qty=order_qty
                )
                
                quantity_required = availability["quantity_required"]
                quantity_available = availability["quantity_available"]
                quantity_shortage = availability["quantity_shortage"]
                
                if quantity_shortage > 0:
                    can_fulfill = False
                
                result.append({
                    "component_id": component_id,
                    "name": name,
                    "quantity_required": quantity_required,
                    "quantity_available": quantity_available,
                    "quantity_shortage": quantity_shortage,
                })
    
    
    return{
        "product_id": product_id,
        "order_qty": order_qty,
        "components": result,
        "can_fulfill": can_fulfill
    }

@app.post("/reserve")
def reserve_inventory(request: AvailabilityRequest):
    product_id = request.product_id
    order_qty = request.order_qty
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                ''' 
                select id from items
                where id = %s
                ''', (product_id,))
            product = cur.fetchone()
            if product is None:
                raise HTTPException(status_code=404, detail="item does not exist")
            cur.execute('''
                        select parent_id from bom_item
                        where parent_id = %s
                        limit 1
                         ''',(product_id,))
            bom = cur.fetchone()
            if bom is None:
                raise HTTPException(status_code=404, detail="item does not exist in bom")
            cur.execute(
                '''
                select
                    bom_item.component_id as component_id,
                    items.name as name,
                    bom_item.quantity as quantity,
                    inventory.quantity_on_hand as quantity_on_hand,
                    inventory.quantity_reserved as quantity_reserved,
                    inventory.item_id as inventory_item_id
                from bom_item
                join items
                    on bom_item.component_id = items.id
                left join inventory
                    on bom_item.component_id = inventory.item_id
                where bom_item.parent_id = %s
                for update of inventory
                ''', (product_id,))
            components = cur.fetchall()
            new_components = []
            for component in components:
                component_id = component[0]
                component_name = component[1]
                bom_quantity = component[2]
                quantity_on_hand = component[3]
                old_quantity_reserved = component[4]
                inventory_item_id = component[5]
                
                if inventory_item_id is None:
                    raise HTTPException(
                        status_code = 409,
                        detail = f'No inventory record for component {component_name} (ID: {component_id})'
                    )
                
                availability = calculate_availability(
                    bom_quantity=bom_quantity,
                    quantity_on_hand=quantity_on_hand,
                    quantity_reserved=old_quantity_reserved,
                    order_qty=order_qty
                )
                
                quantity_shortage = availability["quantity_shortage"]
                if quantity_shortage > 0:
                    raise HTTPException(status_code=409, detail=f'Not enough inventory for component {component_name} (ID: {component_id}). Shortage: { quantity_shortage}')
                
                new_components.append(
                    {
                        "component_id": component_id,
                        "name": component_name,
                        "old_quantity_reserved": old_quantity_reserved,
                        "quantity_on_hand": quantity_on_hand,
                        "quantity_required": availability["quantity_required"],
                    }
                )
            for component in new_components:
                component_id = component["component_id"]
                quantity_required = component["quantity_required"]
                cur.execute(
                    '''
                    update inventory
                    set quantity_reserved = quantity_reserved + %s
                    where item_id = %s
                    ''',
                    (quantity_required, component_id)
                    )
            return {
                "message": f"Inventory reserved for product {product_id} with order quantity {order_qty}.",
                "components": new_components
            }