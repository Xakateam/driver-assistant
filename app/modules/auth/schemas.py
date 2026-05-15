from pydantic import BaseModel, Field


class RequestCodeIn(BaseModel):
    phone: str = Field(min_length=1, examples=["+79991234567"])


class RequestCodeOut(BaseModel):
    message: str
    phone: str
    demo_code: str


class VerifyCodeIn(BaseModel):
    phone: str = Field(min_length=1, examples=["+79991234567"])
    code: str = Field(min_length=4, max_length=8, examples=["1234"])


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
