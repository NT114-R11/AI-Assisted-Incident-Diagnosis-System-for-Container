from pydantic import BaseModel, ConfigDict
import uuid
class BillingAddressCreate(BaseModel):
    address: str
    city: str

class BillingAddressUpdate(BaseModel):
    address: str | None = None
    city: str | None = None

class BillingAddressResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    address: str
    city: str
    model_config = ConfigDict(from_attributes=True)
