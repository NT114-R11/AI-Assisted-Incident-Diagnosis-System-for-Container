from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.cart_item import CartItemResponse

class CartCreate(BaseModel):
    customer_id: int

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cart_id: int
    customer_id: int
    total_price: Decimal
    items: list[CartItemResponse]