from pydantic import BaseModel, ConfigDict, EmailStr

class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None

class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    phone: str | None = None
    model_config = ConfigDict(from_attributes=True)