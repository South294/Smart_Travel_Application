from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=128)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)
