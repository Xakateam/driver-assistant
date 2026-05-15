from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.modules.ml import service

router = APIRouter()


@router.post("/recalculate-me")
async def recalculate_me(current_user: CurrentUserDep) -> dict[str, object]:
    return service.recalculate_user(current_user.id)
