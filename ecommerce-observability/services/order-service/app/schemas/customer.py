from pydantic import BaseModel, ConfigDict

class CustomerCreate(BaseModel):
    name: str
    email: str 
    phone: str | None = None

class CustomerUpdate(BaseModel):
    name: str
    email: str
    phone: str | None = None

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    phone: str | None
    model_config = ConfigDict(from_attributes=True)