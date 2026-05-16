from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list[JsonScalar] | dict[str, JsonScalar]
Metadata: TypeAlias = dict[str, JsonValue]


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
    status: Literal["paid", "debt"]


class BalanceOut(ApiModel):
    amount: float
    currency: str = "RUB"
    forecast_days_left: int | None


class TransactionOut(ApiModel):
    id: str
    type: Literal["top_up", "trip_charge", "debt"]
    amount: float
    currency: str = "RUB"
    description: str
    created_at: datetime


class TopUpOut(ApiModel):
    status: Literal["success"]
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
    status: Literal["overdue"]
    due_text: str
    deep_link: str
    created_at: datetime


class DebtSummaryOut(ApiModel):
    count: int
    amount: float
    currency: str = "RUB"
    has_overdues: bool


class DebtPaymentOut(ApiModel):
    status: Literal["paid"]
    debt_id: str
    balance: BalanceOut
    debts_summary: DebtSummaryOut
    transaction: TransactionOut


class DeviceRegisterOut(ApiModel):
    id: str
    status: Literal["registered"]
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
    status: Literal["unread", "read"]
    created_at: datetime
    read_at: datetime | None
    action: str | None
    action_at: datetime | None
    metadata: Metadata = Field(default_factory=dict)


class NotificationActionOut(ApiModel):
    id: str
    action: str
    status: Literal["saved"]
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
    status: Literal["pending", "accepted", "declined"]
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


class FeedItemOut(ApiModel):
    id: str
    kind: Literal["trip", "overdue", "payment"]
    title: str
    subtitle: str
    amount: float
    currency: str = "RUB"
    status: Literal["paid", "debt", "success"]
    occurred_at: datetime
    deep_link: str
    metadata: Metadata = Field(default_factory=dict)


class FeedOut(ApiModel):
    items: list[FeedItemOut]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)


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
