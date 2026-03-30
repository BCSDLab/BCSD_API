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
    name: str
    department: str
    student_id: str
    school_email: str
    phone: str
    track: str
    grade: str


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    routing: str


class MeResponse(BaseModel):
    id: str
    email: str


class MessageResponse(BaseModel):
    message: str
