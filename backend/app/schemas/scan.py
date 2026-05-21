from datetime import datetime
from typing import Dict
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


#Requests
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-Z0-9_À-ſ]+$")
    password: str = Field(..., min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UpdateUsernameRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-Z0-9_À-ſ]+$")

#Responses
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    username: str
    created_at: datetime
    email_verified: bool

class TokenResponse(BaseModel):
    user: UserResponse
    message: str = "Giris basarili"


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: UUID
    user_id: UUID
    original_filename: str
    upload_date: datetime
    has_tumor: bool
    tumor_class: str
    confidence: float
    all_probabilities: Dict[str, float]

class ScanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: UUID
    original_filename: str
    upload_date: datetime
    has_tumor: bool
    tumor_class: str
    confidence: float


class MessageResponse(BaseModel):
    message: str    
    
