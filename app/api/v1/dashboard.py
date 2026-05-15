from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.modules.dashboard.service import get_dashboard as build_dashboard

router = APIRouter()


@router.get("")
async def get_dashboard(current_user: CurrentUserDep) -> dict[str, object]:
    return build_dashboard(current_user.id)
