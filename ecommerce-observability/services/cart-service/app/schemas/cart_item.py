from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
import uuid
class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)

class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: uuid.UUID
    quantity: int
    price: Decimal
    product_id: uuid.UUID