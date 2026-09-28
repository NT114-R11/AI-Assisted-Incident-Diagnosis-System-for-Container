from pydantic import BaseModel, ConfigDict, EmailStr
from app.schemas.authority import AuthorityResponse

class UserBase(BaseModel):

    email: EmailStr


class UserCreate(UserBase):

    password: str

    enable: bool = True


class UserUpdate(BaseModel):

    password: str | None = None

    enable: bool | None = None


class UserResponse(UserBase):

    enable: bool
    authorities: list[AuthorityResponse] = []
    model_config = ConfigDict(from_attributes=True)