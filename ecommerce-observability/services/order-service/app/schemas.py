from pydantic import BaseModel

class OrderCreate(BaseModel):
    customer_name: str

    product_name: str

    quantity: int

    total_price: float

class OrderStatusUpdate(BaseModel):
    pass