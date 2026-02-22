from app.schemas.common import BaseSchema


class LoginRequest(BaseSchema):

    username: str
    password: str


class TokenResponse(BaseSchema):

    access_token: str
    token_type: str = "bearer"
