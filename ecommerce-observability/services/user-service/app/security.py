import os
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User


SECRET_KEY = os.getenv("JWT_SECRET_KEY","CHANGE_THIS_IN_DOCKER_COMPOSE")
ALGORITHM = "HS256"


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")
security_scheme = HTTPBearer()
def hash_password(password:str) -> str:
    """Mapp password into utf-8 table """
    password_bytes = password.encode("utf-8")

    # start hashing
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return hashed.decode("utf-8")

def verify_password(plain_password:str, hashed_password:str) ->bool:

    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    
def create_access_token(email: str, authorities: list[str]) -> str:
    expired = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": email,
        "authorities": authorities,
        "exp": expired
    }

    return jwt.encode(payload,SECRET_KEY, algorithm=ALGORITHM)

# def get_current_user (token: str = Depends(oauth2_schema), db: Session= Depends(get_db)) -> User:
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme),db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.get(User,email)
    if not user:
        raise credentials_exception
    if not user.enable:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return user

def require_authority(authority: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:

        authorities = {item.authority for item in current_user.authorities}

        if authority not in authorities:
            raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail="Insufficient authority")
        
        return current_user
    return checker