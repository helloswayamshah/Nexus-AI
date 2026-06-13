from pydantic import BaseModel, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    display_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
