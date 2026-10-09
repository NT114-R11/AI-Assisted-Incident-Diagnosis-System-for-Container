import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.database import Base


if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order import Order


class BillingAddress(Base):
    __tablename__ = "billing_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="billing_addresses"
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="billing_address"
    )