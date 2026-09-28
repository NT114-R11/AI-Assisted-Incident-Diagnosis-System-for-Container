from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.authority import Authority
from app.models.user import User
from app.schemas.authority import AuthorityCreate, AuthorityResponse
from app.security import require_authority

router = APIRouter(prefix="/authorities", tags=["Authorities"])


@router.post("/", response_model=AuthorityResponse, status_code=status.HTTP_201_CREATED)
def create_authority(data: AuthorityCreate, db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    user = db.get(User, data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")

    authority = Authority(
        email=data.email,
        authority=data.authority.upper()
    )
    db.add(authority)
    
    try:
        db.commit()
        db.refresh(authority)
        return authority
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User already has this authority"
        )


@router.get("/{email}", response_model=list[AuthorityResponse])
def get_user_authorities(email: str, db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    user = db.get(User, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")

    statement = select(Authority).where(Authority.email == email)
    return db.scalars(statement).all()


@router.delete("/{email}/{authority}")
def delete_authority(email: str, authority: str, db: Session = Depends(get_db), _: User = Depends(require_authority("ADMIN"))):
    statement = select(Authority).where(
        Authority.email == email,
        Authority.authority == authority.upper()
    )
    authority_record = db.scalars(statement).first()
    
    if not authority_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authority not found")

    db.delete(authority_record)
    db.commit()
    return {"message": "Authority deleted successfully"}