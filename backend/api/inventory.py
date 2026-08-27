from fastapi import APIRouter, HTTPException
import psycopg
from pydantic import BaseModel, Field
from backend.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME
from backend.services.availability import calculate_availability
from backend.database import get_connection

router = APIRouter()

class AvailabilityRequest(BaseModel):
    product_id: int = Field(gt=0)
    order_qty: int = Field(gt=0)


class ReservationRequest(BaseModel):
    order_id: int = Field(gt=0)

    
@router.post("/availability-check")
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

@router.post("/reserve")
def reserve_inventory(request: ReservationRequest):
    order_id = request.order_id
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                        select product_id, quantity, status from orders
                        where id = %s
                        for update
                        ''', (order_id,))
            order = cur.fetchone()
            if order is None:
                raise HTTPException(status_code = 404, detail="order not found")
            product_id = order[0]
            order_qty = order[1]
            order_status = order[2]
            if order_status != "pending":
                raise HTTPException(status_code=409, detail="order cannot be reserved in its current status")
            
            cur.execute('''
                        select
                            bom_item.component_id,
                            items.name,
                            bom_item.quantity as bom_quantity
                        from bom_item
                        join items
                            on bom_item.component_id = items.id
                        where bom_item.parent_id = %s
                        ''', (product_id,))
            bom_components = cur.fetchall()
            
            if len(bom_components) == 0:
                raise HTTPException(status_code=404, detail="components not found")
            
            component_ids = [component[0] for component in bom_components]
            
            cur.execute('''
                        select item_id, quantity_on_hand, quantity_reserved as old_quantity_reserved
                        from inventory
                        where item_id = ANY(%s)
                        for update
                        ''', (component_ids,))
            inventory_rows = cur.fetchall()
        
            inventory_by_id = { row[0]: {
                "quantity_on_hand": row[1],
                "old_quantity_reserved": row[2]
            } for row in inventory_rows}
            
            components_to_reserve = []
            
            for component in bom_components:
                component_id = component[0]
                component_name = component[1]
                bom_quantity = component[2]
                
                inventory = inventory_by_id.get(component_id)
                if inventory is None:
                    raise HTTPException(status_code=409,
                                        detail=f"inventory record not found for component {component_name}")
                
                
                availability = calculate_availability(
                    bom_quantity=bom_quantity,
                    quantity_on_hand=inventory["quantity_on_hand"],
                    quantity_reserved=inventory["old_quantity_reserved"],
                    order_qty=order_qty
                )
                
                if availability["quantity_shortage"] > 0:
                    raise HTTPException(status_code=409, detail=f'Insufficient inventory for component {component_id}')
                
                components_to_reserve.append(
                    {
                        "component_id": component_id,
                        "quantity_required": availability["quantity_required"]
                    }
                )
            
            for component in components_to_reserve:
                cur.execute('''
                            update inventory
                            set quantity_reserved = quantity_reserved + %s
                            where item_id = %s''', (component["quantity_required"], component["component_id"]))
            
            cur.execute('''
                        update orders
                        set status = 'reserved'
                        where id = %s
                        returning status
                        ''', (order_id,))
            order_status = cur.fetchone()[0]
            return {
                "message": f"Inventory reserved for order {order_id}",
                "order_id": order_id,
                "components": components_to_reserve,
                "order_status": order_status
            }