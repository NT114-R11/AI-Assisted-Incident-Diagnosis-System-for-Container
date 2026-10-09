from pydantic import BaseModel, ConfigDict
import uuid
class ProductBase(BaseModel):
    product_name:str
    quantity: int = 0
    description: str | None = None
    manufacturer: str | None = None
    categories: str | None = None
    price: float 
    seller_id: uuid.UUID

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name:str | None = None
    quantity: int | None = None
    description: str | None = None
    manufacturer: str | None = None
    categories: str | None = None
    price: float  | None = None
    seller_id: uuid.UUID | None = None

class ProductResponse(ProductBase):
    product_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class StockUpdate(BaseModel):
    quantity: int