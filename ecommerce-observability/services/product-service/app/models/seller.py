import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column ,relationship 
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.product import Product
class Seller(Base):
    __tablename__ = "sellers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    shop_name: Mapped[str] = mapped_column(
        String(50),
        nullable= False
    )
    user_email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    phone: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    products: Mapped[list["Product"]] = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
