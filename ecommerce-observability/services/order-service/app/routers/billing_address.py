from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.models.customer import Customer
from app.models.billing_address import BillingAddress
from app.schemas.billing_address import (BillingAddressUpdate, BillingAddressCreate, BillingAddressResponse)

router = APIRouter(prefix="/billing-addresses", tags=["Billing Addresses"])

@router.post("/customers/{customer_id}", response_model=BillingAddressResponse)
def create_billing_address(customer_id: int, data: BillingAddressCreate, db: Session = Depends(get_db)):

    customer = db.get(Customer, customer_id) # Get the customer who need to update their shipping address

    if customer is None: # check customer exists
        raise HTTPException(status_code=404, detail="Customer not found")
    address = BillingAddress( #add their address
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
        raise HTTPException(status_code=400, detail="Could not create billing address due to database constraint")

@router.get("/customers/{customer_id}", response_model=list[BillingAddressResponse])
def get_customer_billing_addresses(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer,customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found!")
    
    statement = select(BillingAddress).where(BillingAddress.customer_id == customer_id)
    return db.scalars(statement).all()

@router.get("/{address_id}", response_model= BillingAddressResponse)
def get_billing_address(address_id: int, db:Session = Depends(get_db)):
    address = db.get(BillingAddress,address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Billing address not found! Please add one.")
    return address

@router.put("/{address_id}", response_model=BillingAddressResponse)
def update_billing_address(address_id: int, data: BillingAddressUpdate, db: Session = Depends(get_db)):
    statement = select(BillingAddress).where(BillingAddress.id == address_id).with_for_update()
    address = db.scalars(statement).first()

    if address is None:
        raise HTTPException(status_code=404, detail="Billing address not found! Please add one.")
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
def delete_billing_address(address_id: int, db: Session = Depends(get_db)):
    statement = select(BillingAddress).where(BillingAddress.id == address_id).with_for_update()
    address = db.scalars(statement).first()
    if address is None:
        raise HTTPException(status_code=404, detail="Billing address not found!")
    try:
        db.delete(address)
        db.commit()
        return {"message" : "Billing address was deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete address associated with existing orders")
