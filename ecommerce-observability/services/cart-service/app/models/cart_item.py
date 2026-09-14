from sqlalchemy import ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0   
    )
    price: Mapped[float] = mapped_column(
        Numeric,
        nullable=False,
        default=0.00
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.cart_id"),
        nullable=False
    )
    cart = relationship(
        "Cart",
        back_populates="items"
    )
