from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class Authority(Base):
    __tablename__ = "authorities"

    email: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.email"),
        primary_key=True
    )
    authority: Mapped[str] = mapped_column(
        String(50),
        primary_key=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="authorities"
    )

    """
    Because a single user can have multiple roles, compose 2 primary key
    """