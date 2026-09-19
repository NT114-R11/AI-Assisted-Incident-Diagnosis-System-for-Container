from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class OrderItemResponse(BaseModel):
    id: int
    order_number: int
    product_id: int
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)