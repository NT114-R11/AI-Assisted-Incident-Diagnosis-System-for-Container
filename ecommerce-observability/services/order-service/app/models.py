from sqlalchemy import String, Integer, Numeric

from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id")
    )
    cart_id : Mapped[int] = mapped_column(
        ForeignKey("carts.cart_id")
    )

    quantity: Mapped[int] = mapped_column(Integer)

    total_price: Mapped[float] = mapped_column(Numeric(10,2))

    status: Mapped[str] = mapped_column(String(50), default="PENDING")

    