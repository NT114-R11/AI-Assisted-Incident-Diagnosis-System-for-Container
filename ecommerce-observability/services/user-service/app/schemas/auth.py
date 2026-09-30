from pydantic import BaseModel, EmailStr,Field,ConfigDict

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password at least 6 characters")

class UserResponse(BaseModel):
    email: str
    enable: bool
    model_config = ConfigDict(from_attributes=True)
