from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.shipping_address import ShippingAddress
    from app.models.billing_address import BillingAddress

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id : Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="customer"
    )
    shipping_addresses: Mapped[list["ShippingAddress"]] = relationship(
        "ShippingAddress",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    billing_addresses: Mapped[list["BillingAddress"]] = relationship(
        "BillingAddress",
        back_populates="customer",
        cascade="all, delete-orphan",
    )