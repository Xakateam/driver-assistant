from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.api.v1.schemas import DebtOut, DebtSummaryOut
from app.modules.billing import service

router = APIRouter()


@router.get("", response_model=list[DebtOut])
async def list_debts(current_user: CurrentUserDep) -> list[DebtOut]:
    return service.list_debts(current_user.id)


@router.get("/summary", response_model=DebtSummaryOut)
async def get_debt_summary(current_user: CurrentUserDep) -> DebtSummaryOut:
    return service.get_debt_summary(current_user.id)
