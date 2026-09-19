import httpx
import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.customer import Customer
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress
from app.schemas.order import (OrderCreate, OrderResponse, OrderUpdate)

logger = logging.getLogger(__name__)
CART_SERVICE_URL = "http://cart-service:8000"
router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderResponse)
def create_order (data: OrderCreate, db: Session = Depends(get_db)):
    #Check customer
    customer = db.get(Customer, data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found!")
    # Check shipping address
    shipping_address = db.get(ShippingAddress, data.shipping_address_id)
    if not shipping_address:
        raise HTTPException(status_code=404, detail="Shipping address not found! Create ones")
    if shipping_address.customer_id != data.customer_id:
        raise HTTPException(status_code=400, detail="Shipping address does not belong to customer")

    #Check billing address
    billing_address = db.get(BillingAddress, data.billing_address_id)
    if not billing_address:
        raise HTTPException(status_code=404, detail="Billing address not found! Create ones")
    if billing_address.customer_id != data.customer_id:
        raise HTTPException(status_code=400, detail="Billing address does not belong to customer")
    
    # Call to cart service
    try:
        response = httpx.get(f"{CART_SERVICE_URL}/carts/{data.cart_id}", timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Cart Service unavailable")
    
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Cart not found")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Cart-Service error")
    
    cart_data = response.json()
    cart_items = cart_data.get("items", [])
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty. Cannot place order.")
    # Create order
    order = Order(
        customer_id=data.customer_id,
        cart_id=data.cart_id,
        shipping_address_id=data.shipping_address_id,
        billing_address_id=data.billing_address_id,
        total_price=Decimal(str(cart_data.get("total_price", 0)))
    )
    # Create order item to storge history's shopping
    for item in cart_items:
        order_item = OrderItem(
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=Decimal(str(item["price"]))
        )
        order.items.append(order_item)

    db.add(order)
    try:            
        db.commit()
        db.refresh(order)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid customer, address, or cart references")
    # Clear cart out order when place order successfully
    try:
        httpx.delete(f"{CART_SERVICE_URL}/carts/{data.cart_id}", timeout=5.0)
    except httpx.RequestError as exc:
        logger.warning(f"Order {order.order_number} created, but failed to clear cart {data.cart_id}: {exc}")
    return order

@router.get("/", response_model=list[OrderResponse])
def get_orders(db:Session = Depends(get_db)):
    statement = select(Order).options(joinedload(Order.items))
    
    return db.scalars(statement).unique().all()

@router.get("/{order_number}", response_model=OrderResponse)
def get_order(order_number:int, db:Session = Depends(get_db)):
    statement = select(Order).where(Order.order_number == order_number).options(joinedload(Order.items))
    order = db.scalars(statement).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found!")
    return order

@router.put("/{order_number}", response_model=OrderResponse)
def update_order(order_number: int , data: OrderUpdate, db : Session = Depends(get_db)):
    order = db.get(Order, order_number)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found!")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    try:
        db.commit()
        db.refresh(order)
        return order
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update order")
@router.delete("/{order_number}")
def delete_order(order_number:int , db:Session = Depends(get_db)):
    order = db.get(Order, order_number)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found!")
    try:
        db.delete(order)
        db.commit()
        return {"message" : "Order was deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete order due to constraint dependencies")