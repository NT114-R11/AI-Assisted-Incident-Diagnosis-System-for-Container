from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.get("/",response_model= list[ProductResponse])
def get_products(page: int = Query(default=1, ge=1), # Defalt page is 1
                per_page: int= Query(default=10, ge=1, le=100), # Set a default number of item, user can get in a time.
                db: Session = Depends(get_db)):
    skip = (page - 1) * per_page #Calculate the item skip in a page
    statement = (select(Product).order_by(Product.product_id).offset(skip).limit(per_page))
    products = db.scalars(statement).all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail='Product not found!')
    
    return product

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product_data: ProductCreate, db:Session = Depends(get_db)):
    product = Product(**product_data.model_dump()) ## spread out the object
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}", response_model= ProductResponse)
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    statement = select(Product).where(Product.product_id == product_id).with_for_update()
    product = db.scalars(statement).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found!")
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product,field, value)
    try:
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Update conflicts with existing product data")


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id:int, db:Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found!")
    db.delete(product)
    db.commit()
