from pydantic import BaseModel, ConfigDict, EmailStr
class SellerBase(BaseModel):
    user_email: EmailStr
    shop_name: str
    description: str | None = None
    phone: str | None = None

class SellerCreate(SellerBase):
    pass

class SellerUpdate(BaseModel):
    shop_name : str | None = None   
    description: str | None = None  
    phone: str | None = None

class SellerResponse(SellerBase):
    id: int
    model_config =ConfigDict(from_attributes = True)
