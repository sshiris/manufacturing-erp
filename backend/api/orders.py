from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import psycopg
from backend.config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME)
from backend.database import get_connection

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