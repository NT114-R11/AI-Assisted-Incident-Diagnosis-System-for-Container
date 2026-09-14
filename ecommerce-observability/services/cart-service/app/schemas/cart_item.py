from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)

class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    quantity: int
    price: Decimal
    product_id: int