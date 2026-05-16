from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.api.v1.schemas import DashboardOut
from app.modules.dashboard.service import get_dashboard as build_dashboard

router = APIRouter()


@router.get("", response_model=DashboardOut)
async def get_dashboard(current_user: CurrentUserDep) -> DashboardOut:
    return build_dashboard(current_user.id)
