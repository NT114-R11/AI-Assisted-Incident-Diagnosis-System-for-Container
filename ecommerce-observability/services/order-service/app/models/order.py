import uuid
from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String,Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.shipping_address import ShippingAddress
    from app.models.billing_address import BillingAddress
    from app.models.order_item import OrderItem

class Order(Base):
    __tablename__ ="orders"

    order_number: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )
    shipping_address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipping_addresses.id"),
        nullable=False
    )
    billing_address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_addresses.id"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING"
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
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )