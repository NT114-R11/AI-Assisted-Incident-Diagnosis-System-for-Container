from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base

class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
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
        nullable=False
    )
    price: Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False,
        default=0.00
    )