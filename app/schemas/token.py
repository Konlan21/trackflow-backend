from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    jti: str
    type: str
    iat: int
    exp: int