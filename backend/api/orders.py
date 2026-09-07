from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import psycopg
from backend.config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME)
from backend.database import get_connection
from typing import Literal

router = APIRouter()


class OrderCreateRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    estimated_delivery_date: datetime | None = None

@router.post("/orders")
def create_order(request: OrderCreateRequest):
    product_id = request.product_id
    quantity = request.quantity
    unit_price = request.unit_price
    estimated_delivery_date = request.estimated_delivery_date
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                select id from items
                where id = %s''', (product_id,))
            product = cur.fetchone()
            if product is None:
                raise HTTPException(status_code=404, detail="Product not found")
            
            
            cur.execute('''
                insert into orders (
                    product_id,
                    quantity,
                    unit_price,
                    estimated_delivery_date
                ) values (
                    %s,
                    %s,
                    %s,
                    %s
                )
                returning 
                    id,
                    product_id,
                    quantity,
                    unit_price,
                    status,
                    created_at,
                    estimated_delivery_date;
                                        ''', (
                    product_id,
                    quantity,
                    unit_price,
                    estimated_delivery_date
                                        ))
            order = cur.fetchone()
                    
    return {
        "message": "order created successfully",
        "order": {
            "id": order[0],
            "product_id": order[1],
            "quantity": order[2],
            "unit_price": order[3],
            "status": order[4],
            "created_at": order[5],
            "estimated_delivery_date": order[6]
        }
    }
    
@router.get("/orders/{order_id}")
def get_order(order_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                select
                    orders.id,
                    orders.product_id,
                    items.name as product_name,
                    orders.quantity,
                    orders.unit_price,
                    orders.unit_price * orders.quantity as total_price,
                    orders.status,
                    orders.created_at,
                    orders.estimated_delivery_date
                from orders
                join items
                    on orders.product_id = items.id
                where orders.id = %s
                ''', (order_id,))
            order = cur.fetchone()
            if order is None:
                raise HTTPException(status_code= 404, detail="Order not found")
            return {
                "id": order[0],
                "product_id": order[1],
                "product_name": order[2],
                "quantity": order[3],
                "unit_price": order[4],
                "total_price": order[5],
                "status": order[6],
                "created_at": order[7],
                "estimated_delivery_date": order[8]
            }
@router.get("/orders")
def get_orders():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                select
                    orders.id,
                    items.name as product_name,
                    orders.quantity,
                    orders.unit_price * orders.quantity as total_price,
                    orders.status,
                    orders.created_at,
                    orders.estimated_delivery_date
                from orders
                join items
                    on orders.product_id = items.id
                order by orders.created_at desc
                ''')
            orders = cur.fetchall()
            
            return [
                {
                    "id": order[0],
                    "product_name": order[1],
                    "quantity": order[2],
                    "total_price": order[3],
                    "status": order[4],
                    "created_at": order[5],
                    "estimated_delivery_date": order[6]
                }
                for order in orders
            ]
class UpdateOrderStatusRequest(BaseModel):
    status: Literal["in_progress"]
    
@router.post("/orders/{order_id}/start")
def update_order_status(order_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                select id, status from orders
                where id = %s
                for update
                ''', (order_id,))
            
            order = cur.fetchone()
            if order is None:
                raise HTTPException(status_code=404, detail="Order not found")
            
            current_status = order[1]
            
            if current_status != "reserved":
                raise HTTPException(
                    status_code=409,
                    detail=f"order status {current_status} cannot be updated to in_progress"
                )
            
            cur.execute(
                '''
                update orders
                set status = %s
                where id = %s
                returning status 
                ''', ("in_progress", order_id)
            )
            
            updated_order = cur.fetchone()[0]
            
            return {
                "status": updated_order,
                "order_id": order_id,
                "message": f"order status updated to {updated_order}"
            }
            
@router.post("/orders/{order_id}/complete")
def complete_order(order_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                select
                    id, status, product_id, quantity
                from orders
                where id = %s
                for update
                ''', (order_id,)                
            )
            order = cur.fetchone()
            if order is None:
                raise HTTPException(status_code=404, detail="Order not found")
            
            product_id = order[2]
            current_status = order[1]
            order_quantity = order[3]
            
            if current_status != "in_progress":
                raise HTTPException(
                    status_code=409,
                    detail=f"can not complete order with status {current_status}"
                )
            
            cur.execute(
                '''
                select 
                    component_id,
                    quantity
                from bom_item
                where parent_id = %s
                ''', (product_id,)
            )
            bom_items = cur.fetchall()
            if not bom_items:
                raise HTTPException(
                    status_code=404,
                    detail=f"No BOM items found for product {product_id}"
                )
            component_ids = [
                item[0]
                for item in bom_items
            ]
            cur.execute(
                '''
                select
                    item_id,
                    quantity_on_hand,
                    quantity_reserved
                from inventory
                where item_id = any(%s)
                for update''', (component_ids,)   
            )
            inventory_rows = cur.fetchall()
            inventory_dict = {
                row[0]:{
                    "quantity_on_hand": row[1],
                    "quantity_reserved": row[2]
                }
                for row in inventory_rows
            }
            components_to_consume = []
            for component_id, bom_quantity in bom_items:
                inventory = inventory_dict.get(component_id)
                if inventory is None:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Inventory record not found for component {component_id}"
                    )
                quantity_required = bom_quantity * order_quantity
                if inventory["quantity_on_hand"] < quantity_required:
                    raise HTTPException(
                        status_code=409,
                        detail=f"not enough on_hand inventory for component {component_id}. required: {quantity_required}, on_hand: {inventory['quantity_on_hand']}"
                    )
                    
                if inventory["quantity_reserved"] < quantity_required:
                    raise HTTPException(
                        status_code=409,
                        detail=f"not enough reserved inventory for component {component_id}. required: {quantity_required}, reserved: {inventory['quantity_reserved']}"
                    )
                components_to_consume.append(
                    {
                        "component_id": component_id,
                        "quantity_required": quantity_required
                    }
                )
                
            for component in components_to_consume:
                cur.execute(
                    '''
                    update inventory
                    set quantity_on_hand = quantity_on_hand - %s,
                        quantity_reserved = quantity_reserved - %s
                    where item_id = %s''', (
                        component["quantity_required"],
                        component["quantity_required"],
                        component["component_id"]
                    )
                )
                
            cur.execute(
                '''
                update orders
                set status = 'completed'
                where id = %s
                returning status
                ''', 
                (order_id,)
            )
            
            updated_order_status = cur.fetchone()[0]
            
            return {
                "order_id": order_id,
                "status": updated_order_status
            }