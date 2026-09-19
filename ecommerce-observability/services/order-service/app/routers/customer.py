from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.customer import Customer
from app.schemas.customer import (CustomerCreate, CustomerResponse, CustomerUpdate)

router = APIRouter(prefix="/customers", tags=["Customers"])

#Create a customer
@router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    statement = select(Customer).where(Customer.email == customer.email)
    existing_customer = db.scalars(statement).first()

    if existing_customer:
        raise HTTPException(status_code=409, detail="Email is already exists")
    new_customer = Customer(
        name = customer.name,
        email = customer.email,
        phone = customer.phone
    )
    try:
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        return new_customer
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email is already exists")

# Get customer
@router.get("/", response_model=list[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
    result = db.execute(select(Customer))
    return result.scalars().all()

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db:Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found!")
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id:int, data: CustomerUpdate, db:Session = Depends(get_db)):
    statement = select(Customer).where(Customer.customer_id == customer_id).with_for_update()
    customer = db.scalars(statement).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found!")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer,field,value)
    try:
        db.commit()
        db.refresh(customer)
        return customer
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists!")

@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db:Session = Depends(get_db)):
    statement = select(Customer).where(Customer.customer_id == customer_id).with_for_update()
    customer = db.scalars(statement).first()
    if customer is None:
        raise HTTPException(status_code=404,detail= "Customer does not exist")
    try:
        db.delete(customer)
        db.commit()
        return {"message": "Customer deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete customer with active orders or addresses.")
    