from pydantic import BaseModel, ConfigDict

class ProductBase(BaseModel):
    product_name:str
    quantity: int = 0
    description: str | None = None
    manufacturer: str | None = None
    categories: str | None = None
    price: float 
    seller_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name:str | None = None
    quantity: int | None = None
    description: str | None = None
    manufacturer: str | None = None
    categories: str | None = None
    price: float  | None = None
    seller_id: int | None = None

class ProductResponse(ProductBase):
    product_id: int
    model_config = ConfigDict(from_attributes=True)