from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.shipping_address import ShippingAddress
    from app.models.billing_address import BillingAddress

class Order(Base):
    __tablename__ ="orders"

    order_number: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    cart_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )
    shipping_address_id: Mapped[int] = mapped_column(
        ForeignKey("shipping_addresses.id"),
        nullable=False
    )
    billing_address_id: Mapped[int] = mapped_column(
        ForeignKey("billing_addresses.id"),
        nullable=False
    )
    status: Mapped[int] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="orders"
    )
    shipping_address: Mapped["ShippingAddress"] = relationship(
        "ShippingAddress",
        back_populates="orders"
    )
    billing_address: Mapped["BillingAddress"] = relationship(
        "BillingAddress",
        back_populates="orders"
    )