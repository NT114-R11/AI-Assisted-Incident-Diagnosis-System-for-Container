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