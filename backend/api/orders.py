from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import psycopg
from backend.config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME)

router = APIRouter()


class OrderCreateRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    estimated_delivery_date: datetime | None = None
    
def get_connection():
    return psycopg.connect(
        host = DB_HOST,
        port = DB_PORT,
        dbname = DATABASE_NAME,
        user = DB_USER,
        password = DB_PASSWORD
    )

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