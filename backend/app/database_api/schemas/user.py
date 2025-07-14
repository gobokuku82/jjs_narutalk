from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str  # 'admin' or 'user'

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInfo(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True  # Pydantic v2에서 orm_mode 대신 사용 