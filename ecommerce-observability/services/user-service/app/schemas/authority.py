from pydantic import BaseModel, ConfigDict, EmailStr


class AuthorityCreate(BaseModel):

    email: EmailStr

    authority: str


class AuthorityResponse(BaseModel):

    email: EmailStr

    authority: str

    model_config = ConfigDict(from_attributes=True)