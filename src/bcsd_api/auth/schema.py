from pydantic import BaseModel


class LoginRequest(BaseModel):
    google_token: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    email: str


class ConfirmEmailRequest(BaseModel):
    email: str
    code: str


class ConfirmEmailResponse(BaseModel):
    verified: bool


class RegisterRequest(BaseModel):
    google_token: str
    school_email: str
    phone: str
    firebase_token: str
    track: str


class MessageResponse(BaseModel):
    message: str
