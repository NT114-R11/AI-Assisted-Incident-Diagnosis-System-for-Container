from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.database.database import get_db
from app.models.seller import Seller
from app.schemas.seller import (SellerCreate, SellerResponse, SellerUpdate)

router = APIRouter(prefix="/sellers", tags=["Sellers"])

@router.post("/", response_model=SellerResponse)
def create_seller(data: SellerCreate, db: Session = Depends(get_db)):
    seller = Seller(**data.model_dump())
    db.add(seller)
    try:
        db.commit()
        db.refresh(seller)
        return seller
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code= 400, detail="Seller with this email already exists.")

@router.get("/", response_model=list[SellerResponse])
def get_sellers(db: Session = Depends(get_db)):
    statement = select(Seller)
    return db.scalars(statement).all()

@router.get("/{seller_id}", response_model=SellerResponse)
def get_seller(seller_id:int, db:Session = Depends(get_db)):
    seller = db.get(Seller, seller_id)

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found!")
    return seller

@router.put("/{seller_id}", response_model=SellerResponse)
def update_seller(seller_id: int, data: SellerUpdate, db: Session = Depends(get_db)):
    statement = select(Seller).where(Seller.id == seller_id).with_for_update()

    seller = db.scalars(statement).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found!")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr( seller,field,value)
    try:
        db.commit()
        db.refresh(seller)
        return seller
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Fail to update seller")

@router.delete("/{seller_id}")
def delete_seller(seller_id:int, db:Session = Depends(get_db)):
    statement = select(Seller).where(Seller.id == seller_id).with_for_update()
    seller = db.scalars(statement).first()

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found!")
    try:
        db.delete(seller)
        db.commit()
        return {"message" : "Seller deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete seller due to dependencies")

