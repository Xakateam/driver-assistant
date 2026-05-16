from pydantic import BaseModel


class MlStatusOut(BaseModel):
    status: str
    model_version: str
    users_with_segments: int
    users_with_forecasts: int = 0
    users_total: int = 0
    runtime: dict[str, object] | None = None
