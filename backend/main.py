from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg
from backend.config import (
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DATABASE_NAME
)
from backend.services.availability import calculate_availability
from backend.api.orders import router as orders_router
from backend.api.inventory import router as inventory_router

app = FastAPI()

app.include_router(orders_router)
app.include_router(inventory_router)

