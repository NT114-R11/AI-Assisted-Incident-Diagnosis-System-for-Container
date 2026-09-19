from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.models.customer import Customer
from app.models.shipping_address import ShippingAddress
from app.schemas.shipping_address import (ShippingAddressCreate, ShippingAddressResponse, ShippingAddressUpdate)

router = APIRouter(prefix="/shipping-addresses", tags=["Shipping Addresses"])

@router.post("/customers/{customer_id}", response_model=ShippingAddressResponse)
def create_shipping_address(customer_id: int, data: ShippingAddressCreate, db: Session = Depends(get_db)):

    customer = db.get(Customer, customer_id) # Get the customer who need to update their shipping address

    if customer is None: # check customer exists
        raise HTTPException(status_code=404, detail="Customer not found")
    address = ShippingAddress( #add their address
        customer_id = customer_id,
        address = data.address,
        city = data.city
    )
    db.add(address)
    try:
        db.commit()
        db.refresh(address)
        return address
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create shipping address due to database constraint")


@router.get("/customers/{customer_id}", response_model=list[ShippingAddressResponse])
def get_customer_shipping_addresses(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer,customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found!")
    
    statement = select(ShippingAddress).where(ShippingAddress.customer_id == customer_id)
    return db.scalars(statement).all()

@router.get("/{address_id}", response_model= ShippingAddressResponse)
def get_shipping_address(address_id: int, db:Session = Depends(get_db)):
    address = db.get(ShippingAddress,address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Shipping address not found! Please add one.")
    return address

@router.put("/{address_id}", response_model=ShippingAddressResponse)
def update_shipping_address(address_id: int, data: ShippingAddressUpdate, db: Session = Depends(get_db)):
    statement = select(ShippingAddress).where(ShippingAddress.id == address_id).with_for_update()
    address = db.scalars(statement).first()

    if address is None:
        raise HTTPException(status_code=404, detail="Shipping address not found! Please add one.")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address,field, value)
    try:
        db.commit()
        db.refresh(address)
        return address
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update address")
@router.delete("/{address_id}")
def delete_shipping_address(address_id: int, db: Session = Depends(get_db)):
    statement = select(ShippingAddress).where(ShippingAddress.id == address_id).with_for_update()
    address = db.scalars(statement).first()
    if address is None:
        raise HTTPException(status_code=404, detail="Shipping address not found!")
    try:
        db.delete(address)
        db.commit()
        return {"message" : "Shipping address was deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete address associated with existing orders")
