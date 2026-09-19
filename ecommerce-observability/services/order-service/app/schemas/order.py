from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class OrderItemResponse(BaseModel):
    id: int
    order_number: int
    product_id: int
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)
    
class OrderCreate(BaseModel):
    customer_id: int
    cart_id: int
    shipping_address_id: int
    billing_address_id: int


class OrderUpdate(BaseModel):
    status: str | None = None


class OrderResponse(BaseModel):
    order_number: int
    customer_id: int
    cart_id: int
    total_price: Decimal
    order_date: datetime 
    shipping_address_id: int
    billing_address_id: int
    status: str   
    items: list[OrderItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)