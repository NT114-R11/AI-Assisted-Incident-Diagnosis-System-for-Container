from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING: 
    from app.models.customer import Customer
    from app.models.order import Order

class ShippingAddress(Base):
    __tablename__ ="shipping_addresses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable= False
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="shipping_addresses"
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="shipping_address"
    )