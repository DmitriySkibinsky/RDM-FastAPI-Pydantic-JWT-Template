from pydantic import BaseModel

from schemas.base import CamelModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(CamelModel):
    id: int
    username: str
    role: int


class Token(CamelModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
