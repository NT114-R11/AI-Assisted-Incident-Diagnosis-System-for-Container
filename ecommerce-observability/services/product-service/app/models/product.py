import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.seller import Seller

class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    product_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    categories: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    price: Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False,
        default=0.00
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False
    )
    seller: Mapped["Seller"] = relationship(
        "Seller",
        back_populates="products"
    )

    