from pydantic import BaseModel, ConfigDict

class ShippingAddressCreate(BaseModel):
    address: str
    city: str
class ShippingAddressUpdate(BaseModel):
    address: str | None = None
    city: str | None = None

class ShippingAddressResponse(BaseModel):
    id: int
    customer_id: int
    address: str
    city: str
    model_config = ConfigDict(from_attributes=True)

