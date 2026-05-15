from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUserDep
from app.modules.users.schemas import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUserDep) -> UserOut:
    return UserOut(id=current_user.id, phone=current_user.phone)
