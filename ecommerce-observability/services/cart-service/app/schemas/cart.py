from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.schemas.cart_item import CartItemResponse
import uuid
class CartCreate(BaseModel):
    customer_id: uuid.UUID

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cart_id: uuid.UUID
    customer_id: uuid.UUID
    total_price: Decimal
    items: list[CartItemResponse] = []