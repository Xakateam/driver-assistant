from pydantic import BaseModel


class MlStatusOut(BaseModel):
    status: str
    model_version: str
    users_with_segments: int
