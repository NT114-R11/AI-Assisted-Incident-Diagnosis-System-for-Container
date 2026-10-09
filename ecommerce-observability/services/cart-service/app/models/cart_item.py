import uuid
from sqlalchemy import ForeignKey, Numeric, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
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
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carts.cart_id"),
        nullable=False
    )
    cart = relationship(
        "Cart",
        back_populates="items"
    )
