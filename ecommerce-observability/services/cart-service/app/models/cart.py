import uuid
from sqlalchemy import Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base

class Cart(Base): 
    __tablename__ = "carts"
    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True
    )

    total_price: Mapped[float] = mapped_column(
        Numeric(12,2),
        default=0,
        nullable=False
    )

    items: Mapped[list["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade= "all, delete-orphan"
    )