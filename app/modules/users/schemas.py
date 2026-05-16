from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: str
    phone: str = Field(examples=["+79991234567"])
    segment: str = "commuter"
    ml_cluster_id: int | None = None
    ml_cluster_name: str | None = None
    predicted_spend_next_month: float | None = None
    favorite_route_name: str | None = None
    ml_model_version: str | None = None
    ml_updated_at: str | None = None
