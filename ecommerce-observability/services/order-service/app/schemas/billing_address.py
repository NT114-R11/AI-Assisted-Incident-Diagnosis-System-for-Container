from pydantic import BaseModel, ConfigDict

class BillingAddressCreate(BaseModel):
    address: str
    city: str

class BillingAddressUpdate(BaseModel):
    address: str | None = None
    city: str | None = None

class BillingAddressResponse(BaseModel):
    id: int 
    customer_id: int
    address: str
    city: str
    model_config = ConfigDict(from_attributes=True)
