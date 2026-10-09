import httpx
import uuid
import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request,status

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.customer import Customer
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress
from app.request_context import build_forward_headers
from app.schemas.order import (OrderCreate, OrderResponse, OrderUpdate)

logger = logging.getLogger(__name__)
CART_SERVICE_URL = "http://cart-service:8000"
PRODUCT_SERVICE_URL = "http://product-service:8000"
router = APIRouter(prefix="/orders", tags=["Orders"])

# Helper Function: Dealing with stock rollback in case of order creation failure
async def rollback_stock(client: httpx.AsyncClient, items: list):
    for item in items:
        try:
            await client.patch(
                f"{PRODUCT_SERVICE_URL}/products/{item['product_id']}/restore-stock",
                json={"quantity": item["quantity"]}
            )
        except Exception as e:
            logger.error(f"Critical: Failed to rollback stock for product {item['product_id']}: {e}")


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    # Check if customer exists and validate shipping/billing addresses
    customer = db.get(Customer, data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found!")

    shipping_address = db.get(ShippingAddress, data.shipping_address_id)
    if not shipping_address or shipping_address.customer_id != data.customer_id:
        raise HTTPException(status_code=400, detail="Invalid shipping address")

    billing_address = db.get(BillingAddress, data.billing_address_id)
    if not billing_address or billing_address.customer_id != data.customer_id:
        raise HTTPException(status_code=400, detail="Invalid billing address")

    deducted_items = []   # roollback stock in case of failure
    order_items = []      # List of OrderItem 

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Get cart details from Cart Service
        try:
            cart_resp = await client.get(f"{CART_SERVICE_URL}/carts/{data.cart_id}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Cart Service unavailable")

        if cart_resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Cart not found")
        if cart_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Cart-Service error")

        cart_data = cart_resp.json()
        cart_items = cart_data.get("items", [])
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty. Cannot place order.")

        # 3. Deduct stock for each item in the cart from Product Service
        for item in cart_items:
            p_id = item["product_id"]
            qty = item["quantity"]

            try:
                stock_resp = await client.patch(
                    f"{PRODUCT_SERVICE_URL}/products/{p_id}/deduct-stock",
                    json={"quantity": qty},
                )
            except httpx.RequestError:
                await rollback_stock(client, deducted_items)
                raise HTTPException(status_code=503, detail="Product Service unavailable during stock deduction")

            if stock_resp.status_code != 200:
                await rollback_stock(client, deducted_items)
                raise HTTPException(
                    status_code=stock_resp.status_code,
                    detail=f"Failed to deduct stock for product {p_id}: {stock_resp.json().get('detail')}",
                )

            product = stock_resp.json()
            unit_price = Decimal(str(product["price"]))   

            deducted_items.append({"product_id": p_id, "quantity": qty})
            order_items.append(OrderItem(product_id=p_id, quantity=qty, price=unit_price))

    # 4. Create the order in the database
    total_price = sum((i.price * i.quantity for i in order_items), Decimal("0.00"))

    order = Order(
        customer_id=data.customer_id,
        cart_id=data.cart_id,
        shipping_address_id=data.shipping_address_id,
        billing_address_id=data.billing_address_id,
        total_price=total_price,
        status="PENDING",
    )
    order.items.extend(order_items)

    db.add(order)
    try:
        db.commit()
        db.refresh(order)
    except IntegrityError:
        db.rollback()
        async with httpx.AsyncClient(timeout=5.0) as client:
            await rollback_stock(client, deducted_items)
        raise HTTPException(status_code=400, detail="Invalid references on Order creation")

    # 5. Delete the cart from Cart Service after successful order creation
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.delete(f"{CART_SERVICE_URL}/carts/{data.cart_id}")
    except httpx.RequestError as exc:
        logger.warning(f"Order {order.order_number} created, but failed to clear cart {data.cart_id}: {exc}")

    return order
@router.get("/", response_model=list[OrderResponse])
def get_orders(db:Session = Depends(get_db)):
    statement = select(Order).options(joinedload(Order.items))
    
    return db.scalars(statement).unique().all()

@router.get("/{order_number}", response_model=OrderResponse)
def get_order(order_number: uuid.UUID, db:Session = Depends(get_db)):
    statement = select(Order).where(Order.order_number == order_number).options(joinedload(Order.items))
    order = db.scalars(statement).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found!")
    return order


""" Update an existing order """


@router.put("/{order_number}", response_model=OrderResponse)
def update_order(order_number: uuid.UUID , data: OrderUpdate, db : Session = Depends(get_db)):
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


@router.put("/{order_number}/cancel", response_model=OrderResponse)
async def cancel_order(order_number: uuid.UUID, db: Session = Depends(get_db)):
    """API Cancel an order and restore stock for its items"""
    statement = select(Order).where(Order.order_number == order_number).options(joinedload(Order.items))
    order = db.scalars(statement).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found!")
    
    if order.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Order is already cancelled")

    # 1. Restore stock for items in the cancelled order
    async with httpx.AsyncClient(timeout=5.0) as client:
        for item in order.items:
            try:
                await client.patch(
                    f"{PRODUCT_SERVICE_URL}/products/{item.product_id}/restore-stock",
                    json={"quantity": item.quantity}
                )
            except httpx.RequestError as exc:
                logger.error(f"Failed to restore stock for product {item.product_id} on order {order_number} cancel: {exc}")

    # 2. Update order status to CANCELLED
    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_number}")
def delete_order(order_number: uuid.UUID, db:Session = Depends(get_db)):
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