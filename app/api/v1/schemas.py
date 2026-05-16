from datetime import datetime
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field


JsonScalar: TypeAlias = str | int | float | bool | None
Metadata: TypeAlias = dict[str, JsonScalar]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TripOut(ApiModel):
    id: str
    vehicle_id: str
    road_name: str
    started_at: datetime
    finished_at: datetime
    entry_point: str
    exit_point: str
    distance_km: float
    amount: float
    currency: str = "RUB"
    status: str


class BalanceOut(ApiModel):
    amount: float
    currency: str = "RUB"
    forecast_days_left: int | None


class TransactionOut(ApiModel):
    id: str
    type: str
    amount: float
    currency: str = "RUB"
    description: str
    created_at: datetime


class TopUpOut(ApiModel):
    status: str
    balance: BalanceOut
    transaction: TransactionOut


class AutopayOut(ApiModel):
    enabled: bool
    threshold_amount: float
    top_up_amount: float
    payment_method: str
    updated_at: datetime


class DebtOut(ApiModel):
    id: str
    trip_id: str
    road_name: str
    amount: float
    currency: str = "RUB"
    status: str
    due_text: str
    deep_link: str
    created_at: datetime


class DebtSummaryOut(ApiModel):
    count: int
    amount: float
    currency: str = "RUB"
    has_overdues: bool


class DeviceRegisterOut(ApiModel):
    id: str
    status: str
    platform: str
    created_at: datetime
    updated_at: datetime


class NotificationOut(ApiModel):
    id: str
    user_id: str
    type: str
    title: str
    body: str
    deep_link: str | None
    status: str
    created_at: datetime
    read_at: datetime | None
    action: str | None
    action_at: datetime | None
    metadata: Metadata = Field(default_factory=dict)


class NotificationActionOut(ApiModel):
    id: str
    action: str
    status: str
    action_at: datetime


class NotificationRuleOut(ApiModel):
    id: str
    type: str
    title: str
    enabled: bool
    channel: str
    placeholder: bool


class RecommendationOut(ApiModel):
    id: str
    user_id: str
    type: str
    category_id: int
    title: str
    body: str
    status: str
    priority: int
    predicted_ctr: float = Field(ge=0, le=1)
    created_at: datetime
    decided_at: datetime | None
    metadata: Metadata = Field(default_factory=dict)


class ForecastOut(ApiModel):
    month_expected_spend: float
    remaining_month_spend: float
    low_balance_risk: bool
    source: str


class DashboardUserOut(ApiModel):
    id: str
    phone: str
    segment: str
    ml_cluster_id: int | None
    ml_cluster_name: str | None
    predicted_spend_next_month: float | None
    favorite_route_name: str | None
    ml_updated_at: datetime | None


class PrimaryVehicleOut(ApiModel):
    id: str
    plate_number: str
    name: str | None
    is_primary: bool


class DashboardOut(ApiModel):
    user: DashboardUserOut
    balance: BalanceOut
    autopay: AutopayOut
    forecast: ForecastOut
    debts_summary: DebtSummaryOut
    primary_vehicle: PrimaryVehicleOut | None
    recent_trips: list[TripOut]
    notifications: list[NotificationOut]
    recommendations: list[RecommendationOut]
