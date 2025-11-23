from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    login: EmailStr
    project_id: UUID
    env: str = Field(..., pattern="^(prod|preprod|stage)$")
    domain: str = Field(default="regular", pattern="^(canary|regular)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    locktime: Optional[int] = None


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    locktime: Optional[int]

    class Config:
        from_attributes = True


class UserLockRequest(BaseModel):
    user_id: UUID

class UserLockResponse(BaseModel):
    success: bool
    message: str
    locktime: Optional[int] = None