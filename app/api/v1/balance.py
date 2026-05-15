from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUserDep
from app.modules.billing import service

router = APIRouter()


class TopUpIn(BaseModel):
    amount: Decimal = Field(gt=0, examples=[1000])
    payment_method: str = Field(default="demo_card")


@router.get("")
async def get_balance(current_user: CurrentUserDep) -> dict[str, object]:
    return service.get_balance(current_user.id)


@router.post("/top-up")
async def top_up(
    payload: TopUpIn,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    return service.top_up(
        user_id=current_user.id,
        amount=float(payload.amount),
        payment_method=payload.payment_method,
    )


@router.get("/transactions")
async def get_transactions(current_user: CurrentUserDep) -> list[dict[str, object]]:
    return service.list_transactions(current_user.id)
