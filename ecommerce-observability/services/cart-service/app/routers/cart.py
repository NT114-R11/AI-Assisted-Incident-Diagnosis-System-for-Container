from decimal import Decimal
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database.database import get_db
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.schemas.cart import CartCreate, CartResponse
from app.schemas.cart_item import (CartItemCreate, CartItemResponse, CartItemUpdate)

router = APIRouter(prefix="/carts", tags=["Carts"])

#Get product service 
PRODUCT_SERVICE_URL = "http://product-service:8000"

# A helper function calculate total price
def recalculate_cart_total(cart: Cart, db:Session = Depends(get_db)):
    statement = select(CartItem).where(Cart.cart_id == cart.cart_id) 
    items = db.scalars(statement).all()#Get all object in a cart
    cart.total_price = sum (item.price * item.quantity for item in items) # calculate all items which is store in the cart

# Create cart
@router.post("/", response_model=CartResponse, status_code=201)
def create_cart(cart_data:CartCreate, db: Session = Depends(get_db)):
    statement = select(Cart).where(Cart.customer_id == cart_data.customer_id)

    existing_cart = db.scalars(statement).first()
    if existing_cart:
        raise HTTPException(status_code=409, detail="Customer already has a cart")
    cart = Cart(customer_id= cart_data.customer_id, total_price=0)
    db.add(cart)
    try:
        db.commit()
        db.refresh(cart)
        return cart
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Customer already has a cart")
# Load Cart
@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(cart_id:int, db: Session = Depends(get_db)):
    cart = db.get(Cart, cart_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart



# Add item to list
@router.post("/{cart_id}/items", response_model=CartItemResponse, status_code=201)
def add_cart_item(cart_id:int, item_data: CartItemCreate, db:Session = Depends(get_db)):
    cart = db.get(Cart, cart_id) # Choose the card which prepare to add an item
    statement = select(Cart).where(Cart.cart_id == cart_id).with_for_update()
    cart = db.scalars(statement).first()
    if cart is None: # Check if there is no card, raise an error to announce user
        raise HTTPException(status_code=404, detail="Cart not found!")
    try:
        # Add product to cart process
        response = httpx.get(f"{PRODUCT_SERVICE_URL}/products/{item_data.product_id}", timeout=5.0) # Take a product form produc-service,
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="product-service gone wrong") # Announce product-service go down
    
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Product not found!") # if there are no product, raise error   
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to get product information")
    product = response.json()

    #Check stock: if the product do not enough for request from client
    if item_data.quantity > product["quantity"]:
        raise HTTPException(status_code=400, detail="Not enough product quality")
    # Check if product already exists in cart

    #1. Take a cartitem to examine product id
    item_stmt = select(CartItem).where(
        CartItem.cart_id == cart_id,
        CartItem.product_id == item_data.product_id
    )
    cart_item = db.scalars(item_stmt).first()
    if cart_item: #if the item exists in a cart, do update its quantity.
        new_quantity = cart_item.quantity + item_data.quantity
        if new_quantity > product["quantity"]:
            raise HTTPException(status_code=400, detail="Not enough product quantity")
        cart_item.quantity = new_quantity
        cart_item.price = Decimal(str(product["price"]))
    else: # if the item does not exists in a cart, make a new CartItem.
        cart_item = CartItem(cart_id =cart_id,
                            product_id=item_data.product_id,
                            quantity = item_data.quantity,
                            price= Decimal(str(product["price"])))
        db.add(cart_item)
    db.flush()
    #Recalculate the total price again
    recalculate_cart_total(cart,db)
    try:    
        db.commit()
        db.refresh(cart_item)
        return cart_item
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrent request error on cart item")
@router.put("/{cart_id}/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(cart_id:int, 
                    item_id: int, 
                    item_data: CartItemUpdate, 
                    db: Session = Depends(get_db)):
    pass
    cart = db.get(Cart, cart_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found!")
    cart_item = db.get(CartItem, item_id)

    if cart_item is None or cart_item.cart_id != cart_id: #Check if the items is in the cart 
        raise HTTPException(status_code=404, detail="Cart item not found")
    try:
        response = httpx.get(f"{PRODUCT_SERVICE_URL}/products/{cart_item.product_id}", timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503,detail="Product-serivce gone wrong")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found!")
    product = response.json()

    if item_data.quantity > product["quantity"]:
        raise HTTPException(status_code=400, detail="Not enough product quantity")
    cart_item.quantity = item_data.quantity
    cart_item.price = Decimal(str(product["price"]))
    db.flush()
    statement = select(CartItem).where(
        CartItem.cart_id == cart_id
    )
    items = db.scalars(statement).all()
    cart.total_price = sum(item.price * item.quantity for item in items)
    db.commit()
    db.refresh(cart_item)
    return cart_item
# Delete item out of cart
@router.delete("/{cart_id}/items/{item_id}", status_code=204)
def delete_cart_item(cart_id:int, item_id:int,db:Session = Depends(get_db)):
    statement = select(Cart).where(Cart.cart_id == cart_id).with_for_update()
    cart = db.scalars(statement).first()
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart is not found!")
    cart_item = db.get(CartItem, item_id)
    if cart_item is None or cart_item.cart_id != cart_id:
        raise HTTPException(status_code=404, detail="Item is not found in your cart")
    db.delete(cart_item)
    db.flush()
    recalculate_cart_total(cart,db)
    db.commit()

@router.delete("/{cart_id}", status_code=204)
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.get(Cart, cart_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found!")
    db.delete(cart)
    db.commit()