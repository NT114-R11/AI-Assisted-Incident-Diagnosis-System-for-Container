from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.security import get_current_user, hash_password, require_authority

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        email=data.email,
        password=hash_password(data.password),
        enable=data.enable
    )
    db.add(user)

    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User with this email already exists."
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    statement = select(User)
    return db.scalars(statement).all()


@router.get("/{email}", response_model=UserResponse)
def get_user(email: str, db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    user = db.get(User, email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")
    return user


@router.put("/{email}", response_model=UserResponse)
def update_user(email: str, data: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    user = db.get(User, email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")

    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    elif "password" in update_data:
        del update_data["password"]

    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user")


@router.delete("/{email}")
def delete_user(email: str, db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    statement = select(User).where(User.email == email).with_for_update()
    user = db.scalars(statement).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete user")