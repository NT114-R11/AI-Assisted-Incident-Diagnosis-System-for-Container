from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
import uuid
class OrderItemResponse(BaseModel):
    id: uuid.UUID
    order_number: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)
    
class OrderCreate(BaseModel):
    customer_id: uuid.UUID
    cart_id: uuid.UUID
    shipping_address_id: uuid.UUID
    billing_address_id: uuid.UUID


class OrderUpdate(BaseModel):
    status: str | None = None


class OrderResponse(BaseModel):
    order_number: uuid.UUID
    customer_id: uuid.UUID
    cart_id: uuid.UUID
    total_price: Decimal
    order_date: datetime 
    shipping_address_id: uuid.UUID
    billing_address_id: uuid.UUID
    status: str   
    items: list[OrderItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)