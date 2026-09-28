from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
if TYPE_CHECKING:
    from app.models.authority import Authority


class User(Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        nullable=False
    )
    password: Mapped[str] = mapped_column(
        String(128),
        nullable= False
    )
    enable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    authorities: Mapped[list["Authority"]] = relationship(
        "Authority",
        back_populates="user",
        cascade="all, delete-orphan"
    )

