from sqlalchemy import Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

class Cart(Base): 
    __tablename__ = "carts"
    cart_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer,
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