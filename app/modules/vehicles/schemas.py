from pydantic import BaseModel, ConfigDict, Field


class VehicleCreateIn(BaseModel):
    plate_number: str = Field(min_length=1, examples=["A123BC777"])
    name: str | None = Field(default=None, examples=["Kia Rio"])
    is_primary: bool = True


class VehicleUpdateIn(BaseModel):
    plate_number: str | None = Field(default=None, min_length=1, examples=["A123BC777"])
    name: str | None = Field(default=None, examples=["Kia Rio"])
    is_primary: bool | None = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plate_number: str
    name: str | None
    is_primary: bool
