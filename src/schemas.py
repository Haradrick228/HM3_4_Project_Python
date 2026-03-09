from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: HttpUrl

class LinkResponse(BaseModel):
    id: int
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class LinkStats(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    access_count: int
    last_accessed: Optional[datetime]
    expires_at: Optional[datetime]

class ExpiredLinkResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expired_at: datetime
    total_accesses: int

    class Config:
        from_attributes = True
