from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: str
    phone: str = Field(examples=["+79991234567"])
    segment: str = "commuter"
