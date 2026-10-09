from pydantic import BaseModel, ConfigDict
import uuid
class ShippingAddressCreate(BaseModel):
    address: str
    city: str
class ShippingAddressUpdate(BaseModel):
    address: str | None = None
    city: str | None = None

class ShippingAddressResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    address: str
    city: str
    model_config = ConfigDict(from_attributes=True)

