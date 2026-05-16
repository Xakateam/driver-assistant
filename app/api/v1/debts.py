from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUserDep
from app.api.v1.schemas import DebtOut, DebtPaymentOut, DebtSummaryOut
from app.modules.billing import service

router = APIRouter()


@router.get("", response_model=list[DebtOut])
async def list_debts(current_user: CurrentUserDep) -> list[DebtOut]:
    return service.list_debts(current_user.id)


@router.get("/summary", response_model=DebtSummaryOut)
async def get_debt_summary(current_user: CurrentUserDep) -> DebtSummaryOut:
    return service.get_debt_summary(current_user.id)


@router.post("/{debt_id}/pay", response_model=DebtPaymentOut)
async def pay_debt(
    debt_id: str,
    current_user: CurrentUserDep,
) -> DebtPaymentOut:
    result = service.pay_debt(current_user.id, debt_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Debt not found")
    return result
