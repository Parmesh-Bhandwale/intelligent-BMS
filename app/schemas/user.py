from pydantic import EmailStr
from app.schemas.common import BaseSchema


class UserBase(BaseSchema):

    username: str
    email: EmailStr


class UserCreate(UserBase):

    password: str


class UserResponse(UserBase):

    id: int
    is_active: bool = True
    role: str = "user"
