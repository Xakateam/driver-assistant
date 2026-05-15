from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.modules.billing import service

router = APIRouter()


@router.get("")
async def list_debts(current_user: CurrentUserDep) -> list[dict[str, object]]:
    return service.list_debts(current_user.id)


@router.get("/summary")
async def get_debt_summary(current_user: CurrentUserDep) -> dict[str, object]:
    return service.get_debt_summary(current_user.id)
