import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select

from app.database.database import Base, SessionLocal, engine
from app.models import User, Authority
from app.routers import auth, authority, user
from app.security import hash_password

TITLE = "User Service"
VERSION = "1.0.0"


def create_bootstrap_admin():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_pw = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_pw:
        return

    db = SessionLocal()
    try:
        user = db.get(User, admin_email)
        if not user:
            user = User(
                email=admin_email,
                password=hash_password(admin_pw),
                enable=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        admin_authority = db.scalars(
            select(Authority).where(
                Authority.email == admin_email,
                Authority.authority == "ADMIN"
            )
        ).first()

        if not admin_authority:
            db.add(Authority(
                email=admin_email,
                authority="ADMIN"
            ))
            db.commit()
    except Exception as e:
        print(f"[Warning] Bootstrap admin failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto create tables if not exists
    Base.metadata.create_all(bind=engine)
    # Create initial admin account on startup
    create_bootstrap_admin()
    yield


app = FastAPI(
    title=TITLE,
    version=VERSION,
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(authority.router)


@app.get("/")
def root():
    return {
        "service": "User service", 
        "status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "user-service"
    }