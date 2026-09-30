from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.database import get_db
from app.models.user import User
from app.models.authority import Authority
from app.schemas.auth import (LoginRequest, TokenResponse,RegisterRequest, UserResponse)
from app.security import hash_password
from app.security import (create_access_token, verify_password)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(data:LoginRequest, db:Session = Depends(get_db)):
    statement = select(User).options(selectinload(User.authorities)).where(User.email == data.email)
    user = db.scalars(statement).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    if not user.enable:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    
    
    authorities = [item.authority for item in user.authorities]
    token = create_access_token(email=user.email, authorities=authorities)
    return TokenResponse(access_token=token)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(User.email == data.email))

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
    
    new_user = User(
        email=data.email,
        password=hash_password(data.password),
        enable=True
    )

    default_authority = db.scalar(select(Authority).where(Authority.authority == "USER"))
    if default_authority:
        new_user.authorities.append(default_authority)

    db.add(new_user)
    db.commit()
    # Get authorities
    statement = select(User).options(selectinload(User.authorities)).where(User.email == data.email)
    created_user = db.scalar(statement)

    return created_user