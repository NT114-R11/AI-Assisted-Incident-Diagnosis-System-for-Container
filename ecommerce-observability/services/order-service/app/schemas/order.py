from datetime import datetime
from pydantic import BaseModel, ConfigDict

class OrderCreate(BaseModel):
    customer_id: int
    cart_id: int
    shipping_address_id: int
    billing_address_id: int
class OrderUpdate(BaseModel):
    status: str

class OrderResponse(BaseModel):
    order_number: int
    customer_id: int
    cart_id: int
    order_data: datetime
    shipping_address_id: int
    billing_address_id: int
    model_config = ConfigDict(from_attributes=True)